"""Per-shelf cropping experiment. Each shelf band from a crops file is inspected separately with
the unchanged inspector (same prompt, model, MAX_IMAGE_DIM, validation); the per-shelf counts are
then summed and statuses recomputed from the totals. Experiment only — the app is not changed.

    python -m eval.shelf_crop_experiment --truth data/demo/compliant.truth.json \
        --crops data/demo/compliant.crops.json --runs 3

Per-crop statuses from the model are ignored: the spec's expected counts are whole-bay totals, so a
model judging one shelf against them says "partial" for everything. Status comes from summed counts.
"""

import argparse
import base64
import dataclasses
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from app import amd_client, inspector
from app.config import REPO_ROOT, load_settings
from app.models import ComplianceResult, InspectionError, ItemCheck, Spec
from eval.count_experiment import OUT_DIR, score_run


def merge_shelf_results(spec: Spec, shelf_results: list[ComplianceResult]) -> ComplianceResult:
    """Combine one validated result per shelf into a whole-bay result. Pure function.

    - If any shelf has no validated items, or reports an item as needs_review, that item is
      needs_review (a partial sum is not a count).
    - If any shelf reports an item misplaced, it stays misplaced.
    - Otherwise the status follows the summed count: >= expected present, 0 missing, else partial.
    """
    checks = []
    for spec_item in spec.items:
        per_shelf = []
        for shelf in shelf_results:
            match = next((c for c in shelf.items if c.item_id == spec_item.item_id), None)
            per_shelf.append(match)
        counts = [c.detected_count if c else 0 for c in per_shelf]
        total = sum(counts)
        notes = "; ".join(f"shelf {n}: {c.note}" for n, c in enumerate(per_shelf, 1) if c and c.note)
        unusable = [n for n, c in enumerate(per_shelf, 1) if c is None or c.status == "needs_review"]
        if unusable:
            status = "needs_review"
            notes = f"No usable count for shelf {', '.join(map(str, unusable))}. " + notes
        elif any(c.status == "misplaced" for c in per_shelf):
            status = "misplaced"
        elif total >= spec_item.expected_count:
            status = "present"
        elif total == 0:
            status = "missing"
        else:
            status = "partial"
        checks.append(ItemCheck(
            item_id=spec_item.item_id,
            expected_count=spec_item.expected_count,
            detected_count=total,
            status=status,
            confidence=min((c.confidence for c in per_shelf if c), default=0.0),
            note=notes or None,
            shelf_counts=counts,
        ))
    return ComplianceResult(
        spec_id=spec.spec_id,
        items=checks,
        overall_status=inspector.derive_overall_status(checks),
        is_mock=any(r.is_mock for r in shelf_results),
        model_name=shelf_results[0].model_name if shelf_results else None,
        latency_s=round(sum(r.latency_s or 0 for r in shelf_results), 2),
    )


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", required=True)
    parser.add_argument("--crops", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--model", default=None, help="override MODEL_NAME for this run only")
    args = parser.parse_args()

    truth = json.loads(Path(args.truth).read_text())
    crops = json.loads(Path(args.crops).read_text())
    spec = Spec.load(REPO_ROOT / truth["spec"])
    settings = load_settings()
    if args.model:
        settings = dataclasses.replace(settings, model_name=args.model)
    if settings.mock_mode:
        print("MOCK_MODE is on; experiments must use the real endpoint.", file=sys.stderr)
        return 2

    full = inspector.load_image((REPO_ROOT / crops["image"]).read_bytes())
    shelf_bytes = [_png(full.crop(tuple(box))) for box in crops["shelves"]]
    sent_sizes = [
        list(Image.open(io.BytesIO(base64.b64decode(inspector.encode_image(b).split(",", 1)[1]))).size)
        for b in shelf_bytes
    ]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experiment": "per-shelf crops (hand-placed oracle bands)",
        "model": settings.model_name,
        "endpoint_host": settings.endpoint_host,
        "max_image_dim": inspector.MAX_IMAGE_DIM,
        "crops": crops,
        "image_sent_sizes": sent_sizes,
        "spec_id": spec.spec_id,
        "truth": truth,
        "runs": [],
    }
    print(f"crops={len(shelf_bytes)} sent={sent_sizes} model={settings.model_name} endpoint={settings.endpoint_host}")

    for n in range(1, args.runs + 1):
        run = {"run": n, "shelves": []}
        shelf_results = []
        for i, data in enumerate(shelf_bytes, 1):
            raws = []

            def chat(s, messages, **kwargs):
                reply = amd_client.chat_completion(s, messages, **kwargs)
                raws.append(reply)
                return reply

            started = time.perf_counter()
            try:
                result = inspector.inspect(spec, data, settings, chat=chat)
                shelf_results.append(result)
                run["shelves"].append({"shelf": i, "latency_s": result.latency_s, "raw_replies": raws,
                                       "result": result.model_dump()})
            except InspectionError as exc:
                run["shelves"].append({"shelf": i, "latency_s": round(time.perf_counter() - started, 2),
                                       "raw_replies": raws, "error": f"{exc.stage}: {exc.detail}"})
                print(f"run {n} shelf {i}: ERROR {exc.stage}: {exc.detail[:120]}")
                break
            time.sleep(2)

        if len(shelf_results) == len(shelf_bytes):
            merged = merge_shelf_results(spec, shelf_results)
            s = score_run(merged, truth)
            run.update(merged=merged.model_dump(), score=s, latency_s=merged.latency_s)
            per = ", ".join(f"{c.item_id} {c.detected_count}/{truth['counts'][c.item_id]} {c.shelf_counts} {c.status}"
                            for c in merged.items)
            print(f"run {n}: {merged.latency_s}s total | exact {s['exact_counts']}/{s['n_items']} | "
                  f"abs err {s['total_abs_count_error']} | overall {merged.overall_status} "
                  f"({'correct' if s['overall_correct'] else 'WRONG'}) | {per}")
        record["runs"].append(run)
        if n < args.runs:
            time.sleep(3)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = OUT_DIR / f"{stamp}_compliant_shelfcrops_{settings.model_name}.json"
    out.write_text(json.dumps(record, indent=2))
    print(f"recorded: {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
