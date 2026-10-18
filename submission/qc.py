"""Final quality control for the submission package. Usage: <python with Pillow> submission/qc.py"""

import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
MP4 = ROOT / "video/shelf-sense-demo.mp4"
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout + subprocess.run(cmd, capture_output=True, text=True).stderr


# --- video
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(MP4)],
                                  capture_output=True, text=True).stdout or "{}")
streams = {s["codec_type"]: s for s in probe.get("streams", [])}
v, a = streams.get("video", {}), streams.get("audio", {})
dur = float(probe.get("format", {}).get("duration", 0))
check("MP4 exists", MP4.exists(), f"{MP4.stat().st_size / 1e6:.1f} MB" if MP4.exists() else "missing")
check("Video 1920x1080 H.264", v.get("width") == 1920 and v.get("height") == 1080 and v.get("codec_name") == "h264",
      f"{v.get('width')}x{v.get('height')} {v.get('codec_name')} {v.get('r_frame_rate')}")
check("Duration 2–3 min", 120 <= dur <= 180, f"{dur:.2f} s")
nb = int(v.get("nb_frames", 0))
check("Frame count matches 30 fps", abs(nb - round(dur * 30)) <= 2, f"{nb} frames")
check("Audio stream present", a.get("codec_name") is not None, f"{a.get('codec_name')} {a.get('sample_rate')} Hz {a.get('channels')} ch")
vol = run("ffmpeg", "-hide_banner", "-i", str(MP4), "-af", "volumedetect", "-vn", "-f", "null", "-")
mean = re.search(r"mean_volume: (-?[\d.]+) dB", vol)
peak = re.search(r"max_volume: (-?[\d.]+) dB", vol)
check("Audio is not silent", mean and float(mean.group(1)) > -40, f"mean {mean.group(1) if mean else '?'} dB, peak {peak.group(1) if peak else '?'} dB")
scenes = run("ffmpeg", "-hide_banner", "-i", str(MP4), "-vf", "fps=2,select=gt(scene\\,0.02),showinfo", "-an", "-f", "null", "-")
changes = len(re.findall(r"pts_time:", scenes))
frz = run("ffmpeg", "-hide_banner", "-i", str(MP4), "-vf", "freezedetect=n=0.001:d=6", "-an", "-f", "null", "-")
freezes = len(re.findall(r"freeze_start", frz))
check("Motion, not a slideshow", changes >= 10 and freezes <= 3, f"{changes} visible changes at 2 fps (crossfades, no hard cuts), {freezes} still span(s) ≥6 s")

# --- captions
srt = (ROOT / "video/shelf-sense-demo.srt").read_text()
times = re.findall(r"(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})", srt)
secs = [(int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000, int(h2) * 3600 + int(m2) * 60 + int(s2) + int(ms2) / 1000)
        for h, m, s, ms, h2, m2, s2, ms2 in times]
check("SRT captions valid and inside the video", secs and all(a < b for a, b in secs) and secs[-1][1] <= dur + 0.1
      and all(secs[i][0] >= secs[i - 1][0] for i in range(1, len(secs))), f"{len(secs)} cues, last ends {secs[-1][1]:.2f} s")
check("Narration WAVs (Chatterbox) present", len(list((ROOT / "video/remotion/public/vo").glob("*.wav"))) == 10, "10 scenes")
check("Narration audio file", (ROOT / "video/shelf-sense-narration.wav").exists(), "")

# --- deck
pptx = ROOT / "presentation/ShelfSense_Pitch_Deck.pptx"
with zipfile.ZipFile(pptx) as z:
    slides = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    notes = [n for n in z.namelist() if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", n)]
    deck_text = " ".join(re.sub(r"<[^>]+>", " ", z.read(n).decode("utf8")) for n in slides + notes)
check("PPTX opens, 8 slides with notes", len(slides) == 8 and len(notes) == 8, f"{len(slides)} slides, {len(notes)} notes")
try:
    import pymupdf
    pages = pymupdf.open(ROOT / "presentation/ShelfSense_Pitch_Deck.pdf").page_count
except Exception:
    pages = len(re.findall(rb"/Type\s*/Page[^s]", (ROOT / "presentation/ShelfSense_Pitch_Deck.pdf").read_bytes()))
check("PDF has 8 pages", pages == 8, f"{pages} pages")

# --- cover
from PIL import Image  # noqa: E402

w, h = Image.open(ROOT / "assets/cover.png").size
check("Cover is 16:9", abs(w / h - 16 / 9) < 0.01, f"{w}x{h}")

# --- secrets and claims
env = dict(line.split("=", 1) for line in (REPO / ".env").read_text().splitlines() if "=" in line)
key = env.get("AMD_API_KEY", "").strip()
# Account identifiers to scan for live in a gitignored file, so this script does not contain them.
private = ROOT / ".qc-private"
markers = [m for m in private.read_text().split() if m] if private.exists() else []
leaks = []
for f in ROOT.rglob("*"):
    if not f.is_file() or f == private or any(p in f.parts for p in ("node_modules", ".tts-venv")) or f.suffix in (".mp4", ".webm", ".wav", ".png", ".jpg", ".jpeg"):
        continue
    t = f.read_bytes()
    if (key and key.encode() in t) or any(m.encode() in t for m in markers):
        leaks.append(str(f.relative_to(ROOT)))
check("No API key or account IDs in submission files", not leaks and bool(key), ", ".join(leaks) or "none found")
texts = deck_text + " " + srt + " " + (ROOT / "SUBMISSION.md").read_text() + " " + (ROOT / "video/narration_script.md").read_text()
texts += " ".join(f.read_text() for f in (ROOT / "video/remotion/src").rglob("*.tsx"))  # on-screen text of every scene
bad = [p for p in (r"\bMI300", r"\b\d{2,3}(\.\d)?% accura", r"revenue at risk", r"verified (financial )?loss", r"guarantee")
       if re.search(p, texts, re.I)]
claims_ok = not bad and "Unverified" in deck_text
check("No unsupported claims; unverified label present", claims_ok, ", ".join(bad) or "clean")
vllm = [m.group(0) for m in re.finditer(r"[^.]*\b(?:vLLM|ROCm)\b[^.]*", texts)]
check("vLLM/ROCm only mentioned as not claimed", all(re.search(r"no |not|don.t", s, re.I) for s in vllm), f"{len(vllm)} mention(s)")

# --- repository integrity
check("Experiment records intact", len(list((REPO / "docs/experiments").glob("*.json"))) == 24, "24 records")
diff = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--", "app", "tests", "docs", "README.md", "specs", "data"],
                      capture_output=True, text=True).stdout.strip()
check("App, tests, docs, README unchanged", diff == "", diff or "clean")

width = max(len(n) for n, *_ in results)
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
print(f"\n{sum(ok for _, ok, _ in results)}/{len(results)} checks passed")
