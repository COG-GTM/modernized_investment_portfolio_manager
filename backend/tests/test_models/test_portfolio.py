"""Tests for Portfolio model translated from PORTFLIO.cpy."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.models.portfolio import Portfolio


class TestPortfolio:
    def test_valid_individual_portfolio(self) -> None:
        port = Portfolio(
            port_id="PORT0001",
            port_account_no="1234567890",
            port_client_name="John Doe",
            port_client_type="I",
            port_create_date="20240320",
            port_status="A",
            port_total_value=Decimal("100000.00"),
            port_cash_balance=Decimal("5000.00"),
        )
        assert port.port_client_type == "I"
        assert port.port_status == "A"
        assert port.port_total_value == Decimal("100000.00")

    def test_valid_corporate_portfolio(self) -> None:
        port = Portfolio(
            port_id="PORT0002",
            port_account_no="9876543210",
            port_client_name="Acme Corp",
            port_client_type="C",
        )
        assert port.port_client_type == "C"

    def test_valid_trust_portfolio(self) -> None:
        port = Portfolio(
            port_id="PORT0003",
            port_account_no="5555555555",
            port_client_name="Family Trust",
            port_client_type="T",
        )
        assert port.port_client_type == "T"

    def test_invalid_client_type(self) -> None:
        with pytest.raises(ValidationError):
            Portfolio(
                port_id="PORT0001",
                port_account_no="1234567890",
                port_client_type="X",  # invalid
            )

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            Portfolio(
                port_id="PORT0001",
                port_account_no="1234567890",
                port_client_type="I",
                port_status="X",  # invalid
            )

    def test_invalid_account_no_length(self) -> None:
        with pytest.raises(ValidationError, match="10 characters"):
            Portfolio(
                port_id="PORT0001",
                port_account_no="12345",  # too short
                port_client_type="I",
            )

    def test_default_financial_values(self) -> None:
        port = Portfolio(
            port_id="PORT0001",
            port_account_no="1234567890",
            port_client_type="I",
        )
        assert port.port_total_value == Decimal("0.00")
        assert port.port_cash_balance == Decimal("0.00")

    def test_all_status_values(self) -> None:
        for status in ["A", "C", "S"]:
            port = Portfolio(
                port_id="PORT0001",
                port_account_no="1234567890",
                port_client_type="I",
                port_status=status,
            )
            assert port.port_status == status
