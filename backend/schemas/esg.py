from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

REASON_MIN_LENGTH = 10
REASON_MAX_LENGTH = 1000
CHANGED_BY_MAX_LENGTH = 8
DEFAULT_CHANGED_BY = "SYSTEM"


def _validate_reason(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) < REASON_MIN_LENGTH:
        raise ValueError(f"Reason must be at least {REASON_MIN_LENGTH} characters")
    if len(trimmed) > REASON_MAX_LENGTH:
        raise ValueError(f"Reason must be at most {REASON_MAX_LENGTH} characters")
    return trimmed


def _validate_changed_by(value: Optional[str]) -> str:
    if value is None or not value.strip():
        return DEFAULT_CHANGED_BY
    trimmed = value.strip()
    if len(trimmed) > CHANGED_BY_MAX_LENGTH:
        raise ValueError(f"changedBy must be at most {CHANGED_BY_MAX_LENGTH} characters")
    return trimmed


class EsgOverrideRequest(BaseModel):
    # strict rejects booleans and numeric strings; allow_inf_nan rejects NaN/Infinity
    value: float = Field(..., ge=0, strict=True, allow_inf_nan=False)
    reason: str = Field(..., strict=True)
    changedBy: Optional[str] = Field(default=None, validate_default=True)

    _reason = field_validator("reason")(_validate_reason)
    _changed_by = field_validator("changedBy")(_validate_changed_by)


class EsgClearOverrideRequest(BaseModel):
    reason: str = Field(..., strict=True)
    changedBy: Optional[str] = Field(default=None, validate_default=True)

    _reason = field_validator("reason")(_validate_reason)
    _changed_by = field_validator("changedBy")(_validate_changed_by)


class EsgOverrideDetails(BaseModel):
    value: float
    reason: str
    overriddenBy: str
    overriddenAt: datetime


class EsgMetricResponse(BaseModel):
    accountNumber: str
    portfolioId: str
    hasMetric: bool
    asOfMonth: Optional[str]
    metric: Literal["WACI"] = "WACI"
    unit: str = "tCO2e per $M revenue"
    computedValue: Optional[float]
    effectiveValue: Optional[float]
    source: Literal["computed", "override", "none"]
    coveragePct: Optional[float]
    computedAt: Optional[datetime]
    override: Optional[EsgOverrideDetails]
