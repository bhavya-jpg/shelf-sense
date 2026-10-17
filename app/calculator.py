"""Deterministic financial exposure calculator (BLUEPRINT §8, Milestone 2).

Pure functions: no I/O, no model calls. Money is computed with Decimal and rounded
half-up to cents, so identical inputs always give identical outputs.
"""

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from app.models import ComplianceResult, ExposureSummary, ItemCheck, RevenueImpact, Spec, SpecItem

CENT = Decimal("0.01")

COUNT_BASIS = {
    False: (
        "Counts are estimated by the AI model from the photo and have not been independently verified, "
        "so every amount is an unverified estimate and may be wrong."
    ),
    True: "Counts were independently verified by a person.",
}

ASSUMPTIONS = (
    "Unit value = unit_margin_usd from the spec, an author-entered demo assumption (not POS data). "
    "Missing: expected units x unit value. "
    "Partial: (expected - detected) units x unit value. "
    "Present: $0. "
    "Misplaced, needs_review, or counts that contradict the reported status: excluded from the estimate ($0), "
    "kept visible as unresolved, with an upper bound of expected units x unit value shown separately. "
    "If a unit value is absent or invalid, the amount is reported as unavailable, never as $0. "
    "Figures are one-off gross margin on the missing units, not revenue and not a daily rate."
)


def exposure_label(counts_verified: bool) -> str:
    """User-facing name of the headline figure. Only verified counts may drop "Estimated"/"Unverified"."""
    return "Margin at Risk (Verified Counts)" if counts_verified else "Estimated Margin at Risk (Unverified)"


def _money(units: int, unit_value: float) -> float:
    return float((Decimal(units) * Decimal(str(unit_value))).quantize(CENT, rounding=ROUND_HALF_UP))


def _usd(amount: float) -> str:
    return f"${amount:,.2f}"


def validate_unit_value(value: Optional[float]) -> tuple[Optional[float], Optional[str]]:
    """Return (usable value, None) or (None, reason it is unusable). $0 is a valid value."""
    if value is None:
        return None, "the spec has no unit_margin_usd for this item"
    if not math.isfinite(value):
        return None, f"unit_margin_usd is not a finite number ({value})"
    if value < 0:
        return None, f"unit_margin_usd is negative ({value})"
    return float(value), None


def count_inconsistency(check: ItemCheck) -> Optional[str]:
    """Describe a contradiction between the reported status and the counts, if any."""
    e, d = check.expected_count, check.detected_count
    if check.status == "present" and d < e:
        return f"status 'present' but only {d} of {e} detected"
    if check.status == "missing" and d > 0:
        return f"status 'missing' but {d} detected"
    if check.status == "partial" and d >= e:
        return f"status 'partial' but {d} of {e} detected"
    return None


def item_impact(check: ItemCheck, spec_item: SpecItem) -> RevenueImpact:
    unit_value, value_problem = validate_unit_value(spec_item.unit_margin_usd)
    expected, detected = check.expected_count, check.detected_count
    base = dict(
        item_id=check.item_id,
        label=spec_item.label,
        status=check.status,
        expected_count=expected,
        detected_count=detected,
        unit_value_usd=unit_value,
    )
    inconsistency = count_inconsistency(check)

    if check.status == "present" and not inconsistency:
        return RevenueImpact(
            **base, units_missing=0, exposure_status="none", estimated_exposure_usd=0.0,
            assumptions="Present as expected: $0.",
        )

    if check.status in ("missing", "partial") and not inconsistency:
        if check.status == "missing":
            units, formula = expected, f"Missing: {expected} expected units"
        else:
            units, formula = expected - detected, f"Partial: ({expected} expected - {detected} detected) units"
        if unit_value is None:
            return RevenueImpact(
                **base, units_missing=units, exposure_status="unavailable", estimated_exposure_usd=None,
                assumptions=f"{units} units short, but exposure cannot be calculated: {value_problem}.",
            )
        amount = _money(units, unit_value)
        return RevenueImpact(
            **base, units_missing=units, exposure_status="estimated", estimated_exposure_usd=amount,
            assumptions=f"{formula} x {_usd(unit_value)} unit value = {_usd(amount)}.",
        )

    # Unresolved: misplaced, needs_review, or counts that contradict the status.
    reason = inconsistency or {
        "misplaced": "item reported present but in the wrong position",
        "needs_review": "no usable observation from the model",
    }[check.status]
    if unit_value is None:
        potential = None
        bound = f"Upper bound cannot be calculated: {value_problem}."
    else:
        potential = _money(expected, unit_value)
        bound = (
            f"Upper bound if all {expected} expected units were unavailable to shoppers: "
            f"{expected} x {_usd(unit_value)} = {_usd(potential)} (upper bound, not an estimate of actual loss)."
        )
    return RevenueImpact(
        **base, units_missing=None, exposure_status="unresolved", estimated_exposure_usd=0.0,
        potential_exposure_usd=potential,
        assumptions=f"Unresolved ({reason}): excluded from the estimate ($0). {bound}",
    )


def calculate_revenue_impact(result: ComplianceResult, spec: Spec) -> list[RevenueImpact]:
    """Per-item exposure, in spec order. Raises ValueError if result and spec don't line up."""
    if result.spec_id != spec.spec_id:
        raise ValueError(f"result is for spec {result.spec_id!r}, not {spec.spec_id!r}")
    if not result.items:
        raise ValueError("no validated item observations; the calculator must not run on unvalidated output")

    checks = {c.item_id: c for c in result.items}
    if len(checks) != len(result.items):
        raise ValueError("duplicate item_id in result")
    spec_items = {i.item_id: i for i in spec.items}
    if set(checks) != set(spec_items):
        raise ValueError(
            f"result items {sorted(checks)} do not match spec items {sorted(spec_items)}"
        )
    for item_id, check in checks.items():
        if check.expected_count != spec_items[item_id].expected_count:
            raise ValueError(f"expected_count for {item_id!r} differs from the spec")

    return [item_impact(checks[i.item_id], i) for i in spec.items]


def summarize_exposure(result: ComplianceResult, spec: Spec) -> ExposureSummary:
    if not result.items:
        # §8: no number is better than a wrong number — nothing is computed from unvalidated output.
        return ExposureSummary(
            spec_id=spec.spec_id,
            calculation_available=False,
            unavailable_reason="The model output could not be validated, so no financial figures were calculated.",
            items=[],
            estimated_exposure_usd=None,
            estimate_is_complete=False,
            unresolved_potential_usd=None,
            unresolved_potential_is_complete=False,
            unresolved_item_ids=[],
            unavailable_item_ids=[],
            assumptions=f"{COUNT_BASIS[result.counts_verified]} {ASSUMPTIONS}",
            counts_verified=result.counts_verified,
        )

    impacts = calculate_revenue_impact(result, spec)
    estimated = sum(
        (Decimal(str(i.estimated_exposure_usd)) for i in impacts if i.estimated_exposure_usd is not None),
        Decimal(0),
    )
    unresolved = [i for i in impacts if i.exposure_status == "unresolved"]
    potential = sum(
        (Decimal(str(i.potential_exposure_usd)) for i in unresolved if i.potential_exposure_usd is not None),
        Decimal(0),
    )
    unavailable_ids = [i.item_id for i in impacts if i.exposure_status == "unavailable"]

    return ExposureSummary(
        spec_id=spec.spec_id,
        calculation_available=True,
        items=impacts,
        estimated_exposure_usd=float(estimated.quantize(CENT)),
        estimate_is_complete=not unavailable_ids,
        unresolved_potential_usd=float(potential.quantize(CENT)),
        unresolved_potential_is_complete=all(i.potential_exposure_usd is not None for i in unresolved),
        unresolved_item_ids=[i.item_id for i in unresolved],
        unavailable_item_ids=unavailable_ids,
        assumptions=f"{COUNT_BASIS[result.counts_verified]} {ASSUMPTIONS}",
        counts_verified=result.counts_verified,
    )
