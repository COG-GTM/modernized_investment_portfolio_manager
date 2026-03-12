"""Tests for PositionRecord model translated from POSREC.cpy."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.models.position_record import PositionRecord


class TestPositionRecord:
    def test_valid_active_position(self) -> None:
        pos = PositionRecord(
            pos_portfolio_id="PORT0001",
            pos_date="20240320",
            pos_investment_id="AAPL000001",
            pos_quantity=Decimal("100.0000"),
            pos_cost_basis=Decimal("15000.00"),
            pos_market_value=Decimal("17500.00"),
            pos_currency="USD",
            pos_status="A",
        )
        assert pos.pos_status == "A"
        assert pos.pos_quantity == Decimal("100.0000")

    def test_gain_loss_calculation(self) -> None:
        pos = PositionRecord(
            pos_portfolio_id="PORT0001",
            pos_date="20240320",
            pos_investment_id="AAPL000001",
            pos_quantity=Decimal("100.0000"),
            pos_cost_basis=Decimal("15000.00"),
            pos_market_value=Decimal("17500.00"),
        )
        assert pos.calculate_gain_loss() == Decimal("2500.00")

    def test_gain_loss_percent(self) -> None:
        pos = PositionRecord(
            pos_portfolio_id="PORT0001",
            pos_date="20240320",
            pos_investment_id="AAPL000001",
            pos_quantity=Decimal("100.0000"),
            pos_cost_basis=Decimal("10000.00"),
            pos_market_value=Decimal("12000.00"),
        )
        assert pos.calculate_gain_loss_percent() == Decimal("20.00")

    def test_gain_loss_percent_zero_cost(self) -> None:
        pos = PositionRecord(
            pos_portfolio_id="PORT0001",
            pos_date="20240320",
            pos_investment_id="AAPL000001",
            pos_quantity=Decimal("100.0000"),
            pos_cost_basis=Decimal("0.00"),
            pos_market_value=Decimal("12000.00"),
        )
        assert pos.calculate_gain_loss_percent() == Decimal("0.00")

    def test_negative_gain_loss(self) -> None:
        pos = PositionRecord(
            pos_portfolio_id="PORT0001",
            pos_date="20240320",
            pos_investment_id="AAPL000001",
            pos_quantity=Decimal("100.0000"),
            pos_cost_basis=Decimal("20000.00"),
            pos_market_value=Decimal("17500.00"),
        )
        assert pos.calculate_gain_loss() == Decimal("-2500.00")

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PositionRecord(
                pos_portfolio_id="PORT0001",
                pos_date="20240320",
                pos_investment_id="AAPL000001",
                pos_quantity=Decimal("100"),
                pos_cost_basis=Decimal("15000"),
                pos_market_value=Decimal("17500"),
                pos_status="X",  # invalid
            )

    def test_all_status_values(self) -> None:
        for status in ["A", "C", "P"]:
            pos = PositionRecord(
                pos_portfolio_id="PORT0001",
                pos_date="20240320",
                pos_investment_id="AAPL000001",
                pos_quantity=Decimal("100"),
                pos_cost_basis=Decimal("15000"),
                pos_market_value=Decimal("17500"),
                pos_status=status,
            )
            assert pos.pos_status == status
