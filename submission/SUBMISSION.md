# Shelf-Sense: submission copy (lablab.ai, AMD Developer Hackathon: ACT III)

Paste-ready text for the portal. Lengths were measured: short description 150 characters, long description 1,585 characters (254 words). The portal's character limits were not available in any document we have, so check them in the form.

## 1. Project title

Shelf-Sense

## 2. Short description

Photograph a shelf, get per-product counts, a compliance verdict, an estimated margin at risk and a restocking list. Vision on AMD; decisions in code.

## 3. Long description

Shelf audits are still done by eye: someone walks the aisle, counts facings and writes them down. Gaps sit unnoticed between walks, counts differ between people, and nobody knows what a missing facing costs.

Shelf-Sense turns one shelf photograph into a preliminary compliance report. The user picks a shelf specification, adds a photo and runs one inspection. Gemma-4-31B-IT, called through AMD Developer Cloud's Token Factory, counts each product shelf by shelf. Everything after that is plain Python: Pydantic validation with one stricter retry, invented items dropped, unreliable or contradictory counts sent to review, a verdict computed from per-product statuses, and an estimated margin at risk computed with Decimal arithmetic from demo unit margins. A second AMD call may word the restocking note, but every name, count and figure in it is inserted by code, and the app labels who wrote it.

We measured it honestly on a self-taken photo with a hand-counted ground truth. A shelf-by-shelf prompt cut the counting error from 8 boxes to 1. The model still misses one half-hidden box, at 100% confidence, so the fully stocked demo shelf is reported as short. Higher resolution and a second model did not fix it; per-shelf cropping did but overcounted, so it is not in production. That is why every dollar figure is labelled "Estimated Margin at Risk (Unverified)" and per-shelf counts are shown for a quick human check. All 24 experiment records, with raw model replies, are in the repository.

Built with Streamlit, Python, Pydantic and Docker; 195 offline tests. MIT licensed.

## 4. Challenge

**Reinvent Commerce.** This name comes from `BLUEPRINT.md` §2, the only challenge description available to us. Pick the matching entry in the portal's list; if its wording differs, choose the commerce/retail track.

## 5. Technology tags

AMD Developer Cloud · Token Factory · Gemma · Vision-language model · Python · Streamlit · Pydantic · Docker · OpenAI-compatible API

## 6. Public demo URL

**`<RENDER URL — not recorded anywhere in the repo; paste the live Render URL>`**

## 7. Public repository

https://github.com/bhavya-jpg/shelf-sense

## 8. Demo video

Upload `submission/video/shelf-sense-demo.mp4` (1920×1080, H.264 with AAC narration). Captions: `submission/video/shelf-sense-demo.srt`.

## 9. Pitch deck

`submission/presentation/ShelfSense_Pitch_Deck.pdf` (upload), with the editable `ShelfSense_Pitch_Deck.pptx` alongside.

## 10. Cover image

`submission/assets/cover.png` (1920×1080, 16:9).

## What is implemented vs experimental

| Implemented (production) | Experimental or planned |
|---|---|
| One vision call per inspection to Gemma-4-31B-IT on AMD Token Factory | Per-shelf cropping (Experiment 4): hand-placed crops, not adopted |
| Pydantic validation, retry, review flags for unreliable counts | Better counting under occlusion |
| Verdict and estimated margin at risk computed in code, labelled unverified | Human verification of uncertain findings |
| AMD-worded action note with code-inserted figures and a template fallback | Evaluation on many more shelves; real-store testing |
| Three-page web app, Docker, 195 offline tests | |

## Claims we deliberately do not make

- No accuracy percentage or benchmark: the evaluation is one self-taken photo.
- No measured retail losses: the margin figure uses author-entered demo margins ($1.00 per unit).
- No GPU model, vLLM or ROCm claims: Token Factory is a hosted service and its response names the provider only as `self-dploy`.
