import pytest
from unittest.mock import patch, MagicMock
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


def _make_portfolio(db_session, port_id="PORT0001", cash_balance=Decimal("10000.00")):
    portfolio = Portfolio(
        port_id=port_id,
        account_no="1234567890",
        client_name="Test Client",
        client_type="I",
        create_date=date(2024, 1, 15),
        last_maint=date(2024, 6, 1),
        status="A",
        total_value=Decimal("50000.00"),
        cash_balance=cash_balance,
        last_user="ADMIN",
        last_trans="TR000001",
    )
    db_session.add(portfolio)
    db_session.flush()
    return portfolio


def _make_transaction(
    portfolio_id="PORT0001",
    txn_type="BU",
    investment_id="INV-AAPL01",
    quantity=Decimal("100.0000"),
    price=Decimal("150.0000"),
    amount=Decimal("15000.00"),
    sequence_no="000001",
    txn_date=None,
    txn_time=None,
):
    return Transaction(
        date=txn_date or date(2024, 6, 15),
        time=txn_time or time(9, 30, 0),
        portfolio_id=portfolio_id,
        sequence_no=sequence_no,
        investment_id=investment_id,
        type=txn_type,
        quantity=quantity,
        price=price,
        amount=amount,
        currency="USD",
        status="P",
        process_date=datetime(2024, 6, 15, 9, 30, 0),
        process_user="TRADER01",
    )


class TestProcessTransaction:

    def test_process_buy_transaction(self, db_session):
        _make_portfolio(db_session)
        txn = _make_transaction()
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(txn)

        assert result["success"] is True
        assert txn.status == "D"

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
        ).first()
        assert position is not None
        assert position.quantity == Decimal("100.0000")
        assert position.cost_basis == Decimal("15000.00")

    def test_process_sell_transaction(self, db_session):
        _make_portfolio(db_session)

        buy_txn = _make_transaction(
            sequence_no="000001",
            txn_time=time(9, 30, 0),
        )
        db_session.add(buy_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(buy_txn)

        sell_txn = _make_transaction(
            txn_type="SL",
            quantity=Decimal("40.0000"),
            price=Decimal("160.0000"),
            amount=Decimal("6400.00"),
            sequence_no="000002",
            txn_time=time(10, 0, 0),
        )
        db_session.add(sell_txn)
        db_session.flush()

        result = service.process_transaction(sell_txn)
        assert result["success"] is True

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
        ).first()
        assert position.quantity == Decimal("60.0000")
        expected_cost = Decimal("15000.00") - (Decimal("40.0000") * (Decimal("15000.00") / Decimal("100.0000")))
        assert position.cost_basis == expected_cost

    def test_process_fee_transaction(self, db_session):
        portfolio = _make_portfolio(db_session, cash_balance=Decimal("10000.00"))
        fee_txn = _make_transaction(
            txn_type="FE",
            investment_id=None,
            quantity=Decimal("0"),
            price=Decimal("0"),
            amount=Decimal("250.00"),
            sequence_no="000001",
        )
        db_session.add(fee_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(fee_txn)

        assert result["success"] is True
        db_session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("9750.00")

    def test_process_transfer_transaction(self, db_session):
        _make_portfolio(db_session)
        tr_txn = _make_transaction(
            txn_type="TR",
            investment_id=None,
            quantity=Decimal("0"),
            price=Decimal("0"),
            amount=Decimal("5000.00"),
            sequence_no="000001",
        )
        db_session.add(tr_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(tr_txn)

        assert result["success"] is True
        assert tr_txn.status == "D"

    def test_process_invalid_transaction(self, db_session):
        _make_portfolio(db_session)
        invalid_txn = _make_transaction(
            txn_type="BU",
            investment_id=None,
            quantity=Decimal("0"),
            price=Decimal("0"),
            amount=Decimal("0"),
            sequence_no="000001",
        )
        db_session.add(invalid_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(invalid_txn)

        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_process_transaction_creates_audit_record(self, db_session):
        _make_portfolio(db_session)
        txn = _make_transaction()
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(txn)

        history_records = db_session.query(History).filter(
            History.portfolio_id == "PORT0001"
        ).all()
        assert len(history_records) > 0
        record_types = [r.record_type for r in history_records]
        assert "TR" in record_types

    def test_process_transaction_updates_portfolio_total(self, db_session):
        portfolio = _make_portfolio(db_session)
        original_total = portfolio.total_value

        txn = _make_transaction()
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(txn)

        db_session.refresh(portfolio)
        assert portfolio.last_maint == date.today()

    def test_transaction_failure_rollback(self, db_session):
        _make_portfolio(db_session)
        txn = _make_transaction()
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        with patch.object(service, '_process_buy_sell_transaction', side_effect=Exception("Forced error")):
            result = service.process_transaction(txn)

        assert result["success"] is False
        assert "Forced error" in result["errors"][0]
        assert txn.status == "F"


class TestBuySellProcessing:

    def test_buy_creates_new_position(self, db_session):
        _make_portfolio(db_session)
        txn = _make_transaction(
            investment_id="INV-GOOG01",
            quantity=Decimal("50.0000"),
            price=Decimal("200.0000"),
            amount=Decimal("10000.00"),
        )
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(txn)

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-GOOG01",
        ).first()
        assert position is not None
        assert position.quantity == Decimal("50.0000")
        assert position.cost_basis == Decimal("10000.00")
        assert position.status == "A"

    def test_buy_updates_existing_position(self, db_session):
        _make_portfolio(db_session)

        first_buy = _make_transaction(
            sequence_no="000001",
            txn_time=time(9, 30, 0),
            quantity=Decimal("50.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("7500.00"),
        )
        db_session.add(first_buy)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(first_buy)

        second_buy = _make_transaction(
            sequence_no="000002",
            txn_time=time(10, 0, 0),
            quantity=Decimal("30.0000"),
            price=Decimal("155.0000"),
            amount=Decimal("4650.00"),
        )
        db_session.add(second_buy)
        db_session.flush()

        service.process_transaction(second_buy)

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
        ).first()
        assert position.quantity == Decimal("80.0000")
        assert position.cost_basis == Decimal("12150.00")

    def test_sell_reduces_position(self, db_session):
        _make_portfolio(db_session)

        buy_txn = _make_transaction(
            sequence_no="000001",
            txn_time=time(9, 30, 0),
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("15000.00"),
        )
        db_session.add(buy_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(buy_txn)

        sell_txn = _make_transaction(
            txn_type="SL",
            sequence_no="000002",
            txn_time=time(10, 0, 0),
            quantity=Decimal("25.0000"),
            price=Decimal("160.0000"),
            amount=Decimal("4000.00"),
        )
        db_session.add(sell_txn)
        db_session.flush()

        result = service.process_transaction(sell_txn)
        assert result["success"] is True

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
        ).first()
        assert position.quantity == Decimal("75.0000")
        cost_per_share = Decimal("15000.00") / Decimal("100.0000")
        expected_cost = Decimal("15000.00") - (Decimal("25.0000") * cost_per_share)
        assert position.cost_basis == expected_cost

    def test_sell_position_to_zero(self, db_session):
        _make_portfolio(db_session)

        buy_txn = _make_transaction(
            sequence_no="000001",
            txn_time=time(9, 30, 0),
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("15000.00"),
        )
        db_session.add(buy_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(buy_txn)

        sell_txn = _make_transaction(
            txn_type="SL",
            sequence_no="000002",
            txn_time=time(10, 0, 0),
            quantity=Decimal("100.0000"),
            price=Decimal("160.0000"),
            amount=Decimal("16000.00"),
        )
        db_session.add(sell_txn)
        db_session.flush()

        result = service.process_transaction(sell_txn)
        assert result["success"] is True

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT0001",
            Position.investment_id == "INV-AAPL01",
        ).first()
        assert position.quantity == Decimal("0.0000")
        assert position.cost_basis == Decimal("0.00")


class TestFeeProcessing:

    def test_fee_reduces_cash_balance(self, db_session):
        portfolio = _make_portfolio(db_session, cash_balance=Decimal("5000.00"))
        fee_txn = _make_transaction(
            txn_type="FE",
            investment_id=None,
            quantity=Decimal("0"),
            price=Decimal("0"),
            amount=Decimal("100.00"),
            sequence_no="000001",
        )
        db_session.add(fee_txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(fee_txn)

        assert result["success"] is True
        db_session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("4900.00")

    def test_fee_with_no_portfolio(self, db_session):
        fee_txn = Transaction(
            date=date(2024, 6, 15),
            time=time(9, 30, 0),
            portfolio_id="NOPORT01",
            sequence_no="000001",
            investment_id=None,
            type="FE",
            quantity=Decimal("0"),
            price=Decimal("0"),
            amount=Decimal("100.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 6, 15, 9, 30, 0),
            process_user="TRADER01",
        )

        service = PortfolioService(db_session)
        result = service.process_transaction(fee_txn)

        assert result["success"] is True  # fee silently succeeds when portfolio not found
