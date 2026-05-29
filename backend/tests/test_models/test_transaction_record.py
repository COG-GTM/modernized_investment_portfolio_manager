"""Tests for TransactionRecord model translated from TRNREC.cpy."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.models.transaction_record import TransactionRecord


class TestTransactionRecord:
    def test_valid_buy_transaction(self) -> None:
        trn = TransactionRecord(
            trn_date="20240320",
            trn_time="143000",
            trn_portfolio_id="PORT0001",
            trn_sequence_no="000001",
            trn_investment_id="AAPL000001",
            trn_type="BU",
            trn_quantity=Decimal("100.0000"),
            trn_price=Decimal("150.2500"),
            trn_amount=Decimal("15025.00"),
            trn_currency="USD",
            trn_status="P",
        )
        assert trn.trn_type == "BU"
        assert trn.trn_quantity == Decimal("100.0000")
        assert trn.trn_amount == Decimal("15025.00")
        assert trn.trn_status == "P"

    def test_valid_sell_transaction(self) -> None:
        trn = TransactionRecord(
            trn_date="20240320",
            trn_time="143000",
            trn_portfolio_id="PORT0001",
            trn_sequence_no="000002",
            trn_investment_id="MSFT000001",
            trn_type="SL",
            trn_quantity=Decimal("50.0000"),
            trn_price=Decimal("400.0000"),
            trn_amount=Decimal("20000.00"),
        )
        assert trn.trn_type == "SL"
        assert trn.trn_currency == "USD"  # default

    def test_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransactionRecord(
                trn_date="20240320",
                trn_time="143000",
                trn_portfolio_id="PORT0001",
                trn_sequence_no="000001",
                trn_investment_id="AAPL000001",
                trn_type="XX",  # invalid
                trn_quantity=Decimal("100"),
                trn_price=Decimal("150"),
                trn_amount=Decimal("15000"),
            )

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransactionRecord(
                trn_date="20240320",
                trn_time="143000",
                trn_portfolio_id="PORT0001",
                trn_sequence_no="000001",
                trn_investment_id="AAPL000001",
                trn_type="BU",
                trn_quantity=Decimal("100"),
                trn_price=Decimal("150"),
                trn_amount=Decimal("15000"),
                trn_status="X",  # invalid
            )

    def test_invalid_date_length(self) -> None:
        with pytest.raises(ValidationError, match="8 characters"):
            TransactionRecord(
                trn_date="2024",  # too short
                trn_time="143000",
                trn_portfolio_id="PORT0001",
                trn_sequence_no="000001",
                trn_investment_id="AAPL000001",
                trn_type="BU",
                trn_quantity=Decimal("100"),
                trn_price=Decimal("150"),
                trn_amount=Decimal("15000"),
            )

    def test_all_status_values(self) -> None:
        for status in ["P", "D", "F", "R"]:
            trn = TransactionRecord(
                trn_date="20240320",
                trn_time="143000",
                trn_portfolio_id="PORT0001",
                trn_sequence_no="000001",
                trn_investment_id="AAPL000001",
                trn_type="BU",
                trn_quantity=Decimal("100"),
                trn_price=Decimal("150"),
                trn_amount=Decimal("15000"),
                trn_status=status,
            )
            assert trn.trn_status == status

    def test_all_type_values(self) -> None:
        for trn_type in ["BU", "SL", "TR", "FE"]:
            trn = TransactionRecord(
                trn_date="20240320",
                trn_time="143000",
                trn_portfolio_id="PORT0001",
                trn_sequence_no="000001",
                trn_investment_id="AAPL000001",
                trn_type=trn_type,
                trn_quantity=Decimal("100"),
                trn_price=Decimal("150"),
                trn_amount=Decimal("15000"),
            )
            assert trn.trn_type == trn_type

    def test_decimal_precision(self) -> None:
        trn = TransactionRecord(
            trn_date="20240320",
            trn_time="143000",
            trn_portfolio_id="PORT0001",
            trn_sequence_no="000001",
            trn_investment_id="AAPL000001",
            trn_type="BU",
            trn_quantity=Decimal("100.5678"),
            trn_price=Decimal("150.1234"),
            trn_amount=Decimal("15087.40"),
        )
        assert trn.trn_quantity == Decimal("100.5678")
        assert trn.trn_price == Decimal("150.1234")
