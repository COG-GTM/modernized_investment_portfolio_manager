"""ESG emissions feed: loader, WACI computation wrapper, override and audit (RP-46 .. RP-51)."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import Portfolio
from models.esg import EsgLoadBatch, StgEsgEmissions, EsgLoadReject, PortfolioEsgMetrics, EsgOverrideAudit

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
WACI_SCRIPT = SQL_DIR / "esg_waci_v1.sql"

FEED_COLUMNS = ["as_of_month", "investment_id", "scope1_tco2e", "scope2_tco2e", "revenue_musd"]
AS_OF_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MIN_REASON_LENGTH = 10


class EsgFeedError(Exception):
    """Raised when the whole file cannot be processed (missing file, bad header)."""


class EsgValidationError(Exception):
    """Raised for invalid override requests; message is safe to show to the user."""


class PortfolioNotFound(Exception):
    pass


@dataclass
class LoadResult:
    batch_id: str
    file_name: str
    as_of_months: List[str]
    loaded_rows: int
    rejected_rows: int
    skipped: bool = False
    rejects: List[dict] = field(default_factory=list)


@dataclass
class ComputeResult:
    as_of_month: str
    portfolios: int
    computed_at: datetime


def _parse_decimal(raw: Optional[str], column: str, errors: List[str], *, required: bool, minimum: Optional[Decimal] = None, positive: bool = False) -> Optional[Decimal]:
    value = (raw or "").strip()
    if value == "":
        if required:
            errors.append(f"{column} missing")
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        errors.append(f"{column} is not numeric: {value!r}")
        return None
    if parsed.is_nan() or parsed.is_infinite():
        errors.append(f"{column} is not a finite number")
        return None
    if minimum is not None and parsed < minimum:
        errors.append(f"{column} must be >= {minimum}, got {parsed}")
        return None
    if positive and parsed <= 0:
        errors.append(f"{column} must be positive, got {parsed}")
        return None
    return parsed


def validate_feed_row(row: dict) -> tuple[Optional[dict], List[str]]:
    """Return (clean_row, errors). clean_row is None when there are errors."""
    errors: List[str] = []
    as_of_month = (row.get("as_of_month") or "").strip()
    if not AS_OF_MONTH_RE.match(as_of_month):
        errors.append(f"as_of_month must be YYYY-MM, got {as_of_month!r}")
    investment_id = (row.get("investment_id") or "").strip()
    if not investment_id:
        errors.append("investment_id missing")
    elif len(investment_id) > 10:
        errors.append("investment_id longer than 10 characters")
    scope1 = _parse_decimal(row.get("scope1_tco2e"), "scope1_tco2e", errors, required=True, minimum=Decimal("0"))
    scope2 = _parse_decimal(row.get("scope2_tco2e"), "scope2_tco2e", errors, required=True, minimum=Decimal("0"))
    revenue = _parse_decimal(row.get("revenue_musd"), "revenue_musd", errors, required=True, positive=True)
    if errors:
        return None, errors
    return {
        "as_of_month": as_of_month,
        "investment_id": investment_id,
        "scope1_tco2e": scope1,
        "scope2_tco2e": scope2,
        "revenue_musd": revenue,
    }, []


def load_esg_feed(db: Session, path: str | Path) -> LoadResult:
    """Copy a monthly emissions CSV into stg_esg_emissions; malformed rows go to esg_load_rejects.

    Re-running the same file (same SHA-256) is a no-op and returns the original batch.
    A corrected re-send of a month (different content) replaces the staging rows for
    (as_of_month, investment_id) instead of duplicating them.
    """
    path = Path(path)
    if not path.is_file():
        raise EsgFeedError(f"Feed file not found: {path}")
    content = path.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()

    existing = db.query(EsgLoadBatch).filter(EsgLoadBatch.file_sha256 == sha256).first()
    if existing:
        return LoadResult(
            batch_id=existing.batch_id,
            file_name=existing.file_name,
            as_of_months=[existing.as_of_month] if existing.as_of_month else [],
            loaded_rows=existing.loaded_rows,
            rejected_rows=existing.rejected_rows,
            skipped=True,
        )

    reader = csv.DictReader(content.decode("utf-8-sig").splitlines())
    header = [h.strip() for h in (reader.fieldnames or [])]
    missing = [c for c in FEED_COLUMNS if c not in header]
    if missing:
        raise EsgFeedError(f"Feed header is missing columns: {', '.join(missing)}")

    now = datetime.now()
    batch = EsgLoadBatch(
        batch_id=str(uuid.uuid4()),
        file_name=path.name,
        file_sha256=sha256,
        loaded_at=now,
        loaded_rows=0,
        rejected_rows=0,
    )
    db.add(batch)
    db.flush()

    seen: set[tuple[str, str]] = set()
    months: set[str] = set()
    rejects: List[dict] = []
    loaded = 0
    for row_no, raw in enumerate(reader, start=2):
        raw = {(k or "").strip(): v for k, v in raw.items()}
        clean, errors = validate_feed_row(raw)
        if clean:
            key = (clean["as_of_month"], clean["investment_id"])
            if key in seen:
                errors = [f"duplicate investment_id {clean['investment_id']} for {clean['as_of_month']} in file"]
                clean = None
            else:
                seen.add(key)
        if clean is None:
            reason = "; ".join(errors)
            db.add(EsgLoadReject(
                load_batch_id=batch.batch_id,
                source_row_no=row_no,
                raw_row=json.dumps(raw),
                reason=reason,
                rejected_at=now,
            ))
            rejects.append({"row_no": row_no, "reason": reason, "raw": raw})
            continue

        months.add(clean["as_of_month"])
        staged = db.query(StgEsgEmissions).filter(
            StgEsgEmissions.as_of_month == clean["as_of_month"],
            StgEsgEmissions.investment_id == clean["investment_id"],
        ).first()
        if staged is None:
            staged = StgEsgEmissions(as_of_month=clean["as_of_month"], investment_id=clean["investment_id"])
            db.add(staged)
        staged.load_batch_id = batch.batch_id
        staged.scope1_tco2e = clean["scope1_tco2e"]
        staged.scope2_tco2e = clean["scope2_tco2e"]
        staged.revenue_musd = clean["revenue_musd"]
        staged.source_row_no = row_no
        staged.loaded_at = now
        loaded += 1

    batch.loaded_rows = loaded
    batch.rejected_rows = len(rejects)
    batch.as_of_month = sorted(months)[0] if len(months) == 1 else (sorted(months)[-1] if months else None)
    db.commit()
    return LoadResult(
        batch_id=batch.batch_id,
        file_name=batch.file_name,
        as_of_months=sorted(months),
        loaded_rows=loaded,
        rejected_rows=len(rejects),
        rejects=rejects,
    )


def compute_waci(db: Session, as_of_month: str) -> ComputeResult:
    """Run the versioned SQL script that computes WACI for every portfolio for one month."""
    if not AS_OF_MONTH_RE.match(as_of_month or ""):
        raise EsgValidationError("as_of_month must be in YYYY-MM format")
    sql = WACI_SCRIPT.read_text()
    computed_at = datetime.now()
    db.execute(text(sql), {"as_of_month": as_of_month, "computed_at": computed_at})
    db.commit()
    count = db.query(PortfolioEsgMetrics).filter(PortfolioEsgMetrics.as_of_month == as_of_month).count()
    return ComputeResult(as_of_month=as_of_month, portfolios=count, computed_at=computed_at)


def load_and_compute(db: Session, path: str | Path) -> tuple[LoadResult, List[ComputeResult]]:
    load = load_esg_feed(db, path)
    return load, [compute_waci(db, m) for m in load.as_of_months]


def get_portfolio_by_account(db: Session, account_number: str) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.account_no == account_number).first()
    if portfolio is None:
        raise PortfolioNotFound(account_number)
    return portfolio


def get_current_metric(db: Session, portfolio_id: str) -> Optional[PortfolioEsgMetrics]:
    """The metric for the most recent as-of month that has been computed for the portfolio."""
    return (
        db.query(PortfolioEsgMetrics)
        .filter(PortfolioEsgMetrics.portfolio_id == portfolio_id)
        .order_by(PortfolioEsgMetrics.as_of_month.desc())
        .first()
    )


def _validate_reason(reason: Optional[str]) -> str:
    cleaned = (reason or "").strip()
    if len(cleaned) < MIN_REASON_LENGTH:
        raise EsgValidationError(f"Reason is mandatory and must be at least {MIN_REASON_LENGTH} characters")
    return cleaned


def set_override(db: Session, portfolio_id: str, value: Decimal, reason: str, changed_by: str) -> PortfolioEsgMetrics:
    """Override the WACI for the current as-of month and append an audit row."""
    reason = _validate_reason(reason)
    if value is None or Decimal(value) < 0:
        raise EsgValidationError("Override value must be non-negative")
    metric = get_current_metric(db, portfolio_id)
    if metric is None:
        raise EsgValidationError("No carbon intensity metric exists for this portfolio yet; load the ESG feed first")
    now = datetime.now()
    old_value = metric.effective_value
    metric.override_value = Decimal(value)
    metric.override_reason = reason
    metric.override_by = changed_by
    metric.override_at = now
    db.add(EsgOverrideAudit(
        portfolio_id=portfolio_id,
        as_of_month=metric.as_of_month,
        action="OVERRIDE",
        old_value=old_value,
        new_value=Decimal(value),
        reason=reason,
        changed_by=changed_by,
        changed_at=now,
    ))
    db.commit()
    db.refresh(metric)
    return metric


def clear_override(db: Session, portfolio_id: str, reason: str, changed_by: str) -> PortfolioEsgMetrics:
    """Remove the override for the current as-of month; the computed value becomes effective again."""
    reason = _validate_reason(reason)
    metric = get_current_metric(db, portfolio_id)
    if metric is None:
        raise EsgValidationError("No carbon intensity metric exists for this portfolio")
    if metric.override_value is None:
        raise EsgValidationError("There is no override to clear for the current as-of month")
    now = datetime.now()
    old_value = metric.override_value
    metric.override_value = None
    metric.override_reason = None
    metric.override_by = None
    metric.override_at = None
    db.add(EsgOverrideAudit(
        portfolio_id=portfolio_id,
        as_of_month=metric.as_of_month,
        action="CLEAR",
        old_value=old_value,
        new_value=metric.waci_computed,
        reason=reason,
        changed_by=changed_by,
        changed_at=now,
    ))
    db.commit()
    db.refresh(metric)
    return metric


def list_audit(db: Session, portfolio_id: str) -> List[EsgOverrideAudit]:
    return (
        db.query(EsgOverrideAudit)
        .filter(EsgOverrideAudit.portfolio_id == portfolio_id)
        .order_by(EsgOverrideAudit.changed_at.desc(), EsgOverrideAudit.id.desc())
        .all()
    )
