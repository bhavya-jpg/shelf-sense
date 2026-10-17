import pytest
from pydantic import ValidationError

from app.config import REPO_ROOT
from tests.conftest import FIXTURES
from app.models import ItemCheck, ModelItemObservation, ModelOutput, Spec


def obs(**overrides):
    data = {"item_id": "brand_a_cereal", "detected_count": 3, "status": "partial", "confidence": 70}
    data.update(overrides)
    return data


def test_real_specs_load():
    paths = sorted((REPO_ROOT / "specs").glob("*.json"))
    assert paths
    for path in paths:
        spec = Spec.load(path)
        assert all(i.unit_margin_usd is not None for i in spec.items), path


def test_fixture_spec_loads():
    spec = Spec.load(FIXTURES / "cereal_endcap.json")
    assert spec.spec_id == "cereal_endcap_v1"
    assert [i.item_id for i in spec.items] == ["brand_a_cereal", "brand_b_cereal", "promo_sign"]


def test_valid_observation_parses():
    o = ModelItemObservation.model_validate(obs(note="three boxes"))
    assert o.status == "partial" and o.detected_count == 3 and o.note == "three boxes"


@pytest.mark.parametrize("raw, expected", [(150, 100.0), (-5, 0.0), (55.5, 55.5)])
def test_confidence_is_clamped_not_rejected(raw, expected):
    assert ModelItemObservation.model_validate(obs(confidence=raw)).confidence == expected
    check = ItemCheck(item_id="x", expected_count=1, detected_count=1, status="present", confidence=raw)
    assert check.confidence == expected


@pytest.mark.parametrize("status", ["needs_review", "absent", "OK", ""])
def test_model_may_not_use_other_statuses(status):
    # needs_review is code-assigned only; the model must stick to the 4 literals.
    with pytest.raises(ValidationError):
        ModelItemObservation.model_validate(obs(status=status))


def test_item_check_accepts_code_assigned_needs_review():
    c = ItemCheck(item_id="x", expected_count=1, detected_count=0, status="needs_review", confidence=0)
    assert c.status == "needs_review"


@pytest.mark.parametrize("count", [-1, 2.5, "many"])
def test_detected_count_must_be_non_negative_int(count):
    with pytest.raises(ValidationError):
        ModelItemObservation.model_validate(obs(detected_count=count))


@pytest.mark.parametrize("field", ["item_id", "detected_count", "status", "confidence"])
def test_missing_required_field_rejected(field):
    data = obs()
    del data[field]
    with pytest.raises(ValidationError):
        ModelItemObservation.model_validate(data)


def test_model_output_requires_items_list():
    with pytest.raises(ValidationError):
        ModelOutput.model_validate({"notes": "looks fine"})


def test_spec_rejects_negative_expected_count():
    with pytest.raises(ValidationError):
        Spec.model_validate(
            {"spec_id": "s", "location": "l", "items": [
                {"item_id": "a", "label": "A", "expected_count": -1, "unit_margin_usd": 1, "est_daily_unit_sales": 1}
            ]}
        )
