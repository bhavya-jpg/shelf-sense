"""app/ui.py: pure HTML builders. Escaping, labels and note parsing (no Streamlit needed)."""

from app import ui
from app.action_agent import template_note
from app.calculator import summarize_exposure
from app.models import ActionNote
from tests.conftest import make_result

STOCKOUT = {"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("partial", 2)}


def view(spec, overrides=None):
    result = make_result(overrides)
    summary = summarize_exposure(result, spec)
    return result, summary, template_note(result, summary, spec)


def test_model_and_user_text_is_escaped(spec):
    result, summary, _ = view(spec)
    result.items[0].note = '<script>alert(1)</script> & "quotes"'
    out = ui.observations_table(result, summary)
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "<img" not in ui.file_meta('<img src=x onerror=alert(1)>.png', 2048, (10, 10), "uploaded")
    assert "<b>" not in ui.notice("bad", "Error", "<b>bold</b>")


def test_dollar_amounts_never_reach_markdown_as_latex(spec):
    _, summary, _ = view(spec, STOCKOUT)
    out = ui.stats(make_result(STOCKOUT), summary)
    assert "$" not in out and "&#36;9.20" in out


def test_stat_strip_always_labels_the_estimate_unverified(spec):
    result, summary, _ = view(spec, STOCKOUT)
    out = ui.stats(result, summary)
    assert "Estimated Margin at Risk (Unverified)" in out and "Unverified · AI-estimated counts" in out
    assert "Verified Counts" not in out


def test_discrepancies_include_overcounts_and_unresolved(spec):
    _, summary, _ = view(spec, {"brand_a_cereal": ("present", 7), "brand_b_cereal": ("misplaced", 4)})
    ids = [i.item_id for i in ui.discrepancy_items(summary)]
    assert ids == ["brand_a_cereal", "brand_b_cereal"]  # 7 of 6 overcount + misplaced; promo sign fine
    _, clean, _ = view(spec)
    assert ui.discrepancy_items(clean) == [] and "No discrepancies" in ui.discrepancies(clean)


def test_items_table_shows_backend_values_and_badges(spec):
    result, summary, _ = view(spec, STOCKOUT)
    out = ui.items_table(result, summary)
    assert "Brand A Cereal Box" in out and "ss-badge--bad" in out and "Missing" in out
    assert "&#36;7.20" in out and "−6" in out
    assert "Upper bound" not in out  # nothing unresolved, so no bound column
    _, summary2, _ = view(spec, {"brand_b_cereal": ("misplaced", 4)})
    assert "Upper bound" in ui.items_table(make_result({"brand_b_cereal": ("misplaced", 4)}), summary2)


def test_parse_note_splits_template_into_parts(spec):
    _, summary, note = view(spec, STOCKOUT)
    parts = ui.parse_note(note.text, [i.label for i in summary.items])
    assert [it["label"] for it in parts["items"]] == ["Brand A Cereal Box", "Brand B Cereal Box"]
    assert parts["items"][0]["action"] == "Restock Brand A Cereal Box with 6 units."
    assert parts["next"].startswith("restock 2 items")
    assert any("Estimated Margin at Risk (Unverified): $9.20." in line for line in parts["foot"])


def test_actions_panel_labels_its_source(spec):
    _, summary, note = view(spec, STOCKOUT)
    assert "Deterministic template" in ui.actions(note, summary)
    amd = note.model_copy(update={"source": "amd", "model_name": "Gemma-4-31B-IT", "latency_s": 4.2, "ai_attempted": True})
    out = ui.actions(amd, summary)
    assert "AMD-worded · Gemma-4-31B-IT" in out and "Deterministic template" not in out
    unavailable = ActionNote(text="No action note: x", source="unavailable")
    assert "No action note" in ui.actions(unavailable, summary)


def test_workspace_head_reflects_configuration_state():
    assert "Gemma-4-31B-IT" in ui.workspace_head("Gemma-4-31B-IT", "developer.amd.com.cn", mock=False, configured=True)
    assert "MOCK MODE" in ui.workspace_head("Gemma-4-31B-IT", "x", mock=True, configured=True)
    assert "Inference not configured" in ui.workspace_head(None, None, mock=False, configured=False)
