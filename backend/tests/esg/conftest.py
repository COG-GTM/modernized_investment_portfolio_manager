"""
Shared fixtures for the ESG carbon intensity acceptance suite (Jira epic RP-45).

The suite was written from the acceptance criteria before the implementation
landed. Everything the tests assume about the implementation is spelled out in
fixtures/README.md and docs/specs/esg-test-matrix.md:

* ``services.esg_service`` exposes ``load_feed(path) -> LoadResult`` and
  ``compute_waci(as_of_month) -> list``.
* Database access goes through ``models.database.SessionLocal`` so the suite
  can point it at a throw-away SQLite file built with ``alembic upgrade head``.
* Tables: ``stg_esg_emissions``, ``stg_esg_emissions_rejects``,
  ``portfolio_esg_metrics``, ``esg_override_audit``.
* The acting user for overrides is taken from the ``X-User`` request header.

Select one story with ``pytest -m rp47``; the whole suite with ``-m esg``.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

AS_OF_MONTH = "2026-10"
NEXT_MONTH = "2026-11"

FEED_2026_10 = FIXTURES_DIR / "esg" / "2026-10" / "esg_emissions_2026-10.csv"
FEED_2026_10_WITH_REJECTS = FIXTURES_DIR / "esg" / "2026-10" / "esg_emissions_2026-10_with_rejects.csv"
FEED_2026_10_SHORT_ROWS = FIXTURES_DIR / "esg" / "2026-10" / "esg_emissions_2026-10_short_rows.csv"
FEED_2026_11 = FIXTURES_DIR / "esg" / "2026-11" / "esg_emissions_2026-11.csv"

# Hand-computed expectations, see fixtures/README.md for the arithmetic.
PORTFOLIO_MAIN = "PORT0001"
ACCOUNT_MAIN = "1234567890"
PORTFOLIO_ZERO_MV = "PORT0002"
ACCOUNT_ZERO_MV = "2222222222"
PORTFOLIO_NO_METRIC = "PORT0003"
ACCOUNT_NO_METRIC = "3333333333"
ACCOUNT_UNKNOWN = "9999999999"

EXPECTED_WACI_MAIN = Decimal("3.3")          # tCO2e per $M revenue
EXPECTED_COVERAGE_MAIN = Decimal("90.0")     # percent of market value with emissions data
EXPECTED_WACI_MAIN_2026_11 = Decimal("3.075")
EXPECTED_COVERAGE_MAIN_2026_11 = Decimal("100.0")
WACI_TOLERANCE = Decimal("0.0005")

STAGING_TABLE = "stg_esg_emissions"
REJECTS_TABLE = "stg_esg_emissions_rejects"
METRICS_TABLE = "portfolio_esg_metrics"
AUDIT_TABLE = "esg_override_audit"

ESG_ROUTE = "/api/portfolio/{account_number}/esg"
OVERRIDE_ROUTE = "/api/portfolio/{account_number}/esg/override"
AUDIT_ROUTE = "/api/portfolio/{account_number}/esg/audit"

STORY_MARKERS = {
    "rp46": "Ingest monthly ESG feed from inbound bucket into staging",
    "rp47": "Compute WACI per portfolio in a database procedure",
    "rp48": "Expose carbon intensity through the portfolio API",
    "rp49": "Show carbon intensity on the portfolio dashboard",
    "rp50": "Override with a reason",
    "rp51": "Audit trail",
    "rp52": "Automated tests",
}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "esg: ESG carbon intensity acceptance suite (Jira epic RP-45)")
    for key, title in STORY_MARKERS.items():
        config.addinivalue_line("markers", f"{key}: Jira {key.upper()} - {title}")


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
@dataclass
class EsgDb:
    url: str
    path: Path
    engine: Any
    Session: Any

    def tables(self) -> List[str]:
        return inspect(self.engine).get_table_names()

    def columns(self, table: str) -> List[str]:
        return [c["name"] for c in inspect(self.engine).get_columns(table)]

    def rows(self, sql: str, **params: Any) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params)
            return [dict(r._mapping) for r in result]

    def scalar(self, sql: str, **params: Any) -> Any:
        with self.engine.connect() as conn:
            return conn.execute(text(sql), params).scalar()

    def execute(self, sql: str, **params: Any) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(sql), params)

    def count(self, table: str, where: str = "1=1", **params: Any) -> int:
        return int(self.scalar(f"SELECT COUNT(*) FROM {table} WHERE {where}", **params))

    def require_table(self, table: str, story: str) -> None:
        if table not in self.tables():
            pytest.fail(f"{story}: table '{table}' is not created by the Alembic migrations")


def _run_migrations(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")


@pytest.fixture
def esg_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> EsgDb:
    """A fresh SQLite database at Alembic head, bound into models.database."""
    db_path = tmp_path / "esg_acceptance.db"
    url = f"sqlite:///{db_path}"
    _run_migrations(url)

    engine = create_engine(url, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    import models
    import models.database as models_database

    for module in (models, models_database):
        monkeypatch.setattr(module, "engine", engine)
        monkeypatch.setattr(module, "SessionLocal", session_factory)

    for name in ("services.esg_service", "routers.esg", "routers.portfolio", "app.main"):
        module = sys.modules.get(name)
        if module is None:
            continue
        for attr, value in (("engine", engine), ("SessionLocal", session_factory)):
            if hasattr(module, attr):
                monkeypatch.setattr(module, attr, value)

    monkeypatch.setenv("PORTFOLIO_DATABASE_URL", url)
    monkeypatch.setenv("DATABASE_URL", url)

    db = EsgDb(url=url, path=db_path, engine=engine, Session=session_factory)
    yield db
    engine.dispose()


def _add_portfolio(session: Session, port_id: str, account_no: str, name: str):
    from models import Portfolio

    portfolio = Portfolio(
        port_id=port_id,
        account_no=account_no,
        client_name=name,
        client_type="I",
        create_date=date(2024, 1, 15),
        last_maint=date(2026, 10, 31),
        status="A",
        total_value=Decimal("0.00"),
        cash_balance=Decimal("0.00"),
        last_user="SEED",
        last_trans="SEED0001",
    )
    session.add(portfolio)
    return portfolio


def add_position(
    session: Session,
    portfolio_id: str,
    investment_id: str,
    market_value: str,
    on: date = date(2026, 10, 31),
    status: str = "A",
    quantity: str = "100",
) -> None:
    from models import Position

    session.add(
        Position(
            portfolio_id=portfolio_id,
            date=on,
            investment_id=investment_id,
            quantity=Decimal(quantity),
            cost_basis=Decimal(market_value),
            market_value=Decimal(market_value),
            currency="USD",
            status=status,
            last_maint_date=datetime(2026, 10, 31, 18, 0, 0),
            last_maint_user="SEED",
        )
    )


@pytest.fixture
def seeded_portfolios(esg_db: EsgDb) -> EsgDb:
    """Portfolios and month-end positions that the hand-computed WACI relies on.

    PORT0001 / 1234567890: INV0000001 60,000; INV0000002 30,000; INV0000003 10,000
    PORT0002 / 2222222222: INV0000004 with zero market value
    PORT0003 / 3333333333: no positions, never gets a metric
    """
    session = esg_db.Session()
    try:
        _add_portfolio(session, PORTFOLIO_MAIN, ACCOUNT_MAIN, "Main Portfolio")
        add_position(session, PORTFOLIO_MAIN, "INV0000001", "60000.00")
        add_position(session, PORTFOLIO_MAIN, "INV0000002", "30000.00")
        add_position(session, PORTFOLIO_MAIN, "INV0000003", "10000.00")

        _add_portfolio(session, PORTFOLIO_ZERO_MV, ACCOUNT_ZERO_MV, "Zero Value Portfolio")
        add_position(session, PORTFOLIO_ZERO_MV, "INV0000004", "0.00", quantity="0")

        _add_portfolio(session, PORTFOLIO_NO_METRIC, ACCOUNT_NO_METRIC, "No Metric Portfolio")
        session.commit()
    finally:
        session.close()
    return esg_db


# --------------------------------------------------------------------------- #
# Staging / metrics helpers (used to decouple stories from each other)
# --------------------------------------------------------------------------- #
def stage_emissions(
    db: EsgDb,
    rows: Iterable[Dict[str, Any]],
    as_of_month: str = AS_OF_MONTH,
    batch_id: str = "batch-test-0001",
) -> None:
    """Insert staging rows directly so RP-47 does not depend on the RP-46 loader."""
    db.require_table(STAGING_TABLE, "RP-47")
    for row in rows:
        db.execute(
            f"INSERT INTO {STAGING_TABLE} "
            "(as_of_month, investment_id, scope1_tco2e, scope2_tco2e, revenue_musd, load_batch_id) "
            "VALUES (:as_of_month, :investment_id, :scope1, :scope2, :revenue, :batch_id)",
            as_of_month=as_of_month,
            investment_id=row["investment_id"],
            scope1=row.get("scope1_tco2e"),
            scope2=row.get("scope2_tco2e"),
            revenue=row.get("revenue_musd"),
            batch_id=batch_id,
        )


MAIN_FEED_ROWS_2026_10 = [
    {"investment_id": "INV0000001", "scope1_tco2e": 120.0, "scope2_tco2e": 80.0, "revenue_musd": 50.0},
    {"investment_id": "INV0000002", "scope1_tco2e": 30.0, "scope2_tco2e": 15.0, "revenue_musd": 15.0},
    {"investment_id": "INV0000003", "scope1_tco2e": 10.0, "scope2_tco2e": 5.0, "revenue_musd": None},
    {"investment_id": "INV0000004", "scope1_tco2e": 500.0, "scope2_tco2e": 250.0, "revenue_musd": 25.0},
    {"investment_id": "INV0000009", "scope1_tco2e": 7.5, "scope2_tco2e": 2.5, "revenue_musd": 10.0},
]


def insert_metric(
    db: EsgDb,
    portfolio_id: str,
    as_of_month: str = AS_OF_MONTH,
    computed_value: Optional[Decimal] = EXPECTED_WACI_MAIN,
    coverage_pct: Optional[Decimal] = EXPECTED_COVERAGE_MAIN,
    computed_at: Optional[datetime] = None,
) -> None:
    """Insert a computed metric row directly so RP-48/50/51 do not depend on RP-47."""
    db.require_table(METRICS_TABLE, "RP-48")
    db.execute(
        f"INSERT INTO {METRICS_TABLE} (portfolio_id, as_of_month, computed_value, coverage_pct, computed_at) "
        "VALUES (:portfolio_id, :as_of_month, :computed_value, :coverage_pct, :computed_at)",
        portfolio_id=portfolio_id,
        as_of_month=as_of_month,
        computed_value=None if computed_value is None else float(computed_value),
        coverage_pct=None if coverage_pct is None else float(coverage_pct),
        computed_at=(computed_at or datetime(2026, 11, 1, 2, 0, 0)).isoformat(sep=" "),
    )


def field(obj: Any, *names: str, default: Any = None) -> Any:
    """Read a field from a dict, ORM object or dataclass under any of the given names."""
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def as_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def approx_equal(actual: Any, expected: Decimal, tolerance: Decimal = WACI_TOLERANCE) -> bool:
    actual_dec = as_decimal(actual)
    return actual_dec is not None and abs(actual_dec - expected) <= tolerance


_AUDIT_ALIASES = {
    "who": ("changed_by", "overridden_by", "user", "username", "actor", "who", "created_by", "last_user"),
    "when": ("changed_at", "overridden_at", "created_at", "timestamp", "when", "occurred_at"),
    "old_value": ("old_value", "previous_value", "before_value"),
    "new_value": ("new_value", "value", "after_value"),
    "reason": ("reason",),
    "as_of_month": ("as_of_month", "month"),
    "portfolio_id": ("portfolio_id", "port_id"),
}


def normalise_audit(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map the audit columns named in RP-51 (who, when, old/new value, reason, month)
    onto canonical keys regardless of the physical column names chosen."""
    out: Dict[str, Any] = dict(row)
    for canonical, aliases in _AUDIT_ALIASES.items():
        for alias in aliases:
            if alias in row:
                out[canonical] = row[alias]
                break
    return out


def audit_rows(db: EsgDb, portfolio_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db.require_table(AUDIT_TABLE, "RP-51")
    where = "1=1"
    params: Dict[str, Any] = {}
    if portfolio_id is not None:
        where = "portfolio_id = :portfolio_id"
        params["portfolio_id"] = portfolio_id
    return [normalise_audit(r) for r in db.rows(f"SELECT * FROM {AUDIT_TABLE} WHERE {where} ORDER BY rowid", **params)]


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
def _route_paths() -> List[str]:
    from app.main import app

    return [re.sub(r"\{[^}]+\}", "{}", getattr(r, "path", "")) for r in app.routes]


def route_exists(path: str, method: Optional[str] = None) -> bool:
    from app.main import app

    wanted = re.sub(r"\{[^}]+\}", "{}", path)
    for route in app.routes:
        if re.sub(r"\{[^}]+\}", "{}", getattr(route, "path", "")) != wanted:
            continue
        if method is None or method.upper() in (getattr(route, "methods", None) or set()):
            return True
    return False


def require_route(path: str, method: str, story: str) -> None:
    if not route_exists(path, method):
        pytest.skip(f"{story}: {method} {path} is not registered on the FastAPI app yet")


@pytest.fixture
def client(seeded_portfolios: EsgDb):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def pm_headers() -> Dict[str, str]:
    return {"X-User": "pm_jane"}


def esg_url(account: str) -> str:
    return ESG_ROUTE.format(account_number=account)


def override_url(account: str) -> str:
    return OVERRIDE_ROUTE.format(account_number=account)


def audit_url(account: str) -> str:
    return AUDIT_ROUTE.format(account_number=account)


def put_override(client, account: str, value: Any, reason: Any, headers: Optional[Dict[str, str]] = None):
    body: Dict[str, Any] = {}
    if value is not None:
        body["value"] = value
    if reason is not None:
        body["reason"] = reason
    return client.put(override_url(account), json=body, headers=headers or {"X-User": "pm_jane"})


def clear_override(client, account: str, reason: str, headers: Optional[Dict[str, str]] = None):
    return client.request(
        "DELETE",
        override_url(account),
        json={"reason": reason},
        headers=headers or {"X-User": "pm_jane"},
    )


def error_text(response) -> str:
    try:
        return str(response.json()).lower()
    except ValueError:
        return response.text.lower()
