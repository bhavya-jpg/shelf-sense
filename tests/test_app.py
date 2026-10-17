"""Streamlit UI driven headlessly with streamlit.testing.AppTest. No real AMD calls:
runs use MOCK_MODE or an unreachable local URL."""

import io

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


def test_app_starts_and_loads_spec_in_mock_mode(env):
    env.setenv("MOCK_MODE", "true")
    at = start()
    assert at.title[0].value == "Shelf-Sense"
    assert "MOCK MODE" in texts(at.warning)
    assert at.selectbox(key="spec_name").value == "cereal_endcap"  # tests/fixtures/cereal_endcap.json
    assert "Aisle 4 endcap" in texts(at.markdown) and "cereal_endcap_v1" in texts(at.markdown)
    assert at.button(key="run").disabled  # no photo yet
    assert "Results appear here" in texts(at.info)


def test_missing_config_is_explained_and_blocks_runs(env):
    at = start()
    assert "Inference is not configured" in texts(at.error)
    at.button(key="demo_synthetic").click().run()
    assert at.button(key="run").disabled


def test_invalid_image_is_rejected_without_inference(env):
    env.setenv("MOCK_MODE", "true")
    at = start()
    at.button(key="demo_broken").click().run()
    assert not at.exception
    assert "not a readable JPEG/PNG image" in texts(at.error)
    assert at.button(key="run").disabled


def test_mock_run_shows_labelled_results(env):
    env.setenv("MOCK_MODE", "true")
    at = start()
    at.button(key="demo_synthetic").click().run()
    assert not at.button(key="run").disabled
    at.button(key="run").click().run()
    assert not at.exception
    assert "MOCK RESULT" in texts(at.warning)
    assert "Non-compliant" in texts(at.error)
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Estimated Margin at Risk (Unverified)"] == "$2.00"
    assert "AI-estimated counts" in texts(at.info)  # unverified-estimate notice is shown
    assert "confirmed" not in (texts(at.markdown) + texts(at.caption) + texts(at.warning)).lower()  # mock: Brand B 2 of 4 x $1.00
    assert len(at.dataframe) == 2  # spec table + results table
    assert "MOCK_MODE" in texts(at.caption)  # action note labelled as template due to mock
    assert "revenue at risk" not in (texts(at.markdown) + texts(at.caption)).lower()


def test_amd_failure_is_shown_with_retry_not_a_crash(env):
    env.setenv("AMD_API_URL", "http://127.0.0.1:9/v1")  # nothing listens here
    env.setenv("MODEL_NAME", "test-model")
    at = start()
    at.button(key="demo_synthetic").click().run()
    at.button(key="run").click().run()
    assert not at.exception
    assert "Could not reach the AMD inference endpoint" in texts(at.error)
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
