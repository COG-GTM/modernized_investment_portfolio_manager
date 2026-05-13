import pytest
from decimal import Decimal
from datetime import date, datetime, time
from unittest.mock import patch
from sqlalchemy.orm import sessionmaker

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History
from services.portfolio_service import PortfolioService


@pytest.fixture
def db_session(engine):
    """Override conftest db_session with autoflush=True so History seq_no
    counting works correctly when multiple audit records are created in
    the same process_transaction call."""
    Session = sessionmaker(autocommit=False, autoflush=True, bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


class TestProcessTransactionBuy:
    """process_transaction() with BUY type."""

    def test_buy_creates_position_and_updates_portfolio(self, db_session, persisted_portfolio):
        transaction = Transaction(
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
            process_user="TESTUSER",
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
        assert position.quantity == Decimal("50.0000")
        assert position.cost_basis == Decimal("7500.00")

        assert transaction.status == "D"

        history_records = db_session.query(History).filter(
            History.portfolio_id == "PORT0001",
        ).all()
        assert len(history_records) >= 1

        portfolio = db_session.query(Portfolio).filter(
            Portfolio.port_id == "PORT0001",
        ).first()
        assert portfolio.last_maint == date.today()


class TestProcessTransactionSell:
    """process_transaction() with SELL type."""

    def test_sell_reduces_quantity_and_adjusts_cost_basis(
        self, db_session, persisted_portfolio_with_position
    ):
        transaction = Transaction(
            date=date(2024, 1, 15),
            time=time(10, 0, 0),
            portfolio_id="PORT0001",
            sequence_no="000002",
            investment_id="INV-AAPL01",
            type="SL",
            quantity=Decimal("30.0000"),
            price=Decimal("185.0000"),
            amount=Decimal("5550.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(transaction)

        assert result["success"] is True

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
            Position.date == date(2024, 1, 15),
        ).first()
        assert position.quantity == Decimal("70.0000")
        # cost_basis proportional: 15000 - (30 * 15000/100) = 10500
        assert position.cost_basis == Decimal("10500.00")


class TestProcessTransactionFee:
    """process_transaction() with FEE type."""

    def test_fee_reduces_cash_balance_and_creates_audit(self, db_session, persisted_portfolio):
        initial_cash = persisted_portfolio.cash_balance

        transaction = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000003",
            type="FE",
            amount=Decimal("250.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(transaction)

        assert result["success"] is True

        portfolio = db_session.query(Portfolio).filter(
            Portfolio.port_id == "PORT0001",
        ).first()
        assert portfolio.cash_balance == initial_cash - Decimal("250.00")

        fee_audits = db_session.query(History).filter(
            History.portfolio_id == "PORT0001",
            History.record_type == "PT",
        ).all()
        assert len(fee_audits) >= 1


class TestProcessTransactionTransfer:
    """process_transaction() with TRANSFER type."""

    def test_transfer_processes_without_error(self, db_session, persisted_portfolio):
        transaction = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000004",
            type="TR",
            amount=Decimal("0.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(transaction)

        assert result["success"] is True
        assert result["errors"] == []
        assert transaction.status == "D"


class TestProcessTransactionValidation:
    """process_transaction() validation failure."""

    def test_invalid_portfolio_id_returns_failure(self, db_session):
        transaction = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="BAD",
            sequence_no="000001",
            investment_id="INV-AAPL01",
            type="BU",
            quantity=Decimal("50.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("7500.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )

        service = PortfolioService(db_session)
        result = service.process_transaction(transaction)

        assert result["success"] is False
        assert len(result["errors"]) > 0


class TestProcessTransactionException:
    """process_transaction() exception handling."""

    def test_exception_transitions_status_to_failed(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0002",
            account_no="9876543210",
            client_name="Exception Test",
            client_type="I",
            create_date=date(2024, 1, 1),
            status="A",
            total_value=Decimal("10000.00"),
            cash_balance=Decimal("5000.00"),
            last_user="TESTUSER",
        )
        transaction = Transaction(
            date=date(2024, 6, 15),
            time=time(11, 0, 0),
            portfolio_id="PORT0002",
            sequence_no="000001",
            investment_id="INV-GOOG01",
            type="BU",
            quantity=Decimal("10.0000"),
            price=Decimal("100.0000"),
            amount=Decimal("1000.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(portfolio)
        db_session.add(transaction)
        db_session.commit()

        service = PortfolioService(db_session)

        with patch.object(
            service,
            "_process_buy_sell_transaction",
            side_effect=Exception("Processing error"),
        ):
            result = service.process_transaction(transaction)

        assert result["success"] is False
        assert "Processing error" in result["errors"][0]
        assert transaction.status == "F"


class TestProcessBuySellNewPosition:
    """_process_buy_sell_transaction() creates new position."""

    def test_new_position_created(self, db_session, persisted_portfolio):
        transaction = Transaction(
            date=date(2024, 7, 1),
            time=time(10, 0, 0),
            portfolio_id="PORT0001",
            sequence_no="000005",
            investment_id="INV-MSFT01",
            type="BU",
            quantity=Decimal("25.0000"),
            price=Decimal("300.0000"),
            amount=Decimal("7500.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        service._process_buy_sell_transaction(transaction)

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-MSFT01",
            Position.date == date(2024, 7, 1),
        ).first()
        assert position is not None
        assert position.quantity == Decimal("25.0000")
        assert position.cost_basis == Decimal("7500.00")
        assert position.currency == "USD"
        assert position.status == "A"


class TestProcessBuySellExistingPosition:
    """_process_buy_sell_transaction() updates existing position."""

    def test_existing_position_updated(self, db_session, persisted_portfolio_with_position):
        transaction = Transaction(
            date=date(2024, 1, 15),
            time=time(14, 0, 0),
            portfolio_id="PORT0001",
            sequence_no="000006",
            investment_id="INV-AAPL01",
            type="BU",
            quantity=Decimal("20.0000"),
            price=Decimal("160.0000"),
            amount=Decimal("3200.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        service._process_buy_sell_transaction(transaction)

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
            Position.date == date(2024, 1, 15),
        ).first()
        assert position.quantity == Decimal("120.0000")
        assert position.cost_basis == Decimal("18200.00")


class TestProcessFeeWithPortfolio:
    """_process_fee_transaction() with portfolio."""

    def test_cash_balance_deducted_and_audit_created(self, db_session, persisted_portfolio):
        initial_cash = persisted_portfolio.cash_balance

        transaction = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000007",
            type="FE",
            amount=Decimal("500.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        service._process_fee_transaction(transaction)

        portfolio = db_session.query(Portfolio).filter(
            Portfolio.port_id == "PORT0001",
        ).first()
        assert portfolio.cash_balance == initial_cash - Decimal("500.00")

        fee_audits = db_session.query(History).filter(
            History.portfolio_id == "PORT0001",
            History.record_type == "PT",
            History.reason_code == "FEE",
        ).all()
        assert len(fee_audits) >= 1


class TestProcessFeeWithoutPortfolio:
    """_process_fee_transaction() without portfolio."""

    def test_no_portfolio_handles_gracefully(self, db_session):
        transaction = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="NOPORT01",
            sequence_no="000008",
            type="FE",
            amount=Decimal("100.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )

        service = PortfolioService(db_session)
        service._process_fee_transaction(transaction)

        fee_audits = db_session.query(History).filter(
            History.portfolio_id == "NOPORT01",
            History.record_type == "PT",
        ).all()
        assert len(fee_audits) == 0
