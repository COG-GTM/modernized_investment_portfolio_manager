"""Shared fixtures for the ESG feature tests (RP-52). Each test gets a fresh SQLite file."""
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from models import Base, Portfolio, Position, get_db  # noqa: E402
import models.esg  # noqa: E402,F401  (registers the ESG tables on Base)

SAMPLE_FEED = BACKEND_DIR / "inbound" / "esg" / "2026-10" / "esg_emissions_2026-10.csv"
AS_OF = "2026-10"
ACCOUNT = "1234567890"
PORT_ID = "PF-12345"


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'esg_test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()


def add_portfolio(db, port_id=PORT_ID, account_no=ACCOUNT, status="A"):
    portfolio = Portfolio(
        port_id=port_id, account_no=account_no, client_name="Sample Client", client_type="I",
        create_date=date(2024, 1, 15), last_maint=date.today(), status=status,
        total_value=Decimal("0"), cash_balance=Decimal("0"), last_user="TEST", last_trans="TEST",
    )
    db.add(portfolio)
    db.flush()
    return portfolio


def add_position(db, investment_id, market_value, port_id=PORT_ID, status="A", on=None):
    position = Position(
        portfolio_id=port_id, date=on or date(2026, 10, 31), investment_id=investment_id,
        quantity=Decimal("1"), cost_basis=Decimal(str(market_value)), market_value=Decimal(str(market_value)),
        currency="USD", status=status, last_maint_date=datetime.now(), last_maint_user="TEST",
    )
    db.add(position)
    db.flush()
    return position


@pytest.fixture
def seeded_db(db):
    """Mirror of seed_database.py: one active portfolio with AAPL, MSFT, GOOGL, TSLA."""
    add_portfolio(db)
    add_position(db, "AAPL", "27787.50")
    add_position(db, "MSFT", "37885.00")
    add_position(db, "GOOGL", "10692.00")
    add_position(db, "TSLA", "49134.00")
    db.commit()
    return db


@pytest.fixture
def client(engine, seeded_db):
    from app.main import app

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def write_feed(tmp_path, rows, name="esg_emissions_2026-10.csv", header="as_of_month,investment_id,scope1_tco2e,scope2_tco2e,revenue_musd"):
    path = tmp_path / name
    path.write_text("\n".join([header, *rows]) + "\n")
    return path
