# BLUEPRINT.md — Shelf-Sense
AMD Developer Hackathon: ACT III · Reinvent Commerce track
Prepared for implementation by a coding agent (Claude Code). Do not redesign — if something here seems wrong, flag it, don't silently change it.

**Status:** project selected, concept locked (see `AMD_HACKATHON_PROJECT_DECISION.md` in this repo's history for the full comparison against 3 alternatives). This document is the single source of truth for implementation.

---

## How to use this document

Everything marked **[ASSUMPTION — VERIFY]** is something I could not confirm from the hackathon's public pages and must be checked by a human in Milestone 0, before relying on it. Everything else is treated as settled. If an assumption turns out false, stop and re-plan that section specifically — don't improvise around it silently.

---

## 1. PROJECT OVERVIEW

**Project name:** Shelf-Sense

**One-line description:** A zero-shot vision copilot that checks a shelf photo against a plain-language spec and turns any gap into a dollar-estimated restocking action.

**Problem statement:** Retail stock-outs and shelf-compliance failures (missing facings, wrong placement, missing promo signage) quietly cost revenue. Checking shelves is still mostly manual, infrequent, and inconsistent across stores, and small/mid retailers can't afford traditional automated-inspection hardware.

**Target users:** Store managers and retail-ops staff at a single store or small chain who currently check shelves by eye and want a fast, photo-based second opinion — not enterprise chains with existing AOI/planogram-compliance hardware.

**Proposed solution:** Photograph a shelf. The system compares it against a plain-language spec of what should be there, returns a structured per-item compliance result from a vision-language model, and — critically — a **deterministic, non-LLM** estimate of revenue at risk plus a plain-language action note.

**Why it matters:** This directly answers the Reinvent Commerce track's own stated idea list ("in-store computer vision") and its explicit judging ask for "a measurable effect on revenue, margin, conversion, retention, inventory, or service quality" — the revenue-at-risk number is that measurable effect, computed transparently, not asserted.

**Competitive differentiation:** The zero-shot-VLM-inspection *pattern* has precedent (an MIT-licensed prior-hackathon project, `AsBuilt-Lens`, applied it to PCB assembly QC). Shelf-Sense is a new domain, new dataset, new workflow, and new application code — see `AMD_HACKATHON_REPOSITORY_AUDIT.md` §3 for exactly what is and isn't reused. The differentiator against this round's live competitors is architectural discipline: **the model never produces the final verdict or the dollar figure — code does, from the model's structured observations.** This directly avoids the hackathon's own named failure modes ("unsupported performance claims," "generic chatbots").

---

## 2. HACKATHON COMPLIANCE

**Selected track:** Reinvent Commerce ("Help a business understand its customers and take better action").

**Relevant judging criteria** (all four apply; this is how each is answered):
- *Application of Technology* — the VLM call is the computational core of every inspection, not decoration.
- *Business Value* — the revenue-at-risk calculator directly answers the track's stated measurable-effect requirement.
- *Originality* — new domain/workflow informed by, not copied from, prior patterns (see §1 differentiation).
- *Presentation* — demo shows three distinct outcomes (compliant / stock-out / misplaced), proving the system discriminates between failure types, not just "flags something."

**Mandatory AMD integration:** AMD is required to be eligible for any prize. Shelf-Sense's compute core (the vision-language model) runs via **vLLM on ROCm, served through AMD Developer Cloud / Token Factory** — this is not optional and not a secondary feature.

**How the integration will work:** Every single inspection run makes one real HTTP call to an AMD-hosted, OpenAI-compatible vLLM endpoint. No local/CPU fallback model is used for the actual submitted demo. (A `MOCK_MODE` exists for offline development only — see §8 and §12 — and must never be the mode used in the submitted video or live demo.)

**How we will demonstrate it:** (a) the demo video shows real, un-cut latency on each of the three scenarios; (b) the README includes the literal `vllm serve` command and endpoint used; (c) if time allows, a terminal/log line showing the AMD endpoint hostname is visible on-screen during the recording.

**Submission requirements (from prior research, restated here so the coding agent doesn't need to re-derive them):**
- Project title, short description, long description, technology & category tags
- Cover image, video presentation (**≤5 minutes, ≤300MB** — this is a general lablab.ai platform rule, carried over as a strong assumption, not confirmed ACT-III-specific), slide presentation
- Public GitHub repository, demo application URL, demo application platform named
- Submission "must be original and MIT-compliant" (organiser's own wording)

**Relevant restrictions:**
- No AGPL-licensed components (rules out stock Ultralytics YOLO — not used here anyway, since this is a VLM-based approach, not a YOLO detector).
- Never commit API keys — environment variables only.
- No scraped/copyrighted shelf images — all demo and eval photos must be self-taken.

**Assumptions requiring verification:**
1. **[ASSUMPTION — VERIFY]** Exact submission cutoff hour/timezone — unresolved in research; build and submit assuming the earlier of the two candidate end-dates, not the later one.
2. **[ASSUMPTION — VERIFY]** That AMD Token Factory issues an **API key against a hosted inference endpoint** reachable over the public internet (like Fireworks/OpenAI), rather than requiring you to keep a private Jupyter notebook instance running as your own server. This is inferred from the hackathon's own FAQ ("Just the api from the tokenfactory") and from how other ACT III teams describe using it, but was not directly confirmed on a technical-access page. **This is the single most important thing to verify in Milestone 0** — it determines whether Shelf-Sense can be deployed on an external host (Render) at all, or whether the whole app must run inside the Token Factory notebook environment instead.
3. **[ASSUMPTION — VERIFY]** The exact model name(s) available through Token Factory with vision/multimodal capability (candidates: a Qwen3-VL variant, a multimodal Gemma 3 variant). Treat the model name as a config value (§12), not a hardcoded string, specifically because of this uncertainty.
4. **[ASSUMPTION — VERIFY]** The 5-minute/300MB video limit — carried over from lablab's general submission guidelines, not re-confirmed on the ACT III page itself.

---

## 3. PRODUCT REQUIREMENTS

**Core user journey:**
1. User opens the app.
2. User selects a spec (P0: exactly one hardcoded spec — "Aisle 4 cereal endcap").
3. User uploads a shelf photo, or picks one of the 3 bundled demo photos.
4. App shows a loading state, then: an annotated result, a per-item status table, a revenue-at-risk figure with its assumptions shown, and a plain-language action note.
5. (P2 stretch) User can run a second photo and compare.

**Required pages (single-page app, no routing needed for MVP):**
- One page: spec selector + photo input + results panel. No login, no history, no settings page.

**Required features (P0 unless marked):**
1. Spec selection (hardcoded single spec for P0; dropdown of 2–3 specs is P2).
2. Photo upload (file picker) + "use a demo photo" quick-select.
3. VLM compliance check → structured JSON (§7, §8).
4. Deterministic revenue-at-risk calculation (§8).
5. Plain-language action note (P1 — template-based fallback is P0, LLM-generated version is P1; see §8 fallback behaviour).
6. Annotated image overlay showing per-item status (P1 — a plain results table is sufficient for P0).

**Inputs:** one image file (JPEG/PNG, shelf/display photo), one spec (structured JSON, not free text, for P0 — see §7).

**Outputs:** a `ComplianceResult` object (§7) rendered as a table + summary text + revenue figure; optionally an annotated image.

**Empty states:** before any photo is selected/uploaded, show the spec summary and a clear "upload a photo or pick a demo photo to begin" prompt — no blank screen.

**Loading states:** a visible spinner/status text ("Running inspection on AMD-hosted Qwen3-VL via vLLM...") while awaiting the model response — inspection calls are expected to take several seconds, this must not look frozen.

**Error handling:**
- Endpoint unreachable → clear, specific error message ("Could not reach the AMD inference endpoint — check AMD_API_URL") with a retry button, never a silent failure or a raw stack trace in the UI.
- Malformed/unparseable model JSON → one automatic retry with a stricter re-prompt; if that also fails, show a "needs manual review" state rather than crashing or fabricating a result.
- No photo selected when the user clicks "run" → inline validation message, no API call made.

**Demo scenario (drives the required 3 demo photos):**
1. **Compliant shelf** — all expected items present in expected quantity → fast "compliant" result, $0 revenue at risk.
2. **Stock-out shelf** — a facing is clearly missing → "non_compliant," flagged item, non-zero revenue-at-risk figure, action note recommending restock.
3. **Misplaced-item shelf** — items present but in the wrong position/mixed with another product → a *different* status code than stock-out ("misplaced," not "missing") — this is what proves the system discriminates failure types, not just "something's off."

---

## 4. SYSTEM ARCHITECTURE

Deliberately a **single-process monolith** — per the hackathon's own time constraint and the explicit instruction to avoid unnecessary architecture complexity. No microservices, no message queue, no database.

| Layer | Choice | Why |
|---|---|---|
| **Frontend** | Streamlit, served by the same process as the backend logic | Fastest path to a working, demo-able UI for a solo/small-team same-day build; proven pattern for this exact category of app (zero-shot-VLM-inspection demos) in the repository audit. No separate frontend build step, no API versioning overhead. |
| **Backend** | Plain Python modules imported directly by the Streamlit app (no separate FastAPI service) | A public REST API is not required by the hackathon and would be pure added complexity for zero product benefit at this scope. If a future milestone needs a real API, `inspector.py`'s functions are already structured so they could be wrapped by FastAPI later without rewriting logic. |
| **AI/model-serving layer** | vLLM, OpenAI-compatible endpoint, served on AMD ROCm via AMD Developer Cloud / Token Factory | This is the mandatory, judged integration. OpenAI-compatible means standard `openai` Python client or plain `requests` can call it — no proprietary SDK needed. |
| **AMD technology integration** | The vLLM endpoint above; every inspection and every action-note generation call goes through it | See §2 for exactly how this is demonstrated. |
| **Data sources** | Self-taken photos only (3 demo + 15–30 eval), checked into the repo under `data/` | Avoids any scraped-image copyright risk; "do not fabricate datasets" — these are real photos of a real staged or real-world shelf. |
| **Storage** | None required beyond the filesystem (uploaded photo held in memory/session for the duration of one run) | No login, no history in the P0/P1 scope (§14), so no database is justified. |
| **External APIs** | Exactly one: the AMD-hosted vLLM OpenAI-compatible endpoint | No other third-party API calls in the MVP. |
| **Deployment architecture** | Single Docker container, deployed to a free-tier container host (Render — matches a pattern already used successfully by a live ACT III competitor, LineGuard) **[ASSUMPTION — VERIFY per §2 item 2: this only works if the vLLM endpoint is reachable from outside AMD's network]** | Simplest viable path that still produces a real, public, logged-out-reachable demo URL, which the hackathon explicitly requires. |

**Data flow:**
```
User photo + spec (JSON)
        │
        ▼
inspector.py: builds a structured prompt (spec + image) 
        │
        ▼
amd_client.py: POST to AMD vLLM OpenAI-compatible endpoint
        │
        ▼
Raw model response (expected: JSON string)
        │
        ▼
models.py: parse + validate against ComplianceResult schema
  (on failure → one retry with stricter prompt → "needs_review" fallback)
        │
        ▼
calculator.py: deterministic revenue-at-risk calc (pure Python, no model call)
        │
        ▼
action_agent.py: (P1) second AMD vLLM call → plain-language action note
                 (P0 fallback: Python string template, no model call)
        │
        ▼
app.py: renders table + figure + note (+ P1 annotated image)
```

---

## 5. REPOSITORY AND DEPENDENCY PLAN

| Name | URL | Purpose | Licence | Obligations | Integration approach | Mandatory/Optional |
|---|---|---|---|---|---|---|
| vLLM | `https://github.com/vllm-project/vllm` | Model-serving engine on the AMD side (run by/via Token Factory, not installed in our own container) | Apache-2.0 **[GENERAL KNOWLEDGE — confirm on the LICENSE file if we ever vendor any of its code, which the current plan does not require]** | Standard Apache-2.0 notice preservation if code is copied; we are calling it as a *service*, not embedding its code, so no obligation is triggered in our repo | Consumed only as an HTTP endpoint; nothing from this repo is copied into ours | **Mandatory** (it is the serving layer on AMD's side) |
| Streamlit | `https://github.com/streamlit/streamlit` | UI framework | Apache-2.0 **[GENERAL KNOWLEDGE]** | Standard notice preservation (satisfied automatically via `pip install streamlit`, no source copied) | `pip` dependency | Mandatory |
| Pillow | `https://github.com/python-pillow/Pillow` | Image loading/annotation | HPND (permissive, MIT-like) **[GENERAL KNOWLEDGE]** | Minimal — permissive | `pip` dependency | Mandatory |
| `requests` (or `httpx`) | `https://github.com/psf/requests` | HTTP calls to the AMD endpoint | Apache-2.0 **[GENERAL KNOWLEDGE]** | Minimal | `pip` dependency | Mandatory |
| `pydantic` | `https://github.com/pydantic/pydantic` | Schema validation for the model's structured output (§7) | MIT **[GENERAL KNOWLEDGE]** | Minimal | `pip` dependency | Mandatory |
| `pytest` | `https://github.com/pytest-dev/pytest` | Test runner | MIT **[GENERAL KNOWLEDGE]** | Minimal | `pip` dev-dependency | Mandatory (for §11) |
| AMD ROCm serving docs/pattern | `https://rocm.docs.amd.com`, `https://rocm.blogs.amd.com/artificial-intelligence/vllm/README.html` | Reference for the exact `vllm serve` invocation and OpenAI-compatible request shape | N/A — official AMD documentation, not a code dependency | None — public documentation, reused as a *reference command*, explicitly AMD's own intended usage | Copy the documented serve command into our own setup notes/README, attributed | Mandatory (as a reference, not as vendored code) |

**Explicitly not used, and why (carried over from the repository audit):**
- **Ultralytics YOLO** — AGPL-3.0/commercial dual licence, conflicts with the "MIT-compliant" submission rule; also unnecessary, since this is a VLM zero-shot approach, not a trained detector.
- **`JaDi03/AsBuilt-Lens`** — MIT-licensed and legally reusable, but deliberately **not forked or copied**, to keep Shelf-Sense a genuinely original submission (see §1). Only its *documented latency target* (≤8s) is reused as a benchmark reference, not its code.
- **Open WebUI, n8n** — not applicable to this product's scope; both carry licence caveats documented in the repository audit that have no reason to be taken on here.

No repository with an unclear licence is used as reusable code anywhere in this plan.

---

## 6. REPOSITORY STRUCTURE

```
shelf-sense/
├── app/
│   ├── __init__.py
│   ├── app.py              # Streamlit entrypoint — UI only, calls into the modules below
│   ├── config.py            # env var loading (AMD_API_URL, AMD_API_KEY, MODEL_NAME, MOCK_MODE)
│   ├── models.py            # Pydantic schemas: Spec, ItemCheck, ComplianceResult, RevenueImpact
│   ├── amd_client.py        # thin wrapper: POST to the AMD vLLM OpenAI-compatible endpoint
│   ├── inspector.py         # prompt construction + call + parse/validate/retry (§8)
│   ├── calculator.py        # deterministic revenue-at-risk formula — pure functions, no I/O
│   ├── action_agent.py      # P1: second AMD call → action note; P0 fallback: string template
│   └── annotate.py          # P1: draws status overlay on the image with Pillow
├── specs/
│   └── cereal_endcap.json   # the one hardcoded P0 spec
├── data/
│   ├── demo/                # 3 demo photos: compliant.jpg, stockout.jpg, misplaced.jpg
│   └── eval/                # 15–30 labeled eval images + labels.csv (§11)
├── eval/
│   └── run_eval.py          # computes precision/recall/latency against data/eval, prints a report
├── tests/
│   ├── test_models.py
│   ├── test_calculator.py
│   └── test_inspector_validation.py
├── assets/
│   ├── cover.png            # 16:9 submission cover image
│   └── screenshot.png
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── README.md
├── BLUEPRINT.md             # this file
└── AMD_HACKATHON_PROJECT_DECISION.md   # carried over from research phase, for context
```

---

## 7. DATA AND API CONTRACTS

### 7.1 Spec format (`specs/cereal_endcap.json`)
```json
{
  "spec_id": "cereal_endcap_v1",
  "location": "Aisle 4 endcap",
  "items": [
    {"item_id": "brand_a_cereal", "label": "Brand A Cereal Box", "expected_count": 6, "unit_margin_usd": 1.20, "est_daily_unit_sales": 8},
    {"item_id": "brand_b_cereal", "label": "Brand B Cereal Box", "expected_count": 4, "unit_margin_usd": 1.00, "est_daily_unit_sales": 5},
    {"item_id": "promo_sign", "label": "Promo Sign", "expected_count": 1, "unit_margin_usd": 0, "est_daily_unit_sales": 0}
  ]
}
```
`unit_margin_usd` and `est_daily_unit_sales` are **author-entered assumptions for the demo spec**, clearly labeled as such in the UI and README — never presented as real retail data.

### 7.2 Internal data models (`app/models.py`, Pydantic)

```python
class ItemCheck(BaseModel):
    item_id: str
    expected_count: int
    detected_count: int
    status: Literal["present", "missing", "partial", "misplaced"]
    confidence: float        # 0.0–100.0
    note: Optional[str] = None

class ComplianceResult(BaseModel):
    spec_id: str
    items: list[ItemCheck]
    overall_status: Literal["compliant", "non_compliant", "needs_review"]
    raw_model_notes: Optional[str] = None

class RevenueImpact(BaseModel):
    item_id: str
    units_missing: int
    unit_margin_usd: float
    est_daily_lost_sales_units: float
    est_daily_revenue_at_risk_usd: float
    assumptions: str          # human-readable explanation of the formula used
```

**Validation rules:**
- `status` must be one of the 4 literal values — anything else from the model triggers the retry path (§8).
- `confidence` must be in `[0, 100]`; out-of-range values are clamped, not rejected outright (log a warning).
- `detected_count` must be a non-negative integer.
- If the model returns an item not present in the spec, drop it and log a warning (don't let hallucinated items corrupt the report).
- If the model omits an item that *is* in the spec, treat it as `status="needs_review"`, `confidence=0` for that item, not `"missing"` — the model didn't say it was missing, it said nothing, and those are different claims.

**Error format (internal, raised as a custom exception, caught at the `app.py` boundary):**
```python
class InspectionError(Exception):
    def __init__(self, stage: str, detail: str):
        self.stage = stage      # "endpoint_unreachable" | "parse_failed" | "validation_failed"
        self.detail = detail
```

### 7.3 AMD endpoint request/response contract

Outbound request (OpenAI-compatible chat completions, multimodal content array):
```python
POST {AMD_API_URL}/chat/completions
Headers: {"Authorization": f"Bearer {AMD_API_KEY}"}  # if Token Factory requires a key — see §2 assumption
Body: {
  "model": "{MODEL_NAME}",       # config value, see §12
  "messages": [
    {"role": "system", "content": "<inspection instructions + required JSON schema>"},
    {"role": "user", "content": [
        {"type": "text", "text": "<spec, rendered as readable text>"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<...>"}}
    ]}
  ],
  "temperature": 0.1,
  "max_tokens": 1024
}
```
Expected response body: standard OpenAI chat-completion shape; `choices[0].message.content` is expected to be a JSON string matching `ComplianceResult` (minus `spec_id`, which we attach ourselves).

**No public-facing REST API is exposed by this app in the P0/P1 scope** — Streamlit calls these modules directly in-process. If a judge or future milestone needs a scriptable endpoint, that is explicitly P3 (§14).

---

## 8. AI WORKFLOW

**Model inputs:** the spec (rendered as readable text, not raw JSON, inside the prompt) + the uploaded image (base64-encoded, inline).

**Model outputs:** a JSON string matching the `ComplianceResult` item list (see §7.2) — the model is instructed to return *only* structured JSON, nothing else.

**Prompt/orchestration responsibilities (code, not the model):**
- Rendering the spec into prompt text.
- Enforcing the output schema via explicit instruction + a one-shot retry with a stricter "return ONLY valid JSON matching this schema" instruction if the first parse fails.
- All arithmetic (revenue-at-risk) — **never delegated to the model.**
- The action note (P1) is a *separate*, second model call that receives the already-validated `ComplianceResult` + `RevenueImpact` as input and is asked only to phrase them in plain language — it cannot change any number, because the numbers are passed in as already-fixed text, not computed by it.

**AMD inference path:** both the compliance-check call and the (P1) action-note call go through the same `amd_client.py` wrapper, hitting the same AMD-hosted vLLM endpoint. There is no non-AMD model call anywhere in the real (non-mock) execution path.

**Structured output validation:** Pydantic validation per §7.2, with the retry-then-fallback behaviour described there.

**Fallback behaviour:**
- Compliance check: unparseable after 1 retry → `overall_status="needs_review"`, show the raw model text to the user instead of a fabricated structured result, and the revenue calculator is **not run** on unvalidated data (no number is better than a wrong number here).
- Action note (P1): if the second model call fails for any reason, fall back to a deterministic Python string template built from the already-computed `RevenueImpact` list (e.g., `f"Restock {item.label}: {item.units_missing} units short, est. ${item.est_daily_revenue_at_risk_usd:.2f}/day at risk."`) — this keeps the app never fully broken by a second model-call failure, and is P0-safe (the template path has no AMD dependency, by design, as the guaranteed-working fallback).
- `MOCK_MODE=true` (local dev only, never the submission/demo configuration): `amd_client.py` returns a fixed, clearly-labeled fake `ComplianceResult` instead of calling any endpoint, purely so the UI can be developed before the AMD endpoint is confirmed working. **This must be explicitly off (`MOCK_MODE=false` / unset) for every demo recording and the deployed instance**, per the rule against claiming AMD usage that isn't real.

**Evaluation approach:** see §11 — a held-out labeled subset of `data/eval`, precision/recall per status class, plus end-to-end latency, computed by `eval/run_eval.py` and reported verbatim (not rounded up, not cherry-picked) in the README and slides.

---

## 9. UI/UX SPECIFICATION

**Visual direction:** plain, legible, "operations tool" feel, not a marketing landing page — a store manager should understand the result in under 10 seconds. Minimal color use: green/amber/red only for status, not decoration.

**Layout:** single column on mobile, two-column on desktop — left: spec + photo input; right: results panel. Streamlit's default layout with `st.columns(2)` is sufficient; no custom CSS required for P0.

**Navigation:** none needed — single page, single flow.

**Components:**
- Spec summary card (read-only for P0).
- File uploader + "use demo photo" button row (3 buttons, one per demo scenario).
- "Run inspection" button, disabled until a photo is selected.
- Results panel: status badge (compliant/non-compliant/needs-review), per-item table, revenue-at-risk card with its stated assumptions visible, action note text block.
- (P1) Annotated image with colored boxes/labels per item status.

**Information hierarchy:** overall status first (biggest, top), then the dollar figure (second-biggest — this is the business-value headline), then the per-item table (detail), then the action note (what to do about it), then raw/debug info last and collapsed by default.

**Responsive behaviour:** Streamlit's default responsive column collapse (stacks to one column on narrow viewports) is sufficient — no custom breakpoints required for P0/P1.

**Charts/visualisations:** none required for P0. P2 stretch: a simple bar chart of revenue-at-risk by item if `eval/run_eval.py` output is shown in the app itself (not required — the eval report can just be a printed/markdown artifact for the README).

**Accessibility basics:** every status badge must also carry a text label, not color alone (colorblind-safe by default, since we're already pairing color with text); all images need `alt` text via Streamlit's `caption` parameter; font sizes left at Streamlit defaults (already accessible).

---

## 10. IMPLEMENTATION MILESTONES

### Milestone 0 — Access verification (do this before writing any app code)
- **Goal:** confirm the AMD assumptions in §2 before architecture decisions are locked in further.
- **Tasks:** log into Token Factory; confirm whether it issues a public API key + base URL, or only a notebook environment; identify the exact name of an available vision-capable model; do one raw `curl`/Python request against the endpoint and get back *any* valid chat-completion response.
- **Acceptance criteria:** a successful, non-mocked HTTP 200 response from the AMD endpoint, saved as a text file for reference.
- **Commands:** `curl -X POST "$AMD_API_URL/chat/completions" -H "Authorization: Bearer $AMD_API_KEY" -H "Content-Type: application/json" -d '{"model":"<name>","messages":[{"role":"user","content":"ping"}]}'`
- **Common failure modes:** endpoint requires a different auth scheme than `Bearer`; model name wrong (check the Token Factory UI's model list); GPU pod still provisioning (can take several minutes) — don't treat the first failure as fatal, retry after a short wait.

### Milestone 1 — Minimal working end-to-end path
- **Goal:** one photo, one spec, one real AMD inference call, one parsed `ComplianceResult` printed to a terminal. No UI yet.
- **Files:** `app/config.py`, `app/models.py`, `app/amd_client.py`, `app/inspector.py`, `specs/cereal_endcap.json`, `data/demo/compliant.jpg` (at least one real photo).
- **Tasks:** implement config loading, the Pydantic models, the AMD client wrapper, the prompt builder, and the parse/validate/retry logic; run it as a script against one demo photo.
- **Acceptance criteria:** running `python -m app.inspector --spec specs/cereal_endcap.json --image data/demo/compliant.jpg` prints a valid `ComplianceResult` with no exceptions, using a real (non-mock) AMD call.
- **Tests:** `tests/test_models.py` (schema validation edge cases from §7.2), `tests/test_inspector_validation.py` (retry/fallback logic, can use a mocked AMD response for this specific test, not the live endpoint).
- **Common failure modes:** model returns prose instead of JSON (fix the system prompt to be more insistent, add a "return ONLY JSON" line); base64 image too large for the request (resize to a reasonable max dimension, e.g. 1024px, before encoding).

### Milestone 2 — Deterministic revenue calculator
- **Goal:** turn a `ComplianceResult` into a `RevenueImpact` list with zero model calls.
- **Files:** `app/calculator.py`, `tests/test_calculator.py`.
- **Tasks:** implement `calculate_revenue_impact(result: ComplianceResult, spec: Spec) -> list[RevenueImpact]` as a pure function.
- **Acceptance criteria:** unit tests cover compliant (zero impact), stock-out (positive impact, correct formula), and partial/misplaced cases.
- **Tests:** `pytest tests/test_calculator.py -v`.
- **Common failure modes:** off-by-one in `units_missing` when `detected_count > expected_count` (treat as 0 missing, not negative).

### Milestone 3 — Action note (P1, with P0-safe fallback)
- **Goal:** plain-language action text from the `RevenueImpact` list, with a template fallback that requires no model call.
- **Files:** `app/action_agent.py`.
- **Tasks:** implement the template-based version first (P0-safe), then the AMD-call version on top of it as the default with the template as its fallback (§8).
- **Acceptance criteria:** both paths produce non-empty, grammatically sane text for all three demo scenarios.

### Milestone 4 — Streamlit UI
- **Goal:** the full user journey from §3, wired to Milestones 1–3.
- **Files:** `app/app.py`.
- **Tasks:** implement the layout from §9, wire up the demo-photo quick-select buttons, implement all three states (empty/loading/error) from §3.
- **Acceptance criteria:** a human can run all three demo scenarios through the actual UI and see visibly different, correct results for each.
- **Commands:** `streamlit run app/app.py`.
- **Common failure modes:** Streamlit re-running the whole script on every interaction causing duplicate API calls — use `st.session_state` to cache the last result instead of recomputing on unrelated UI interactions.

### Milestone 5 — Evaluation
- **Goal:** real precision/recall/latency numbers on the labeled eval set.
- **Files:** `eval/run_eval.py`, `data/eval/*.jpg`, `data/eval/labels.csv`.
- **Tasks:** label 15–30 self-taken photos by hand; run every one through `inspector.py`; compare against labels; compute and print precision/recall per status class and mean/median latency.
- **Acceptance criteria:** a reproducible report (plain text or markdown table) with real numbers, used verbatim in the README — no rounding up, no cherry-picked subset.
- **Commands:** `python eval/run_eval.py --data data/eval`.

### Milestone 6 — Containerize and deploy
- **Goal:** a public, logged-out-reachable demo URL.
- **Files:** `Dockerfile`, `.env.example`.
- **Tasks:** write the Dockerfile (§12); test a clean `docker build && docker run` from scratch, with only `.env` values set, no other local state; deploy to Render (or the confirmed-working host per §2/Milestone 0's findings).
- **Acceptance criteria:** opening the deployed URL in a private/incognito browser window, with no prior session, successfully runs all three demo scenarios end-to-end.
- **Commands:** `docker build -t shelf-sense . && docker run -p 8501:8501 --env-file .env shelf-sense`.
- **Common failure modes:** the deployed host can't reach the AMD endpoint (firewall/network — this is why Milestone 0 matters so much); env vars not set on the host's dashboard (easy to forget, since local `.env` doesn't travel with the deploy).

### Milestone 7 — Documentation and submission assets
- **Goal:** everything in §13, ready to paste into the submission form.
- **Files:** `README.md`, `assets/cover.png`, demo video, slides.
- **Acceptance criteria:** the full submission checklist in §15 is satisfied.

---

## 11. TESTING

- **Unit tests:** `test_models.py` (Pydantic validation edge cases per §7.2 — missing fields, out-of-range confidence, unknown status values), `test_calculator.py` (compliant/stockout/partial/over-stocked cases).
- **API tests:** none in the public sense (§7.3 — no exposed REST API); `test_inspector_validation.py` covers the retry/fallback logic against a **mocked** AMD response (not a live call, so this test suite runs offline and in CI without needing credentials).
- **Integration tests:** one explicitly-marked, opt-in test (`@pytest.mark.live`) that makes a real AMD call end-to-end — run manually before each demo recording, not in every CI run, to avoid burning GPU time/credits on every commit.
- **AI output validation:** covered by the Pydantic schema (§7.2) plus the retry-then-needs-review fallback (§8) — there is no scenario in which an invalid model response reaches the UI as if it were valid.
- **AMD integration verification:** Milestone 0's saved raw response, plus the `@pytest.mark.live` integration test, plus the on-screen evidence described in §2.
- **Manual demo checklist (run this immediately before recording the video and again right before final submission):**
  - [ ] Compliant photo → correct "compliant" result, $0 at risk.
  - [ ] Stock-out photo → correct "non_compliant," correct item flagged, non-zero $ figure with visible assumptions.
  - [ ] Misplaced photo → status is `"misplaced"`, distinct from the stock-out case.
  - [ ] Deployed URL works from a fresh/incognito browser session.
  - [ ] `MOCK_MODE` is off on the deployed instance.
  - [ ] README setup steps work on a genuinely clean clone (not just "works on my machine").

---

## 12. DEPLOYMENT

**Simplest viable approach:** one Dockerized Streamlit service, deployed to Render's free/starter web-service tier, built directly from the GitHub repo (Render's native GitHub-connected deploy, no separate CI pipeline needed).

**Dockerfile (shape, not final content — implement exactly this structure):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Environment variables (`.env.example` — committed; real `.env` is gitignored):**
```
AMD_API_URL=https://<token-factory-endpoint>/v1
AMD_API_KEY=<your-token-factory-api-key>
MODEL_NAME=<confirmed-vision-model-name-from-milestone-0>
MOCK_MODE=false
```

**Setup commands (local dev):**
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
streamlit run app/app.py
```

**Secrets handling:** `.env` is in `.gitignore` from the first commit; Render's own dashboard environment-variable UI holds the real values for the deployed instance; the README explicitly instructs "never commit `.env`," matching the hackathon's own stated rule.

**What we are deliberately not doing:** no Kubernetes, no separate database service, no CDN, no custom domain, no CI/CD pipeline beyond Render's native git-push deploy — all of that would be infrastructure we cannot realistically configure correctly before the deadline, for zero judging benefit at this scope.

---

## 13. DOCUMENTATION AND SUBMISSION

**README structure:**
1. One-paragraph pitch (from §1).
2. Screenshot/GIF of the three demo scenarios.
3. **"How this uses AMD"** section — the exact `vllm serve`/endpoint details, stated plainly, with the real eval latency numbers from Milestone 5.
4. Setup instructions that a stranger can follow on a clean clone (the literal commands from §12).
5. Architecture diagram or the data-flow block from §4.
6. Evaluation results table (real numbers from Milestone 5, labeled as coming from a small self-made dataset — not implied to be a large/industry benchmark).
7. Limitations (see below — be honest, don't oversell).
8. Licence notices for every dependency in §5.

**Installation instructions:** exactly the commands in §12, verified to work on a clean clone as part of Milestone 6/7's acceptance criteria.

**Architecture explanation:** the §4 table and data-flow diagram, reused directly.

**AMD integration evidence:** the real endpoint/model details, the real eval latency numbers, and (if captured) the on-screen log line from the demo recording.

**Limitations (be explicit about these, don't bury them):**
- Eval set is small (15–30 self-taken photos) — results are indicative, not a large-scale benchmark; stated as such everywhere the numbers appear.
- Spec authoring is manual/hardcoded for the submitted MVP (no auto-discovery of shelf layout).
- Revenue-at-risk uses author-entered assumptions for unit margin/daily sales in the demo spec — clearly a worked example, not live POS data.
- Single-location, single-spec scope; no multi-store, no persistence/history.

**Attribution and licence notices:** a short table in the README listing every dependency from §5 with its licence, plus an explicit one-line note that the zero-shot-VLM-inspection *pattern* draws conceptual inspiration from the prior MIT-licensed `AsBuilt-Lens` project (credited, not copied — per §1/§5).

**Demo video structure (≤5 min target per §2's assumption):**
1. (15s) Problem statement, one sentence.
2. (20s) Compliant-shelf run.
3. (40s) Stock-out run — pause on the revenue-at-risk figure and its assumptions.
4. (30s) Misplaced-item run — call out explicitly that the status differs from the stock-out case.
5. (30s) Quick architecture callout: "every one of those calls just went to Qwen3-VL running on AMD via vLLM on ROCm" — show the README's AMD section or a terminal log line.
6. (15s) Close: who it's for, what it's not (limitations), link to the repo.

**Slide outline:** Problem → Solution (one screenshot) → Architecture (the §4 diagram) → AMD integration (the same evidence as the README section) → Business value (the revenue-at-risk mechanic, explained) → Real eval numbers → Limitations/what's next.

**Final submission checklist (from the earlier hackathon-requirements research, restated so nothing is missed at 2 a.m.):**
- [ ] Project title, short description, long description
- [ ] Selected challenge = Reinvent Commerce
- [ ] Technology tags filled in
- [ ] Cover image (16:9) uploaded
- [ ] Demo video uploaded (≤5 min, ≤300MB per the carried-over assumption)
- [ ] Slide presentation uploaded
- [ ] Public GitHub repository link, confirmed reachable logged-out
- [ ] Demo application platform named (Render)
- [ ] Demo application URL, confirmed reachable logged-out, `MOCK_MODE` off
- [ ] README runnable by a stranger on a clean clone

---

## 14. TIME-CRITICAL PRIORITIES

**P0 — mandatory for a valid submission:**
- Milestone 0 access verification
- Milestone 1 (real AMD call, validated structured output)
- Milestone 2 (deterministic revenue calculator)
- Action note **template fallback** (not the LLM version)
- Milestone 4 minimal UI (upload/select photo → see a result)
- Milestone 6 (Dockerized, deployed, publicly reachable)
- README with real, working setup instructions and AMD-integration evidence
- Demo video, slides, and a fully completed submission form

**P1 — important for judging quality:**
- Action note via the second AMD call (on top of the P0 template fallback)
- Milestone 5 real evaluation numbers (precision/recall/latency)
- Annotated image overlay (`annotate.py`)
- Clean error handling for all three states in §3
- Polish on the loading/empty states

**P2 — optional polish, only if P0 and P1 are fully done with time to spare:**
- Multiple selectable specs (not just the one hardcoded demo spec)
- Auto-discovery of visible items (no manual spec authoring)
- A results-trend chart in-app
- A documented pass using a Gemma-family vision model specifically, to also qualify for the Google partner prize

**P3 — explicitly out of scope, do not build:**
- User accounts/login
- A database or any persistence beyond one session
- Multi-store or multi-photo history
- Any second input modality (sensor data, video) — this is image-only
- Evolus track integration — this submission targets the Reinvent Commerce track only

---

## 15. DEFINITION OF DONE

The project is ready to submit when **all** of the following are simultaneously true:

1. The deployed demo URL loads for a logged-out stranger in a fresh browser session.
2. All three demo scenarios (compliant / stock-out / misplaced) run successfully through the real UI and produce visibly different, correct results.
3. Every one of those three runs makes a real call to the AMD-hosted vLLM endpoint — `MOCK_MODE` is confirmed off on the deployed instance.
4. The revenue-at-risk figure is computed by `calculator.py` (verifiable by reading the code — not asserted by the model).
5. `eval/run_eval.py` has been run for real, and its real output numbers (not placeholders) appear in the README.
6. A stranger can clone the repo fresh and follow the README to a working local run, with no undocumented manual steps.
7. The GitHub repository is public, and contains no committed secrets (`.env` is absent from the repo, `.env.example` is present).
8. The demo video and slides exist, are uploaded, and the video stays within the assumed 5-minute/300MB limit.
9. The lablab.ai submission form is fully completed per the §13 checklist and has been submitted (not left as a draft).
10. Every dependency in §5 is accounted for with its licence, and nothing AGPL or unclear-licence is present in the shipped code.

If any one of these ten is false, the project is not done — regardless of how much P2 polish exists on top of it.
