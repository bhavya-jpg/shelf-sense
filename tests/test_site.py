"""Site pages: router smoke test, landing/method markup, and the landing figures checked against
the recorded experiments so the marketing copy can't drift from the evidence."""

import glob
import json
import statistics
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from streamlit.testing.v1 import AppTest

from app import site
from app.config import REPO_ROOT


def test_router_renders_navbar_and_footer(monkeypatch, tmp_path):
    monkeypatch.setenv("SHELF_SENSE_DOTENV", str(tmp_path / "no.env"))
    at = AppTest.from_file(str(REPO_ROOT / "app" / "app.py"), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "Shelf-Sense" in text and "ss-footer" in text and "MIT licence" in text


def test_landing_sections_render_and_cite_sources():
    page = "".join([site.hero_top(), site.hero_lede(), site.product_frame(), site.problem_section(),
                    site.how_section(), site.features_section(), site.evidence_section(),
                    site.honest_section(), site.amd_section(), site.final_cta()])
    for phrase in ("Shelf", "Shelves are still", "Count on AMD", "Measured,", "Honest by design",
                   "Every inspection", "docs/experiments/", "a case study, not a benchmark"):
        assert phrase in page
    assert "/app/static/product.jpg" in page and "/app/static/shelf.jpg" in page
    assert "revenue at risk" not in page.lower() and "confirmed" not in page.lower()


def test_static_images_exist():
    for name in ("product.jpg", "shelf.jpg"):
        assert (REPO_ROOT / "app" / "static" / name).stat().st_size > 10_000


def test_marquee_duplicates_items_for_a_seamless_loop():
    out = site.marquee(["Alpha", "Beta"])
    assert out.count("Alpha") == 2 and 'aria-hidden="true"' in out


def test_method_page_sections():
    page = site.method_head() + site.method_flow() + site.method_money() + site.method_evaluation() + site.method_limits()
    assert "Estimated Margin at Risk (Unverified)" in page and "MiniCPM-V-4.7-35B-A3B" in page
    assert "What we" in page and "Verified" in page


def test_landing_figures_match_the_experiment_records():
    records = [json.loads(Path(f).read_text()) for f in glob.glob(str(REPO_ROOT / "docs" / "experiments" / "*.json"))]
    assert len(records) == site.FACTS["experiment_records"]

    production = [  # whole image, production prompt, 1024 px, Gemma, successful runs
        run for rec in records
        if rec.get("prompt_variant") == "current" and rec.get("max_image_dim", 1024) == 1024
        and rec.get("model") == "Gemma-4-31B-IT" and "shelfcrops" not in rec.get("experiment", "")
        for run in rec["runs"] if run.get("score")
    ]
    latencies = [r["latency_s"] for r in production]
    assert len(production) == site.FACTS["production_runs"]
    def one_dp(x):  # half-up on the recorded decimal value, as the README/site round it (18.15 -> 18.2)
        return str(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    assert one_dp(statistics.median(latencies)) == site.FACTS["median_latency_s"]
    assert site.FACTS["latency_range"] == f"{one_dp(min(latencies))}–{one_dp(max(latencies))} s"
    assert sum(r["score"]["overall_correct"] for r in production) == 0  # the "0/9" claim

    baseline = [run["score"]["total_abs_count_error"] for rec in records if rec.get("prompt_variant") == "baseline_v1"
                for run in rec["runs"]]
    assert set(baseline) == {site.FACTS["error_before"]}
    assert min(r["score"]["total_abs_count_error"] for r in production) == site.FACTS["error_after"]
