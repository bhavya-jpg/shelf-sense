"""Shelf-Sense Streamlit UI (BLUEPRINT §3, §9). Layout and session state only — all logic
lives in app.pipeline / inspector / calculator / action_agent.

Run: streamlit run app/app.py
"""

import hashlib
import logging
import os
import sys
from pathlib import Path

# `streamlit run app/app.py` puts app/ first on sys.path; put the repo root first so
# `import app` resolves to the package, not to this file.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app import presenters  # noqa: E402
from app.config import REPO_ROOT, ConfigError, load_settings  # noqa: E402
from app.models import InspectionError, Spec  # noqa: E402
from app.pipeline import MAX_UPLOAD_MB, run_inspection, validate_image  # noqa: E402

log = logging.getLogger("shelf_sense.ui")

SPEC_DIR = Path(os.environ.get("SHELF_SENSE_SPEC_DIR", REPO_ROOT / "specs"))
DEMO_DIR = Path(os.environ.get("SHELF_SENSE_DEMO_DIR", REPO_ROOT / "data" / "demo"))
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")

st.set_page_config(page_title="Shelf-Sense", layout="wide")


# --- state helpers ---------------------------------------------------------------

def _select_image(name: str, data: bytes, source: str) -> None:
    try:
        preview, error = validate_image(data), None
    except InspectionError as exc:
        preview, error = None, presenters.error_message(exc)
    st.session_state.image = {
        "name": name,
        "data": data,
        "source": source,
        "sha": hashlib.sha256(data).hexdigest(),
        "preview": preview,
        "error": error,
    }


def _on_upload() -> None:
    uploaded = st.session_state.get("uploader")
    if uploaded is not None:
        _select_image(uploaded.name, uploaded.getvalue(), "upload")
    elif (st.session_state.get("image") or {}).get("source") == "upload":
        st.session_state.image = None


def _select_demo(path: str) -> None:
    _select_image(Path(path).name, Path(path).read_bytes(), "demo")


def _request_retry() -> None:
    st.session_state.retry = True


@st.cache_data
def _spec_paths() -> dict[str, str]:
    return {p.stem: str(p) for p in sorted(SPEC_DIR.glob("*.json"))}


# --- header ----------------------------------------------------------------------

st.title("Shelf-Sense")
st.caption(
    "Check a shelf photo against its spec: per-item status from a vision model, estimated margin at risk "
    "computed by code, and a list of actions."
)

try:
    settings, config_error = load_settings(), None
except ConfigError as exc:
    settings, config_error = None, str(exc)

if config_error:
    st.error(f"Inference is not configured, so inspections can't run. {config_error}")
elif settings.mock_mode:
    st.warning(
        "**MOCK MODE.** Inspections return a fixed fake result and make no AMD inference call. "
        "Turn MOCK_MODE off for demos and deployment."
    )
else:
    st.caption(f"Inference: **{settings.model_name}** via AMD Developer Cloud Token Factory (`{settings.endpoint_host}`)")

left, right = st.columns([2, 3], gap="large")

# --- left: inputs ----------------------------------------------------------------

with left:
    st.subheader("1. Spec")
    spec_paths = _spec_paths()
    spec = None
    if not spec_paths:
        st.error(f"No spec files found in {SPEC_DIR}.")
    else:
        spec_name = st.selectbox("Inspection spec", list(spec_paths), key="spec_name")
        try:
            spec = Spec.load(spec_paths[spec_name])
        except Exception as exc:  # malformed spec file: show it, don't crash the page
            st.error(f"Spec file {spec_name}.json is invalid: {type(exc).__name__}: {str(exc)[:300]}")
    if spec:
        st.markdown(f"**{spec.location}** · `{spec.spec_id}`")
        st.dataframe(
            [
                {
                    "Product": i.label,
                    "Expected": i.expected_count,
                    "Unit margin (demo assumption)": presenters.usd(i.unit_margin_usd)
                    if i.unit_margin_usd is not None else "Not set",
                }
                for i in spec.items
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Unit margins are author-entered demo assumptions, not real retail data.")

    st.subheader("2. Shelf photo")
    demo_files = sorted(p for p in DEMO_DIR.glob("*") if p.suffix.lower() in IMAGE_SUFFIXES) if DEMO_DIR.is_dir() else []
    if demo_files:
        st.caption("Use a demo photo:")
        cols = st.columns(len(demo_files))
        for col, path in zip(cols, demo_files):
            col.button(path.stem.replace("_", " ").title(), key=f"demo_{path.stem}",
                       on_click=_select_demo, args=(str(path),), use_container_width=True)
    else:
        st.caption("No demo photos are bundled yet. Upload a shelf photo instead.")
    st.file_uploader(f"Upload a shelf photo (JPEG or PNG, up to {MAX_UPLOAD_MB} MB)",
                     type=["jpg", "jpeg", "png"], key="uploader", on_change=_on_upload)

    image = st.session_state.get("image")
    if image and image["error"]:
        st.error(f"**{image['name']}**: {image['error']}")
    elif image:
        st.image(image["preview"], caption=f"{image['name']} (orientation as sent to the model)",
                 use_container_width=True)

    st.subheader("3. Inspect")
    ready = bool(settings and spec and image and not image["error"])
    clicked = st.button("Run inspection", key="run", type="primary", disabled=not ready, use_container_width=True)
    if not ready:
        if not image:
            st.caption("Upload a photo or pick a demo photo to enable the inspection.")
        elif image["error"]:
            st.caption("Choose a readable JPEG or PNG photo to enable the inspection.")
        elif not settings:
            st.caption("Configure the inference endpoint (see the message at the top) to enable the inspection.")

# --- right: run + results ----------------------------------------------------------

with right:
    run_key = f"{spec.spec_id}:{image['sha']}" if ready else None

    if ready and (clicked or st.session_state.pop("retry", False)):
        label = (
            "Running MOCK inspection (no AMD call)…" if settings.mock_mode
            else f"Running inspection on {settings.model_name} via the AMD Token Factory endpoint…"
        )
        with st.status(label, expanded=False) as status:
            try:
                st.session_state.outcome = {"key": run_key, "run": run_inspection(spec, image["data"], settings)}
                status.update(label="Inspection complete", state="complete")
            except InspectionError as exc:
                st.session_state.outcome = {"key": run_key, "error": presenters.error_message(exc)}
                status.update(label="Inspection failed", state="error")
            except Exception as exc:  # never show a raw stack trace in the UI
                log.exception("unexpected inspection failure")
                st.session_state.outcome = {"key": run_key, "error": f"Unexpected error ({type(exc).__name__}). Retry; if it persists, check the server log."}
                status.update(label="Inspection failed", state="error")

    outcome = st.session_state.get("outcome")
    st.subheader("Results")
    if not outcome or not ready:
        st.info("Pick a spec and a shelf photo, then run the inspection. Results appear here.")
    elif outcome["key"] != run_key:
        st.info("The photo or spec changed since the last inspection. Run the inspection again to see results for it.")
    elif "error" in outcome:
        st.error(presenters.md(outcome["error"]))
        st.button("Retry inspection", key="retry_button", on_click=_request_retry)
    else:
        run = outcome["run"]
        result, summary, note = run.result, run.summary, run.note

        if result.is_mock:
            st.warning("**MOCK RESULT.** Fixed fake data. No AMD inference call was made.")

        kind, text = presenters.overall_badge(result)
        getattr(st, kind)(f"**Overall status: {text}**")

        c1, c2 = st.columns(2)
        c1.metric(presenters.estimate_label(summary), presenters.estimated_value(summary),
                  help=presenters.estimate_help(summary))
        c2.metric(presenters.POTENTIAL_LABEL, presenters.potential_value(summary),
                  help="Upper bound for misplaced / needs-review items. Not included in the estimate.")
        for msg_kind, msg in presenters.exposure_messages(summary):
            getattr(st, msg_kind)(presenters.md(msg))

        if not result.items:
            st.warning("The model's output could not be validated after one retry, so no item results are shown.")
            with st.expander("Raw model output"):
                st.code(result.raw_model_notes or "(empty)", language=None)
        else:
            st.markdown("**Items**")
            st.dataframe(presenters.item_rows(result, summary, note), hide_index=True, use_container_width=True)
            st.caption("Model confidence is self-reported by the model and is not calibrated.")

        st.markdown("**Recommended actions**")
        st.markdown(presenters.note_markdown(note.text))
        st.caption(presenters.md(presenters.note_source_caption(note)))

        if summary.calculation_available:
            with st.expander("How the figures are calculated"):
                st.markdown(presenters.md(summary.assumptions))
                for i in summary.items:
                    st.markdown(presenters.md(f"- **{i.label}**: {i.assumptions}"))

        with st.expander("Technical details"):
            st.markdown(
                presenters.md(
                    f"- Inference: {'MOCK (no AMD call)' if result.is_mock else 'real call to the AMD Token Factory endpoint'}\n"
                    f"- Model: {result.model_name or 'n/a'}\n"
                    f"- Endpoint host: {settings.endpoint_host if settings and not result.is_mock else 'n/a'}\n"
                    f"- Inspection latency: {result.latency_s}s\n"
                    f"- Action note: {note.source}"
                    + (f" ({note.latency_s}s)" if note.latency_s is not None else "")
                )
            )
            if result.raw_model_notes and result.items:
                st.caption(presenters.md(f"Model notes: {result.raw_model_notes}"))
            st.json(result.model_dump(), expanded=False)
