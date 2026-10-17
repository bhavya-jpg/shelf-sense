from app import presenters
from app.action_agent import template_note
from app.calculator import summarize_exposure
from app.models import ActionNote, ComplianceResult, InspectionError
from tests.conftest import make_result, spec_with


def view(spec, overrides=None):
    result = make_result(overrides)
    summary = summarize_exposure(result, spec)
    return result, summary, template_note(result, summary, spec)


def test_item_rows_use_spec_labels_and_calculator_values(spec):
    result, summary, note = view(spec, {"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("misplaced", 4)})
    rows = {r["Product"]: r for r in presenters.item_rows(result, summary, note)}
    assert set(rows) == {"Brand A Cereal Box", "Brand B Cereal Box", "Promo Sign"}
    a, b = rows["Brand A Cereal Box"], rows["Brand B Cereal Box"]
    assert (a["Expected"], a["Detected"], a["Status"], a["Estimated Margin at Risk (Unverified)"]) == (6, 0, "Missing", "$7.20")
    assert a["Action"] == "Restock Brand A Cereal Box with 6 units."
    assert b["Status"] == "Misplaced" and b["Estimated Margin at Risk (Unverified)"] == "Unresolved (excluded)"
    assert b["Potential (upper bound)"] == "$4.00"
    assert rows["Promo Sign"]["Action"] == "—"
    assert a["Per shelf (top to bottom)"] == "—"  # not reported in this result

    result.items[0].shelf_counts = [0, 0]
    rows = {r["Product"]: r for r in presenters.item_rows(result, summary, note)}
    assert rows["Brand A Cereal Box"]["Per shelf (top to bottom)"] == "0 / 0"


def test_metric_values(spec):
    _, s, _ = view(spec, {"brand_b_cereal": ("misplaced", 4)})
    assert presenters.estimated_value(s) == "$0.00" and presenters.potential_value(s) == "$4.00"
    _, s, _ = view(spec)
    assert presenters.potential_value(s) == "None"


def test_zero_estimate_with_unresolved_is_flagged(spec):
    _, s, _ = view(spec, {"brand_b_cereal": ("misplaced", 4)})
    kinds_texts = presenters.exposure_messages(s)
    assert any("does not mean there is no risk" in t for _, t in kinds_texts)
    assert any("Brand B Cereal Box" in t for _, t in kinds_texts)


def test_unavailable_value_shown_as_lower_bound(spec):
    spec = spec_with(spec, "brand_a_cereal", unit_margin_usd=None)
    _, s, _ = view(spec, {"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("partial", 2)})
    assert presenters.estimated_value(s) == "at least $2.00"
    assert any("not counted as $0" in t for _, t in presenters.exposure_messages(s))


def test_unvalidated_result_shows_not_calculated(spec):
    result = ComplianceResult(spec_id=spec.spec_id, items=[], overall_status="needs_review")
    s = summarize_exposure(result, spec)
    assert presenters.estimated_value(s) == "Not calculated"
    assert presenters.exposure_messages(s)[0][0] == "warning"


def test_overall_badges_always_have_text():
    for status, (kind, text) in presenters.OVERALL.items():
        assert kind in {"success", "error", "warning"} and text


def test_note_markdown_escapes_dollars_and_keeps_lines():
    md = presenters.note_markdown("Headline.\n\n- A: $7.20. Action: Restock.\n\nTotal: $9.20.\nNext: go.")
    assert r"\$7.20" in md and r"\$9.20" in md and "$7" not in md.replace(r"\$", "")
    assert "Total: \\$9.20.  \nNext: go.  " in md


def test_note_source_captions_never_mislabel_template():
    amd = ActionNote(text="x", source="amd", ai_attempted=True, model_name="Gemma-4-31B-IT", latency_s=4.2)
    fallback = ActionNote(text="x", source="template", ai_attempted=True, fallback_reason="HTTP 429")
    plain = ActionNote(text="x", source="template")
    assert "Gemma-4-31B-IT" in presenters.note_source_caption(amd)
    assert presenters.note_source_caption(fallback).startswith("Deterministic template")
    assert "HTTP 429" in presenters.note_source_caption(fallback)
    assert presenters.note_source_caption(plain) == "Deterministic template."


def test_error_messages_are_actionable():
    msg = presenters.error_message(InspectionError("endpoint_unreachable", "boom"))
    assert "Check AMD_API_URL" in msg and "boom" in msg
    assert "retry" in presenters.error_message(InspectionError("endpoint_error", "HTTP 429")).lower()
