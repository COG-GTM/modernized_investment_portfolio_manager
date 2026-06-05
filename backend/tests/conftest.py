import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models.database import Base, Portfolio, Position
from models.transactions import Transaction
from models.history import History
from decimal import Decimal
from datetime import date, datetime, time


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def sample_portfolio():
    return Portfolio(
        port_id="TEST0001",
        account_no="1234567890",
        client_name="Test Client",
        client_type="I",
        create_date=date(2024, 1, 15),
        last_maint=date(2024, 6, 1),
        status="A",
        total_value=Decimal("100000.00"),
        cash_balance=Decimal("5000.00"),
        last_user="TESTUSER",
        last_trans="TR000001",
    )


@pytest.fixture
def sample_position():
    return Position(
        portfolio_id="TEST0001",
        date=date(2024, 6, 1),
        investment_id="AAPL123456",
        quantity=Decimal("100.0000"),
        cost_basis=Decimal("15000.00"),
        market_value=Decimal("18500.00"),
        currency="USD",
        status="A",
        last_maint_date=datetime(2024, 6, 1, 10, 0, 0),
        last_maint_user="TESTUSER",
    )


@pytest.fixture
def sample_transaction():
    return Transaction(
        date=date(2024, 6, 1),
        time=time(10, 30, 0),
        portfolio_id="TEST0001",
        sequence_no="000001",
        investment_id="AAPL123456",
        type="BU",
        quantity=Decimal("100.0000"),
        price=Decimal("150.0000"),
        amount=Decimal("15000.00"),
        currency="USD",
        status="P",
        process_date=datetime(2024, 6, 1, 10, 30, 0),
        process_user="TESTUSER",
    )


@pytest.fixture
def persisted_portfolio(db_session, sample_portfolio):
    db_session.add(sample_portfolio)
    db_session.flush()
    return sample_portfolio
