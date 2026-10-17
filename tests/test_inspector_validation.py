"""Retry/fallback logic against MOCKED chat responses — no live AMD call (§11)."""

import base64
import io
import json

import pytest
from PIL import Image

from app import inspector
from app.models import InspectionError
from tests.conftest import make_image_bytes


def reply(items, notes=None):
    return json.dumps({"items": items, "notes": notes})


ALL_PRESENT = [
    {"item_id": "brand_a_cereal", "detected_count": 6, "status": "present", "confidence": 92},
    {"item_id": "brand_b_cereal", "detected_count": 4, "status": "present", "confidence": 88},
    {"item_id": "promo_sign", "detected_count": 1, "status": "present", "confidence": 95},
]


class FakeChat:
    """Returns queued replies in order and records every call's messages."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, settings, messages):
        self.calls.append(messages)
        return self.replies.pop(0)


def run(spec, image_bytes, settings, *replies):
    chat = FakeChat(*replies)
    return inspector.inspect(spec, image_bytes, settings, chat=chat), chat


def test_valid_reply_first_try(spec, image_bytes, settings):
    result, chat = run(spec, image_bytes, settings, reply(ALL_PRESENT, "all good"))
    assert len(chat.calls) == 1
    assert result.overall_status == "compliant"
    assert [i.status for i in result.items] == ["present"] * 3
    assert result.raw_model_notes == "all good"
    assert result.model_name == "test-vlm" and result.is_mock is False
    assert result.latency_s is not None


def test_markdown_fenced_json_is_accepted(spec, image_bytes, settings):
    result, chat = run(spec, image_bytes, settings, "```json\n" + reply(ALL_PRESENT) + "\n```")
    assert len(chat.calls) == 1 and result.overall_status == "compliant"


def test_prose_then_valid_uses_one_stricter_retry(spec, image_bytes, settings):
    result, chat = run(spec, image_bytes, settings, "The shelf looks fully stocked!", reply(ALL_PRESENT))
    assert len(chat.calls) == 2
    retry = chat.calls[1]
    assert retry[-2] == {"role": "assistant", "content": "The shelf looks fully stocked!"}
    assert "Return ONLY valid JSON" in retry[-1]["content"]
    assert result.overall_status == "compliant"


def test_invalid_status_triggers_retry(spec, image_bytes, settings):
    bad = [dict(ALL_PRESENT[0], status="out_of_stock")] + ALL_PRESENT[1:]
    result, chat = run(spec, image_bytes, settings, reply(bad), reply(ALL_PRESENT))
    assert len(chat.calls) == 2 and result.overall_status == "compliant"


def test_two_bad_replies_fall_back_to_needs_review_without_fabrication(spec, image_bytes, settings):
    result, chat = run(spec, image_bytes, settings, "no json here", "still no json")
    assert len(chat.calls) == 2  # exactly one retry
    assert result.overall_status == "needs_review"
    assert result.items == []  # no fabricated structured result
    assert result.raw_model_notes == "still no json"  # raw text surfaced to the user


def test_hallucinated_item_is_dropped(spec, image_bytes, settings):
    items = ALL_PRESENT + [{"item_id": "brand_z_soda", "detected_count": 3, "status": "present", "confidence": 99}]
    result, _ = run(spec, image_bytes, settings, reply(items))
    assert [i.item_id for i in result.items] == ["brand_a_cereal", "brand_b_cereal", "promo_sign"]


def test_omitted_item_is_needs_review_not_missing(spec, image_bytes, settings):
    result, _ = run(spec, image_bytes, settings, reply(ALL_PRESENT[:2]))
    sign = result.items[2]
    assert sign.item_id == "promo_sign"
    assert sign.status == "needs_review" and sign.confidence == 0
    assert result.overall_status == "needs_review"


def test_stockout_is_non_compliant(spec, image_bytes, settings):
    items = [dict(ALL_PRESENT[0], detected_count=0, status="missing")] + ALL_PRESENT[1:]
    result, _ = run(spec, image_bytes, settings, reply(items))
    assert result.overall_status == "non_compliant"
    assert result.items[0].status == "missing"


def test_misplaced_is_distinct_from_missing(spec, image_bytes, settings):
    items = [dict(ALL_PRESENT[1], status="misplaced")] + [ALL_PRESENT[0], ALL_PRESENT[2]]
    result, _ = run(spec, image_bytes, settings, reply(items))
    by_id = {i.item_id: i.status for i in result.items}
    assert by_id["brand_b_cereal"] == "misplaced"
    assert result.overall_status == "non_compliant"


def test_definite_failure_outranks_needs_review(spec, image_bytes, settings):
    items = [dict(ALL_PRESENT[0], detected_count=2, status="partial")]  # other two omitted
    result, _ = run(spec, image_bytes, settings, reply(items))
    assert result.overall_status == "non_compliant"


def test_expected_count_comes_from_spec_not_model(spec, image_bytes, settings):
    items = [dict(i, expected_count=999) for i in ALL_PRESENT]
    result, _ = run(spec, image_bytes, settings, reply(items))
    assert [i.expected_count for i in result.items] == [6, 4, 1]


def test_model_overall_verdict_is_ignored(spec, image_bytes, settings):
    items = [dict(ALL_PRESENT[0], detected_count=0, status="missing")] + ALL_PRESENT[1:]
    raw = json.dumps({"items": items, "overall_status": "compliant"})
    result, _ = run(spec, image_bytes, settings, raw)
    assert result.overall_status == "non_compliant"


def test_endpoint_error_propagates(spec, image_bytes, settings):
    def failing_chat(settings, messages):
        raise InspectionError("endpoint_unreachable", "Could not reach the AMD inference endpoint")

    with pytest.raises(InspectionError) as exc_info:
        inspector.inspect(spec, image_bytes, settings, chat=failing_chat)
    assert exc_info.value.stage == "endpoint_unreachable"


def test_prompt_contains_spec_and_image_but_no_money(spec, image_bytes, settings):
    _, chat = run(spec, image_bytes, settings, reply(ALL_PRESENT))
    messages = chat.calls[0]
    assert [m["role"] for m in messages] == ["user"]  # no system message: endpoint 500s on system + image
    user_content = messages[0]["content"]
    text = user_content[0]["text"]
    assert "Return ONLY a JSON object" in text
    assert "brand_a_cereal" in text and "expected count 6" in text
    assert "margin" not in text.lower() and "$" not in text
    assert user_content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


@pytest.mark.parametrize("fmt", ["JPEG", "PNG"])
def test_image_is_resized_to_max_dim(fmt):
    url = inspector.encode_image(make_image_bytes((3000, 1200), fmt))
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert max(img.size) == inspector.MAX_IMAGE_DIM and img.format == "JPEG"


def test_non_image_bytes_raise_invalid_image():
    with pytest.raises(InspectionError) as exc_info:
        inspector.encode_image(b"definitely not an image")
    assert exc_info.value.stage == "invalid_image"


# --- count-verifiability guards (financial safety) -----------------------------

STARS_OK = {"item_id": "brand_a_cereal", "shelf_counts": [3, 3], "detected_count": 6, "count_reliable": True,
            "status": "present", "confidence": 100}


def test_consistent_shelf_counts_keep_status_and_are_carried_through(spec, image_bytes, settings):
    result, _ = run(spec, image_bytes, settings, reply([STARS_OK] + ALL_PRESENT[1:]))
    a = result.items[0]
    assert a.status == "present" and a.shelf_counts == [3, 3]
    assert result.overall_status == "compliant"


def test_model_flagged_unreliable_count_becomes_needs_review(spec, image_bytes, settings):
    item = dict(STARS_OK, detected_count=5, shelf_counts=[3, 2], status="partial", count_reliable=False,
                note="glare on the top shelf")
    result, _ = run(spec, image_bytes, settings, reply([item] + ALL_PRESENT[1:]))
    a = result.items[0]
    assert a.status == "needs_review"  # not a confirmed 'partial' shortfall
    assert a.detected_count == 5  # the model's number is kept, not altered
    assert "does not support a reliable count" in a.note and "glare on the top shelf" in a.note
    assert result.overall_status == "needs_review"


def test_shelf_counts_not_summing_to_total_becomes_needs_review(spec, image_bytes, settings):
    item = dict(STARS_OK, shelf_counts=[3, 1], detected_count=6)
    result, _ = run(spec, image_bytes, settings, reply([item] + ALL_PRESENT[1:]))
    assert result.items[0].status == "needs_review"
    assert "[3, 1] sum to 4, not its total of 6" in result.items[0].note


def test_replies_without_new_fields_still_work(spec, image_bytes, settings):
    result, _ = run(spec, image_bytes, settings, reply(ALL_PRESENT))
    assert result.overall_status == "compliant" and result.items[0].shelf_counts is None


def test_negative_shelf_count_triggers_retry(spec, image_bytes, settings):
    bad = [dict(STARS_OK, shelf_counts=[7, -1])] + ALL_PRESENT[1:]
    result, chat = run(spec, image_bytes, settings, reply(bad), reply(ALL_PRESENT))
    assert len(chat.calls) == 2 and result.overall_status == "compliant"


def test_reliable_flag_true_is_not_treated_as_proof(spec, image_bytes, settings):
    # A short count the model calls reliable stays a reported shortfall; the flag adds no trust.
    item = dict(STARS_OK, shelf_counts=[3, 2], detected_count=5, status="partial", count_reliable=True)
    result, _ = run(spec, image_bytes, settings, reply([item] + ALL_PRESENT[1:]))
    assert result.items[0].status == "partial"


def test_prompt_asks_for_the_fields_the_parser_checks():
    for field in ("shelf_counts", "count_reliable", "shelves_visible", "TOP shelf to the BOTTOM shelf"):
        assert field in inspector.SYSTEM_PROMPT


def test_max_image_dim_is_read_at_call_time_and_never_enlarges(monkeypatch):
    def sent_size(url):
        return Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).size

    monkeypatch.setattr(inspector, "MAX_IMAGE_DIM", 1536)
    assert sent_size(inspector.encode_image(make_image_bytes((3000, 1500)))) == (1536, 768)
    assert sent_size(inspector.encode_image(make_image_bytes((1354, 1024)))) == (1354, 1024)  # native kept
    assert sent_size(inspector.encode_image(make_image_bytes((3000, 1500)), max_dim=1024)) == (1024, 512)
