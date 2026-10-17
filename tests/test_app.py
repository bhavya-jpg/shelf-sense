"""Streamlit UI driven headlessly with streamlit.testing.AppTest. No real AMD calls:
runs use MOCK_MODE or an unreachable local URL."""

import html
import io
import re

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from app.config import REPO_ROOT

APP = str(REPO_ROOT / "app" / "app.py")


@pytest.fixture
def demo_dir(tmp_path):
    buf = io.BytesIO()
    Image.new("RGB", (1200, 900), (180, 160, 120)).save(buf, format="JPEG")
    (tmp_path / "synthetic.jpg").write_bytes(buf.getvalue())
    (tmp_path / "broken.png").write_bytes(b"not an image")
    return tmp_path


@pytest.fixture
def env(monkeypatch, demo_dir):
    for var in ("AMD_API_URL", "AMD_API_KEY", "MODEL_NAME", "MOCK_MODE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SHELF_SENSE_DOTENV", str(demo_dir / "no.env"))  # never read the real .env
    monkeypatch.setenv("SHELF_SENSE_DEMO_DIR", str(demo_dir))
    monkeypatch.setenv("SHELF_SENSE_SPEC_DIR", str(REPO_ROOT / "tests" / "fixtures"))
    return monkeypatch


def start():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def texts(elements):
    return " ".join(e.value for e in elements)


def page_text(at) -> str:
    """Visible text of the custom HTML components and markdown (tags stripped, entities decoded)."""
    raw = texts(at.markdown) + " " + texts(at.caption)
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def test_app_starts_and_loads_spec_in_mock_mode(env):
    env.setenv("MOCK_MODE", "true")
    at = start()
    assert "Shelf-Sense" in page_text(at)
    assert "MOCK MODE" in page_text(at)
    assert at.selectbox(key="spec_name").value == "cereal_endcap"  # tests/fixtures/cereal_endcap.json
    assert "Aisle 4 endcap" in texts(at.markdown) and "cereal_endcap_v1" in texts(at.markdown)
    assert at.button(key="run").disabled  # no photo yet
    assert "Results appear here" in page_text(at)


def test_missing_config_is_explained_and_blocks_runs(env):
    at = start()
    assert "Inference is not configured" in page_text(at)
    at.button(key="demo_synthetic").click().run()
    assert at.button(key="run").disabled


def test_invalid_image_is_rejected_without_inference(env):
    env.setenv("MOCK_MODE", "true")
    at = start()
    at.button(key="demo_broken").click().run()
    assert not at.exception
    assert "not a readable JPEG/PNG image" in page_text(at)
    assert at.button(key="run").disabled


def test_mock_run_shows_labelled_results(env):
    env.setenv("MOCK_MODE", "true")
    at = start()
    at.button(key="demo_synthetic").click().run()
    assert not at.button(key="run").disabled
    at.button(key="run").click().run()
    assert not at.exception
    text = page_text(at)
    assert "MOCK RESULT" in text
    assert "Non-compliant" in text
    # Stat strip: label and value of the unverified estimate (mock: Brand B 2 of 4 x $1.00).
    assert re.search(r"Estimated Margin at Risk \(Unverified\)\s+\$2\.00", text)
    assert "AI-estimated counts" in text  # unverified-estimate notice is shown
    assert "confirmed" not in text.lower()
    assert "Product results" in text and "Brand B Cereal Box" in text  # results table rendered
    assert "MOCK_MODE" in text  # action note labelled as template due to mock
    assert "Deterministic template" in text and "AMD-worded" not in text
    assert "revenue at risk" not in text.lower()


def test_amd_failure_is_shown_with_retry_not_a_crash(env):
    env.setenv("AMD_API_URL", "http://127.0.0.1:9/v1")  # nothing listens here
    env.setenv("MODEL_NAME", "test-model")
    at = start()
    at.button(key="demo_synthetic").click().run()
    at.button(key="run").click().run()
    assert not at.exception
    assert "Could not reach the AMD inference endpoint" in page_text(at)
    assert at.button(key="retry_button")


def test_rerun_does_not_repeat_inference(env, monkeypatch):
    env.setenv("MOCK_MODE", "true")
    at = start()
    at.button(key="demo_synthetic").click().run()
    at.button(key="run").click().run()
    first = at.session_state["outcome"]["run"]
    at.run()  # an unrelated rerun
    assert at.session_state["outcome"]["run"] is first


def test_streamlit_upload_limit_matches_app_limit():
    import tomllib

    from app.pipeline import MAX_UPLOAD_MB

    config = tomllib.loads((REPO_ROOT / ".streamlit" / "config.toml").read_text())
    assert config["server"]["maxUploadSize"] == MAX_UPLOAD_MB
