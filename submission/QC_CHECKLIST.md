# Shelf-Sense submission: QC checklist

Re-run the automated part with `.venv/bin/python submission/qc.py` (needs Pillow and ffmpeg; PyMuPDF optional). The account-identifier scan reads its markers from the gitignored `submission/.qc-private`.

## Automated (qc.py, 18/18 passing)

| Check | Result |
|---|---|
| MP4 exists | 20.5 MB |
| Video 1920×1080 H.264, 30 fps | pass |
| Duration 2–3 min | 149.50 s |
| Frame count matches 30 fps | 4,485 frames |
| Audio stream | AAC, 48 kHz, stereo |
| Audio not silent | mean −19.2 dB, peak −0.8 dB |
| Motion, not a slideshow | 40 visible changes at 2 fps (crossfades, no hard cuts); 1 near-still span ≥6 s (61.4–68.1 s, slow pan over the result while narration plays) |
| SRT valid, inside the video | 28 cues, last ends 146.03 s |
| Chatterbox narration WAVs | 10 scenes |
| Standalone narration audio | `video/shelf-sense-narration.wav` |
| PPTX | 8 slides, 8 presenter notes |
| PDF | 8 pages |
| Cover | 1920×1080 (16:9) |
| No API key or account identifiers in text files | none found |
| No unsupported claims (MI300, accuracy %, revenue at risk, verified loss, guarantee); "Unverified" label present | clean |
| vLLM/ROCm mentioned only as not claimed | 2 mentions, both "no … claims" |
| 24 experiment records intact | pass |
| `app/`, `tests/`, `docs/`, `specs/`, `data/`, `README.md` unchanged | clean |

## Manual checks done

- [x] Contact sheet of the final MP4 reviewed (4–122 s): footage fills its frame, captions do not overlap content, the inspection shown is one real run (Non-compliant, Koko Krunch 7 of 8, $1.00 unverified, Gemma-4-31B-IT, 13.23 s).
- [x] Sped-up wait is disclosed on screen (6.05×, real wait 15.9 s) and in the narration.
- [x] Narration transcribed back with Whisper base.en; every line ≥ 0.88 word match, retakes for the two lowest lines. Remaining: in the closing line Whisper hears "decisions and code" for "decisions in code".
- [x] Deck rendered to PNG and reviewed slide by slide (left-aligned titles, no overflow, no overlap); pptx validator passed.
- [x] Every number in the video, deck and copy traces to the repo: 8→1 boxes, median 18.2 s over 9 runs (11.7–45.8 s), 24 records, 195 offline tests, $1.00 demo unit margin.
- [x] Short description 150 characters, long description 1,585 characters.

## Open before submitting

- [ ] Paste the live Render URL into `SUBMISSION.md` §6 (placeholder left on purpose).
- [ ] Check the portal's character limits and challenge list against `SUBMISSION.md`.
- [ ] Watch the MP4 once start to finish with sound.
