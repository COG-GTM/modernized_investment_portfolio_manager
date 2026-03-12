"""
Position Updater.

Migrated from: POSUPDT.cbl (stub in source repo), POSREC.cpy
Updates portfolio positions based on validated transactions: applies
buy/sell transactions, recalculates totals, updates market values.

Pipeline position: Step 2 (after transaction validation).
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .return_codes import ReturnCode, ReturnStatus

logger = logging.getLogger(__name__)


@dataclass
class PositionUpdate:
    """Record of a single position update applied."""

    portfolio_id: str
    investment_id: str
    transaction_type: str
    quantity_change: Decimal
    cost_change: Decimal
    new_quantity: Decimal
    new_cost_basis: Decimal
    timestamp: str = ""


@dataclass
class UpdateSummary:
    """Summary of a position update batch run."""

    total_transactions: int = 0
    positions_created: int = 0
    positions_updated: int = 0
    positions_closed: int = 0
    errors: int = 0
    total_buy_amount: Decimal = Decimal("0.00")
    total_sell_amount: Decimal = Decimal("0.00")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class PositionUpdater:
    """
    Updates portfolio positions based on validated transactions.

    Migrated from POSUPDT.cbl. The COBOL program reads validated
    transactions sequentially, looks up the corresponding position
    in the VSAM position master, applies the transaction (buy adds
    to quantity/cost, sell reduces), and rewrites the position record.

    Pipeline position: Step 2 (runs after TransactionValidator).
    """

    def __init__(self, db_session: Optional[Session] = None) -> None:
        self._db = db_session
        self._summary = UpdateSummary()
        self._updates: List[PositionUpdate] = []
        self._return_status = ReturnStatus(program_id="POSUPD00")
        logger.info("PositionUpdater initialized")

    def process_transactions(
        self, transactions: List[Dict]
    ) -> Tuple[List[PositionUpdate], int]:
        """
        Process a batch of validated transactions and update positions.

        Returns (list of updates applied, return_code).
        Mirrors the main loop of POSUPDT which reads each transaction,
        looks up the position, and applies the update.
        """
        self._summary = UpdateSummary(
            start_time=datetime.now(),
            total_transactions=len(transactions),
        )
        self._updates.clear()

        for txn in transactions:
            try:
                update = self._apply_transaction(txn)
                if update:
                    self._updates.append(update)
            except Exception as e:
                self._summary.errors += 1
                logger.error(
                    "Error processing transaction %s: %s",
                    txn.get("sequence_no", "?"),
                    e,
                )

        self._summary.end_time = datetime.now()

        # Determine return code
        if self._summary.errors > 0 and self._summary.errors == self._summary.total_transactions:
            rc = ReturnCode.ERROR
        elif self._summary.errors > 0:
            rc = ReturnCode.WARNING
        else:
            rc = ReturnCode.SUCCESS

        self._return_status.set_code(
            rc,
            f"Position updates: {len(self._updates)} applied, "
            f"{self._summary.positions_created} created, "
            f"{self._summary.positions_updated} updated, "
            f"{self._summary.errors} errors",
        )

        logger.info(
            "Position update complete: transactions=%d updates=%d created=%d "
            "updated=%d closed=%d errors=%d RC=%d",
            self._summary.total_transactions,
            len(self._updates),
            self._summary.positions_created,
            self._summary.positions_updated,
            self._summary.positions_closed,
            self._summary.errors,
            rc,
        )

        return self._updates, rc

    def apply_buy(
        self,
        portfolio_id: str,
        investment_id: str,
        quantity: Decimal,
        price: Decimal,
        currency: str = "USD",
    ) -> PositionUpdate:
        """
        Apply a buy transaction to a position.

        If the position doesn't exist, create it.
        If it exists, add to quantity and cost basis.
        """
        amount = quantity * price
        current_qty, current_cost = self._get_current_position(portfolio_id, investment_id)

        if current_qty == Decimal("0") and current_cost == Decimal("0"):
            # New position
            new_qty = quantity
            new_cost = amount
            self._create_position(portfolio_id, investment_id, new_qty, new_cost, currency)
            self._summary.positions_created += 1
        else:
            # Update existing position
            new_qty = current_qty + quantity
            new_cost = current_cost + amount
            self._update_position(portfolio_id, investment_id, new_qty, new_cost)
            self._summary.positions_updated += 1

        self._summary.total_buy_amount += amount

        update = PositionUpdate(
            portfolio_id=portfolio_id,
            investment_id=investment_id,
            transaction_type="BU",
            quantity_change=quantity,
            cost_change=amount,
            new_quantity=new_qty,
            new_cost_basis=new_cost,
            timestamp=datetime.now().isoformat(),
        )
        logger.debug(
            "Buy applied: portfolio=%s investment=%s qty=%s price=%s",
            portfolio_id,
            investment_id,
            quantity,
            price,
        )
        return update

    def apply_sell(
        self,
        portfolio_id: str,
        investment_id: str,
        quantity: Decimal,
        price: Decimal,
    ) -> PositionUpdate:
        """
        Apply a sell transaction to a position.

        Reduces quantity and proportionally reduces cost basis.
        If quantity reaches zero, marks position as closed.
        """
        amount = quantity * price
        current_qty, current_cost = self._get_current_position(portfolio_id, investment_id)

        if current_qty <= Decimal("0"):
            raise ValueError(
                f"Cannot sell from position with zero quantity: {portfolio_id}/{investment_id}"
            )

        if quantity > current_qty:
            raise ValueError(
                f"Sell quantity {quantity} exceeds position quantity {current_qty}"
            )

        # Proportional cost basis reduction
        if current_qty > Decimal("0"):
            cost_per_unit = current_cost / current_qty
        else:
            cost_per_unit = Decimal("0")

        cost_reduction = cost_per_unit * quantity
        new_qty = current_qty - quantity
        new_cost = current_cost - cost_reduction

        if new_qty == Decimal("0"):
            self._close_position(portfolio_id, investment_id)
            self._summary.positions_closed += 1
        else:
            self._update_position(portfolio_id, investment_id, new_qty, new_cost)
            self._summary.positions_updated += 1

        self._summary.total_sell_amount += amount

        update = PositionUpdate(
            portfolio_id=portfolio_id,
            investment_id=investment_id,
            transaction_type="SL",
            quantity_change=-quantity,
            cost_change=-cost_reduction,
            new_quantity=new_qty,
            new_cost_basis=new_cost,
            timestamp=datetime.now().isoformat(),
        )
        logger.debug(
            "Sell applied: portfolio=%s investment=%s qty=%s price=%s",
            portfolio_id,
            investment_id,
            quantity,
            price,
        )
        return update

    def get_summary(self) -> UpdateSummary:
        """Return the update summary."""
        return self._summary

    def get_return_status(self) -> ReturnStatus:
        """Return the current return status."""
        return self._return_status

    def _apply_transaction(self, txn: Dict) -> Optional[PositionUpdate]:
        """Apply a single transaction to the appropriate position."""
        txn_type = txn.get("type", "")
        portfolio_id = str(txn.get("portfolio_id", ""))
        investment_id = str(txn.get("investment_id", ""))
        quantity = Decimal(str(txn.get("quantity", 0)))
        price = Decimal(str(txn.get("price", 0)))
        currency = txn.get("currency", "USD")

        if txn_type == "BU":
            return self.apply_buy(portfolio_id, investment_id, quantity, price, currency)
        elif txn_type == "SL":
            return self.apply_sell(portfolio_id, investment_id, quantity, price)
        elif txn_type in ("TR", "FE"):
            # Transfer and fee transactions update amounts but not positions directly
            logger.debug("Non-position transaction type: %s", txn_type)
            return None
        else:
            logger.warning("Unknown transaction type: %s", txn_type)
            return None

    def _get_current_position(
        self, portfolio_id: str, investment_id: str
    ) -> Tuple[Decimal, Decimal]:
        """
        Get current position quantity and cost basis.

        Uses DB if available, otherwise returns zeros (new position).
        """
        if self._db:
            try:
                from models.database import Position

                pos = (
                    self._db.query(Position)
                    .filter(
                        Position.portfolio_id == portfolio_id,
                        Position.investment_id == investment_id,
                        Position.status == "A",
                    )
                    .first()
                )
                if pos:
                    return (
                        pos.quantity or Decimal("0"),
                        pos.cost_basis or Decimal("0"),
                    )
            except Exception as e:
                logger.warning("Could not query position: %s", e)

        return Decimal("0"), Decimal("0")

    def _create_position(
        self,
        portfolio_id: str,
        investment_id: str,
        quantity: Decimal,
        cost_basis: Decimal,
        currency: str = "USD",
    ) -> None:
        """Create a new position record."""
        if self._db:
            try:
                from models.database import Position

                position = Position(
                    portfolio_id=portfolio_id,
                    date=date.today(),
                    investment_id=investment_id,
                    quantity=quantity,
                    cost_basis=cost_basis,
                    market_value=cost_basis,  # Initial market value = cost
                    currency=currency,
                    status="A",
                    last_maint_date=datetime.now(),
                    last_maint_user="BATCH",
                )
                self._db.add(position)
                self._db.flush()
            except Exception as e:
                logger.warning("Could not create position in DB: %s", e)

    def _update_position(
        self,
        portfolio_id: str,
        investment_id: str,
        quantity: Decimal,
        cost_basis: Decimal,
    ) -> None:
        """Update an existing position record."""
        if self._db:
            try:
                from models.database import Position

                pos = (
                    self._db.query(Position)
                    .filter(
                        Position.portfolio_id == portfolio_id,
                        Position.investment_id == investment_id,
                        Position.status == "A",
                    )
                    .first()
                )
                if pos:
                    pos.quantity = quantity
                    pos.cost_basis = cost_basis
                    pos.last_maint_date = datetime.now()
                    pos.last_maint_user = "BATCH"
                    self._db.flush()
            except Exception as e:
                logger.warning("Could not update position in DB: %s", e)

    def _close_position(self, portfolio_id: str, investment_id: str) -> None:
        """Mark a position as closed (quantity reached zero)."""
        if self._db:
            try:
                from models.database import Position

                pos = (
                    self._db.query(Position)
                    .filter(
                        Position.portfolio_id == portfolio_id,
                        Position.investment_id == investment_id,
                        Position.status == "A",
                    )
                    .first()
                )
                if pos:
                    pos.status = "C"
                    pos.quantity = Decimal("0")
                    pos.cost_basis = Decimal("0")
                    pos.last_maint_date = datetime.now()
                    pos.last_maint_user = "BATCH"
                    self._db.flush()
            except Exception as e:
                logger.warning("Could not close position in DB: %s", e)
