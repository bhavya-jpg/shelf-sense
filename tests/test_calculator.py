"""Milestone 2: deterministic financial exposure. Pure functions, no AMD calls.

Unit values come from tests/fixtures/cereal_endcap.json (author-entered demo assumptions):
brand_a_cereal $1.20 x 6, brand_b_cereal $1.00 x 4, promo_sign $0 x 1.
"""

import math

import pytest

from app.calculator import (
    ASSUMPTIONS,
    COUNT_BASIS,
    calculate_revenue_impact,
    count_inconsistency,
    summarize_exposure,
    validate_unit_value,
)
from app.models import ComplianceResult, ItemCheck, Spec

from tests.conftest import EXPECTED, by_id, make_result, spec_with


# --- the five statuses -------------------------------------------------------

def test_compliant_is_zero_with_nothing_unresolved(spec):
    s = summarize_exposure(make_result(), spec)
    assert s.calculation_available and s.estimate_is_complete
    assert s.estimated_exposure_usd == 0.0 and s.unresolved_potential_usd == 0.0
    assert s.unresolved_item_ids == [] and s.unavailable_item_ids == []
    assert all(i.exposure_status == "none" and i.units_missing == 0 for i in s.items)


def test_missing_uses_expected_units(spec):
    s = summarize_exposure(make_result({"brand_a_cereal": ("missing", 0)}), spec)
    a = by_id(s)["brand_a_cereal"]
    assert a.exposure_status == "estimated" and a.units_missing == 6
    assert a.estimated_exposure_usd == 7.20  # 6 x $1.20
    assert "6 expected units x $1.20 unit value = $7.20" in a.assumptions
    assert s.estimated_exposure_usd == 7.20


def test_partial_uses_only_the_missing_units(spec):
    s = summarize_exposure(make_result({"brand_b_cereal": ("partial", 2)}), spec)
    b = by_id(s)["brand_b_cereal"]
    assert b.units_missing == 2 and b.estimated_exposure_usd == 2.00  # (4 - 2) x $1.00
    assert s.estimated_exposure_usd == 2.00


def test_partial_with_zero_detected_equals_missing(spec):
    b = by_id(summarize_exposure(make_result({"brand_b_cereal": ("partial", 0)}), spec))["brand_b_cereal"]
    assert b.exposure_status == "estimated" and b.units_missing == 4 and b.estimated_exposure_usd == 4.00


def test_stockout_scenario_total(spec):
    s = summarize_exposure(make_result({"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("partial", 2)}), spec)
    assert s.estimated_exposure_usd == 9.20  # $7.20 + $2.00
    assert s.estimate_is_complete and s.unresolved_item_ids == []


def test_misplaced_is_excluded_from_estimate_but_unresolved(spec):
    s = summarize_exposure(make_result({"brand_b_cereal": ("misplaced", 4)}), spec)
    b = by_id(s)["brand_b_cereal"]
    assert b.exposure_status == "unresolved" and b.estimated_exposure_usd == 0.0
    assert b.units_missing is None
    assert b.potential_exposure_usd == 4.00  # 4 x $1.00 upper bound
    assert "not an estimate of actual loss" in b.assumptions
    assert s.estimated_exposure_usd == 0.0
    assert s.unresolved_item_ids == ["brand_b_cereal"]  # $0 confirmed is NOT presented as no issue
    assert s.unresolved_potential_usd == 4.00


def test_needs_review_is_excluded_from_estimate_but_unresolved(spec):
    s = summarize_exposure(make_result({"brand_a_cereal": ("needs_review", 0)}), spec)
    a = by_id(s)["brand_a_cereal"]
    assert a.exposure_status == "unresolved" and a.estimated_exposure_usd == 0.0
    assert a.potential_exposure_usd == 7.20
    assert s.unresolved_item_ids == ["brand_a_cereal"]


def test_estimate_and_potential_are_never_mixed(spec):
    s = summarize_exposure(
        make_result({"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("misplaced", 4)}), spec
    )
    assert s.estimated_exposure_usd == 7.20
    assert s.unresolved_potential_usd == 4.00


# --- missing / invalid financial data ----------------------------------------

@pytest.mark.parametrize("bad_value, reason", [
    (None, "no unit_margin_usd"),
    (-1.0, "negative"),
    (math.nan, "not a finite number"),
    (math.inf, "not a finite number"),
])
def test_missing_or_invalid_price_is_unavailable_not_zero(spec, bad_value, reason):
    spec = spec_with(spec, "brand_a_cereal", unit_margin_usd=bad_value)
    s = summarize_exposure(make_result({"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("partial", 2)}), spec)
    a = by_id(s)["brand_a_cereal"]
    assert a.exposure_status == "unavailable"
    assert a.estimated_exposure_usd is None  # not silently $0
    assert a.units_missing == 6 and a.unit_value_usd is None
    assert reason in a.assumptions
    # Total covers only what could be valued and says it is incomplete.
    assert s.estimated_exposure_usd == 2.00 and s.estimate_is_complete is False
    assert s.unavailable_item_ids == ["brand_a_cereal"]


def test_unresolved_item_without_price_has_no_upper_bound(spec):
    spec = spec_with(spec, "brand_b_cereal", unit_margin_usd=None)
    s = summarize_exposure(make_result({"brand_b_cereal": ("misplaced", 4)}), spec)
    b = by_id(s)["brand_b_cereal"]
    assert b.exposure_status == "unresolved" and b.potential_exposure_usd is None
    assert "Upper bound cannot be calculated" in b.assumptions
    assert s.unresolved_potential_is_complete is False


def test_missing_price_on_present_item_does_not_matter(spec):
    spec = spec_with(spec, "brand_a_cereal", unit_margin_usd=None)
    s = summarize_exposure(make_result(), spec)
    assert s.estimated_exposure_usd == 0.0 and s.estimate_is_complete


def test_spec_value_of_zero_is_a_real_zero(spec):
    # promo_sign has an author-entered $0 unit value: a confirmed $0, not "unavailable".
    s = summarize_exposure(make_result({"promo_sign": ("missing", 0)}), spec)
    p = by_id(s)["promo_sign"]
    assert p.exposure_status == "estimated" and p.estimated_exposure_usd == 0.0 and p.units_missing == 1
    assert p.status == "missing"  # the issue itself stays visible


def test_spec_loads_with_absent_or_null_financial_fields():
    spec = Spec.model_validate({"spec_id": "s", "location": "l", "items": [
        {"item_id": "a", "label": "A", "expected_count": 2},
        {"item_id": "b", "label": "B", "expected_count": 1, "unit_margin_usd": None},
    ]})
    assert [i.unit_margin_usd for i in spec.items] == [None, None]


@pytest.mark.parametrize("value, ok", [(0.0, True), (1.2, True), (None, False), (-0.01, False), (math.nan, False)])
def test_validate_unit_value(value, ok):
    usable, problem = validate_unit_value(value)
    assert (usable is not None) == ok and (problem is None) == ok


# --- zero units and inconsistent counts --------------------------------------

def test_zero_expected_units_gives_zero_exposure(spec):
    spec = spec_with(spec, "brand_a_cereal", expected_count=0)
    result = make_result({"brand_a_cereal": ("missing", 0)})
    result.items[0].expected_count = 0
    a = by_id(summarize_exposure(result, spec))["brand_a_cereal"]
    assert a.exposure_status == "estimated" and a.units_missing == 0 and a.estimated_exposure_usd == 0.0


def test_overstock_present_is_zero_not_negative(spec):
    a = by_id(summarize_exposure(make_result({"brand_a_cereal": ("present", 9)}), spec))["brand_a_cereal"]
    assert a.exposure_status == "none" and a.units_missing == 0 and a.estimated_exposure_usd == 0.0


@pytest.mark.parametrize("status, detected, fragment", [
    ("missing", 3, "status 'missing' but 3 detected"),
    ("partial", 6, "status 'partial' but 6 of 6 detected"),
    ("partial", 8, "status 'partial' but 8 of 6 detected"),
    ("present", 4, "status 'present' but only 4 of 6 detected"),
])
def test_inconsistent_counts_are_unresolved_not_confirmed(spec, status, detected, fragment):
    s = summarize_exposure(make_result({"brand_a_cereal": (status, detected)}), spec)
    a = by_id(s)["brand_a_cereal"]
    assert a.exposure_status == "unresolved" and a.estimated_exposure_usd == 0.0
    assert a.units_missing is None and a.potential_exposure_usd == 7.20
    assert fragment in a.assumptions
    assert s.unresolved_item_ids == ["brand_a_cereal"]


def test_count_inconsistency_none_for_consistent_checks():
    def check(status, d):
        return ItemCheck(item_id="x", expected_count=4, detected_count=d, status=status, confidence=50)

    assert count_inconsistency(check("missing", 0)) is None
    assert count_inconsistency(check("partial", 3)) is None
    assert count_inconsistency(check("present", 4)) is None
    assert count_inconsistency(check("misplaced", 4)) is None


# --- unvalidated output and mismatched inputs --------------------------------

def test_unvalidated_result_produces_no_figures(spec):
    result = ComplianceResult(spec_id=spec.spec_id, items=[], overall_status="needs_review", raw_model_notes="prose")
    s = summarize_exposure(result, spec)
    assert s.calculation_available is False and s.unavailable_reason
    assert s.estimated_exposure_usd is None and s.unresolved_potential_usd is None
    with pytest.raises(ValueError, match="must not run on unvalidated output"):
        calculate_revenue_impact(result, spec)


def test_spec_id_mismatch_raises(spec):
    with pytest.raises(ValueError, match="not 'cereal_endcap_v1'"):
        summarize_exposure(make_result(spec_id="other_spec"), spec)


def test_item_set_mismatch_raises(spec):
    result = make_result()
    result.items = result.items[:2]
    with pytest.raises(ValueError, match="do not match spec items"):
        calculate_revenue_impact(result, spec)


def test_duplicate_item_raises(spec):
    result = make_result()
    result.items.append(result.items[0])
    with pytest.raises(ValueError, match="duplicate"):
        calculate_revenue_impact(result, spec)


def test_expected_count_must_match_spec(spec):
    result = make_result()
    result.items[0].expected_count = 99
    with pytest.raises(ValueError, match="differs from the spec"):
        calculate_revenue_impact(result, spec)


# --- determinism and rounding -------------------------------------------------

def test_deterministic_and_order_follows_spec(spec):
    result = make_result({"brand_a_cereal": ("missing", 0), "brand_b_cereal": ("misplaced", 4)})
    result.items.reverse()
    first, second = summarize_exposure(result, spec), summarize_exposure(result, spec)
    assert first == second
    assert [i.item_id for i in first.items] == list(EXPECTED)


def test_cent_exact_arithmetic(spec):
    # Float math gives 3 x 0.1 = 0.30000000000000004; Decimal gives exactly 0.30.
    spec = spec_with(spec, "brand_b_cereal", unit_margin_usd=0.1)
    b = by_id(summarize_exposure(make_result({"brand_b_cereal": ("partial", 1)}), spec))["brand_b_cereal"]
    assert b.estimated_exposure_usd == 0.30


def test_half_cent_rounds_up(spec):
    spec = spec_with(spec, "promo_sign", unit_margin_usd=0.005)
    p = by_id(summarize_exposure(make_result({"promo_sign": ("missing", 0)}), spec))["promo_sign"]
    assert p.estimated_exposure_usd == 0.01


def test_assumptions_are_attached(spec):
    s = summarize_exposure(make_result(), spec)
    assert s.assumptions == f"{COUNT_BASIS[False]} {ASSUMPTIONS}"
    assert "author-entered" in ASSUMPTIONS and "not revenue" in ASSUMPTIONS
