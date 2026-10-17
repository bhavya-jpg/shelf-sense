"""Merge logic for the per-shelf cropping experiment (deterministic, no model calls)."""

from app.models import ComplianceResult, ItemCheck
from eval.shelf_crop_experiment import merge_shelf_results

EXPECTED = {"brand_a_cereal": 6, "brand_b_cereal": 4, "promo_sign": 1}


def shelf(counts, statuses=None, items_missing=()):
    """One shelf's validated result; per-shelf model statuses default to 'partial' (meaningless)."""
    statuses = statuses or {}
    items = [
        ItemCheck(item_id=i, expected_count=EXPECTED[i], detected_count=counts.get(i, 0),
                  status=statuses.get(i, "partial"), confidence=90 - n, note=f"{i} seen")
        for n, i in enumerate(EXPECTED) if i not in items_missing
    ]
    return ComplianceResult(spec_id="cereal_endcap_v1", items=items, overall_status="non_compliant", latency_s=2.0)


def by_id(result):
    return {c.item_id: c for c in result.items}


def test_counts_are_summed_and_status_recomputed_from_totals(spec):
    merged = merge_shelf_results(spec, [
        shelf({"brand_a_cereal": 3, "brand_b_cereal": 2, "promo_sign": 1}),
        shelf({"brand_a_cereal": 3, "brand_b_cereal": 2}),
    ])
    a, b, p = (by_id(merged)[i] for i in EXPECTED)
    assert (a.detected_count, a.shelf_counts, a.status) == (6, [3, 3], "present")  # per-shelf "partial" ignored
    assert (b.detected_count, b.status) == (4, "present")
    assert (p.detected_count, p.shelf_counts, p.status) == (1, [1, 0], "present")
    assert merged.overall_status == "compliant"
    assert merged.latency_s == 4.0


def test_shortfall_and_zero_totals(spec):
    merged = merge_shelf_results(spec, [shelf({"brand_a_cereal": 2, "brand_b_cereal": 0, "promo_sign": 1})])
    assert by_id(merged)["brand_a_cereal"].status == "partial"
    assert by_id(merged)["brand_b_cereal"].status == "missing"
    assert merged.overall_status == "non_compliant"


def test_needs_review_on_any_shelf_makes_item_needs_review(spec):
    merged = merge_shelf_results(spec, [
        shelf({"brand_a_cereal": 3, "brand_b_cereal": 4, "promo_sign": 1}),
        shelf({"brand_a_cereal": 3}, statuses={"brand_a_cereal": "needs_review"}),
    ])
    a = by_id(merged)["brand_a_cereal"]
    assert a.status == "needs_review" and "No usable count for shelf 2" in a.note
    assert merged.overall_status == "needs_review"


def test_unparseable_shelf_makes_every_item_needs_review(spec):
    empty = ComplianceResult(spec_id="cereal_endcap_v1", items=[], overall_status="needs_review", latency_s=1.0)
    merged = merge_shelf_results(spec, [shelf({"brand_a_cereal": 6, "brand_b_cereal": 4, "promo_sign": 1}), empty])
    assert all(c.status == "needs_review" for c in merged.items)


def test_misplaced_on_a_shelf_is_kept(spec):
    merged = merge_shelf_results(spec, [
        shelf({"brand_a_cereal": 6, "brand_b_cereal": 4, "promo_sign": 1}, statuses={"brand_b_cereal": "misplaced"}),
    ])
    assert by_id(merged)["brand_b_cereal"].status == "misplaced"


def test_confidence_is_the_lowest_shelf_value(spec):
    merged = merge_shelf_results(spec, [shelf({"brand_a_cereal": 6}), shelf({"brand_a_cereal": 0})])
    assert by_id(merged)["brand_a_cereal"].confidence == 90
