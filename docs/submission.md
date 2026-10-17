# Submission kit: Shelf-Sense

Text for the lablab.ai ACT III portal form, plus the demo video script, slide outline and a pre-submission checklist. The field list comes from BLUEPRINT §2/§13. Check it against the live portal: the ≤5 min / ≤300 MB video limit was carried over from lablab's general rules and is **not** confirmed for ACT III.

## Form fields

**Project title:** Shelf-Sense

**Track:** Reinvent Commerce

**Short description:**
Photograph a shelf, check it against its planned layout, and get restocking actions with an estimated margin at risk. The vision model runs on AMD Developer Cloud; the verdict and the money are computed by code.

**Long description:**
Retail stock-outs and messy shelves cost revenue, and small retailers still check them by eye. Shelf-Sense turns one ordinary shelf photo into a structured check. The user picks a spec (which products, how many) and uploads a photo. Gemma-4-31B-IT, served by AMD Developer Cloud's Token Factory, counts each product shelf by shelf.

The design rule is that the model only observes:
- Code validates its output, drops invented products, and turns contradictory or self-flagged unreliable counts into "needs review".
- Code computes the verdict and the dollar figure.
- A second AMD call may word the action list, but cannot change any name, count or number.

Because a vision model can miss a half-hidden box, the dollar figure is labelled **Estimated Margin at Risk (Unverified)**. Per-shelf counts are shown so staff can check them quickly.

We measured this honestly against a hand-counted shelf photo across 24 experiment records:
- A shelf-by-shelf prompt cut the counting error from 8 boxes to 1.
- Higher resolution and a second model didn't fix the last, half-hidden box.
- Per-shelf cropping fixed the verdict but introduced overcounts.

All of these results are documented in the repository.

**Technology tags:** AMD Developer Cloud, Token Factory, Gemma, vision-language model, Python, Streamlit, Pydantic, Docker, OpenAI-compatible API

**Demo application platform:** Render (Docker), *once deployed. See the checklist.*

**Repository / demo URLs:** *to be filled in after the repo is public and the app is deployed.*

**Cover image:** `assets/cover.png` (1920×1080, 16:9)

## Demo video script (target ~3½ min, cap 5 min)

Record with `MOCK_MODE=false` on the deployed URL (or locally), uncut, so the real latency shows.

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | Title / cover | "Stock-outs cost stores money, and most shelves are still checked by eye. Shelf-Sense turns one photo into a shelf check." |
| 0:20–0:45 | App header (model + endpoint), spec table | "The spec lists what the bay should hold. The margins are demo assumptions. Inference runs on Gemma-4-31B-IT on AMD Developer Cloud Token Factory, and the endpoint is shown right here." |
| 0:45–1:45 | Click **Compliant**, then **Run inspection**. Let the spinner run uncut (~15–40 s) | "One real call to the AMD endpoint. The model counts each product shelf by shelf; code validates the reply and computes everything else." |
| 1:45–2:35 | Results: status, metric, info box, items table with per-shelf column | "This shelf is actually fully stocked, but the model counted one Koko Krunch short. You can see exactly where: shelf two shows 1 instead of 2, because that box is half hidden. That's why the money is labelled *Estimated, Unverified*. The app never presents a model count as fact." |
| 2:35–3:05 | Recommended actions + caption naming who wrote the note | "A second AMD call words the actions. Every name, count and dollar figure is inserted by code; the model only picks the wording." |
| 3:05–3:30 | README *Evaluation* table | "We measured it: the shelf-by-shelf prompt cut the error from 8 boxes to 1. Higher resolution and a second model didn't fix the hidden box; cropping fixed the verdict but overcounted. All runs and raw replies are in the repo." |
| 3:30–3:45 | Repo link | "Shelf-Sense: AMD-hosted vision, code-computed decisions, honest about its limits." |

Only the **Compliant** demo button is offered. The two unmatched photos sit in `data/unmatched/` until they have specs.

## Slide outline (7 slides)

1. **Problem:** shelves are checked by eye; stock-outs quietly lose margin.
2. **Solution:** photo + spec → per-product status, Estimated Margin at Risk (Unverified), actions (screenshot).
3. **Architecture:** the data-flow block from the README; the model observes and code decides.
4. **AMD integration:**
   - Token Factory endpoint, Gemma-4-31B-IT, one call per inspection plus one for the note;
   - median 18.2 s;
   - first HTTP 200 kept as evidence.
5. **Business value:** how the margin figure is computed, the four categories (estimate / unresolved / unavailable / never verified), and why the label says *unverified*.
6. **Evaluation:** the five-row experiment table; one photo, honest numbers.
7. **Limitations and next steps:**
   - automatic shelf detection for cropping;
   - stock-out and misplaced specs;
   - a person-verified count flow;
   - more eval photos.

## Pre-submission checklist

| Item | Status |
|---|---|
| Offline tests pass | ✅ 181 passed, 1 deselected |
| Full UI workflow on the real AMD endpoint (in Docker) | ✅ verified 2026-10-18 |
| `.env` / key excluded from git and from the Docker image | ✅ checked |
| README: setup, architecture, AMD, evaluation, limitations, licences | ✅ |
| MIT `LICENSE` | ✅ (copyright line says "Shelf-Sense authors"; replace with your name if you like) |
| Cover image | ✅ `assets/cover.png` |
| First git commit + **public GitHub repo** | ❌ needs you |
| **Deployed demo URL** (Render) reachable logged-out, `MOCK_MODE=false` | ❌ needs you (account + env vars); then verify the endpoint is reachable from Render |
| Demo video recorded and uploaded | ❌ needs you |
| Slides | ✅ 7-slide deck built as a private Claude artifact (share it or export it to PPTX/PDF from its page, then upload to the portal) |
| Stock-out / misplaced scenarios | ❌ not in this submission; `data/unmatched/missing.png` / `misplaced.png` need specs and ground truth. Demo buttons removed. |
| Submission deadline (exact hour/timezone) | ❓ unverified (BLUEPRINT §2 item 1) |
