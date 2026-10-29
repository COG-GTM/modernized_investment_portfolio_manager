"""
Nightly position file loader.

The custodian drops one CSV per business day under inbound/positions/<as_of_date>/.
Each row is a snapshot of a single holding for an account on that date. Rows are
upserted on the positions primary key (portfolio_id, date, investment_id) so a file
can be replayed without creating duplicates.

Holdings the custodian has not priced yet arrive with an empty market_value. They
are stored as NULL rather than 0.00 so pricing gaps are visible downstream instead
of being masked as a total loss.
"""
import csv
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from models.database import Portfolio, Position

POSITION_FILE_COLUMNS = [
    "as_of_date",
    "account_no",
    "portfolio_id",
    "investment_id",
    "quantity",
    "cost_basis",
    "market_value",
    "currency",
    "status",
]

DEFAULT_INBOUND_ROOT = Path(__file__).resolve().parent.parent / "inbound" / "positions"


@dataclass
class LoadResult:
    file: str
    loaded: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def find_latest_position_file(inbound_root: Path = DEFAULT_INBOUND_ROOT) -> Optional[Path]:
    if not inbound_root.exists():
        return None
    files = sorted(inbound_root.glob("*/positions_*.csv"))
    return files[-1] if files else None


def _parse_decimal(raw: str) -> Optional[Decimal]:
    raw = (raw or "").strip()
    if not raw:
        return None
    return Decimal(raw)


def load_position_file(path: Path, db: Session, user: str = "NIGHTLY") -> LoadResult:
    result = LoadResult(file=str(path))

    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in POSITION_FILE_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            result.errors.append(f"missing columns: {', '.join(missing)}")
            return result

        for line_no, row in enumerate(reader, start=2):
            try:
                as_of = datetime.strptime(row["as_of_date"].strip(), "%Y-%m-%d").date()
                quantity = _parse_decimal(row["quantity"]) or Decimal("0.0000")
                cost_basis = _parse_decimal(row["cost_basis"]) or Decimal("0.00")
                market_value = _parse_decimal(row["market_value"])
            except (ValueError, InvalidOperation) as exc:
                result.errors.append(f"line {line_no}: {exc}")
                result.skipped += 1
                continue

            portfolio = (
                db.query(Portfolio)
                .filter(
                    Portfolio.port_id == row["portfolio_id"].strip(),
                    Portfolio.account_no == row["account_no"].strip(),
                )
                .first()
            )
            if portfolio is None:
                result.errors.append(
                    f"line {line_no}: unknown portfolio {row['portfolio_id']} / account {row['account_no']}"
                )
                result.skipped += 1
                continue

            _upsert_position(db, portfolio, as_of, row, quantity, cost_basis, market_value, user)
            result.loaded += 1

    db.commit()
    return result


def _upsert_position(
    db: Session,
    portfolio: Portfolio,
    as_of: date,
    row: dict,
    quantity: Decimal,
    cost_basis: Decimal,
    market_value: Optional[Decimal],
    user: str,
) -> Position:
    investment_id = row["investment_id"].strip()
    position = db.get(Position, (portfolio.port_id, as_of, investment_id))
    if position is None:
        position = Position(
            portfolio_id=portfolio.port_id,
            date=as_of,
            investment_id=investment_id,
        )
        db.add(position)

    position.quantity = quantity
    position.cost_basis = cost_basis
    position.market_value = market_value
    position.currency = (row.get("currency") or "USD").strip()
    position.status = (row.get("status") or "A").strip()
    position.last_maint_date = datetime.now()
    position.last_maint_user = user

    portfolio.last_maint = date.today()
    portfolio.last_user = user
    return position
