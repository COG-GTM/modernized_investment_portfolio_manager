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
import io
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy import text as sql_text
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
    batch_id: int | None
    file_path: str
    as_of_month: str
    status: str
    failure_reason: str | None = None
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
    reason: str | None = None


def inbound_root(explicit: str | Path | None = None) -> Path:
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


PHYSICAL_LINE_RE = re.compile(r"\r\n|\r|\n")
UPSERT_CHUNK_ROWS = 500
MONTH_LOCK_NAMESPACE = 0x45534700_000000


def _records(content: str) -> list[tuple[int, str, list[str]]]:
    """(first physical line number, raw source text, stripped fields) per CSV record.

    Parses the whole file so quoted cells that span lines stay one record.
    """
    physical = PHYSICAL_LINE_RE.split(content)
    reader = csv.reader(io.StringIO(content, newline=""))
    records = []
    while True:
        start = reader.line_num + 1
        try:
            fields = next(reader)
        except StopIteration:
            return records
        raw = "\n".join(physical[start - 1 : reader.line_num])
        records.append((start, raw, [value.strip() for value in fields]))


def _lock_month(session: Session, month: str) -> None:
    """Serialize loads of one month until commit/rollback so concurrent snapshots cannot interleave."""
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        key = MONTH_LOCK_NAMESPACE + int(month.replace("-", ""))
        session.execute(sql_text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    elif dialect == "sqlite":
        # A no-op write takes SQLite's RESERVED lock, so a second loader waits here before it reads.
        session.execute(sql_text("UPDATE esg_load_batches SET batch_id = batch_id WHERE 0"))


def _reject(code: str, detail: str) -> str:
    return f"{code}: {detail}"[:REASON_MAX_LEN]


def _parse_amount(raw: str, column: str) -> Decimal | str:
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


def _previous_batch(session: Session, month: str, sha256: str) -> EsgLoadBatch | None:
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


def _upsert_staging(session: Session, rows: list[dict]) -> None:
    dialect = session.get_bind().dialect.name
    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    elif dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        for row in rows:
            session.merge(StgEsgEmission(**row))
        return
    updatable = ("scope1_tco2e", "scope2_tco2e", "revenue_musd", "batch_id", "source_row_no", "loaded_at")
    for start in range(0, len(rows), UPSERT_CHUNK_ROWS):
        stmt = insert(StgEsgEmission).values(rows[start : start + UPSERT_CHUNK_ROWS])
        stmt = stmt.on_conflict_do_update(
            index_elements=["as_of_month", "investment_id"],
            set_={name: stmt.excluded[name] for name in updatable},
        )
        session.execute(stmt)


def load_feed(session: Session, path: str | Path, root: str | Path | None = None) -> LoadResult:
    """Load one feed file. Commits on success; rolls back and re-raises on any unexpected error."""
    path = Path(path)
    root_path = inbound_root(root)
    if not path.is_file():
        raise FileNotFoundError(f"ESG feed file not found: {path}")
    file_month = month_from_path(path)
    data = path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    content = _decode(path, data)
    rel_path = _relative_file_path(path, root_path)

    records = _records(content)
    header = records[0][2] if records else []
    rows: list[_Row] = []
    failure_reason = None
    if header != EXPECTED_HEADER:
        failure_reason = BAD_HEADER
    else:
        seen_ids: set = set()
        for line_no, raw, fields in records[1:]:
            if fields in ([], [""]):
                continue
            row = _Row(source_row_no=line_no - 1, raw_line=raw)
            _validate(row, fields, file_month, seen_ids)
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
        _lock_month(session, file_month)
        previous = _previous_batch(session, file_month, sha256)
        if previous is not None:
            skipped = LoadResult(
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
            session.commit()
            return skipped

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


def discover_feeds(root: str | Path | None = None) -> list[Path]:
    return sorted(inbound_root(root).glob("esg/*/esg_emissions_*.csv"))


def load_all(session: Session, root: str | Path | None = None) -> list[LoadResult]:
    return [load_feed(session, path, root) for path in discover_feeds(root)]
