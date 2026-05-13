import pytest
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from datetime import date, time, datetime

from models.database import Base, Portfolio, Position
from models.transactions import Transaction
from models.history import History
from services.portfolio_service import PortfolioService


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(autocommit=False, autoflush=True, bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


class TestEndToEndTransactionFlow:

    def test_full_buy_transaction_flow(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_name="Test Client",
            client_type="I",
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            status="A",
            total_value=Decimal("0.00"),
            cash_balance=Decimal("50000.00"),
            last_user="ADMIN",
            last_trans="TR000001",
        )
        db_session.add(portfolio)
        db_session.flush()

        transaction = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000001",
            investment_id="INV-AAPL01",
            type="BU",
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("15000.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 9, 30, 0),
            process_user="TRADER01",
        )
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(transaction)

        assert result["success"] is True
        assert result["errors"] == []

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
        ).first()
        assert position is not None
        assert position.quantity == Decimal("100.0000")

        audit_records = db_session.query(History).filter(
            History.portfolio_id == "PORT0001"
        ).all()
        assert len(audit_records) >= 1

        updated_portfolio = db_session.query(Portfolio).filter(
            Portfolio.port_id == "PORT0001"
        ).first()
        assert updated_portfolio.total_value is not None

    def test_buy_then_sell_flow(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0002",
            account_no="2345678901",
            client_name="Sell Test Client",
            client_type="I",
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            status="A",
            total_value=Decimal("0.00"),
            cash_balance=Decimal("100000.00"),
            last_user="ADMIN",
            last_trans="TR000001",
        )
        db_session.add(portfolio)
        db_session.flush()

        buy_txn = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0002",
            sequence_no="000001",
            investment_id="INV-MSFT01",
            type="BU",
            quantity=Decimal("100.0000"),
            price=Decimal("200.0000"),
            amount=Decimal("20000.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 9, 30, 0),
            process_user="TRADER01",
        )
        db_session.add(buy_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        buy_result = service.process_transaction(buy_txn)
        assert buy_result["success"] is True

        sell_txn = Transaction(
            date=date(2024, 6, 15),
            time=time(10, 0, 0),
            portfolio_id="PORT0002",
            sequence_no="000002",
            investment_id="INV-MSFT01",
            type="SL",
            quantity=Decimal("50.0000"),
            price=Decimal("210.0000"),
            amount=Decimal("10500.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 10, 0, 0),
            process_user="TRADER01",
        )
        db_session.add(sell_txn)
        db_session.flush()

        sell_result = service.process_transaction(sell_txn)
        assert sell_result["success"] is True

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0002",
            Position.investment_id == "INV-MSFT01",
        ).first()
        assert position is not None
        assert position.quantity == Decimal("50.0000")
        assert position.cost_basis < Decimal("20000.00")

    def test_fee_reduces_cash_balance(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0003",
            account_no="3456789012",
            client_name="Fee Test Client",
            client_type="I",
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            status="A",
            total_value=Decimal("50000.00"),
            cash_balance=Decimal("50000.00"),
            last_user="ADMIN",
            last_trans="TR000001",
        )
        db_session.add(portfolio)
        db_session.flush()

        fee_txn = Transaction(
            date=date(2024, 6, 15),
            time=time(11, 0, 0),
            portfolio_id="PORT0003",
            sequence_no="000001",
            investment_id="FEE-MGMT01",
            type="FE",
            quantity=Decimal("1.0000"),
            price=Decimal("500.0000"),
            amount=Decimal("500.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 11, 0, 0),
            process_user="SYSTEM",
        )
        db_session.add(fee_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(fee_txn)
        assert result["success"] is True

        updated_portfolio = db_session.query(Portfolio).filter(
            Portfolio.port_id == "PORT0003"
        ).first()
        assert updated_portfolio.cash_balance == Decimal("49500.00")

    def test_multiple_transactions_same_portfolio(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0004",
            account_no="4567890123",
            client_name="Multi Txn Client",
            client_type="I",
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            status="A",
            total_value=Decimal("0.00"),
            cash_balance=Decimal("200000.00"),
            last_user="ADMIN",
            last_trans="TR000001",
        )
        db_session.add(portfolio)
        db_session.flush()

        service = PortfolioService(db_session)

        buy_aapl = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0004",
            sequence_no="000001",
            investment_id="INV-AAPL01",
            type="BU",
            quantity=Decimal("50.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("7500.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 9, 30, 0),
            process_user="TRADER01",
        )
        db_session.add(buy_aapl)
        db_session.flush()
        result1 = service.process_transaction(buy_aapl)
        assert result1["success"] is True

        buy_msft = Transaction(
            date=date(2024, 6, 15),
            time=time(10, 0, 0),
            portfolio_id="PORT0004",
            sequence_no="000002",
            investment_id="INV-MSFT01",
            type="BU",
            quantity=Decimal("30.0000"),
            price=Decimal("300.0000"),
            amount=Decimal("9000.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 10, 0, 0),
            process_user="TRADER01",
        )
        db_session.add(buy_msft)
        db_session.flush()
        result2 = service.process_transaction(buy_msft)
        assert result2["success"] is True

        positions = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0004"
        ).all()
        assert len(positions) == 2

        investment_ids = {p.investment_id for p in positions}
        assert "INV-AAPL01" in investment_ids
        assert "INV-MSFT01" in investment_ids

    def test_transaction_validation_prevents_processing(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0005",
            account_no="5678901234",
            client_name="Validation Client",
            client_type="I",
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            status="A",
            total_value=Decimal("50000.00"),
            cash_balance=Decimal("50000.00"),
            last_user="ADMIN",
            last_trans="TR000001",
        )
        db_session.add(portfolio)
        db_session.flush()

        invalid_txn = Transaction(
            date=date(2024, 6, 15),
            time=time(12, 0, 0),
            portfolio_id="PORT0005",
            sequence_no="000001",
            investment_id=None,
            type="BU",
            quantity=Decimal("0"),
            price=Decimal("0"),
            amount=Decimal("0.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 12, 0, 0),
            process_user="TRADER01",
        )
        db_session.add(invalid_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(invalid_txn)

        assert result["success"] is False
        assert len(result["errors"]) > 0
