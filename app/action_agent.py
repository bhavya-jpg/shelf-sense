"""Action note (BLUEPRINT §8, Milestone 3).

The deterministic template is the guaranteed path. On top of it, one AMD call may reword the
actions: it receives only validated facts and returns wording only (a summary sentence, an
order, one instruction per item). Every product name, count, status and dollar figure in the
final note is rendered by code, and the model's wording is validated before it is used.
"""

import json
import logging
import re
import time
from typing import Callable, Optional

from pydantic import BaseModel, Field, ValidationError

from app import amd_client
from app.calculator import count_inconsistency, exposure_label, validate_unit_value
from app.config import Settings
from app.models import ActionNote, ComplianceResult, ExposureSummary, RevenueImpact, Spec

log = logging.getLogger(__name__)

NOTE_TIMEOUT_S = 30
NOTE_MAX_TOKENS = 400
CATEGORY_ORDER = ("restock", "reposition", "review")

UNVERIFIED_BASIS = (
    "This figure is calculated from AI-estimated counts that have not been independently verified; "
    "check the shelf before relying on it."
)

UNAVAILABLE_TEXT = (
    "No action note: the inspection result could not be validated, so there are no verified "
    "findings to act on. Re-take the photo or check the shelf manually."
)

ChatFn = Callable[..., str]


def _usd(amount: float) -> str:
    return f"${amount:,.2f}"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def category(impact: RevenueImpact) -> Optional[str]:
    """restock / reposition / review, or None if the item needs no attention."""
    if impact.exposure_status == "unresolved":
        return "reposition" if impact.status == "misplaced" else "review"
    if impact.status in ("missing", "partial"):
        return "restock"
    return None


class _Entry(BaseModel):
    impact: RevenueImpact
    category: str
    facts: str
    instruction: str


def _entries(result: ComplianceResult, summary: ExposureSummary, spec: Spec) -> list[_Entry]:
    spec_items = {i.item_id: i for i in spec.items}
    checks = {c.item_id: c for c in result.items}
    entries = []
    for impact in summary.items:
        cat = category(impact)
        if cat is None:
            continue
        label = impact.label
        counts = f"{impact.detected_count} of {impact.expected_count} expected detected"
        value_problem = validate_unit_value(spec_items[impact.item_id].unit_margin_usd)[1]
        if impact.potential_exposure_usd is not None:
            bound = f"potential exposure up to {_usd(impact.potential_exposure_usd)} (upper bound)"
        else:
            bound = f"upper bound unavailable ({value_problem})"

        if cat == "restock":
            state = "missing" if impact.status == "missing" else "partially stocked"
            parts = [f"{state} ({counts})"]
            if impact.units_missing:
                parts.append(f"{_plural(impact.units_missing, 'unit')} short")
            if impact.exposure_status == "estimated":
                money = "margin at risk" if summary.counts_verified else "estimated margin at risk"
                parts.append(f"{money} {_usd(impact.estimated_exposure_usd)}")
            else:
                parts.append(f"margin at risk unavailable ({value_problem})")
            units = f" with {_plural(impact.units_missing, 'unit')}" if impact.units_missing else ""
            instruction = f"Restock {label}{units}."
        elif cat == "reposition":
            parts = [f"reported in the wrong position ({counts})", "not included in the estimate", bound]
            instruction = f"Move {label} back to its planned position."
        else:
            reason = (
                "the inspection gave no usable observation"
                if impact.status == "needs_review"
                else f"the counts contradict the reported status: {count_inconsistency(checks[impact.item_id])}"
            )
            parts = [f"needs manual review: {reason}", "not included in the estimate", bound]
            instruction = f"Check {label} on the shelf in person and record what is there."

        entries.append(_Entry(impact=impact, category=cat, facts="; ".join(parts), instruction=instruction))

    return sorted(entries, key=lambda e: CATEGORY_ORDER.index(e.category))  # stable: spec order within a category


def _money_lines(summary: ExposureSummary, entries: list[_Entry]) -> list[str]:
    lines = []
    label, amount = exposure_label(summary.counts_verified), _usd(summary.estimated_exposure_usd)
    if summary.estimate_is_complete:
        lines.append(f"{label}: {amount}.")
    else:
        names = [e.impact.label for e in entries if e.impact.exposure_status == "unavailable"]
        lines.append(
            f"{label}: at least {amount}. "
            f"Not calculable for {_join(names)} because the unit value is unavailable."
        )
    if not summary.counts_verified:
        lines.append(UNVERIFIED_BASIS)
    unresolved = [e.impact.label for e in entries if e.impact.exposure_status == "unresolved"]
    if unresolved:
        bound = f"Unresolved potential exposure (upper bound): {_usd(summary.unresolved_potential_usd)}"
        if not summary.unresolved_potential_is_complete:
            bound += ", excluding items whose unit value is unavailable"
        lines.append(f"Unresolved, not included in the estimate: {_join(unresolved)}. {bound}.")
        if summary.estimated_exposure_usd == 0:
            lines.append(
                "An estimate of $0.00 does not mean there is no risk: the unresolved items still need checking."
            )
    return lines


def _next_step(entries: list[_Entry]) -> str:
    counts = {c: sum(e.category == c for e in entries) for c in CATEGORY_ORDER}
    steps = []
    if counts["restock"]:
        steps.append(f"restock {_plural(counts['restock'], 'item')}")
    if counts["reposition"]:
        steps.append(f"move {_plural(counts['reposition'], 'misplaced item')}")
    if counts["review"]:
        steps.append(f"check {_plural(counts['review'], 'item')} in person")
    return f"Next: {_join(steps)}, then re-run the inspection to check the shelf again."


def _render(spec: Spec, summary: ExposureSummary, entries: list[_Entry], ai_summary: Optional[str] = None) -> str:
    if not entries:
        return (
            f"{spec.location}: all {_plural(len(summary.items), 'item')} present as expected. "
            f"No action required.\n{exposure_label(summary.counts_verified)}: {_usd(summary.estimated_exposure_usd)}."
            + ("" if summary.counts_verified else f"\n{UNVERIFIED_BASIS}")
        )
    headline = f"{spec.location}: {_plural(len(entries), 'item')} need{'s' if len(entries) == 1 else ''} attention."
    lines = [headline]
    if ai_summary:
        lines.append(ai_summary)
    lines.append("")
    lines += [f"- {e.impact.label}: {e.facts}. Action: {e.instruction}" for e in entries]
    lines.append("")
    lines += _money_lines(summary, entries)
    lines.append(_next_step(entries))
    return "\n".join(lines)


def _check_inputs(result: ComplianceResult, summary: ExposureSummary, spec: Spec) -> None:
    if not (result.spec_id == summary.spec_id == spec.spec_id):
        raise ValueError("result, exposure summary and spec refer to different specs")


def template_note(result: ComplianceResult, summary: ExposureSummary, spec: Spec) -> ActionNote:
    """Deterministic note built only from validated facts. No model call."""
    _check_inputs(result, summary, spec)
    if not result.items or not summary.calculation_available:
        return ActionNote(text=UNAVAILABLE_TEXT, source="unavailable")
    entries = _entries(result, summary, spec)
    return ActionNote(
        text=_render(spec, summary, entries),
        source="template",
        item_actions={e.impact.item_id: e.instruction for e in entries},
    )


# --- AMD-worded note ------------------------------------------------------------

NOTE_PROMPT = """You are writing the action list for a store employee after an automated shelf inspection. The facts below are final and were computed by software. Do not change, recompute or restate them.

Write:
- "summary": one short sentence telling the employee what to focus on first.
- "actions": one entry per item below, ordered by what the employee should handle first (highest estimated margin at risk first, then repositioning, then manual checks). Each "instruction" is one short, plain imperative sentence (at most 25 words) saying what to do for that item.

Rules:
- Use only the item_id values given, and include every item exactly once.
- Do NOT write any digits, number words, counts, prices, percentages or currency. The software adds all numbers.
- Do not name products. The software adds the product name in front of each instruction.
- Do not guess causes (such as theft or supplier problems) or claim anything not in the facts.
- Do not say that no action is needed or that the shelf is compliant.

Return ONLY a JSON object, no markdown and no other text:
{"summary": "...", "actions": [{"item_id": "...", "instruction": "..."}]}

Facts:
"""

_DIGITS_OR_MONEY = re.compile(r"\d|[$€£¥%]|\b(usd|dollars?|cents?|percent)\b", re.IGNORECASE)
_NUMBER_WORDS = re.compile(
    r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|dozens?|hundreds?)\b",
    re.IGNORECASE,
)
_NO_ACTION = re.compile(
    r"no action|nothing to do|no issues?|all (good|clear|fine)|fully stocked|\bcompliant\b", re.IGNORECASE
)


class _AIAction(BaseModel):
    item_id: str
    instruction: str = Field(min_length=3, max_length=200)


class _AINote(BaseModel):
    summary: str = Field(min_length=3, max_length=300)
    actions: list[_AIAction]


def validate_ai_note(raw: str, expected_ids: list[str]) -> _AINote:
    """Parse and check the model's wording. Raises ValueError if it is unusable."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end < start:
        raise ValueError("no JSON object in reply")
    try:
        note = _AINote.model_validate(json.loads(raw[start : end + 1]))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"reply does not match the note schema: {str(exc)[:200]}") from exc

    ids = [a.item_id for a in note.actions]
    if len(ids) != len(set(ids)) or set(ids) != set(expected_ids):
        raise ValueError(f"actions cover {sorted(ids)}, expected exactly {sorted(expected_ids)}")
    for text in [note.summary] + [a.instruction for a in note.actions]:
        if _DIGITS_OR_MONEY.search(text) or _NUMBER_WORDS.search(text):
            raise ValueError(f"model wording contains numbers or money: {text!r}")
        if _NO_ACTION.search(text):
            raise ValueError(f"model wording claims no action is needed: {text!r}")
    return note


def _facts_payload(spec: Spec, entries: list[_Entry]) -> str:
    return json.dumps(
        {
            "location": spec.location,
            "items_needing_attention": [
                {"item_id": e.impact.item_id, "product": e.impact.label, "category": e.category, "facts": e.facts}
                for e in entries
            ],
        },
        indent=2,
    )


def generate_action_note(
    result: ComplianceResult,
    summary: ExposureSummary,
    spec: Spec,
    settings: Optional[Settings],
    *,
    chat: ChatFn = amd_client.chat_completion,
) -> ActionNote:
    """AMD-worded note when possible; otherwise the deterministic template, labelled as such."""
    template = template_note(result, summary, spec)
    if template.source == "unavailable":
        return template
    if settings is None:
        return template
    if settings.mock_mode:
        return template.model_copy(update={"fallback_reason": "MOCK_MODE is on; no AMD call was made"})

    entries = _entries(result, summary, spec)
    if not entries:
        return template.model_copy(update={"fallback_reason": "nothing needs attention; no AMD call was made"})

    messages = [{"role": "user", "content": NOTE_PROMPT + _facts_payload(spec, entries)}]
    started = time.perf_counter()
    try:
        raw = chat(settings, messages, max_tokens=NOTE_MAX_TOKENS, timeout_s=NOTE_TIMEOUT_S)
        ai = validate_ai_note(raw, [e.impact.item_id for e in entries])
    except Exception as exc:  # any failure of the optional AMD wording falls back to the template (§8)
        reason = f"{type(exc).__name__}: {str(exc)[:200]}"
        log.warning("AMD action note unusable, using template: %s", reason)
        return template.model_copy(
            update={"ai_attempted": True, "fallback_reason": reason, "model_name": settings.model_name}
        )

    by_id = {e.impact.item_id: e for e in entries}
    ordered = [by_id[a.item_id].model_copy(update={"instruction": a.instruction}) for a in ai.actions]
    return ActionNote(
        text=_render(spec, summary, ordered, ai_summary=ai.summary),
        source="amd",
        item_actions={e.impact.item_id: e.instruction for e in ordered},
        ai_attempted=True,
        model_name=settings.model_name,
        latency_s=round(time.perf_counter() - started, 2),
    )
