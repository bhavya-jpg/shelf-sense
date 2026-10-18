"""Write the SRT captions, the narration script and the shot list from the same timings the video uses."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
vo = json.loads((ROOT / "remotion/src/data/vo.json").read_text())
narr = json.loads((ROOT / "tts/narration.json").read_text())
edit = json.loads((ROOT / "remotion/src/data/edit.json").read_text())["inspect"]
cap = json.loads((ROOT / "remotion/src/data/capture.json").read_text())
ORDER = ["s1_hook", "s2_problem", "s3_solution", "s4_demo", "s5_results", "s6_actions", "s7_arch", "s8_eval", "s9_amd", "s10_close"]
FPS, T = 30, 14
dur = lambda s: math.ceil((vo[s]["seconds"] + (3.2 if s == "s10_close" else 0.5)) * FPS)  # noqa: E731
starts, f = {}, 0
for s in ORDER:
    starts[s] = f / FPS
    f += dur(s) - T
total = (f + T) / FPS

def ts(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

srt, n = [], 0
for s in ORDER:
    for line in vo[s]["lines"]:
        n += 1
        srt.append(f"{n}\n{ts(starts[s] + line['start'])} --> {ts(starts[s] + line['end'] + 0.2)}\n{line['text']}\n")
(ROOT / "shelf-sense-demo.srt").write_text("\n".join(srt))

TITLES = {
    "s1_hook": ("Hook", "Kinetic type over the real demo shelf photo (greyscale, slow push)."),
    "s2_problem": ("The problem", "Four columns draw in on each line: manual, infrequent, inconsistent, unpriced."),
    "s3_solution": ("The solution", "Wordmark, the three steps, 'Model counts / Code decides'; real landing-page footage on the right."),
    "s4_demo": ("Real demo", f"Real screen recording: spec, Compliant photo, Run, processing, result. Wait shown {edit['speedup']}x faster with an on-screen badge (real wait {edit['realWaitS']} s)."),
    "s5_results": ("The result", "Camera moves over real screenshots of the same run: per-shelf table, verdict and stats, the unverified notice."),
    "s6_actions": ("Actions", "Real screenshot of the AMD-worded action note; badge and 'inserted by code'."),
    "s7_arch": ("Architecture", "Five-node diagram: photo + spec, AMD Token Factory (model), validation, calculator, action note (code)."),
    "s8_eval": ("Evaluation", "8 -> 1 counting error; real photo of shelf 2 with the half-hidden box outlined (hand-marked ground truth); hand count vs model."),
    "s9_amd": ("Inference on AMD", "Lime panel; model, endpoint, calls, recorded latency, what is not claimed."),
    "s10_close": ("Close", "Planned roadmap (labelled planned), then wordmark, repo URL and the synthetic-voice / sped-up credit line."),
}
script = ["# Shelf-Sense demo video: narration script (final)\n",
          "Voice: Chatterbox (Resemble AI, MIT), generated locally; checked back with Whisper. "
          "`say` is what the model was given (spelled for pronunciation); captions use the written form.\n"]
shots = [f"# Shelf-Sense demo video: shot list\n\n1920x1080, 30 fps, {total:.1f} s. Scene lengths come from the narration; scenes cross-fade over {T} frames.\n",
         f"Real footage and screenshots: one real inspection on the AMD endpoint (captured {cap['captured_at']}), "
         f"result: {cap['clips']['inspect']['result_text']['verdict']}, {cap['clips']['inspect']['result_text']['run_meta'].splitlines()[0]}.\n",
         "| # | Time | Scene | Visual |", "|---|---|---|---|"]
for i, s in enumerate(ORDER, 1):
    title, visual = TITLES[s]
    script.append(f"\n## {i}. {title}  ({ts(starts[s])[:-4]} – {ts(starts[s] + dur(s) / FPS)[:-4]})\n")
    for k, line in enumerate(narr[i - 1]["lines"]):
        script.append(f"- {line['show']}" + (f"  \n  _say:_ {line['say']}" if line["say"] != line["show"] else ""))
    shots.append(f"| {i} | {ts(starts[s])[3:-4]} | {title} | {visual} |")
(ROOT / "narration_script.md").write_text("\n".join(script) + "\n")
(ROOT / "shot_list.md").write_text("\n".join(shots) + "\n")
print(f"total {total:.2f} s, {n} captions")
