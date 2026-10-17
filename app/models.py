"""Pydantic schemas (BLUEPRINT §7)."""

import json
import logging
from pathlib import Path
from typing import Annotated, Literal, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

log = logging.getLogger(__name__)

# Statuses the model is allowed to return. Anything else triggers the retry path (§8).
ModelStatus = Literal["present", "missing", "partial", "misplaced"]
# "needs_review" is assigned by code only, e.g. when the model omits a spec item (§7.2).
ItemStatus = Literal["present", "missing", "partial", "misplaced", "needs_review"]


class SpecItem(BaseModel):
    item_id: str
    label: str
    expected_count: int = Field(ge=0)
    # Financial fields are author-entered assumptions and may be absent or invalid. They are
    # NOT range-checked here so the calculator can report them as "unavailable" (with a
    # reason) instead of rejecting the whole spec or silently treating them as $0.
    unit_margin_usd: Optional[float] = None
    est_daily_unit_sales: Optional[float] = None


class Spec(BaseModel):
    spec_id: str
    location: str
    items: list[SpecItem] = Field(min_length=1)

    @classmethod
    def load(cls, path: str | Path) -> "Spec":
        return cls.model_validate(json.loads(Path(path).read_text()))


def _clamp_confidence(value: float) -> float:
    if value < 0 or value > 100:
        log.warning("confidence %s out of [0, 100]; clamping", value)
        return min(max(value, 0.0), 100.0)
    return value


Confidence = Annotated[float, AfterValidator(_clamp_confidence)]


class ModelItemObservation(BaseModel):
    """One item as reported by the VLM — the raw, untrusted shape we parse first."""

    item_id: str
    detected_count: int = Field(ge=0)
    status: ModelStatus
    confidence: Confidence
    note: Optional[str] = None
    # Optional so replies without them still parse; used only for consistency checks.
    shelf_counts: Optional[list[Annotated[int, Field(ge=0)]]] = None  # top shelf first
    count_reliable: Optional[bool] = None


class ModelOutput(BaseModel):
    items: list[ModelItemObservation]
    notes: Optional[str] = None
    shelves_visible: Optional[int] = None


class ItemCheck(BaseModel):
    item_id: str
    expected_count: int = Field(ge=0)
    detected_count: int = Field(ge=0)
    status: ItemStatus
    confidence: Confidence  # 0.0–100.0
    note: Optional[str] = None
    shelf_counts: Optional[list[int]] = None  # model's per-shelf counts, top shelf first


class ComplianceResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    spec_id: str
    items: list[ItemCheck]
    overall_status: Literal["compliant", "non_compliant", "needs_review"]
    raw_model_notes: Optional[str] = None
    # Run metadata — so every result says where it came from and how long it took.
    is_mock: bool = False
    model_name: Optional[str] = None
    latency_s: Optional[float] = None
    # True only when a person has independently verified the counts. Nothing sets this today:
    # every count in this app is an AI-model estimate, so every derived amount is unverified.
    counts_verified: bool = False


# none:        item present as expected, $0.
# estimated:   missing/partial with a valid unit value; estimated_exposure_usd is the amount
#              (calculated from the reported counts; unverified unless counts_verified).
# unresolved:  misplaced, needs_review, or counts that contradict the status; excluded from the
#              estimate ($0), with an upper bound in potential_exposure_usd when the value allows.
# unavailable: missing/partial but the unit value is absent/invalid; no amount is calculated.
ExposureStatus = Literal["none", "estimated", "unresolved", "unavailable"]


class RevenueImpact(BaseModel):
    """Per-item financial exposure, computed by app/calculator.py (never by the model)."""

    item_id: str
    label: str
    status: ItemStatus
    expected_count: int
    detected_count: int
    units_missing: Optional[int]  # None when the shortfall cannot be trusted (unresolved)
    unit_value_usd: Optional[float]  # spec unit_margin_usd; None when absent/invalid
    exposure_status: ExposureStatus
    estimated_exposure_usd: Optional[float]  # None only when exposure_status == "unavailable"
    potential_exposure_usd: Optional[float] = None  # upper bound, unresolved items only
    assumptions: str  # human-readable formula or reason for this item


class ExposureSummary(BaseModel):
    spec_id: str
    calculation_available: bool
    unavailable_reason: Optional[str] = None
    items: list[RevenueImpact]
    # Copied from ComplianceResult. False means every amount below is an unverified estimate.
    counts_verified: bool = False
    # Sum of "estimated" item amounts. A lower bound when estimate_is_complete is False.
    estimated_exposure_usd: Optional[float]
    estimate_is_complete: bool
    # Sum of upper bounds for unresolved items. Never added to the estimate.
    unresolved_potential_usd: Optional[float]
    unresolved_potential_is_complete: bool
    unresolved_item_ids: list[str]
    unavailable_item_ids: list[str]
    assumptions: str


class ActionNote(BaseModel):
    """Plain-language action note (app/action_agent.py). `source` always says who worded it."""

    model_config = ConfigDict(protected_namespaces=())

    text: str
    # amd:         AMD model worded the actions; every fact and figure was rendered by code.
    # template:    deterministic template (no model wording).
    # unavailable: inspection result could not be validated; no findings to act on.
    source: Literal["amd", "template", "unavailable"]
    item_actions: dict[str, str] = Field(default_factory=dict)  # item_id -> instruction in this note
    ai_attempted: bool = False
    fallback_reason: Optional[str] = None  # why the template was used instead of the AMD note
    model_name: Optional[str] = None
    latency_s: Optional[float] = None


class InspectionError(Exception):
    STAGES = ("endpoint_unreachable", "endpoint_timeout", "endpoint_error", "parse_failed", "validation_failed", "invalid_image")

    def __init__(self, stage: str, detail: str):
        super().__init__(f"{stage}: {detail}")
        self.stage = stage
        self.detail = detail
