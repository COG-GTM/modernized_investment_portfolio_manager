import sys
import os
import pytest
from decimal import Decimal
from datetime import date, datetime, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.database import Base, Portfolio, Position
from models.transactions import Transaction
from models.history import History


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_portfolio():
    return Portfolio(
        port_id="PORT0001",
        account_no="1234567890",
        client_name="Test Client",
        client_type="I",
        create_date=date(2024, 1, 15),
        last_maint=date(2024, 6, 1),
        status="A",
        total_value=Decimal("50000.00"),
        cash_balance=Decimal("10000.00"),
        last_user="TESTUSER",
        last_trans="00000001",
    )


@pytest.fixture
def sample_position():
    return Position(
        portfolio_id="PORT0001",
        date=date(2024, 1, 15),
        investment_id="INV-AAPL01",
        quantity=Decimal("100.0000"),
        cost_basis=Decimal("15000.00"),
        market_value=Decimal("18500.00"),
        currency="USD",
        status="A",
        last_maint_date=datetime(2024, 6, 1, 10, 30, 0),
        last_maint_user="TESTUSER",
    )


@pytest.fixture
def sample_transaction():
    return Transaction(
        date=date(2024, 6, 15),
        time=time(9, 30, 0),
        portfolio_id="PORT0001",
        sequence_no="000001",
        investment_id="INV-AAPL01",
        type="BU",
        quantity=Decimal("50.0000"),
        price=Decimal("150.0000"),
        amount=Decimal("7500.00"),
        currency="USD",
        status="P",
        process_date=datetime(2024, 6, 15, 9, 30, 0),
        process_user="TESTUSER",
    )


@pytest.fixture
def sample_history():
    return History(
        portfolio_id="PORT0001",
        date="20240615",
        time="09300000",
        seq_no="0001",
        record_type="TR",
        action_code="A",
        before_image=None,
        after_image='{"type": "BU", "quantity": 50}',
        reason_code="PROC",
        process_date=datetime(2024, 6, 15, 9, 30, 0),
        process_user="SYSTEM",
    )


@pytest.fixture
def persisted_portfolio(db_session, sample_portfolio):
    db_session.add(sample_portfolio)
    db_session.flush()
    return sample_portfolio


@pytest.fixture
def persisted_portfolio_with_position(db_session, sample_portfolio, sample_position):
    db_session.add(sample_portfolio)
    db_session.flush()
    db_session.add(sample_position)
    db_session.flush()
    return sample_portfolio


@pytest.fixture
def app():
    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)
