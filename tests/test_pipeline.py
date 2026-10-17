"""Inspection -> calculator -> action note, as the UI runs it. AMD responses are MOCKED."""

import dataclasses
import json

import pytest

from app.models import InspectionError
from app.pipeline import MAX_UPLOAD_MB, run_inspection, validate_image

STOCKOUT_REPLY = json.dumps({"items": [
    {"item_id": "brand_a_cereal", "detected_count": 0, "status": "missing", "confidence": 90},
    {"item_id": "brand_b_cereal", "detected_count": 2, "status": "partial", "confidence": 80},
    {"item_id": "promo_sign", "detected_count": 1, "status": "present", "confidence": 95},
]})
NOTE_REPLY = json.dumps({"summary": "Refill the empty facings first.", "actions": [
    {"item_id": "brand_a_cereal", "instruction": "Fill the empty facings from back stock."},
    {"item_id": "brand_b_cereal", "instruction": "Top up the remaining gaps."},
]})


class QueueChat:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def __call__(self, settings, messages, **kwargs):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def test_result_flows_into_calculator_and_note(spec, image_bytes, settings):
    run = run_inspection(spec, image_bytes, settings, chat=QueueChat(STOCKOUT_REPLY, NOTE_REPLY))
    assert run.result.overall_status == "non_compliant"
    assert run.summary.estimated_exposure_usd == 9.20  # from the calculator, not the model
    assert run.note.source == "amd"
    assert run.note.item_actions == {
        "brand_a_cereal": "Fill the empty facings from back stock.",
        "brand_b_cereal": "Top up the remaining gaps.",
    }
    assert "Estimated Margin at Risk (Unverified): $9.20." in run.note.text


def test_note_failure_does_not_fail_the_run(spec, image_bytes, settings):
    chat = QueueChat(STOCKOUT_REPLY, InspectionError("endpoint_error", "AMD endpoint returned HTTP 429"))
    run = run_inspection(spec, image_bytes, settings, chat=chat)
    assert run.summary.estimated_exposure_usd == 9.20
    assert run.note.source == "template" and run.note.ai_attempted and "429" in run.note.fallback_reason


def test_inspection_failure_raises_for_the_ui(spec, image_bytes, settings):
    with pytest.raises(InspectionError) as exc_info:
        run_inspection(spec, image_bytes, settings,
                       chat=QueueChat(InspectionError("endpoint_unreachable", "no route")))
    assert exc_info.value.stage == "endpoint_unreachable"


def test_unvalidated_output_gives_no_figures_and_no_note(spec, image_bytes, settings):
    run = run_inspection(spec, image_bytes, settings, chat=QueueChat("prose", "more prose"))
    assert run.result.overall_status == "needs_review" and run.result.items == []
    assert run.summary.calculation_available is False
    assert run.note.source == "unavailable"


def test_mock_mode_end_to_end_is_labelled_and_offline(spec, image_bytes, settings, monkeypatch):
    from app import amd_client

    monkeypatch.setattr(amd_client.requests, "post", lambda *a, **k: pytest.fail("no HTTP in MOCK_MODE"))
    run = run_inspection(spec, image_bytes, dataclasses.replace(settings, mock_mode=True))
    assert run.result.is_mock is True
    assert "MOCK_MODE" in run.result.raw_model_notes
    assert run.note.source == "template" and "MOCK_MODE" in run.note.fallback_reason


@pytest.mark.parametrize("data, fragment", [
    (b"", "empty"),
    (b"not an image", "not a readable"),
    (b"\xff" * (MAX_UPLOAD_MB * 1024 * 1024 + 1), "larger than"),
])
def test_invalid_images_rejected_before_any_call(spec, settings, data, fragment):
    with pytest.raises(InspectionError) as exc_info:
        validate_image(data)
    assert exc_info.value.stage == "invalid_image" and fragment in exc_info.value.detail

    def forbid(*a, **k):
        raise AssertionError("no inference call for an invalid image")

    with pytest.raises(InspectionError):
        run_inspection(spec, data, settings, chat=forbid)
