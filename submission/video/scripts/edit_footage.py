"""Cut the real inspection recording to the demo scene's narration, once, with ffmpeg.

Setup and the result play at normal speed; only the wait for the AMD endpoint is sped up, and the
speed-up factor and the real wait are written to edit.json so the video can say so on screen.
Usage: python scripts/edit_footage.py   (after tts/synth.py)
"""

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "remotion"
vo = json.loads((R / "src/data/vo.json").read_text())
cap = json.loads((R / "src/data/capture.json").read_text())["clips"]["inspect"]
FPS, HOLD, TRANSITION = 30, 0.5, 14

target = (vo["s4_demo"]["seconds"] + HOLD) + TRANSITION / FPS + 0.2  # seconds of footage the scene shows
a0 = cap["loaded"] - 0.4
a1 = cap["run"] + 0.5
b1 = cap["result"] - 0.2
c_len = 3.4
b_len = max(2.4, target - (a1 - a0) - c_len)
if (a1 - a0) + b_len + c_len > target:  # long narration-free setup: start later rather than rush it
    a0 = max(0.0, a1 - (target - b_len - c_len))
speed = (b1 - a1) / b_len
segments = [(a0, a1, a1 - a0), (a1, b1, b_len), (b1, b1 + c_len, c_len)]
parts = [
    f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=(PTS-STARTPTS)*{d / (e - s):.6f},fps={FPS}[v{i}]"
    for i, (s, e, d) in enumerate(segments)
]
graph = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(segments))) + f"concat=n={len(segments)}:v=1:a=0,format=yuv420p[out]"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(R / "public/footage/inspect.mp4"), "-filter_complex", graph,
                "-map", "[out]", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-movflags", "+faststart",
                str(R / "public/footage/inspect-edit.mp4")], check=True)
f = lambda t: round((t - a0) * FPS)  # noqa: E731  source time (setup segment) -> edited frame
fast_from, fast_to = f(a1), f(a1) + round(b_len * FPS)
edit = {"inspect": {
    "frames": math.ceil(sum(d for *_, d in segments) * FPS), "speedup": round(speed, 2),
    "realWaitS": round(cap["result"] - cap["run"], 1), "fastFrom": fast_from, "fastTo": fast_to,
    "marks": {"spec": f(cap["spec"]), "photo": f(cap["photo"]), "run": f(cap["run"]), "result": fast_to + 6},
}}
(R / "src/data/edit.json").write_text(json.dumps(edit, indent=1))
print(json.dumps(edit))
