"""Prompt construction, AMD call, parse/validate/retry (BLUEPRINT §8).

CLI: python -m app.inspector --spec specs/nestle_cereal_bay.json --image data/demo/compliant.png
"""

import argparse
import base64
import io
import json
import logging
import sys
import time
from typing import Callable

from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError

from app import amd_client
from app.config import ConfigError, Settings, load_settings
from app.models import ComplianceResult, InspectionError, ItemCheck, ModelItemObservation, ModelOutput, Spec

log = logging.getLogger(__name__)

MAX_IMAGE_DIM = 1024

SYSTEM_PROMPT = """You are a retail shelf-compliance inspector. You receive one shelf photo and a list of items the shelf is expected to contain.

How to count:
1. Look at the WHOLE image, edge to edge and top to bottom, and work out how many shelves are visible. Do not focus only on the most prominent shelves.
2. For each expected item, go shelf by shelf from the TOP shelf to the BOTTOM shelf and count that item's packages on each shelf.
3. An item can appear on several shelves, including shelves that are not next to each other. Check every visible shelf for every item.
4. Count individual physical packages you can see; each box counts once. Do not estimate, round, or count hidden stock behind the visible packages.
5. Distinguish visually different variants where possible and mention them in the note. If the item label says "any variant", count all its variants under that item; never count a different brand.
6. Never count the same package twice.
7. Count a partially hidden package only if enough of it is visible to identify the product.
8. If the image does not support a reliable count for an item (glare, blur, heavy occlusion, cut off at the edge), set count_reliable to false and say why in the note.
9. Never conclude an item is missing or short because you did not notice it on one shelf. Finish checking every shelf first.

For EACH expected item, report:
- item_id: exactly as given in the list
- shelf_counts: packages of that item on each visible shelf, top shelf first (one integer per shelf, 0 where there are none)
- detected_count: the total, equal to the sum of shelf_counts
- count_reliable: true if the image supports a reliable count, otherwise false
- status: exactly one of
    "present"   - at least the expected count is visible, in its expected place
    "partial"   - some, but fewer than the expected count, are visible
    "missing"   - none are visible
    "misplaced" - the item is visible but in the wrong position, or mixed in with a different product
- confidence: number from 0 to 100, how sure you are
- note: one short sentence describing what you saw

Only count something as an item if you can clearly identify it as that product from its packaging. Objects that merely share a colour or shape with an item do not count. If the photo is not a retail shelf, report every item with detected_count 0.

Report only items from the list. Do not invent items. Do not compute prices, totals or an overall verdict.

Return ONLY a JSON object, with no markdown and no text before or after it, in exactly this shape:
{"shelves_visible": 0, "items": [{"item_id": "...", "shelf_counts": [0], "detected_count": 0, "count_reliable": true, "status": "present", "confidence": 0, "note": "..."}], "notes": "optional one-sentence overall observation"}"""

STRICT_RETRY_PROMPT = (
    "Your previous reply could not be used ({error}). "
    "Return ONLY valid JSON matching the schema in the instructions: a single object with an "
    '"items" array. Use only the status values "present", "partial", "missing", "misplaced". '
    "No markdown fences, no text before or after the JSON."
)

ChatFn = Callable[[Settings, list[dict]], str]


def render_spec(spec: Spec) -> str:
    """Spec as readable prompt text. Margins/sales are deliberately left out — money is code-only."""
    lines = [f"Shelf location: {spec.location}", "Expected items:"]
    for item in spec.items:
        lines.append(f'- item_id "{item.item_id}": {item.label}, expected count {item.expected_count}')
    return "\n".join(lines)


def load_image(image_bytes: bytes) -> Image.Image:
    """Decode, EXIF-rotate and convert to RGB — the image the model is shown (before resizing)."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return ImageOps.exif_transpose(img).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InspectionError("invalid_image", "File is not a readable JPEG/PNG image") from exc


def encode_image(image_bytes: bytes, max_dim: int | None = None) -> str:
    """Return a JPEG data URL, EXIF-rotated and shrunk (never enlarged) so the longest side is
    <= max_dim (default: MAX_IMAGE_DIM, read at call time so experiments can override it)."""
    max_dim = max_dim or MAX_IMAGE_DIM
    img = load_image(image_bytes)
    img.thumbnail((max_dim, max_dim))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build_messages(spec: Spec, image_data_url: str) -> list[dict]:
    # Instructions go in the user turn, not a system message: the Token Factory Gemma-4-31B-IT
    # deployment returns HTTP 500 for system message + image (verified 2026-10-17).
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": SYSTEM_PROMPT + "\n\n" + render_spec(spec)},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ],
        },
    ]


def parse_model_output(raw: str) -> ModelOutput:
    """Parse the model's reply. Raises ValueError / ValidationError on anything unusable."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end < start:
        raise ValueError("no JSON object found in reply")
    return ModelOutput.model_validate(json.loads(raw[start : end + 1]))


def derive_overall_status(items: list[ItemCheck]) -> str:
    """The verdict is computed by code from per-item statuses, never taken from the model."""
    statuses = {i.status for i in items}
    if statuses & {"missing", "partial", "misplaced"}:
        return "non_compliant"
    if "needs_review" in statuses:
        return "needs_review"
    return "compliant"


def unverifiable_count_reason(obs: ModelItemObservation) -> str | None:
    """Why a reported count can't be relied on, or None. Deterministic checks only; note that a
    model reporting its count as reliable is NOT evidence that the count is correct."""
    if obs.count_reliable is False:
        return "The model reported that the image does not support a reliable count."
    if obs.shelf_counts is not None and sum(obs.shelf_counts) != obs.detected_count:
        return (
            f"The model's per-shelf counts {obs.shelf_counts} sum to {sum(obs.shelf_counts)}, "
            f"not its total of {obs.detected_count}."
        )
    return None


def build_result(spec: Spec, output: ModelOutput) -> ComplianceResult:
    spec_items = {item.item_id: item for item in spec.items}
    observed = {}
    for obs in output.items:
        if obs.item_id not in spec_items:
            log.warning("dropping item not in spec: %r", obs.item_id)
            continue
        if obs.item_id in observed:
            log.warning("duplicate item from model, keeping first: %r", obs.item_id)
            continue
        observed[obs.item_id] = obs

    checks = []
    for item_id, spec_item in spec_items.items():
        obs = observed.get(item_id)
        if obs is None:
            # The model said nothing about this item — that is not the same claim as "missing".
            checks.append(
                ItemCheck(
                    item_id=item_id,
                    expected_count=spec_item.expected_count,
                    detected_count=0,
                    status="needs_review",
                    confidence=0.0,
                    note="Model did not report on this item.",
                )
            )
        else:
            review_reason = unverifiable_count_reason(obs)
            checks.append(
                ItemCheck(
                    item_id=item_id,
                    expected_count=spec_item.expected_count,
                    detected_count=obs.detected_count,
                    # An unverifiable count must not feed the financial estimate: needs_review
                    # is excluded from it ($0) and stays visible as unresolved.
                    status="needs_review" if review_reason else obs.status,
                    confidence=obs.confidence,
                    note=f"{review_reason} Model note: {obs.note or '-'}" if review_reason else obs.note,
                    shelf_counts=obs.shelf_counts,
                )
            )

    return ComplianceResult(
        spec_id=spec.spec_id,
        items=checks,
        overall_status=derive_overall_status(checks),
        raw_model_notes=output.notes,
    )


def inspect(
    spec: Spec,
    image_bytes: bytes,
    settings: Settings,
    *,
    chat: ChatFn = amd_client.chat_completion,
) -> ComplianceResult:
    """One inspection: image + spec -> validated ComplianceResult. Raises InspectionError on endpoint failure."""
    messages = build_messages(spec, encode_image(image_bytes))
    started = time.perf_counter()

    raw = chat(settings, messages)
    try:
        output = parse_model_output(raw)
    except (ValueError, ValidationError) as exc:
        log.warning("model reply unusable, retrying with stricter prompt: %s", str(exc)[:300])
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": STRICT_RETRY_PROMPT.format(error=str(exc)[:300])},
        ]
        raw = chat(settings, retry_messages)
        try:
            output = parse_model_output(raw)
        except (ValueError, ValidationError) as exc2:
            log.warning("retry also unusable, returning needs_review: %s", str(exc2)[:300])
            output = None

    latency_s = round(time.perf_counter() - started, 2)
    if output is None:
        # No fabricated structure: show the raw text, and downstream code must not compute on it.
        result = ComplianceResult(
            spec_id=spec.spec_id, items=[], overall_status="needs_review", raw_model_notes=raw
        )
    else:
        result = build_result(spec, output)

    result.is_mock = settings.mock_mode
    result.model_name = settings.model_name or None
    result.latency_s = latency_s
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one Shelf-Sense inspection against the AMD endpoint.")
    parser.add_argument("--spec", required=True, help="path to spec JSON")
    parser.add_argument("--image", required=True, help="path to shelf photo (JPEG/PNG)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)

    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    spec = Spec.load(args.spec)
    with open(args.image, "rb") as f:
        image_bytes = f.read()

    if settings.mock_mode:
        print("*** MOCK_MODE IS ON — this is NOT a real AMD inference result ***", file=sys.stderr)
    else:
        print(f"AMD endpoint: {settings.endpoint_host}  model: {settings.model_name}", file=sys.stderr)

    try:
        result = inspect(spec, image_bytes, settings)
    except InspectionError as exc:
        print(f"Inspection failed [{exc.stage}]: {exc.detail}", file=sys.stderr)
        return 1

    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
