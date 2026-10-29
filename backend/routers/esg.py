"""Carbon intensity (WACI) endpoints for the portfolio API (RP-48, RP-50, RP-51)."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.esg import PortfolioEsgMetrics
from models.esg_schemas import (
    EsgAuditEntry, EsgAuditResponse, EsgClearOverrideRequest, EsgMetricResponse,
    EsgOverrideDetails, EsgOverrideRequest,
)
from services import esg_service
from services.esg_service import EsgValidationError, PortfolioNotFound

router = APIRouter(prefix="/api", tags=["esg"])

DEFAULT_USER = "portfolio_manager"


def _to_float(value):
    return float(value) if value is not None else None


def _metric_response(account_number: str, metric: PortfolioEsgMetrics) -> EsgMetricResponse:
    override = None
    if metric.override_value is not None:
        override = EsgOverrideDetails(
            value=float(metric.override_value),
            reason=metric.override_reason or "",
            changed_by=metric.override_by or DEFAULT_USER,
            changed_at=metric.override_at,
        )
    return EsgMetricResponse(
        account_number=account_number,
        portfolio_id=metric.portfolio_id,
        as_of_month=metric.as_of_month,
        computed_value=_to_float(metric.waci_computed),
        effective_value=_to_float(metric.effective_value),
        source=metric.source,
        coverage_pct=float(metric.coverage_pct or 0),
        computed_at=metric.computed_at,
        override=override,
    )


def _portfolio_or_404(db: Session, account_number: str):
    try:
        return esg_service.get_portfolio_by_account(db, account_number)
    except PortfolioNotFound:
        raise HTTPException(status_code=404, detail=f"Account {account_number} not found")


@router.get("/portfolio/{account_number}/esg", response_model=EsgMetricResponse)
def get_esg_metric(account_number: str, db: Session = Depends(get_db)):
    """Carbon intensity (WACI) for the account's portfolio, current as-of month."""
    portfolio = _portfolio_or_404(db, account_number)
    metric = esg_service.get_current_metric(db, portfolio.port_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="No carbon intensity metric available for this account")
    return _metric_response(account_number, metric)


@router.put("/portfolio/{account_number}/esg/override", response_model=EsgMetricResponse)
def put_esg_override(
    account_number: str,
    body: EsgOverrideRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(default=None, alias="X-User"),
):
    """Override the WACI for the current as-of month. Reason is mandatory (min 10 chars)."""
    portfolio = _portfolio_or_404(db, account_number)
    try:
        metric = esg_service.set_override(db, portfolio.port_id, body.value, body.reason, x_user or DEFAULT_USER)
    except EsgValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _metric_response(account_number, metric)


@router.delete("/portfolio/{account_number}/esg/override", response_model=EsgMetricResponse)
def delete_esg_override(
    account_number: str,
    body: EsgClearOverrideRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(default=None, alias="X-User"),
):
    """Clear the override for the current as-of month (audited)."""
    portfolio = _portfolio_or_404(db, account_number)
    try:
        metric = esg_service.clear_override(db, portfolio.port_id, body.reason, x_user or DEFAULT_USER)
    except EsgValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _metric_response(account_number, metric)


@router.get("/portfolio/{account_number}/esg/audit", response_model=EsgAuditResponse)
def get_esg_audit(account_number: str, db: Session = Depends(get_db)):
    """Override history, newest first."""
    portfolio = _portfolio_or_404(db, account_number)
    entries = [
        EsgAuditEntry(
            id=row.id,
            as_of_month=row.as_of_month,
            action=row.action,
            old_value=_to_float(row.old_value),
            new_value=_to_float(row.new_value),
            reason=row.reason,
            changed_by=row.changed_by,
            changed_at=row.changed_at,
        )
        for row in esg_service.list_audit(db, portfolio.port_id)
    ]
    return EsgAuditResponse(account_number=account_number, portfolio_id=portfolio.port_id, entries=entries)
