"""
Shared pytest fixtures for ORM model tests.

Run tests from the backend/ directory:
    cd backend && python -m pytest tests/ -v
"""
import sys
import os
from decimal import Decimal
from datetime import date, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend/ is on sys.path so that `from models.database import ...` works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.database import Base, Portfolio, Position
from models.transactions import Transaction


# ---------------------------------------------------------------------------
# Engine & session fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Function-scoped session with rollback for test isolation."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_portfolio():
    """Factory that returns a Portfolio with sensible defaults."""
    def _make(**overrides):
        defaults = dict(
            port_id="TEST0001",
            account_no="1234567890",
            client_name="Test Client",
            client_type="I",
            status="A",
            cash_balance=Decimal("10000.00"),
            create_date=date.today(),
        )
        defaults.update(overrides)
        return Portfolio(**defaults)
    return _make


@pytest.fixture
def sample_transaction():
    """Factory that returns a Transaction with sensible defaults."""
    def _make(**overrides):
        defaults = dict(
            date=date.today(),
            time=time(9, 30, 0),
            portfolio_id="TEST0001",
            sequence_no="000001",
            investment_id="AAPL123456",
            type="BU",
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
            currency="USD",
            status="P",
        )
        defaults.update(overrides)
        return Transaction(**defaults)
    return _make


@pytest.fixture
def sample_position():
    """Factory that returns a Position with sensible defaults."""
    def _make(**overrides):
        defaults = dict(
            portfolio_id="TEST0001",
            date=date.today(),
            investment_id="AAPL123456",
            quantity=Decimal("100.0000"),
            cost_basis=Decimal("15000.00"),
            market_value=Decimal("16500.00"),
            currency="USD",
            status="A",
        )
        defaults.update(overrides)
        return Position(**defaults)
    return _make
