"""Controlled counting experiment: one image, one spec, one ground-truth file, one prompt variant,
N real calls to the configured AMD endpoint. Every run, including the raw model replies, is
recorded to docs/experiments/ so results can be compared and replayed later.

    python -m eval.count_experiment --truth data/demo/compliant.truth.json --prompt baseline_v1 --runs 2
    python -m eval.count_experiment --truth data/demo/compliant.truth.json --prompt current --runs 2
    python -m eval.count_experiment --truth data/demo/compliant.truth.json --max-dim 1536 --runs 3
    python -m eval.count_experiment --truth data/demo/compliant.truth.json --model MiniCPM-V-4.7-35B-A3B --runs 3

--prompt current uses app/inspector.py as it is; any other name loads eval/prompts/<name>.txt and
swaps it in for this process only. --max-dim likewise overrides inspector.MAX_IMAGE_DIM for this
process only, and --model overrides MODEL_NAME for this process only (.env is not touched).
App behaviour is never changed by this script.
"""

import argparse
import dataclasses
import base64
import hashlib
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from PIL import Image

from app import amd_client, inspector
from app.config import REPO_ROOT, load_settings
from app.models import ComplianceResult, InspectionError, Spec

PROMPT_DIR = REPO_ROOT / "eval" / "prompts"
OUT_DIR = REPO_ROOT / "docs" / "experiments"


def score_run(result: ComplianceResult, truth: dict) -> dict:
    """Compare one result with the ground truth. Pure function."""
    counts, statuses = truth["counts"], truth["statuses"]
    by_id = {i.item_id: i for i in result.items}
    rows = []
    for item_id, true_count in counts.items():
        item = by_id.get(item_id)
        detected = item.detected_count if item else None
        status = item.status if item else None
        rows.append({
            "item_id": item_id,
            "truth": true_count,
            "detected": detected,
            "error": None if detected is None else detected - true_count,
            "status": status,
            "truth_status": statuses[item_id],
            "count_correct": detected == true_count,
            "status_correct": status == statuses[item_id],
        })
    errors = [abs(r["error"]) for r in rows if r["error"] is not None]
    return {
        "items": rows,
        "exact_counts": sum(r["count_correct"] for r in rows),
        "correct_statuses": sum(r["status_correct"] for r in rows),
        "n_items": len(rows),
        "total_abs_count_error": sum(errors) if len(errors) == len(rows) else None,
        "overall_status": result.overall_status,
        "overall_correct": result.overall_status == truth["overall_status"],
    }


def _prompt_text(name: str) -> str:
    return inspector.SYSTEM_PROMPT if name == "current" else (PROMPT_DIR / f"{name}.txt").read_text()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", required=True)
    parser.add_argument("--prompt", default="current")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--max-dim", type=int, default=None, help="override inspector.MAX_IMAGE_DIM")
    parser.add_argument("--model", default=None, help="override MODEL_NAME for this run only")
    args = parser.parse_args()

    truth = json.loads(Path(args.truth).read_text())
    spec = Spec.load(REPO_ROOT / truth["spec"])
    image_bytes = (REPO_ROOT / truth["image"]).read_bytes()
    settings = load_settings()
    if args.model:
        settings = dataclasses.replace(settings, model_name=args.model)
    if settings.mock_mode:
        print("MOCK_MODE is on; experiments must use the real endpoint.", file=sys.stderr)
        return 2

    prompt = _prompt_text(args.prompt)
    max_dim = args.max_dim or inspector.MAX_IMAGE_DIM
    sent = Image.open(io.BytesIO(base64.b64decode(inspector.encode_image(image_bytes, max_dim).split(",", 1)[1])))
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompt_variant": args.prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()[:12],
        "model": settings.model_name,
        "endpoint_host": settings.endpoint_host,
        "image": truth["image"],
        "max_image_dim": max_dim,
        "image_sent_size": list(sent.size),
        "spec_id": spec.spec_id,
        "truth": truth,
        "runs": [],
    }
    print(f"prompt={args.prompt} ({record['prompt_sha256']})  max_dim={max_dim}  model={settings.model_name}  "
          f"endpoint={settings.endpoint_host}  sent={sent.size[0]}x{sent.size[1]}")

    for n in range(1, args.runs + 1):
        raws = []

        def chat(s, messages, **kwargs):
            reply = amd_client.chat_completion(s, messages, **kwargs)
            raws.append(reply)
            return reply

        run = {"run": n, "raw_replies": raws}
        started = time.perf_counter()
        try:
            with mock.patch.object(inspector, "SYSTEM_PROMPT", prompt), mock.patch.object(inspector, "MAX_IMAGE_DIM", max_dim):
                result = inspector.inspect(spec, image_bytes, settings, chat=chat)
            run.update(latency_s=result.latency_s, result=result.model_dump(), score=score_run(result, truth))
            s = run["score"]
            counts = ", ".join(f"{r['item_id']} {r['detected']}/{r['truth']} {r['status']}" for r in s["items"])
            print(f"run {n}: {result.latency_s}s | exact {s['exact_counts']}/{s['n_items']} | "
                  f"abs err {s['total_abs_count_error']} | overall {s['overall_status']} "
                  f"({'correct' if s['overall_correct'] else 'WRONG'}) | {counts}")
        except InspectionError as exc:
            run.update(latency_s=round(time.perf_counter() - started, 2), error=f"{exc.stage}: {exc.detail}")
            print(f"run {n}: ERROR {exc.stage}: {exc.detail[:160]}")
        record["runs"].append(run)
        if n < args.runs:
            time.sleep(3)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = OUT_DIR / f"{stamp}_{Path(args.truth).stem.split('.')[0]}_{args.prompt}_{max_dim}px_{settings.model_name}.json"
    out.write_text(json.dumps(record, indent=2))
    print(f"recorded: {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
