from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.database import Portfolio
from models.esg import PortfolioEsgMetric, PortfolioEsgOverride
from schemas.esg import EsgMetricResponse, EsgOverrideDetails


class AccountNotFoundError(Exception):
    pass


class EsgStateError(Exception):
    """The request is valid but the portfolio's ESG state does not allow it."""


NO_METRIC_MESSAGE = "No ESG metric exists for this account yet"
NO_OVERRIDE_MESSAGE = "No override is active for the current as-of month"


def _float(value: Optional[Decimal], ndigits: Optional[int] = None) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), ndigits) if ndigits is not None else float(value)


def get_portfolio(db: Session, account_number: str) -> Portfolio:
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.account_no == account_number)
        .order_by(Portfolio.port_id)
        .first()
    )
    if portfolio is None:
        raise AccountNotFoundError("Account not found")
    return portfolio


def _current_metric(db: Session, port_id: str) -> Optional[PortfolioEsgMetric]:
    """The current as-of month is the latest month computed for the portfolio."""
    return (
        db.query(PortfolioEsgMetric)
        .filter(PortfolioEsgMetric.port_id == port_id)
        .order_by(PortfolioEsgMetric.as_of_month.desc())
        .first()
    )


def _override_for(db: Session, port_id: str, as_of_month: str) -> Optional[PortfolioEsgOverride]:
    return db.get(PortfolioEsgOverride, (port_id, as_of_month))


def _current_state(db: Session, port_id: str) -> Tuple[Optional[PortfolioEsgMetric], Optional[PortfolioEsgOverride]]:
    metric = _current_metric(db, port_id)
    override = _override_for(db, port_id, metric.as_of_month) if metric else None
    return metric, override


def build_response(
    portfolio: Portfolio,
    metric: Optional[PortfolioEsgMetric],
    override: Optional[PortfolioEsgOverride],
) -> EsgMetricResponse:
    has_metric = metric is not None and metric.positions_total > 0
    override_details = (
        EsgOverrideDetails(
            value=float(override.override_value),
            reason=override.reason,
            overriddenBy=override.overridden_by,
            overriddenAt=override.overridden_at,
        )
        if override
        else None
    )
    computed_value = _float(metric.computed_value, 6) if has_metric else None
    if not has_metric:
        effective_value, source = None, "none"
    elif override:
        effective_value, source = override_details.value, "override"
    else:
        effective_value, source = computed_value, "computed"

    return EsgMetricResponse(
        accountNumber=portfolio.account_no,
        portfolioId=portfolio.port_id,
        hasMetric=has_metric,
        asOfMonth=metric.as_of_month if metric else None,
        computedValue=computed_value,
        effectiveValue=effective_value,
        source=source,
        coveragePct=_float(metric.coverage_pct, 2) if has_metric else None,
        computedAt=metric.computed_at if metric else None,
        override=override_details,
    )


def get_esg_metric(db: Session, account_number: str) -> EsgMetricResponse:
    portfolio = get_portfolio(db, account_number)
    metric, override = _current_state(db, portfolio.port_id)
    return build_response(portfolio, metric, override)


def set_override(db: Session, account_number: str, value: float, reason: str, changed_by: str) -> EsgMetricResponse:
    """Set or replace the override for the portfolio's current as-of month only."""
    portfolio = get_portfolio(db, account_number)
    metric, override = _current_state(db, portfolio.port_id)
    if metric is None or metric.positions_total == 0:
        raise EsgStateError(NO_METRIC_MESSAGE)

    def apply(row: PortfolioEsgOverride) -> None:
        row.override_value = Decimal(str(value))
        row.reason = reason
        row.overridden_by = changed_by
        row.overridden_at = datetime.now().replace(microsecond=0)

    if override is None:
        override = PortfolioEsgOverride(port_id=portfolio.port_id, as_of_month=metric.as_of_month)
        db.add(override)
    apply(override)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request inserted the first override for this month; replace it instead.
        db.rollback()
        override = _override_for(db, portfolio.port_id, metric.as_of_month)
        if override is None:
            raise
        apply(override)
        db.commit()
    db.refresh(override)
    return build_response(portfolio, metric, override)


def clear_override(db: Session, account_number: str, reason: str, changed_by: str) -> EsgMetricResponse:
    """Remove the override for the current as-of month; the reason is kept for the RP-51 audit trail."""
    portfolio = get_portfolio(db, account_number)
    metric, override = _current_state(db, portfolio.port_id)
    if override is None:
        raise EsgStateError(NO_OVERRIDE_MESSAGE)
    db.delete(override)
    db.commit()
    return build_response(portfolio, metric, None)
