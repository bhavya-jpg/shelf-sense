"""Opt-in end-to-end test against the REAL AMD endpoint. Run: pytest -m live -s"""

import pytest

from app import inspector
from app.config import REPO_ROOT, ConfigError, load_settings
from app.models import Spec

PHOTO = REPO_ROOT / "data" / "demo" / "compliant.png"
SPEC = REPO_ROOT / "specs" / "nestle_cereal_bay.json"


@pytest.mark.live
def test_live_inspection_on_demo_photo():
    try:
        settings = load_settings()
    except ConfigError as exc:
        pytest.skip(f"AMD endpoint not configured: {exc}")
    if settings.mock_mode:
        pytest.fail("MOCK_MODE is on — the live test must hit the real AMD endpoint")
    if not PHOTO.is_file():
        pytest.skip(f"missing self-taken demo photo: {PHOTO}")

    spec = Spec.load(SPEC)
    result = inspector.inspect(spec, PHOTO.read_bytes(), settings)

    print(result.model_dump_json(indent=2))
    assert result.is_mock is False
    assert result.items, f"model output was unparseable after retry: {result.raw_model_notes!r}"
    assert {i.item_id for i in result.items} == {i.item_id for i in spec.items}
