"""Pydantic schemas for the ESG endpoints (RP-48, RP-50, RP-51)."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class EsgOverrideDetails(BaseModel):
    value: float
    reason: str
    changed_by: str
    changed_at: datetime


class EsgMetricResponse(BaseModel):
    """Metric payload. has_metric is False (and the metric fields null) for a known account
    that has no computed month yet, so clients can tell "no data" apart from an unknown account (404)."""
    account_number: str
    portfolio_id: str
    has_metric: bool = True
    as_of_month: Optional[str]
    unit: str = "tCO2e per $M revenue"
    computed_value: Optional[float]
    effective_value: Optional[float]
    source: Literal["computed", "override", "none"]
    coverage_pct: Optional[float]
    computed_at: Optional[datetime]
    override: Optional[EsgOverrideDetails] = None


class EsgOverrideRequest(BaseModel):
    value: float = Field(..., ge=0, strict=True, allow_inf_nan=False, description="Override WACI in tCO2e per $M revenue")
    reason: str = Field(..., min_length=10, description="Why the computed value is being overridden")


class EsgClearOverrideRequest(BaseModel):
    reason: str = Field(..., min_length=10)


class EsgAuditEntry(BaseModel):
    id: int
    as_of_month: str
    action: Literal["OVERRIDE", "CLEAR"]
    old_value: Optional[float]
    new_value: Optional[float]
    reason: str
    changed_by: str
    changed_at: datetime


class EsgAuditResponse(BaseModel):
    account_number: str
    portfolio_id: str
    entries: List[EsgAuditEntry]
