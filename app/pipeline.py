"""One inspection run end to end: image validation -> inspector -> calculator -> action note.

No Streamlit here, so the whole flow the UI uses is testable on its own.
"""

from PIL import Image
from pydantic import BaseModel, ConfigDict

from app import amd_client
from app.action_agent import generate_action_note
from app.calculator import summarize_exposure
from app.config import Settings
from app.inspector import inspect, load_image
from app.models import ActionNote, ComplianceResult, ExposureSummary, InspectionError, Spec

MAX_UPLOAD_MB = 15


class PipelineRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    result: ComplianceResult
    summary: ExposureSummary
    note: ActionNote


def validate_image(data: bytes) -> Image.Image:
    """Reject empty/oversized/unreadable files before any inference. Returns the decoded image."""
    if not data:
        raise InspectionError("invalid_image", "The file is empty.")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise InspectionError("invalid_image", f"The file is larger than {MAX_UPLOAD_MB} MB.")
    return load_image(data)


def run_inspection(
    spec: Spec, image_bytes: bytes, settings: Settings, *, chat=amd_client.chat_completion
) -> PipelineRun:
    """Raises InspectionError if the inspection call itself fails. A failed action-note call
    never fails the run — it falls back to the template inside generate_action_note."""
    validate_image(image_bytes)
    result = inspect(spec, image_bytes, settings, chat=chat)
    summary = summarize_exposure(result, spec)
    note = generate_action_note(result, summary, spec, settings, chat=chat)
    return PipelineRun(result=result, summary=summary, note=note)
