"""Dashboard page: the inspection workspace (BLUEPRINT §3, §9). Layout and session state only —
all logic lives in app.pipeline / inspector / calculator / action_agent.

Served by the router in app/app.py (`streamlit run app/app.py`, path /inspect). It also runs on
its own, which is how tests/test_app.py drives it.
"""

import hashlib
import logging
import os
import sys
from pathlib import Path

# Put the repo root first on sys.path so `import app` resolves to the package (needed when this
# page runs on its own; harmless under the router).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from app import presenters, ui  # noqa: E402
from app.config import REPO_ROOT, ConfigError, load_settings  # noqa: E402
from app.models import InspectionError, Spec  # noqa: E402
from app.pipeline import MAX_UPLOAD_MB, run_inspection, validate_image  # noqa: E402

log = logging.getLogger("shelf_sense.ui")

SPEC_DIR = Path(os.environ.get("SHELF_SENSE_SPEC_DIR", REPO_ROOT / "specs"))
DEMO_DIR = Path(os.environ.get("SHELF_SENSE_DEMO_DIR", REPO_ROOT / "data" / "demo"))
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


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


def _clear_image() -> None:
    st.session_state.image = None


def _request_retry() -> None:
    st.session_state.retry = True


@st.cache_data
def _spec_paths() -> dict[str, str]:
    return {p.stem: str(p) for p in sorted(SPEC_DIR.glob("*.json"))}


# --- header ----------------------------------------------------------------------

def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


try:
    settings, config_error = load_settings(), None
except ConfigError as exc:
    settings, config_error = None, str(exc)

html(ui.workspace_head(
    settings.model_name if settings else None,
    settings.endpoint_host if settings else None,
    mock=bool(settings and settings.mock_mode),
    configured=settings is not None,
))
if config_error:
    html(ui.notice("bad", "Not configured", "Inference is not configured, so inspections can't run.", config_error))
elif settings.mock_mode:
    html(ui.notice("warn", "Mock mode", "MOCK MODE. Inspections return a fixed fake result and make no AMD "
                   "inference call. Turn MOCK_MODE off for demos and deployment."))

left, right = st.columns([4, 8], gap="large")

# --- left: inspection setup ------------------------------------------------------------

with left, st.container(border=True):
    html(ui.section("01", "Inspection setup"))
    spec_paths = _spec_paths()
    spec = None
    if not spec_paths:
        html(ui.notice("bad", "No spec", f"No spec files found in {SPEC_DIR}."))
    else:
        spec_name = st.selectbox("Shelf specification", list(spec_paths), key="spec_name")
        try:
            spec = Spec.load(spec_paths[spec_name])
        except Exception as exc:  # malformed spec file: show it, don't crash the page
            html(ui.notice("bad", "Invalid spec", f"Spec file {spec_name}.json is invalid.",
                           f"{type(exc).__name__}: {str(exc)[:300]}"))
    if spec:
        html(ui.label("Expected inventory"))
        html(ui.spec_table(spec))

    html(ui.label("Shelf photograph", f"JPEG / PNG · up to {MAX_UPLOAD_MB} MB"))
    image = st.session_state.get("image")
    if image and image["error"]:
        html(ui.notice("bad", "Can't use file", f"{image['name']}: {image['error']}"))
    elif image:
        st.image(image["preview"], use_container_width=True)
        html(ui.file_meta(image["name"], len(image["data"]), image["preview"].size,
                          "demo photo" if image["source"] == "demo" else "uploaded"))
        html(ui.hint("Sent to the model EXIF-rotated and resized to at most 1024 px."))

    demo_files = sorted(p for p in DEMO_DIR.glob("*") if p.suffix.lower() in IMAGE_SUFFIXES) if DEMO_DIR.is_dir() else []
    if demo_files:
        html(ui.label("Demo photo", "self-taken"))
        cols = st.columns(len(demo_files))
        for col, path in zip(cols, demo_files):
            col.button(path.stem.replace("_", " ").title(), key=f"demo_{path.stem}",
                       on_click=_select_demo, args=(str(path),), use_container_width=True)
    st.file_uploader("Replace photo" if image else "Upload shelf photo", type=["jpg", "jpeg", "png"],
                     key="uploader", on_change=_on_upload)
    if image:
        st.button("Remove photo", key="clear_image", on_click=_clear_image)

    html('<div class="ss-gap"></div>')
    ready = bool(settings and spec and image and not image["error"])
    clicked = st.button("Run inspection  →", key="run", type="primary", disabled=not ready, use_container_width=True)
    if not ready:
        if not image:
            html(ui.hint("Upload a photo or pick the demo photo to enable the inspection."))
        elif image["error"]:
            html(ui.hint("Choose a readable JPEG or PNG photo to enable the inspection."))
        elif not settings:
            html(ui.hint("Configure the inference endpoint (see the message at the top) to enable the inspection."))

# --- right: run + results -----------------------------------------------------------------

with right, st.container(border=True):
    html(ui.section("02", "Results", "AI counts · code decisions"))
    run_key = f"{spec.spec_id}:{image['sha']}" if ready else None

    if ready and (clicked or st.session_state.pop("retry", False)):
        slot = st.empty()
        slot.markdown(ui.processing(settings.model_name, settings.mock_mode), unsafe_allow_html=True)
        try:
            st.session_state.outcome = {"key": run_key, "run": run_inspection(spec, image["data"], settings)}
        except InspectionError as exc:
            st.session_state.outcome = {"key": run_key, "error": presenters.error_message(exc)}
        except Exception as exc:  # never show a raw stack trace in the UI
            log.exception("unexpected inspection failure")
            st.session_state.outcome = {"key": run_key, "error": f"Unexpected error ({type(exc).__name__}). Retry; if it persists, check the server log."}
        slot.empty()

    outcome = st.session_state.get("outcome")
    if not outcome or not ready:
        html(ui.empty_state())
    elif outcome["key"] != run_key:
        html(ui.notice("plain", "Out of date", "The photo or spec changed since the last inspection. "
                       "Run the inspection again to see results for it."))
        html(ui.empty_state())
    elif "error" in outcome:
        headline, _, detail = outcome["error"].partition("\n\nDetails ")
        html(ui.notice("bad", "Inspection failed", headline, f"Details {detail}" if detail else None))
        st.button("Retry inspection", key="retry_button", on_click=_request_retry)
    else:
        run = outcome["run"]
        result, summary, note = run.result, run.summary, run.note

        html(ui.verdict(result, settings.endpoint_host if settings else None))
        if result.is_mock:
            html(ui.notice("warn", "Mock result", "MOCK RESULT. Fixed fake data. No AMD inference call was made."))
        html(ui.stats(result, summary))
        tags = {"info": ("warn", "Unverified"), "warning": ("warn", "Attention")}
        for msg_kind, msg in presenters.exposure_messages(summary):
            kind, tag = tags.get(msg_kind, ("warn", "Attention"))
            html(ui.notice(kind, tag, msg))

        if not result.items:
            html(ui.notice("warn", "Needs review", "The model's output could not be validated after one retry, "
                           "so no item results are shown."))
            with st.expander("Raw model output"):
                st.code(result.raw_model_notes or "(empty)", language=None)
        else:
            html(ui.label("Discrepancies", f"{len(ui.discrepancy_items(summary))} of {len(result.items)} products"))
            html(ui.discrepancies(summary))
            html(ui.label("Product results", "counts from the model · status and money from code"))
            html(ui.items_table(result, summary))

        html('<div class="ss-gap"></div>')
        html(ui.actions(note, summary))
        html('<div class="ss-gap"></div>')

        if result.items:
            with st.expander("Model observations"):
                html(ui.observations_table(result, summary))
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
