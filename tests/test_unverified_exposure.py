"""Regression tests: model-derived money is an unverified estimate, never a verified finding."""

import json
import math

import pytest

from app import presenters
from app.action_agent import UNVERIFIED_BASIS, template_note
from app.calculator import exposure_label, summarize_exposure
from app.inspector import build_result, parse_model_output
from app.models import ComplianceResult
from app.pipeline import run_inspection
from tests.conftest import make_result, spec_with

STOCKOUT = {"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("partial", 2)}
SCENARIOS = [
    {},
    STOCKOUT,
    {"brand_b_cereal": ("misplaced", 4)},
    {"brand_a_cereal": ("needs_review", 0)},
    {"brand_a_cereal": ("missing", 3)},  # contradictory counts
]


def view(spec, overrides, counts_verified=False):
    result = make_result(overrides)
    result.counts_verified = counts_verified
    summary = summarize_exposure(result, spec)
    return result, summary, template_note(result, summary, spec)


def user_facing_text(result, summary, note) -> str:
    rows = presenters.item_rows(result, summary, note)
    parts = [
        note.text,
        presenters.estimate_label(summary),
        presenters.estimate_help(summary),
        presenters.POTENTIAL_LABEL,
        summary.assumptions,
        *(m for _, m in presenters.exposure_messages(summary)),
        *(str(k) + " " + str(v) for row in rows for k, v in row.items()),
        *(i.assumptions for i in summary.items),
    ]
    return "\n".join(parts)


# --- 1. a model-derived amount is not presented as independently verified -----

@pytest.mark.parametrize("overrides", SCENARIOS)
def test_model_derived_amount_is_labelled_unverified(spec, overrides):
    result, summary, note = view(spec, overrides)
    assert summary.counts_verified is False
    assert presenters.estimate_label(summary) == "Estimated Margin at Risk (Unverified)"
    assert "not been independently verified" in presenters.estimate_help(summary)
    assert ("info", presenters.exposure_messages(summary)[0][1]) == presenters.exposure_messages(summary)[0]
    assert "AI-estimated counts" in presenters.exposure_messages(summary)[0][1]
    assert UNVERIFIED_BASIS in note.text
    assert summary.assumptions.startswith("Counts are estimated by the AI model")
    text = user_facing_text(result, summary, note).lower()
    assert "confirmed" not in text  # the old wording that implied verification
    assert "verified counts" not in text


def test_inspector_never_marks_counts_verified(spec, image_bytes, settings):
    reply = json.dumps({"items": [
        {"item_id": i, "detected_count": n, "status": "present", "confidence": 100}
        for i, n in (("brand_a_cereal", 6), ("brand_b_cereal", 4), ("promo_sign", 1))
    ]})
    run = run_inspection(spec, image_bytes, settings, chat=lambda *a, **k: reply)
    assert run.result.counts_verified is False and run.summary.counts_verified is False
    assert presenters.estimate_label(run.summary) == "Estimated Margin at Risk (Unverified)"


def test_only_verified_counts_drop_the_unverified_label(spec):
    # The label follows the count source; a verified result (not produced anywhere today) is the
    # only way to get a figure without "Estimated"/"Unverified".
    _, summary, note = view(spec, STOCKOUT, counts_verified=True)
    assert exposure_label(True) == presenters.estimate_label(summary) == "Margin at Risk (Verified Counts)"
    assert UNVERIFIED_BASIS not in note.text
    assert "Margin at Risk (Verified Counts): $9.20." in note.text
    _, unverified, _ = view(spec, STOCKOUT)
    assert unverified.estimated_exposure_usd == summary.estimated_exposure_usd == 9.20  # same formula


# --- 2. needs_review items are excluded from the estimate --------------------

def test_needs_review_item_is_excluded_from_estimate_and_visible(spec):
    result, summary, note = view(spec, {"brand_a_cereal": ("needs_review", 0), "brand_b_cereal": ("partial", 2)})
    a = {i.item_id: i for i in summary.items}["brand_a_cereal"]
    assert a.exposure_status == "unresolved" and a.estimated_exposure_usd == 0.0
    assert summary.estimated_exposure_usd == 2.00  # Brand B only; Brand A's 6 x $1.20 is not added
    assert summary.unresolved_item_ids == ["brand_a_cereal"]
    row = {r["Product"]: r for r in presenters.item_rows(result, summary, note)}["Brand A Cereal Box"]
    assert row["Status"] == "Needs review" and row["Estimated Margin at Risk (Unverified)"] == "Unresolved (excluded)"
    assert "Brand A Cereal Box: needs manual review" in note.text


def test_count_flagged_unreliable_by_guard_is_excluded(spec):
    raw = json.dumps({"items": [
        {"item_id": "brand_a_cereal", "detected_count": 2, "shelf_counts": [2], "count_reliable": False,
         "status": "partial", "confidence": 100},
        {"item_id": "brand_b_cereal", "detected_count": 4, "status": "present", "confidence": 100},
        {"item_id": "promo_sign", "detected_count": 1, "status": "present", "confidence": 100},
    ]})
    result = build_result(spec, parse_model_output(raw))
    summary = summarize_exposure(result, spec)
    assert result.items[0].status == "needs_review"
    assert summary.estimated_exposure_usd == 0.0 and summary.unresolved_item_ids == ["brand_a_cereal"]


@pytest.mark.parametrize("confidence", [0, 5, 100])
def test_confidence_alone_never_decides_trust(spec, confidence):
    raw = json.dumps({"items": [
        {"item_id": "brand_a_cereal", "detected_count": 4, "status": "partial", "confidence": confidence},
        {"item_id": "brand_b_cereal", "detected_count": 4, "status": "present", "confidence": confidence},
        {"item_id": "promo_sign", "detected_count": 1, "status": "present", "confidence": confidence},
    ]})
    result = build_result(spec, parse_model_output(raw))
    summary = summarize_exposure(result, spec)
    assert result.items[0].status == "partial"  # same outcome at any confidence
    assert summary.estimated_exposure_usd == 2.40  # (6 - 4) x $1.20, still labelled unverified
    assert presenters.estimate_label(summary).endswith("(Unverified)")


# --- 3. a $0 estimate with unresolved items is not "no action" ----------------

def test_zero_estimate_with_unresolved_items_still_requires_action(spec):
    result, summary, note = view(spec, {"brand_b_cereal": ("misplaced", 4)})
    assert summary.estimated_exposure_usd == 0.0
    assert "No action required" not in note.text
    assert "Estimated Margin at Risk (Unverified): $0.00." in note.text
    assert "An estimate of $0.00 does not mean there is no risk" in note.text
    assert any("does not mean there is no risk" in m for _, m in presenters.exposure_messages(summary))
    assert presenters.potential_value(summary) == "$4.00"


# --- 4. missing / invalid financial values stay unavailable -------------------

@pytest.mark.parametrize("bad", [None, -1.0, math.nan, math.inf])
def test_missing_or_invalid_values_remain_unavailable(spec, bad):
    spec = spec_with(spec, "brand_a_cereal", unit_margin_usd=bad)
    result, summary, note = view(spec, STOCKOUT)
    a = {i.item_id: i for i in summary.items}["brand_a_cereal"]
    assert a.exposure_status == "unavailable" and a.estimated_exposure_usd is None
    assert summary.estimate_is_complete is False and summary.unavailable_item_ids == ["brand_a_cereal"]
    assert presenters.estimated_value(summary) == "at least $2.00"
    row = {r["Product"]: r for r in presenters.item_rows(result, summary, note)}["Brand A Cereal Box"]
    assert row["Estimated Margin at Risk (Unverified)"] == "Unavailable (no unit value)"
    assert any("not counted as $0" in m for _, m in presenters.exposure_messages(summary))


def test_unvalidated_output_still_produces_no_figures(spec):
    result = ComplianceResult(spec_id=spec.spec_id, items=[], overall_status="needs_review")
    summary = summarize_exposure(result, spec)
    assert summary.calculation_available is False and summary.estimated_exposure_usd is None
    assert presenters.estimated_value(summary) == "Not calculated"
