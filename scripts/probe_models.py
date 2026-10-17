"""Milestone 0 helper: list endpoint models and test which candidates can actually read an image.

Sends each model a synthetic image with a known answer (5 red circles, 2 blue squares) and
reports the parsed counts and latency. This is a capability probe, not demo or eval data.

    python -m scripts.probe_models                       # default candidates
    python -m scripts.probe_models --models Gemma-4-31B-IT MiniCPM-V-4.7-35B-A3B
"""

import argparse
import base64
import io
import json
import os
import time

import requests
from PIL import Image, ImageDraw

from app.config import REPO_ROOT, _load_dotenv

DEFAULT_CANDIDATES = [
    "Gemma-4-31B-IT",
    "MiniCPM-V-4.7-35B-A3B",
    "DeepSeek-V4-Flash-Vision-Exp",
    "Qwen3.8-27B",
    "MiniCPM-V-4.7-1B",
]
EXPECTED = {"red_circles": 5, "blue_squares": 2}
PROMPT = (
    "Count the shapes in this image. Return ONLY a JSON object, no other text: "
    '{"red_circles": <int>, "blue_squares": <int>}'
)


def probe_image() -> str:
    img = Image.new("RGB", (800, 400), "white")
    d = ImageDraw.Draw(img)
    for i in range(5):
        x = 40 + i * 110
        d.ellipse([x, 40, x + 80, 120], fill=(220, 30, 30))
    for i in range(2):
        x = 150 + i * 250
        d.rectangle([x, 220, x + 100, 320], fill=(30, 60, 220))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=DEFAULT_CANDIDATES)
    args = parser.parse_args()

    _load_dotenv(REPO_ROOT / ".env")
    url = os.environ.get("AMD_API_URL", "").rstrip("/")
    key = os.environ.get("AMD_API_KEY", "")
    if not url or "<" in url:
        raise SystemExit("Set AMD_API_URL in .env first (base URL ending in /v1).")
    headers = {"Authorization": f"Bearer {key}"} if key else {}

    print(f"Endpoint host: {requests.utils.urlparse(url).hostname}")
    r = requests.get(f"{url}/models", headers=headers, timeout=30)
    print(f"GET /models -> HTTP {r.status_code}")
    available = []
    if r.ok:
        available = [m.get("id") for m in r.json().get("data", [])]
        print("Model ids:", ", ".join(available))

    image = probe_image()
    for model in args.models:
        if available and model not in available:
            print(f"\n[{model}] not in /models list, skipping (check exact id above)")
            continue
        body = {
            "model": model,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": image}},
            ]}],
            "temperature": 0.1,
            "max_tokens": 200,
        }
        t0 = time.perf_counter()
        try:
            resp = requests.post(f"{url}/chat/completions", headers=headers, json=body, timeout=120)
        except requests.RequestException as exc:
            print(f"\n[{model}] request failed: {type(exc).__name__}")
            continue
        latency = time.perf_counter() - t0
        if resp.status_code != 200:
            print(f"\n[{model}] HTTP {resp.status_code} in {latency:.1f}s: {resp.text[:200]}")
            continue
        content = resp.json()["choices"][0]["message"]["content"] or ""
        try:
            got = json.loads(content[content.find("{"): content.rfind("}") + 1])
            verdict = "CORRECT" if got == EXPECTED else f"WRONG (expected {EXPECTED})"
        except ValueError:
            got, verdict = None, "UNPARSEABLE"
        print(f"\n[{model}] {latency:.1f}s  {verdict}\n  reply: {content[:200]!r}")
        time.sleep(2)  # per-key shared rate limit: stagger calls


if __name__ == "__main__":
    main()
