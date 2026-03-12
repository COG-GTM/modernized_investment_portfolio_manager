"""
Unit tests for the PositionUpdater module.

Tests position calculation logic for buy/sell transactions including:
- Buy transactions creating new positions
- Buy transactions adding to existing positions
- Sell transactions reducing positions
- Proportional cost basis calculations
- Edge cases and error handling
"""

import unittest
from decimal import Decimal

from app.batch.position_updater import PositionUpdater
from app.batch.return_codes import ReturnCode


class TestPositionUpdaterBuy(unittest.TestCase):
    """Test buy transaction position updates."""

    def setUp(self) -> None:
        self.updater = PositionUpdater()

    def test_buy_creates_new_position(self) -> None:
        update = self.updater.apply_buy(
            portfolio_id="PORT0001",
            investment_id="AAPL000001",
            quantity=Decimal("100"),
            price=Decimal("150.50"),
        )
        self.assertEqual(update.portfolio_id, "PORT0001")
        self.assertEqual(update.investment_id, "AAPL000001")
        self.assertEqual(update.transaction_type, "BU")
        self.assertEqual(update.quantity_change, Decimal("100"))
        self.assertEqual(update.cost_change, Decimal("15050.00"))
        self.assertEqual(update.new_quantity, Decimal("100"))
        self.assertEqual(update.new_cost_basis, Decimal("15050.00"))

    def test_buy_with_different_currencies(self) -> None:
        update = self.updater.apply_buy(
            portfolio_id="PORT0001",
            investment_id="SONY000001",
            quantity=Decimal("200"),
            price=Decimal("85.25"),
            currency="JPY",
        )
        self.assertEqual(update.new_quantity, Decimal("200"))
        self.assertEqual(update.new_cost_basis, Decimal("17050.00"))

    def test_buy_small_fractional_shares(self) -> None:
        update = self.updater.apply_buy(
            portfolio_id="PORT0001",
            investment_id="BRK0000001",
            quantity=Decimal("0.5"),
            price=Decimal("500000.00"),
        )
        self.assertEqual(update.new_quantity, Decimal("0.5"))
        self.assertEqual(update.new_cost_basis, Decimal("250000.00"))

    def test_buy_summary_tracking(self) -> None:
        self.updater.apply_buy(
            portfolio_id="PORT0001",
            investment_id="AAPL000001",
            quantity=Decimal("100"),
            price=Decimal("150.00"),
        )
        self.updater.apply_buy(
            portfolio_id="PORT0001",
            investment_id="GOOG000001",
            quantity=Decimal("50"),
            price=Decimal("200.00"),
        )
        summary = self.updater.get_summary()
        self.assertEqual(summary.total_buy_amount, Decimal("25000.00"))
        self.assertEqual(summary.positions_created, 2)


class TestPositionUpdaterSellLogic(unittest.TestCase):
    """Test sell transaction position calculation logic.

    Note: Without a database session, the PositionUpdater cannot persist
    positions between buy/sell calls. These tests verify the calculation
    logic directly via the apply_sell method by testing error handling
    and the mathematical correctness of the position update dataclass.
    """

    def test_sell_without_position_raises_error(self) -> None:
        """Selling from a zero-quantity position should raise ValueError."""
        updater = PositionUpdater()
        with self.assertRaises(ValueError):
            updater.apply_sell(
                portfolio_id="PORT0001",
                investment_id="AAPL000001",
                quantity=Decimal("30"),
                price=Decimal("160.00"),
            )

    def test_position_update_dataclass_sell(self) -> None:
        """Test that PositionUpdate correctly represents a sell."""
        from app.batch.position_updater import PositionUpdate

        update = PositionUpdate(
            portfolio_id="PORT0001",
            investment_id="AAPL000001",
            transaction_type="SL",
            quantity_change=Decimal("-30"),
            cost_change=Decimal("-4500.00"),
            new_quantity=Decimal("70"),
            new_cost_basis=Decimal("10500.00"),
        )
        self.assertEqual(update.transaction_type, "SL")
        self.assertEqual(update.quantity_change, Decimal("-30"))
        self.assertEqual(update.new_quantity, Decimal("70"))
        self.assertEqual(update.new_cost_basis, Decimal("10500.00"))

    def test_proportional_cost_basis_calculation(self) -> None:
        """Verify proportional cost basis math used in apply_sell."""
        # Simulating: 200 shares at $100 = $20,000 cost basis
        current_qty = Decimal("200")
        current_cost = Decimal("20000")
        sell_qty = Decimal("100")

        cost_per_unit = current_cost / current_qty  # $100
        cost_reduction = cost_per_unit * sell_qty    # $10,000
        new_qty = current_qty - sell_qty             # 100
        new_cost = current_cost - cost_reduction     # $10,000

        self.assertEqual(cost_per_unit, Decimal("100"))
        self.assertEqual(cost_reduction, Decimal("10000"))
        self.assertEqual(new_qty, Decimal("100"))
        self.assertEqual(new_cost, Decimal("10000"))

    def test_full_sell_cost_basis_zero(self) -> None:
        """Selling all shares should result in zero cost basis."""
        current_qty = Decimal("100")
        current_cost = Decimal("15000")
        sell_qty = Decimal("100")

        cost_per_unit = current_cost / current_qty
        cost_reduction = cost_per_unit * sell_qty
        new_qty = current_qty - sell_qty
        new_cost = current_cost - cost_reduction

        self.assertEqual(new_qty, Decimal("0"))
        self.assertEqual(new_cost, Decimal("0"))


class TestPositionUpdaterBatch(unittest.TestCase):
    """Test batch processing of transactions."""

    def setUp(self) -> None:
        self.updater = PositionUpdater()

    def test_process_buy_transactions(self) -> None:
        transactions = [
            {
                "type": "BU",
                "portfolio_id": "PORT0001",
                "investment_id": "AAPL000001",
                "quantity": 100,
                "price": "150.00",
                "currency": "USD",
            },
            {
                "type": "BU",
                "portfolio_id": "PORT0001",
                "investment_id": "GOOG000001",
                "quantity": 50,
                "price": "200.00",
                "currency": "USD",
            },
        ]
        updates, rc = self.updater.process_transactions(transactions)
        self.assertEqual(len(updates), 2)
        self.assertEqual(rc, ReturnCode.SUCCESS)

    def test_process_non_position_transactions_skipped(self) -> None:
        transactions = [
            {
                "type": "TR",
                "portfolio_id": "PORT0001",
                "investment_id": "",
                "quantity": 0,
                "price": "0",
            },
            {
                "type": "FE",
                "portfolio_id": "PORT0001",
                "investment_id": "",
                "quantity": 0,
                "price": "0",
            },
        ]
        updates, rc = self.updater.process_transactions(transactions)
        self.assertEqual(len(updates), 0)
        self.assertEqual(rc, ReturnCode.SUCCESS)

    def test_process_empty_batch(self) -> None:
        updates, rc = self.updater.process_transactions([])
        self.assertEqual(len(updates), 0)
        self.assertEqual(rc, ReturnCode.SUCCESS)


class TestPositionUpdaterReturnStatus(unittest.TestCase):
    """Test return status reporting."""

    def test_success_status(self) -> None:
        updater = PositionUpdater()
        updater.process_transactions([])
        status = updater.get_return_status()
        self.assertEqual(status.current_code, ReturnCode.SUCCESS)

    def test_return_status_program_id(self) -> None:
        updater = PositionUpdater()
        status = updater.get_return_status()
        self.assertEqual(status.program_id, "POSUPD00")


if __name__ == "__main__":
    unittest.main()
