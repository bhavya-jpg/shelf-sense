"""Record real footage of the running Shelf-Sense app (real AMD inference) for the demo video.

Usage: <python with playwright> scripts/capture.py [base_url]   (default http://localhost:8501)
Writes remotion/public/footage/{landing,inspect}.webm and remotion/src/data/capture.json (event marks,
seconds from the start of each clip). Nothing is staged: the inspection is a real call, its latency is
whatever the endpoint takes, and the marks record when each step actually happened.
"""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FOOT = ROOT / "remotion" / "public" / "footage"
DATA = ROOT / "remotion" / "src" / "data" / "capture.json"
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
VIEW = {"width": 1280, "height": 720}  # CSS px; rendered at 1.5x into a 1920x1080 video, so UI text is legible
SIZE = {"width": 1920, "height": 1080}
STILLS = ROOT / "stills"
MAIN = '[data-testid="stMain"]'


def smooth_scroll(page, to_y: float, seconds: float, steps_per_s: int = 30) -> None:
    start = page.evaluate(f"document.querySelector('{MAIN}').scrollTop")
    n = max(1, int(seconds * steps_per_s))
    for i in range(1, n + 1):
        t = i / n
        e = t * t * (3 - 2 * t)  # smoothstep
        page.evaluate(f"document.querySelector('{MAIN}').scrollTo(0, {start + (to_y - start) * e})")
        time.sleep(1 / steps_per_s)


def y_of(page, selector: str, offset: int = 120) -> float:
    """Scroll position that puts the first element matching a Playwright selector `offset` px below the top."""
    return page.locator(selector).first.evaluate(
        "(el, off) => el.getBoundingClientRect().top + document.querySelector('[data-testid=\"stMain\"]').scrollTop - off",
        offset,
    )


def record(browser, name: str, fn) -> dict:
    ctx = browser.new_context(viewport=VIEW, device_scale_factor=1.5, record_video_dir=str(FOOT / "_raw"), record_video_size=SIZE)
    page = ctx.new_page()
    t0 = time.time()
    marks = fn(page, lambda: round(time.time() - t0, 2))
    video = page.video
    ctx.close()
    Path(video.path()).rename(FOOT / f"{name}.webm")
    marks["seconds"] = round(time.time() - t0, 2)
    print(name, marks, flush=True)
    return marks


def shot(page, name: str) -> None:
    """A 1920x1080 still of the current state, from the same session as the footage."""
    STILLS.mkdir(exist_ok=True)
    page.screenshot(path=str(STILLS / f"{name}.png"))


def landing(page, now):
    m = {}
    page.goto(BASE + "/")
    page.locator(".ss-wordmark").wait_for(timeout=60000)
    time.sleep(2.5)
    m["loaded"] = now()
    shot(page, "landing_hero")
    time.sleep(2.0)
    smooth_scroll(page, y_of(page, ".ss-frame", 140), 2.4)
    time.sleep(1.6)
    m["product_frame"] = now()
    smooth_scroll(page, y_of(page, ".ss-cols4", 260), 3.0)
    time.sleep(1.8)
    m["problem"] = now()
    shot(page, "landing_problem")
    smooth_scroll(page, y_of(page, ".ss-how", 220), 2.6)
    time.sleep(1.8)
    m["how"] = now()
    smooth_scroll(page, y_of(page, ".ss-nums", 300), 2.6)
    time.sleep(2.0)
    m["evidence"] = now()
    shot(page, "landing_evidence")
    smooth_scroll(page, y_of(page, ".ss-story", 160), 2.2)
    time.sleep(2.0)
    m["honest"] = now()
    shot(page, "landing_honest")
    return m


def inspect(page, now):
    m = {}
    page.goto(BASE + "/inspect")
    page.get_by_text("Results appear here").wait_for(timeout=60000)
    time.sleep(2.0)
    m["loaded"] = now()
    page.locator('[data-testid="stSelectbox"]').click()
    time.sleep(0.9)
    page.get_by_role("option", name="nestle_cereal_bay").click()
    time.sleep(1.2)
    m["spec"] = now()
    smooth_scroll(page, y_of(page, ".ss-label:has-text('Demo photo')", 360), 1.6)
    time.sleep(0.6)
    page.get_by_role("button", name="Compliant").click()
    page.locator(".ss-file").wait_for(timeout=30000)
    time.sleep(1.4)
    m["photo"] = now()
    shot(page, "inspect_photo")
    smooth_scroll(page, y_of(page, ".ss-file", 520), 1.4)
    time.sleep(0.8)
    page.get_by_role("button", name="Run inspection").click()
    m["run"] = now()
    page.locator(".ss-proc").wait_for(timeout=20000)
    smooth_scroll(page, y_of(page, ".ss-section >> nth=1", 110), 1.2)
    m["processing"] = now()
    shot(page, "inspect_processing")
    page.locator(".ss-verdict").wait_for(timeout=300000)
    m["result"] = now()
    time.sleep(1.0)
    smooth_scroll(page, y_of(page, ".ss-section >> nth=1", 110), 0.8)
    time.sleep(3.2)
    m["verdict_hold"] = now()
    shot(page, "inspect_verdict")
    smooth_scroll(page, y_of(page, ".ss-label:has-text('Discrepancies')", 160), 2.2)
    time.sleep(3.0)
    m["table"] = now()
    shot(page, "inspect_table")
    smooth_scroll(page, y_of(page, ".ss-actions", 120), 2.4)
    time.sleep(3.6)
    m["actions"] = now()
    shot(page, "inspect_actions")
    smooth_scroll(page, y_of(page, ".ss-src-caption", 560), 1.4)
    time.sleep(2.4)
    m["caption"] = now()
    m["result_text"] = {
        "verdict": page.locator(".ss-verdict-v").inner_text(),
        "run_meta": page.locator(".ss-run-meta").inner_text(),
        "stats": page.locator(".ss-stats").inner_text(),
        "note_source": page.locator(".ss-src").first.inner_text(),
    }
    return m


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    out = {"base": BASE, "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "clips": {}}
    out["clips"]["landing"] = record(browser, "landing", landing)
    out["clips"]["inspect"] = record(browser, "inspect", inspect)
    browser.close()
DATA.parent.mkdir(parents=True, exist_ok=True)
DATA.write_text(json.dumps(out, indent=1))
print("wrote", DATA)
