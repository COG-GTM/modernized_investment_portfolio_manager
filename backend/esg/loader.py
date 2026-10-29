"""Load a monthly ESG emissions CSV from the inbound bucket into staging.

Contract (docs/specs/esg-carbon-intensity-feed.md, section 5.1):
- file lives at esg/<YYYY-MM>/esg_emissions_<YYYY-MM>.csv under the inbound root;
- every file processed gets an esg_load_batches row (status C or F);
- accepted rows replace the month's snapshot in stg_esg_emissions, bad rows go to esg_load_rejects;
- re-running the file the month currently reflects is a no-op.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import List, Optional, Sequence, Union

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.esg import EsgLoadBatch, EsgLoadReject, StgEsgEmission

EXPECTED_HEADER = ["as_of_month", "investment_id", "scope1_tco2e", "scope2_tco2e", "revenue_musd"]
DEFAULT_INBOUND_ROOT = "inbound"
INBOUND_ROOT_ENV = "ESG_INBOUND_DIR"

STATUS_COMPLETE = "C"
STATUS_FAILED = "F"

BAD_HEADER = "BAD_HEADER"
EMPTY_FILE = "EMPTY_FILE"
ALL_ROWS_REJECTED = "ALL_ROWS_REJECTED"

INVALID_AS_OF_MONTH = "INVALID_AS_OF_MONTH"
MISSING_INVESTMENT_ID = "MISSING_INVESTMENT_ID"
INVALID_SCOPE1 = "INVALID_SCOPE1"
INVALID_SCOPE2 = "INVALID_SCOPE2"
INVALID_REVENUE = "INVALID_REVENUE"
DUPLICATE_INVESTMENT_ID = "DUPLICATE_INVESTMENT_ID"
WRONG_COLUMN_COUNT = "WRONG_COLUMN_COUNT"

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$", re.ASCII)
FILE_NAME_RE = re.compile(r"^esg_emissions_(\d{4}-(?:0[1-9]|1[0-2]))\.csv$", re.ASCII)
PLAIN_DECIMAL_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$", re.ASCII)
INVESTMENT_ID_MAX_LEN = 10
REASON_MAX_LEN = 200

# Numeric(18, 4): 14 integer digits, 4 decimals.
SCALE = Decimal("0.0001")
MAX_ABS = Decimal(10) ** 14


class EsgFeedError(Exception):
    """The file cannot be processed at all (not found, misnamed, not UTF-8). No batch is written."""


@dataclass
class LoadResult:
    batch_id: Optional[int]
    file_path: str
    as_of_month: str
    status: str
    failure_reason: Optional[str] = None
    row_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    skipped: bool = False

    @property
    def exit_code(self) -> int:
        return 0 if self.status == STATUS_COMPLETE else 1

    def summary(self) -> str:
        if self.skipped:
            state = "complete" if self.status == STATUS_COMPLETE else f"failed: {self.failure_reason}"
            return f"{self.file_path}: already loaded as batch {self.batch_id} ({state}); nothing written"
        text = (
            f"{self.file_path}: batch {self.batch_id} status {self.status}, "
            f"{self.row_count} rows, {self.accepted_count} accepted, {self.rejected_count} rejected"
        )
        if self.failure_reason:
            text += f" ({self.failure_reason})"
        return text


@dataclass
class _Row:
    source_row_no: int
    raw_line: str
    values: dict = field(default_factory=dict)
    reason: Optional[str] = None


def inbound_root(explicit: Union[str, Path, None] = None) -> Path:
    return Path(explicit or os.environ.get(INBOUND_ROOT_ENV) or DEFAULT_INBOUND_ROOT)


def month_from_path(path: Path) -> str:
    match = FILE_NAME_RE.match(path.name)
    if not match:
        raise EsgFeedError(f"{path}: file name must be esg_emissions_<YYYY-MM>.csv")
    month = match.group(1)
    if path.parent.name != month:
        raise EsgFeedError(f"{path}: file for {month} must sit in an esg/{month}/ folder, not {path.parent.name}/")
    return month


def _relative_file_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _decode(path: Path, data: bytes) -> str:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise EsgFeedError(f"{path}: file is not valid UTF-8 ({exc.reason} at byte {exc.start})") from exc
    if "\x00" in text:
        raise EsgFeedError(f"{path}: file contains NUL bytes")
    return text


def _parse_line(line: str) -> List[str]:
    return [value.strip() for value in next(csv.reader([line]))]


def _reject(code: str, detail: str) -> str:
    return f"{code}: {detail}"[:REASON_MAX_LEN]


def _parse_amount(raw: str, column: str) -> Union[Decimal, str]:
    """Return the value rounded to Numeric(18,4), or an error detail string."""
    if not PLAIN_DECIMAL_RE.match(raw):
        return f"{column} {raw!r} is not numeric"
    with localcontext() as ctx:
        ctx.prec = 40
        value = Decimal(raw)
        if value != 0 and value.adjusted() >= 14:
            return f"{column} {raw} exceeds the Numeric(18,4) range"
        rounded = value.quantize(SCALE)
        if abs(rounded) >= MAX_ABS:
            return f"{column} {raw} exceeds the Numeric(18,4) range after rounding to 4 decimals"
    if rounded == 0:
        rounded = Decimal("0.0000")
    if value != 0 and rounded == 0:
        return f"{column} {raw} is below the Numeric(18,4) precision"
    return rounded


def _validate(row: _Row, fields: Sequence[str], file_month: str, seen_ids: set) -> None:
    if len(fields) != len(EXPECTED_HEADER):
        row.reason = _reject(WRONG_COLUMN_COUNT, f"expected {len(EXPECTED_HEADER)} columns, got {len(fields)}")
        return
    month, investment_id, scope1, scope2, revenue = fields

    if not MONTH_RE.match(month):
        row.reason = _reject(INVALID_AS_OF_MONTH, f"{month!r} is not YYYY-MM")
        return
    if month != file_month:
        row.reason = _reject(INVALID_AS_OF_MONTH, f"{month} does not match the file month {file_month}")
        return

    if not investment_id:
        row.reason = _reject(MISSING_INVESTMENT_ID, "investment_id is empty")
        return
    if len(investment_id) > INVESTMENT_ID_MAX_LEN:
        row.reason = _reject(MISSING_INVESTMENT_ID, f"investment_id {investment_id!r} is longer than {INVESTMENT_ID_MAX_LEN} characters")
        return
    if not investment_id.isprintable() or any(ch.isspace() for ch in investment_id):
        row.reason = _reject(MISSING_INVESTMENT_ID, f"investment_id {investment_id!r} contains whitespace or non-printable characters")
        return

    amounts = {}
    for code, column, raw in ((INVALID_SCOPE1, "scope1_tco2e", scope1), (INVALID_SCOPE2, "scope2_tco2e", scope2)):
        parsed = _parse_amount(raw, column) if raw else f"{column} is empty"
        if isinstance(parsed, str):
            row.reason = _reject(code, parsed)
            return
        if parsed < 0:
            row.reason = _reject(code, f"{column} must be non-negative, got {raw}")
            return
        amounts[column] = parsed

    revenue_value = None
    if revenue:
        parsed = _parse_amount(revenue, "revenue_musd")
        if isinstance(parsed, str):
            row.reason = _reject(INVALID_REVENUE, parsed)
            return
        if parsed <= 0:
            row.reason = _reject(INVALID_REVENUE, f"revenue_musd must be greater than 0 when present, got {revenue}")
            return
        revenue_value = parsed

    if investment_id in seen_ids:
        row.reason = _reject(DUPLICATE_INVESTMENT_ID, f"{investment_id} already appears earlier in the file")
        return
    seen_ids.add(investment_id)

    row.values = {
        "as_of_month": month,
        "investment_id": investment_id,
        "scope1_tco2e": amounts["scope1_tco2e"],
        "scope2_tco2e": amounts["scope2_tco2e"],
        "revenue_musd": revenue_value,
    }


def _previous_batch(session: Session, month: str, sha256: str) -> Optional[EsgLoadBatch]:
    """The batch that makes this run a no-op, if any.

    The month's latest complete batch with the same bytes means staging already reflects the file.
    The month's latest batch overall with the same bytes and status F means the same broken file was
    already recorded; writing it again would only duplicate rejects. An older, superseded batch with
    the same bytes does not count: replaying it restores that snapshot as a new batch.
    """
    latest = session.scalars(
        select(EsgLoadBatch).where(EsgLoadBatch.as_of_month == month).order_by(EsgLoadBatch.batch_id.desc()).limit(1)
    ).first()
    if latest is not None and latest.file_sha256 == sha256:
        return latest
    latest_complete = session.scalars(
        select(EsgLoadBatch)
        .where(EsgLoadBatch.as_of_month == month, EsgLoadBatch.status == STATUS_COMPLETE)
        .order_by(EsgLoadBatch.batch_id.desc())
        .limit(1)
    ).first()
    if latest_complete is not None and latest_complete.file_sha256 == sha256:
        return latest_complete
    return None


def _upsert_staging(session: Session, rows: List[dict]) -> None:
    dialect = session.get_bind().dialect.name
    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    elif dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        for row in rows:
            session.merge(StgEsgEmission(**row))
        return
    stmt = insert(StgEsgEmission).values(rows)
    updatable = ("scope1_tco2e", "scope2_tco2e", "revenue_musd", "batch_id", "source_row_no", "loaded_at")
    stmt = stmt.on_conflict_do_update(
        index_elements=["as_of_month", "investment_id"],
        set_={name: stmt.excluded[name] for name in updatable},
    )
    session.execute(stmt)


def load_feed(session: Session, path: Union[str, Path], root: Union[str, Path, None] = None) -> LoadResult:
    """Load one feed file. Commits on success; rolls back and re-raises on any unexpected error."""
    path = Path(path)
    root_path = inbound_root(root)
    if not path.is_file():
        raise FileNotFoundError(f"ESG feed file not found: {path}")
    file_month = month_from_path(path)
    data = path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    text = _decode(path, data)
    rel_path = _relative_file_path(path, root_path)

    previous = _previous_batch(session, file_month, sha256)
    if previous is not None:
        return LoadResult(
            batch_id=previous.batch_id,
            file_path=rel_path,
            as_of_month=file_month,
            status=previous.status,
            failure_reason=previous.failure_reason,
            row_count=previous.row_count,
            accepted_count=previous.accepted_count,
            rejected_count=previous.rejected_count,
            skipped=True,
        )

    lines = text.splitlines()
    header = _parse_line(lines[0]) if lines else []
    rows: List[_Row] = []
    failure_reason = None
    if header != EXPECTED_HEADER:
        failure_reason = BAD_HEADER
    else:
        seen_ids: set = set()
        for line_no, line in enumerate(lines[1:], start=2):
            if not line.strip():
                continue
            row = _Row(source_row_no=line_no - 1, raw_line=line)
            _validate(row, _parse_line(line), file_month, seen_ids)
            rows.append(row)

    accepted = [r for r in rows if r.reason is None]
    rejected = [r for r in rows if r.reason is not None]
    if failure_reason is None and not rows:
        failure_reason = EMPTY_FILE
    elif failure_reason is None and not accepted:
        failure_reason = ALL_ROWS_REJECTED
    status = STATUS_FAILED if failure_reason else STATUS_COMPLETE

    now = datetime.now()
    try:
        batch = EsgLoadBatch(
            file_path=rel_path,
            file_sha256=sha256,
            as_of_month=file_month,
            loaded_at=now,
            row_count=len(rows),
            accepted_count=len(accepted) if status == STATUS_COMPLETE else 0,
            rejected_count=len(rejected),
            status=status,
            failure_reason=failure_reason,
        )
        session.add(batch)
        session.flush()

        session.add_all(
            EsgLoadReject(
                batch_id=batch.batch_id,
                source_row_no=r.source_row_no,
                raw_line=r.raw_line,
                reason=r.reason,
                rejected_at=now,
            )
            for r in rejected
        )

        if status == STATUS_COMPLETE:
            _upsert_staging(
                session,
                [dict(r.values, batch_id=batch.batch_id, source_row_no=r.source_row_no, loaded_at=now) for r in accepted],
            )
            session.execute(
                delete(StgEsgEmission).where(
                    StgEsgEmission.as_of_month == file_month,
                    StgEsgEmission.batch_id != batch.batch_id,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return LoadResult(
        batch_id=batch.batch_id,
        file_path=rel_path,
        as_of_month=file_month,
        status=status,
        failure_reason=failure_reason,
        row_count=batch.row_count,
        accepted_count=batch.accepted_count,
        rejected_count=batch.rejected_count,
    )


def discover_feeds(root: Union[str, Path, None] = None) -> List[Path]:
    return sorted(inbound_root(root).glob("esg/*/esg_emissions_*.csv"))


def load_all(session: Session, root: Union[str, Path, None] = None) -> List[LoadResult]:
    return [load_feed(session, path, root) for path in discover_feeds(root)]
