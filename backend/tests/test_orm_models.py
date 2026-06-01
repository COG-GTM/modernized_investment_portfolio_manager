import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from datetime import date, datetime, time
import json

from models.database import Base, Portfolio, Position
from models.transactions import Transaction
from models.history import History


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


@pytest.fixture
def sample_portfolio(session):
    portfolio = Portfolio(
        port_id="PORT0001",
        account_no="1234567890",
        client_name="Test Client",
        client_type="I",
        create_date=date(2024, 1, 1),
        status="A",
        total_value=Decimal("50000.00"),
        cash_balance=Decimal("10000.00"),
        last_user="ADMIN",
    )
    session.add(portfolio)
    session.commit()
    return portfolio


@pytest.fixture
def sample_position(session, sample_portfolio):
    position = Position(
        portfolio_id=sample_portfolio.port_id,
        date=date(2024, 1, 15),
        investment_id="AAPL123456",
        quantity=Decimal("100.0000"),
        cost_basis=Decimal("15000.00"),
        market_value=Decimal("18500.00"),
        currency="USD",
        status="A",
        last_maint_date=datetime(2024, 1, 15, 10, 0, 0),
        last_maint_user="ADMIN",
    )
    session.add(position)
    session.commit()
    return position


class TestPortfolioModel:
    def test_create_portfolio(self, sample_portfolio):
        assert sample_portfolio.port_id == "PORT0001"
        assert sample_portfolio.account_no == "1234567890"
        assert sample_portfolio.client_name == "Test Client"
        assert sample_portfolio.client_type == "I"
        assert sample_portfolio.status == "A"

    def test_validate_portfolio_valid(self, sample_portfolio):
        result = sample_portfolio.validate_portfolio()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_portfolio_invalid_port_id(self, session):
        portfolio = Portfolio(
            port_id="BAD",
            account_no="1234567890",
            client_type="I",
            status="A",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_validate_portfolio_invalid_account_no(self, session):
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="123",
            client_type="I",
            status="A",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_validate_portfolio_invalid_client_type(self, session):
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="X",
            status="A",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid client type" in result["errors"]

    def test_validate_portfolio_invalid_status(self, session):
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="X",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_calculate_total_value(self, session, sample_portfolio, sample_position):
        total = sample_portfolio.calculate_total_value()
        expected = sample_position.market_value + sample_portfolio.cash_balance
        assert total == expected

    def test_calculate_total_value_no_positions(self, session):
        portfolio = Portfolio(
            port_id="PORT0002",
            account_no="9876543210",
            client_type="C",
            status="A",
            cash_balance=Decimal("5000.00"),
        )
        session.add(portfolio)
        session.commit()
        assert portfolio.calculate_total_value() == Decimal("5000.00")

    def test_update_total_value(self, session, sample_portfolio, sample_position):
        sample_portfolio.update_total_value()
        expected = sample_position.market_value + sample_portfolio.cash_balance
        assert sample_portfolio.total_value == expected
        assert sample_portfolio.last_maint == date.today()

    def test_to_dict(self, sample_portfolio):
        d = sample_portfolio.to_dict()
        assert d["port_id"] == "PORT0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)

    def test_to_dict_null_dates(self, session):
        portfolio = Portfolio(
            port_id="PORT0003",
            account_no="1111111111",
            client_type="T",
            status="S",
        )
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None


class TestPositionModel:
    def test_create_position(self, sample_position):
        assert sample_position.portfolio_id == "PORT0001"
        assert sample_position.investment_id == "AAPL123456"
        assert sample_position.quantity == Decimal("100.0000")
        assert sample_position.status == "A"

    def test_calculate_gain_loss_positive(self, sample_position):
        result = sample_position.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("3500.00")
        expected_pct = (Decimal("3500.00") / Decimal("15000.00")) * 100
        assert result["gain_loss_percent"] == expected_pct

    def test_calculate_gain_loss_no_cost_basis(self, session, sample_portfolio):
        position = Position(
            portfolio_id=sample_portfolio.port_id,
            date=date(2024, 2, 1),
            investment_id="GOOGL12345",
            status="A",
        )
        result = position.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_validate_position_valid(self, sample_position):
        result = sample_position.validate_position()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_position_invalid_portfolio_id(self, session):
        position = Position(
            portfolio_id="BAD",
            date=date(2024, 1, 1),
            investment_id="AAPL123456",
            status="A",
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_validate_position_invalid_investment_id(self, session):
        position = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 1),
            investment_id="SHORT",
            status="A",
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]

    def test_validate_position_invalid_status(self, session):
        position = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 1),
            investment_id="AAPL123456",
            status="Z",
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_validate_position_negative_quantity(self, session):
        position = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 1),
            investment_id="AAPL123456",
            quantity=Decimal("-10"),
            status="A",
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]

    def test_to_dict(self, sample_position):
        d = sample_position.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["investment_id"] == "AAPL123456"
        assert isinstance(d["quantity"], float)
        assert isinstance(d["gain_loss"], float)
        assert isinstance(d["gain_loss_percent"], float)


class TestTransactionModel:
    @pytest.fixture
    def sample_transaction(self, session, sample_portfolio):
        transaction = Transaction(
            date=date(2024, 3, 1),
            time=time(9, 30, 0),
            portfolio_id=sample_portfolio.port_id,
            sequence_no="000001",
            investment_id="AAPL123456",
            type="BU",
            quantity=Decimal("50.0000"),
            price=Decimal("175.0000"),
            amount=Decimal("8750.00"),
            currency="USD",
            status="P",
            process_user="TRADER1",
        )
        session.add(transaction)
        session.commit()
        return transaction

    def test_validate_transaction_valid(self, sample_transaction):
        result = sample_transaction.validate_transaction()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_transaction_invalid_portfolio_id(self, session):
        t = Transaction(
            portfolio_id="BAD",
            sequence_no="000001",
            type="BU",
            status="P",
            investment_id="AAPL123456",
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_validate_transaction_invalid_sequence(self, session):
        t = Transaction(
            portfolio_id="PORT0001",
            sequence_no="01",
            type="BU",
            status="P",
            investment_id="AAPL123456",
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_validate_transaction_invalid_type(self, session):
        t = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="XX",
            status="P",
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_validate_transaction_missing_investment_id_for_buy(self, session):
        t = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            status="P",
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_validate_transaction_zero_quantity(self, session):
        t = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="SL",
            status="P",
            investment_id="AAPL123456",
            quantity=Decimal("0"),
            price=Decimal("100"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_can_transition_to_valid(self, sample_transaction):
        assert sample_transaction.can_transition_to("D") is True
        assert sample_transaction.can_transition_to("F") is True

    def test_can_transition_to_invalid(self, sample_transaction):
        assert sample_transaction.can_transition_to("R") is False

    def test_transition_status_success(self, sample_transaction):
        result = sample_transaction.transition_status("D", "USER1")
        assert result is True
        assert sample_transaction.status == "D"
        assert sample_transaction.process_user == "USER1"
        assert sample_transaction.process_date is not None

    def test_transition_status_failure(self, sample_transaction):
        result = sample_transaction.transition_status("R", "USER1")
        assert result is False
        assert sample_transaction.status == "P"

    def test_calculate_transaction_amount(self, sample_transaction):
        amount = sample_transaction.calculate_transaction_amount()
        expected = Decimal("50.0000") * Decimal("175.0000")
        assert amount == expected

    def test_calculate_transaction_amount_no_values(self, session):
        t = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="FE",
            status="P",
        )
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount(self, sample_transaction):
        sample_transaction.update_amount()
        expected = Decimal("50.0000") * Decimal("175.0000")
        assert sample_transaction.amount == expected

    def test_to_dict(self, sample_transaction):
        d = sample_transaction.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["type"] == "BU"
        assert d["status"] == "P"
        assert isinstance(d["quantity"], float)
        assert isinstance(d["price"], float)

    def test_to_dict_null_values(self, session):
        t = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="FE",
            status="P",
        )
        d = t.to_dict()
        assert d["date"] is None
        assert d["time"] is None
        assert d["quantity"] == 0.0
        assert d["price"] == 0.0


class TestHistoryModel:
    def test_create_audit_record(self, session, sample_portfolio):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PT",
            action_code="A",
            after_data={"key": "value"},
            reason_code="TEST",
            user="TESTER",
            db_session=session,
        )
        assert record.portfolio_id == "PORT0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.reason_code == "TEST"
        assert record.process_user == "TESTER"
        assert record.after_image == json.dumps({"key": "value"})

    def test_create_audit_record_no_session(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="C",
        )
        assert record.seq_no == "0001"

    def test_get_before_data_valid_json(self, session, sample_portfolio):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PT",
            action_code="C",
            before_data={"old": "data"},
        )
        result = record.get_before_data()
        assert result == {"old": "data"}

    def test_get_before_data_none(self):
        record = History(portfolio_id="PORT0001", date="20240101", time="10000000", seq_no="0001")
        assert record.get_before_data() is None

    def test_get_before_data_invalid_json(self):
        record = History(
            portfolio_id="PORT0001",
            date="20240101",
            time="10000000",
            seq_no="0001",
            before_image="not valid json",
        )
        assert record.get_before_data() is None

    def test_get_after_data_valid_json(self):
        record = History(
            portfolio_id="PORT0001",
            date="20240101",
            time="10000000",
            seq_no="0001",
            after_image=json.dumps({"new": "data"}),
        )
        result = record.get_after_data()
        assert result == {"new": "data"}

    def test_get_after_data_none(self):
        record = History(portfolio_id="PORT0001", date="20240101", time="10000000", seq_no="0001")
        assert record.get_after_data() is None

    def test_get_after_data_invalid_json(self):
        record = History(
            portfolio_id="PORT0001",
            date="20240101",
            time="10000000",
            seq_no="0001",
            after_image="{bad json",
        )
        assert record.get_after_data() is None

    def test_to_dict(self, session, sample_portfolio):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PS",
            action_code="D",
            before_data={"before": True},
            after_data={"after": True},
            reason_code="DEL",
            user="ADMIN",
            db_session=session,
        )
        d = record.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["record_type"] == "PS"
        assert d["action_code"] == "D"
        assert d["before_data"] == {"before": True}
        assert d["after_data"] == {"after": True}
        assert d["reason_code"] == "DEL"
        assert d["process_user"] == "ADMIN"
