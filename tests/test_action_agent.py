"""Milestone 3: action note. AMD wording is MOCKED here; the live path is checked separately."""

import dataclasses
import json
import re

import pytest

from app.action_agent import UNAVAILABLE_TEXT, generate_action_note, template_note, validate_ai_note
from app.calculator import summarize_exposure
from app.models import ComplianceResult, InspectionError
from tests.conftest import make_result, spec_with

STOCKOUT = {"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("partial", 2)}
MISPLACED = {"brand_b_cereal": ("misplaced", 4)}


def note_for(spec, overrides=None, settings=None, chat=None, result=None):
    result = result or make_result(overrides)
    summary = summarize_exposure(result, spec)
    if chat is None:
        return template_note(result, summary, spec), summary
    return generate_action_note(result, summary, spec, settings, chat=chat), summary


class FakeChat:
    def __init__(self, reply=None, exc=None):
        self.reply, self.exc, self.calls = reply, exc, []

    def __call__(self, settings, messages, **kwargs):
        self.calls.append((messages, kwargs))
        if self.exc:
            raise self.exc
        return self.reply


def ai_reply(actions, summary="Start with the empty facings, then fix the display."):
    return json.dumps({"summary": summary, "actions": [{"item_id": i, "instruction": t} for i, t in actions]})


def forbid_call(*a, **kw):
    raise AssertionError("no AMD call expected")


# --- template: the five statuses --------------------------------------------

def test_present_compliant(spec):
    note, _ = note_for(spec)
    assert note.source == "template"
    assert note.text == (
        "Aisle 4 endcap: all 3 items present as expected. No action required.\n"
        "Estimated Margin at Risk (Unverified): $0.00.\n"
        "This figure is calculated from AI-estimated counts that have not been independently verified; "
        "check the shelf before relying on it."
    )


def test_missing_and_partial(spec):
    note, _ = note_for(spec, STOCKOUT)
    t = note.text
    assert t.startswith("Aisle 4 endcap: 2 items need attention.")
    assert ("- Brand A Cereal Box: missing (0 of 6 expected detected); 6 units short; "
            "estimated margin at risk $7.20. Action: Restock Brand A Cereal Box with 6 units.") in t
    assert ("- Brand B Cereal Box: partially stocked (2 of 4 expected detected); 2 units short; "
            "estimated margin at risk $2.00. Action: Restock Brand B Cereal Box with 2 units.") in t
    assert "Estimated Margin at Risk (Unverified): $9.20." in t
    assert "Next: restock 2 items, then re-run the inspection to check the shelf again." in t
    assert "Unresolved" not in t and "No action required" not in t


def test_misplaced(spec):
    note, _ = note_for(spec, MISPLACED)
    t = note.text
    assert t.startswith("Aisle 4 endcap: 1 item needs attention.")
    assert "reported in the wrong position (4 of 4 expected detected)" in t
    assert "Action: Move Brand B Cereal Box back to its planned position." in t
    assert "Unresolved, not included in the estimate: Brand B Cereal Box. Unresolved potential exposure (upper bound): $4.00." in t
    assert "Next: move 1 misplaced item, then re-run" in t


def test_needs_review(spec):
    note, _ = note_for(spec, {"promo_sign": ("needs_review", 0)})
    t = note.text
    assert "Promo Sign: needs manual review: the inspection gave no usable observation" in t
    assert "Action: Check Promo Sign on the shelf in person" in t
    assert "Next: check 1 item in person" in t


def test_zero_estimate_with_unresolved_is_not_no_action(spec):
    note, summary = note_for(spec, MISPLACED)
    assert summary.estimated_exposure_usd == 0.0
    assert "No action required" not in note.text
    assert "Estimated Margin at Risk (Unverified): $0.00." in note.text
    assert "An estimate of $0.00 does not mean there is no risk" in note.text


def test_inconsistent_counts_become_manual_review(spec):
    note, _ = note_for(spec, {"brand_a_cereal": ("missing", 3)})
    assert "the counts contradict the reported status: status 'missing' but 3 detected" in note.text
    assert "Restock Brand A" not in note.text  # no confirmed restock claim on contradictory data


def test_all_categories_order_and_next_step(spec):
    note, _ = note_for(spec, {"brand_a_cereal": ("needs_review", 0), "brand_b_cereal": ("misplaced", 4),
                              "promo_sign": ("missing", 0)})
    bullets = [line for line in note.text.splitlines() if line.startswith("- ")]
    assert [b.split(":")[0] for b in bullets] == ["- Promo Sign", "- Brand B Cereal Box", "- Brand A Cereal Box"]
    assert "Next: restock 1 item, move 1 misplaced item and check 1 item in person" in note.text


# --- missing / invalid financial values ------------------------------------

@pytest.mark.parametrize("bad", [None, -2.0, float("nan")])
def test_unavailable_price_is_stated_not_zeroed(spec, bad):
    spec = spec_with(spec, "brand_a_cereal", unit_margin_usd=bad)
    note, _ = note_for(spec, STOCKOUT)
    t = note.text
    assert "Brand A Cereal Box: missing (0 of 6 expected detected); 6 units short; margin at risk unavailable (" in t
    assert "Estimated Margin at Risk (Unverified): at least $2.00. Not calculable for Brand A Cereal Box" in t
    assert "$7.20" not in t


def test_unresolved_without_price_says_bound_unavailable(spec):
    spec = spec_with(spec, "brand_b_cereal", unit_margin_usd=None)
    note, _ = note_for(spec, MISPLACED)
    assert "upper bound unavailable (the spec has no unit_margin_usd for this item)" in note.text
    assert "excluding items whose unit value is unavailable" in note.text


# --- invalid inspection results -----------------------------------------------

def test_invalid_inspection_gives_no_fabricated_note(spec, settings):
    result = ComplianceResult(spec_id=spec.spec_id, items=[], overall_status="needs_review", raw_model_notes="prose")
    note = generate_action_note(result, summarize_exposure(result, spec), spec, settings, chat=forbid_call)
    assert note.source == "unavailable" and note.text == UNAVAILABLE_TEXT
    assert "$" not in note.text and note.ai_attempted is False


def test_mismatched_inputs_raise(spec):
    result = make_result()
    summary = summarize_exposure(result, spec)
    with pytest.raises(ValueError):
        template_note(make_result(spec_id="other"), summary, spec)


# --- AMD-worded note: success --------------------------------------------------

def test_amd_note_success_uses_model_wording_but_code_facts(spec, settings):
    reply = ai_reply([("brand_b_cereal", "Fill the gaps in the second row."),
                      ("brand_a_cereal", "Bring a full case from the back room and fill the empty facings.")])
    chat = FakeChat(reply)
    note, summary = note_for(spec, STOCKOUT, settings, chat)
    assert note.source == "amd" and note.ai_attempted and note.fallback_reason is None
    assert note.model_name == "test-vlm" and note.latency_s is not None
    t = note.text
    assert "Start with the empty facings, then fix the display." in t
    # Model's order and wording, code's facts:
    bullets = [line for line in t.splitlines() if line.startswith("- ")]
    assert bullets == [
        "- Brand B Cereal Box: partially stocked (2 of 4 expected detected); 2 units short; "
        "estimated margin at risk $2.00. Action: Fill the gaps in the second row.",
        "- Brand A Cereal Box: missing (0 of 6 expected detected); 6 units short; "
        "estimated margin at risk $7.20. Action: Bring a full case from the back room and fill the empty facings.",
    ]
    assert "Estimated Margin at Risk (Unverified): $9.20." in t
    # One call, text-only, with the note-specific limits.
    (messages, kwargs), = chat.calls
    assert kwargs == {"max_tokens": 400, "timeout_s": 30}
    assert isinstance(messages[0]["content"], str) and '"item_id": "brand_a_cereal"' in messages[0]["content"]


def test_model_cannot_change_financial_results(spec, settings):
    reply = ai_reply([("brand_a_cereal", "Restock now."), ("brand_b_cereal", "Restock now.")])
    note, summary = note_for(spec, STOCKOUT, settings, FakeChat(reply))
    before = summarize_exposure(make_result(STOCKOUT), spec)
    assert summary == before  # summary object untouched
    amounts = set(re.findall(r"\$[\d,]+\.\d\d", note.text))
    assert amounts == {"$7.20", "$2.00", "$9.20"}  # only code-computed figures appear


# --- AMD-worded note: failure and fallback -------------------------------------

@pytest.mark.parametrize("exc", [
    InspectionError("endpoint_unreachable", "Could not reach the AMD inference endpoint"),
    InspectionError("endpoint_error", "AMD endpoint returned HTTP 429: rate limited"),
    InspectionError("endpoint_error", "AMD endpoint returned HTTP 500"),
    TimeoutError("read timed out"),
])
def test_amd_failure_falls_back_to_template(spec, settings, exc):
    note, _ = note_for(spec, STOCKOUT, settings, FakeChat(exc=exc))
    template, _ = note_for(spec, STOCKOUT)
    assert note.source == "template" and note.ai_attempted is True
    assert note.text == template.text
    assert type(exc).__name__ in note.fallback_reason


MALFORMED = [
    ("prose", "Restock the cereal and fix the sign."),
    ("missing actions", json.dumps({"summary": "Do the restock."})),
    ("dropped item", ai_reply([("brand_a_cereal", "Restock it.")])),
    ("unknown item", ai_reply([("brand_a_cereal", "Restock it."), ("brand_b_cereal", "Restock it."),
                               ("brand_z_soda", "Restock it.")])),
    ("duplicate item", ai_reply([("brand_a_cereal", "Restock it."), ("brand_a_cereal", "Restock it.")])),
    ("digits", ai_reply([("brand_a_cereal", "Add 6 boxes."), ("brand_b_cereal", "Restock it.")])),
    ("money", ai_reply([("brand_a_cereal", "Restock it, about $50 at risk."), ("brand_b_cereal", "Restock it.")])),
    ("number words", ai_reply([("brand_a_cereal", "Add six boxes."), ("brand_b_cereal", "Restock it.")])),
    ("no-action claim", ai_reply([("brand_a_cereal", "Restock it."), ("brand_b_cereal", "Restock it.")],
                                 summary="Shelf is basically compliant, no action needed.")),
    ("empty instruction", ai_reply([("brand_a_cereal", ""), ("brand_b_cereal", "Restock it.")])),
]


@pytest.mark.parametrize("name, reply", MALFORMED, ids=[m[0] for m in MALFORMED])
def test_malformed_ai_output_falls_back(spec, settings, name, reply):
    note, _ = note_for(spec, STOCKOUT, settings, FakeChat(reply))
    template, _ = note_for(spec, STOCKOUT)
    assert note.source == "template" and note.ai_attempted is True and note.fallback_reason
    assert note.text == template.text


def test_validate_ai_note_accepts_fenced_json():
    raw = "```json\n" + ai_reply([("a", "Restock it.")]) + "\n```"
    assert validate_ai_note(raw, ["a"]).actions[0].instruction == "Restock it."


def test_fallback_is_deterministic(spec, settings):
    texts = {note_for(spec, MISPLACED, settings, FakeChat("garbage"))[0].text for _ in range(3)}
    texts.add(note_for(spec, MISPLACED)[0].text)
    assert len(texts) == 1


# --- when no AMD call is made ---------------------------------------------------

def test_compliant_makes_no_amd_call(spec, settings):
    note, _ = note_for(spec, None, settings, forbid_call)
    assert note.source == "template" and note.ai_attempted is False
    assert "nothing needs attention" in note.fallback_reason


def test_mock_mode_makes_no_amd_call_and_says_so(spec, settings):
    note, _ = note_for(spec, STOCKOUT, dataclasses.replace(settings, mock_mode=True), forbid_call)
    assert note.source == "template" and "MOCK_MODE" in note.fallback_reason


def test_no_settings_means_template_only(spec):
    result = make_result(STOCKOUT)
    note = generate_action_note(result, summarize_exposure(result, spec), spec, None, chat=forbid_call)
    assert note.source == "template" and note.ai_attempted is False and note.fallback_reason is None
