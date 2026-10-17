"""Display formatting for the UI. Pure functions over validated models — no calculations."""

from app.calculator import exposure_label
from app.models import ActionNote, ComplianceResult, ExposureSummary, InspectionError

STATUS_LABEL = {
    "present": "Present",
    "missing": "Missing",
    "partial": "Partial",
    "misplaced": "Misplaced",
    "needs_review": "Needs review",
}

# (streamlit alert kind, text label) — colour is always paired with a text label.
OVERALL = {
    "compliant": ("success", "Compliant"),
    "non_compliant": ("error", "Non-compliant"),
    "needs_review": ("warning", "Needs review"),
}

ERROR_HEADLINE = {
    "endpoint_unreachable": "Could not reach the AMD inference endpoint. Check AMD_API_URL and your network, then retry.",
    "endpoint_timeout": "The AMD inference endpoint is reachable but did not answer in time. It is shared and may be busy; retry in a moment.",
    "endpoint_error":"The AMD inference endpoint returned an error. If it says 429 (rate limited) or 5xx, wait a moment and retry.",
    "parse_failed": "The AMD endpoint's response was not a valid chat completion. Retry; if it persists, check MODEL_NAME.",
    "invalid_image": "This file can't be used. Upload a JPEG or PNG photo.",
}


def usd(amount: float) -> str:
    return f"${amount:,.2f}"


def md(text: str) -> str:
    """Escape '$' so Streamlit markdown doesn't treat dollar amounts as LaTeX."""
    return text.replace("$", r"\$")


def error_message(exc: InspectionError) -> str:
    headline = ERROR_HEADLINE.get(exc.stage, "The inspection failed.")
    return f"{headline}\n\nDetails ({exc.stage}): {exc.detail}"


def overall_badge(result: ComplianceResult) -> tuple[str, str]:
    return OVERALL[result.overall_status]


POTENTIAL_LABEL = "Unresolved Potential Exposure (Upper Bound)"


def estimate_label(summary: ExposureSummary) -> str:
    return exposure_label(summary.counts_verified)


def estimate_help(summary: ExposureSummary) -> str:
    if summary.counts_verified:
        return "Missing and partial units x unit margin, from counts verified by a person."
    return (
        "Calculated by code as missing and partial units x unit margin (a demo assumption), using counts "
        "the AI model estimated from the photo. The counts have not been independently verified and may be wrong."
    )


def estimated_value(summary: ExposureSummary) -> str:
    if not summary.calculation_available:
        return "Not calculated"
    value = usd(summary.estimated_exposure_usd)
    return value if summary.estimate_is_complete else f"at least {value}"


def potential_value(summary: ExposureSummary) -> str:
    if not summary.calculation_available:
        return "Not calculated"
    if not summary.unresolved_item_ids:
        return "None"
    value = usd(summary.unresolved_potential_usd)
    return value if summary.unresolved_potential_is_complete else f"at least {value}"


def exposure_messages(summary: ExposureSummary) -> list[tuple[str, str]]:
    """Notices that must accompany the figures (kind, plain text)."""
    if not summary.calculation_available:
        return [("warning", summary.unavailable_reason or "No financial figures were calculated.")]
    labels = {i.item_id: i.label for i in summary.items}
    messages = []
    if not summary.counts_verified:
        messages.append((
            "info",
            "This amount is calculated from AI-estimated counts and may be inaccurate until the counts are "
            "independently verified. Check the shelf before acting on it.",
        ))
    if summary.unavailable_item_ids:
        names = ", ".join(labels[i] for i in summary.unavailable_item_ids)
        messages.append((
            "warning",
            f"The estimate is incomplete: no unit value is available for {names}, so its exposure "
            "could not be calculated (it is not counted as $0).",
        ))
    if summary.unresolved_item_ids:
        names = ", ".join(labels[i] for i in summary.unresolved_item_ids)
        zero = " An estimate of $0.00 does not mean there is no risk." if summary.estimated_exposure_usd == 0 else ""
        messages.append((
            "warning",
            f"Unresolved, not included in the estimate: {names}. These need checking; the upper bound "
            f"assumes all their expected units were unavailable to shoppers and is not an estimate of actual loss.{zero}",
        ))
    return messages


def item_rows(result: ComplianceResult, summary: ExposureSummary, note: ActionNote) -> list[dict]:
    checks = {c.item_id: c for c in result.items}
    rows = []
    for impact in summary.items:
        check = checks[impact.item_id]
        exposure = {
            "none": "$0.00",
            "estimated": usd(impact.estimated_exposure_usd or 0.0),
            "unresolved": "Unresolved (excluded)",
            "unavailable": "Unavailable (no unit value)",
        }[impact.exposure_status]
        rows.append({
            "Product": impact.label,
            "Expected": impact.expected_count,
            "Detected": impact.detected_count,
            "Per shelf (top to bottom)": " / ".join(map(str, check.shelf_counts)) if check.shelf_counts else "—",
            "Status": STATUS_LABEL[impact.status],
            estimate_label(summary): exposure,
            "Potential (upper bound)": usd(impact.potential_exposure_usd) if impact.potential_exposure_usd is not None else "—",
            "Action": note.item_actions.get(impact.item_id, "—"),
            "Model confidence": f"{check.confidence:.0f}%",
            "Model note": check.note or "",
        })
    return rows


def note_markdown(text: str) -> str:
    """Note text -> markdown: escape '$' and keep the note's line breaks."""
    lines = []
    for line in md(text).split("\n"):
        lines.append(line if not line or line.startswith("- ") else line + "  ")
    return "\n".join(lines)


def note_source_caption(note: ActionNote) -> str:
    if note.source == "amd":
        return (
            f"Action wording by {note.model_name} via the AMD Token Factory endpoint ({note.latency_s}s). "
            "Product names, counts, statuses and figures are inserted by code, not the model."
        )
    if note.source == "unavailable":
        return "No action note: the inspection result could not be validated."
    if note.ai_attempted:
        return f"Deterministic template. The AMD-worded note was not used: {note.fallback_reason}"
    if note.fallback_reason:
        return f"Deterministic template ({note.fallback_reason})."
    return "Deterministic template."
