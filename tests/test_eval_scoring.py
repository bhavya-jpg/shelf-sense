from eval.count_experiment import score_run
from tests.conftest import make_result

TRUTH = {
    "counts": {"brand_a_cereal": 6, "brand_b_cereal": 4, "promo_sign": 1},
    "statuses": {"brand_a_cereal": "present", "brand_b_cereal": "present", "promo_sign": "present"},
    "overall_status": "compliant",
}


def test_perfect_run():
    result = make_result()
    result.overall_status = "compliant"
    s = score_run(result, TRUTH)
    assert (s["exact_counts"], s["correct_statuses"], s["total_abs_count_error"]) == (3, 3, 0)
    assert s["overall_correct"] is True


def test_undercount_is_scored_as_errors():
    s = score_run(make_result({"brand_a_cereal": ("partial", 4), "brand_b_cereal": ("partial", 3)}), TRUTH)
    rows = {r["item_id"]: r for r in s["items"]}
    assert rows["brand_a_cereal"]["error"] == -2 and rows["brand_b_cereal"]["error"] == -1
    assert s["exact_counts"] == 1 and s["correct_statuses"] == 1 and s["total_abs_count_error"] == 3
    assert s["overall_correct"] is False


def test_missing_item_in_result_has_no_total_error():
    result = make_result()
    result.items = result.items[:2]
    s = score_run(result, TRUTH)
    assert s["total_abs_count_error"] is None and s["items"][2]["detected"] is None
