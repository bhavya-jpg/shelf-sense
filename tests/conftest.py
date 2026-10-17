import io

import pytest
from PIL import Image

from app.config import REPO_ROOT, Settings
from app.models import ComplianceResult, ItemCheck, Spec

FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def spec() -> Spec:
    return Spec.load(FIXTURES / "cereal_endcap.json")  # placeholder spec used by unit tests


@pytest.fixture
def settings() -> Settings:
    return Settings(api_url="https://amd.example.test/v1", api_key="test-key", model_name="test-vlm", mock_mode=False)


def make_image_bytes(size=(2000, 1500), fmt="JPEG") -> bytes:
    """Synthetic solid-colour image — used only to exercise encoding, never as demo/eval data."""
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 180, 120)).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def image_bytes() -> bytes:
    return make_image_bytes()


EXPECTED = {"brand_a_cereal": 6, "brand_b_cereal": 4, "promo_sign": 1}


def make_result(overrides=None, spec_id="cereal_endcap_v1"):
    """All items present, with per-item (status, detected_count) overrides."""
    overrides = overrides or {}
    items = []
    for item_id, expected in EXPECTED.items():
        status, detected = overrides.get(item_id, ("present", expected))
        items.append(ItemCheck(item_id=item_id, expected_count=expected, detected_count=detected,
                               status=status, confidence=90))
    return ComplianceResult(spec_id=spec_id, items=items, overall_status="non_compliant")


def by_id(summary):
    return {i.item_id: i for i in summary.items}


def spec_with(spec, item_id, **changes):
    data = spec.model_dump()
    for item in data["items"]:
        if item["item_id"] == item_id:
            item.update(changes)
    return Spec.model_validate(data)
