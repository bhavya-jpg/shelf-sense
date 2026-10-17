# Counting experiments

The raw records are the JSON files in this folder, written by `eval/count_experiment.py`. Each one holds the prompt hash, model, endpoint, the image size sent to the model, latency, the raw model replies and the score against the ground truth.

## 2026-10-17: shelf-by-shelf counting prompt (Experiment 1)

- **Image:** `data/demo/compliant.png`, sent at 1024×774 (unchanged).
- **Spec:** `specs/nestle_cereal_bay.json`.
- **Ground truth:** `data/demo/compliant.truth.json`. Fully stocked; Stars 16, Koko Krunch 8, Milo 4, Trix 4.
- **Model and endpoint:** Gemma-4-31B-IT on `developer.amd.com.cn` (unchanged).
- **Only change:** the inspection prompt, from `eval/prompts/baseline_v1.txt` to the current `app/inspector.py` prompt. The new prompt asks for whole-image, shelf-by-shelf counting with per-shelf counts and a reliability flag.
- Runs alternated between the two prompts to share endpoint conditions: 2 baseline, 3 new.

| Prompt | Stars | Koko Krunch | Milo | Trix | Exact counts | Total abs. error | Overall status | Latency |
|---|---|---|---|---|---|---|---|---|
| truth | 16 | 8 | 4 | 4 | | | compliant | |
| baseline_v1 (2 runs, identical) | 11 | 6 | 3 | 4 | 1/4 | 8 | non_compliant ✗ | 20.2 s, 11.9 s |
| new prompt (3 runs, identical) | 16 | **7** | 4 | 4 | 3/4 | 1 | non_compliant ✗ | 16.5 s, 45.8 s, 20.9 s |

- The new prompt's per-shelf counts match the manual count on every shelf except Koko Krunch shelf 2 (1 vs 2). The missed package is a dark Koko Krunch box that is half hidden on shelf 2.
- The model marked every count `count_reliable: true` with confidence 100, including the wrong one. Repeated runs gave identical answers, so run-to-run agreement is not evidence of correctness either.
- Financial effect in the app (shown at the time under the old label "confirmed", since renamed "Estimated Margin at Risk (Unverified)"):
  - baseline: **$8.00** false confirmed margin at risk;
  - new prompt: **$1.00** false confirmed (Koko Krunch, 1 × $1.00).
- **Result:** much better, but still wrong. The compliant shelf is still classified as non-compliant.

## 2026-10-17: native resolution, 1536 px limit (Experiment 2)

- **Only change:** `MAX_IMAGE_DIM` raised from 1024 to 1536, via `eval/count_experiment.py --max-dim` (this process only). Everything else was held fixed:
  - same image, spec and ground truth;
  - the same Experiment 1 prompt (sha `98359f4e9e4d`);
  - Gemma-4-31B-IT on `developer.amd.com.cn`;
  - the same validation and scoring.
- **Preprocessing check:**
  - The native image is 1354×1024 RGBA. Its alpha channel is fully opaque, so converting to RGB loses nothing. It has no EXIF rotation.
  - At 1536 the image is sent at native **1354×1024**, not resized. At 1024 it is sent at 1024×774.
  - The rotation step, RGB conversion and JPEG quality-85 re-encode are identical in both cases. The data URL grows from 237 KB to 352 KB.
- **Runs:** alternated 1536 / 1024 to share endpoint load: 3 at 1536, 2 at 1024. All 5 succeeded on the first attempt (no retries, no invalid output).

| Max dim | Sent size | Stars | Koko Krunch (per shelf) | Milo | Trix | Exact | Abs. error | Overall | Latency |
|---|---|---|---|---|---|---|---|---|---|
| truth | | 16 | 8 (2/2/2/2) | 4 | 4 | | | compliant | |
| 1536 (3 runs) | 1354×1024 | 16 | **7 (2/1/2/2)** | 4 | 4 | 3/4 | 1 | non_compliant ✗ | 14.0, 14.0, 19.6 s |
| 1024 (2 runs) | 1024×774 | 16 | **7 (2/1/2/2)** | 4 | 4 | 3/4 | 1 | non_compliant ✗ | 11.7, 18.2 s |

- The same Koko Krunch box on shelf 2 is missed at both resolutions. Every count was marked `count_reliable: true`.
- Latency: mean 15.9 s at 1536 vs. 14.9 s at 1024 (16.5–45.8 s in Experiment 1). The difference is within the shared endpoint's run-to-run noise.
- **Result:** no accuracy gain. The missed box is hidden behind another box, not too small to see. The app keeps `MAX_IMAGE_DIM = 1024`; 1536 is not adopted because it adds about 50% payload for no benefit.

## 2026-10-17: Experiment 2 replication (after the terminology change)

- Re-run of Experiment 2 with nothing changed on the inference side: prompt sha `98359f4e9e4d`, Gemma-4-31B-IT, `developer.amd.com.cn`, same image, spec, ground truth and scoring. The financial-labelling changes made since then don't touch inference.
- **Runs:** 3 at 1536 (sent 1354×1024), alternated with 2 controls at 1024 (sent 1024×774). All 5 requests succeeded on the first attempt with valid output, and every count was marked `count_reliable: true`.

| Max dim | Run | Stars | Koko Krunch (per shelf) | Milo (per shelf) | Trix | Exact | Abs. error | Overall | Latency |
|---|---|---|---|---|---|---|---|---|---|
| truth | | 16 | 8 (2/2/2/2) | 4 (1/1/1/1) | 4 | | | compliant | |
| 1536 | 1 | 16 | 7 (2/1/2/2) | 4 | 4 | 3/4 | 1 | non_compliant ✗ | 13.8 s |
| 1536 | 2 | 16 | 7 (2/1/2/2) | 4 | 4 | 3/4 | 1 | non_compliant ✗ | 13.8 s |
| 1536 | 3 | 16 | 7 (2/1/2/2) | 4 | 4 | 3/4 | 1 | non_compliant ✗ | 28.5 s |
| 1024 | 1 | 16 | 7 (2/1/2/2) | **5 (2/1/1/1)** | 4 | 2/4 | 2 | non_compliant ✗ | 15.5 s |
| 1024 | 2 | 16 | 7 (2/1/2/2) | 4 | 4 | 3/4 | 1 | non_compliant ✗ | 19.7 s |

- Koko Krunch never reaches 8/8 at either size.
- First run-to-run variation seen with this prompt: one 1024 run counted a second Milo on shelf 1. A partly visible green box sits next to the Milo there. Milo stayed "present", so this overcount adds no money to the estimate.
- **Across Experiment 2 and this replication:**
  - 1536: 6/6 runs identical.
  - 1024 with this prompt: 1 of 7 runs varied (Experiments 1 and 2 plus this one).
  - This is too few runs to call 1536 more stable.
- **Result:** confirms Experiment 2. No accuracy gain on the targeted error. `MAX_IMAGE_DIM` stays 1024.

## 2026-10-17: MiniCPM-V-4.7-35B-A3B vs Gemma-4-31B-IT (Experiment 3)

- **Only change:** the model, via `eval/count_experiment.py --model` (this process only; `.env` still says `MODEL_NAME=Gemma-4-31B-IT`). Everything else was held fixed:
  - same image, spec, ground truth and scoring;
  - the same prompt (sha `98359f4e9e4d`);
  - `MAX_IMAGE_DIM` 1024 (sent 1024×774);
  - the `developer.amd.com.cn` endpoint, `MOCK_MODE=false`.
- **Model available:** MiniCPM-V-4.7-35B-A3B is listed by the endpoint's `/models`.
- **Runs:** MiniCPM attempts alternated with Gemma controls to share endpoint load. File names now include the model.

| Model | Attempts | Succeeded | Stars | Koko Krunch (per shelf) | Milo | Trix | Exact | Abs. error | False stock-outs | Overcounts | Overall | Latency (succeeded) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| truth | | | 16 | 8 (2/2/2/2) | 4 | 4 | | | | | compliant | |
| MiniCPM-V-4.7-35B-A3B | 6 | **2** (4 timed out at 90 s) | 16 | **7 (2/1/2/2)** | 4 | 4 | 3/4 | 1 | Koko Krunch | none | non_compliant ✗ | 32.2, 32.9 s (mean 32.5) |
| Gemma-4-31B-IT (controls) | 2 | 2 | 16 | **7 (2/1/2/2)** | 4 | 4 | 3/4 | 1 | Koko Krunch | none | non_compliant ✗ | 15.2, 38.8 s (mean 27.0) |

- The MiniCPM replies are clearly a different model's output (markdown-fenced, pretty-printed, longer notes), yet they give the **same per-shelf counts as Gemma**. Both miss the half-hidden Koko Krunch box on shelf 2. Both mark every count `count_reliable: true` at confidence 100.
- Only 2 of the 3 requested MiniCPM runs succeeded. The other 4 attempts hit the 90 s client timeout. Earlier, a tiny probe image took MiniCPM 3.3 s, so the timeouts look like endpoint load or queueing for this model on the full request. This was not investigated further.
- **Result:**
  - No accuracy gain. Two different model families make the same miss, which points to a hard occlusion case, not one model's weakness.
  - MiniCPM is not adopted: it is no more accurate and failed 4 of 6 times.
  - Production stays on Gemma-4-31B-IT.

## 2026-10-17: per-shelf crops, hand-placed (Experiment 4)

- **Change:** each shelf is inspected as its own image instead of the whole bay. Everything else was held fixed: prompt sha `98359f4e9e4d`, Gemma-4-31B-IT, `MAX_IMAGE_DIM` 1024, endpoint, validation and scoring.
- **Crops:** `data/demo/compliant.crops.json` holds four bands **placed by hand** for this photo, checked visually so that no box is cut and no neighbouring shelf leaks in. This tests what cropping can do in the best case. It is not automatic shelf detection.
- **Runner:** `eval/shelf_crop_experiment.py`.
  - Strips are sent at 1024×184–191, the same scale as the whole image at 1024, so no pixels are gained.
  - Per-shelf counts are summed. Per-crop model statuses are ignored, because the spec's expected counts are whole-bay totals; status is recomputed from the sums.
  - The merge logic is unit-tested in `tests/test_eval_crops.py`.
- **Runs:** 3 runs × 4 shelf calls. All 12 calls returned valid output first time. One HTTP 429 was absorbed by the client's backoff.

| Run | Stars | Koko Krunch (per shelf) | Milo (per shelf) | Trix | Exact | Abs. error | Overall | Total latency |
|---|---|---|---|---|---|---|---|---|
| truth | 16 | 8 (2/2/2/2) | 4 (1/1/1/1) | 4 | | | compliant | |
| 1 | 16 | **8 (2/2/2/2)** | **6 (2/2/1/1)** | 4 | 3/4 | 2 | **compliant ✓** | 55.5 s |
| 2 | 16 | **8 (2/2/2/2)** | **6 (2/2/1/1)** | 4 | 3/4 | 2 | **compliant ✓** | 37.5 s |
| 3 | 16 | 9 (2/2/3/2) | **6 (2/2/1/1)** | 4 | 2/4 | 3 | **compliant ✓** | 33.0 s |

- **Undercount fixed.** The shelf-2 crop finds the hidden Koko Krunch ("2 boxes visible, one partially obscured").
- **New overcounts.** Milo is counted as 2 on shelves 1 and 2 ("2 green boxes visible"), where a partly visible green box sits beside the Milo. Run 3 also counted a third "variant" Koko Krunch on shelf 3. Every count was still marked `count_reliable: true`.
- **Why the shelf comes out right:** every item now meets or exceeds its expected count, so nothing reads short and the estimate is $0.00. The overall result is right, but the counts are less accurate: total error is 2–3, against 1 for the whole image.
- **Risk:** overcounting is harmless on a fully stocked shelf, but on a real stock-out it could **hide a missing box**. A missed stock-out is worse for this product than a false alarm.
- **Cost:** 4 calls per inspection, 33–56 s total against roughly 12–39 s for one whole-image call, and more exposure to the per-key rate limit (one 429 seen).
- **Result:** promising for the undercount, but not adopted. It still needs:
  1. a test on a real stock-out photo, to see whether overcounting hides real gaps;
  2. automatic shelf detection instead of hand-placed bands;
  3. possibly a rule for partly visible neighbouring boxes.

  Production is unchanged: whole image, Gemma-4-31B-IT, 1024.
