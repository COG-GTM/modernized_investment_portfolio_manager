"""
Portfolio Transaction Processing - Migrated from COBOL PORTTRAN.cbl

Processes financial transactions against portfolio records:
- BU (Buy): Add units and cost to portfolio positions
- SL (Sell): Remove units and cost from portfolio positions
- TR (Transfer): Transfer between portfolios (placeholder)
- FE (Fee): Deduct fees from portfolio cost basis

The COBOL program:
1. Read transactions sequentially from TRANSACTION-FILE
2. Validated each transaction (portfolio exists, valid type, positive amounts)
3. Updated portfolio positions based on transaction type
4. Maintained an audit trail via AUDPROC calls
5. Tracked read/process/error counts
6. Stopped after 100+ errors

Transaction validation checked:
- TRN-PORTFOLIO-ID not spaces and exists in PORTFOLIO-FILE
- TRN-TYPE is valid (BU, SL, TR, FE)
- TRN-QUANTITY > 0
- TRN-PRICE > 0 (except for TR type)
- TRN-AMOUNT > 0 (except for TR type)
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models.database import Portfolio, Position, SessionLocal
from models.transactions import Transaction
from models.history import History

logger = logging.getLogger(__name__)

# Transaction types (from COBOL EVALUATE TRN-TYPE)
TXN_BUY = "BU"
TXN_SELL = "SL"
TXN_TRANSFER = "TR"
TXN_FEE = "FE"
VALID_TXN_TYPES = {TXN_BUY, TXN_SELL, TXN_TRANSFER, TXN_FEE}

# Maximum errors before aborting (from COBOL WS-ERROR-COUNT > 100)
MAX_ERRORS = 100


class TransactionResult:
    """Tracks transaction processing results (mirrors COBOL WS-COUNTERS)."""

    def __init__(self):
        self.read_count: int = 0
        self.process_count: int = 0
        self.error_count: int = 0
        self.errors: List[Dict[str, str]] = []

    def add_error(self, portfolio_id: str, message: str) -> None:
        self.error_count += 1
        self.errors.append({"portfolio_id": portfolio_id, "message": message})
        logger.error("Transaction error for %s: %s", portfolio_id, message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transactions_read": self.read_count,
            "transactions_processed": self.process_count,
            "errors_encountered": self.error_count,
            "errors": self.errors,
        }


class PortfolioTransactionProcessor:
    """
    Portfolio transaction processing service.

    Migrated from COBOL PORTTRAN which:
    - Opened TRANSACTION-FILE (sequential) and PORTFOLIO-FILE (indexed, I-O)
    - Read transactions until EOF or error count > 100
    - Validated each transaction via 2100-VALIDATE-TRANSACTION
    - Updated positions via 2200-UPDATE-POSITIONS
    - Wrote audit records via 2300-UPDATE-AUDIT-TRAIL
    - Displayed summary counts at termination
    """

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def process_transaction(
        self,
        portfolio_id: str,
        transaction_type: str,
        investment_id: Optional[str] = None,
        quantity: Optional[Decimal] = None,
        price: Optional[Decimal] = None,
        amount: Optional[Decimal] = None,
        currency: str = "USD",
        user: str = "SYSTEM",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a single transaction against a portfolio.

        Mirrors COBOL 2100-VALIDATE-TRANSACTION followed by
        2200-UPDATE-POSITIONS:
        1. 2110-CHECK-PORTFOLIO: Verify portfolio exists
        2. 2120-CHECK-TRANSACTION-TYPE: Validate type is BU/SL/TR/FE
        3. 2130-CHECK-AMOUNTS: Verify quantity, price, amount > 0
        4. Dispatch to appropriate processing paragraph
        5. 2300-UPDATE-AUDIT-TRAIL: Write audit record

        Args:
            portfolio_id: Target portfolio ID
            transaction_type: Transaction type (BU, SL, TR, FE)
            investment_id: Investment/security ID (required for BU, SL)
            quantity: Number of units
            price: Price per unit
            amount: Total transaction amount
            currency: Currency code
            user: User performing the transaction

        Returns:
            Tuple of (success, result_dict)
        """
        # 2110-CHECK-PORTFOLIO: Verify portfolio exists
        if not portfolio_id or portfolio_id.isspace():
            return False, {"error": "Portfolio ID is required"}

        portfolio = self.db.query(Portfolio).filter(
            Portfolio.port_id == portfolio_id
        ).first()

        if portfolio is None:
            return False, {"error": f"Invalid Portfolio ID: {portfolio_id}"}

        # 2120-CHECK-TRANSACTION-TYPE
        if transaction_type not in VALID_TXN_TYPES:
            return False, {"error": f"Invalid Transaction Type: {transaction_type}"}

        # 2130-CHECK-AMOUNTS
        if quantity is not None and quantity <= 0:
            return False, {"error": "Quantity must be greater than zero"}

        if transaction_type != TXN_TRANSFER:
            if price is not None and price <= 0:
                return False, {"error": "Price must be greater than zero"}

            if amount is not None and amount <= 0:
                return False, {"error": "Amount must be greater than zero"}

        # Calculate amount if not provided
        if amount is None and quantity is not None and price is not None:
            amount = quantity * price

        try:
            # 2200-UPDATE-POSITIONS: Dispatch by transaction type
            if transaction_type == TXN_BUY:
                result = self._process_buy(portfolio, investment_id, quantity, price, amount, currency, user)
            elif transaction_type == TXN_SELL:
                result = self._process_sell(portfolio, investment_id, quantity, price, amount, currency, user)
            elif transaction_type == TXN_TRANSFER:
                result = self._process_transfer(portfolio, user)
            elif transaction_type == TXN_FEE:
                result = self._process_fee(portfolio, amount, user)
            else:
                return False, {"error": f"Unhandled transaction type: {transaction_type}"}

            if not result[0]:
                return result

            # 2300-UPDATE-AUDIT-TRAIL
            self._update_audit_trail(
                portfolio_id=portfolio_id,
                transaction_type=transaction_type,
                amount=amount,
                quantity=quantity,
                user=user,
                status="SUCC" if result[0] else "FAIL",
            )

            # Update portfolio total value
            portfolio.update_total_value()
            portfolio.last_user = user
            portfolio.last_trans = transaction_type

            self.db.commit()
            return True, {"message": f"Transaction {transaction_type} processed successfully"}

        except Exception as e:
            self.db.rollback()
            logger.error("Error processing transaction for %s: %s", portfolio_id, e)
            return False, {"error": f"Error processing transaction: {e}"}

    def process_batch(
        self,
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Process a batch of transactions.

        Mirrors COBOL 2000-PROCESS-TRANSACTIONS loop which read
        transactions until EOF or error count exceeded 100:

        PERFORM 2000-PROCESS-TRANSACTIONS
            UNTIL END-OF-FILE
            OR WS-ERROR-COUNT > 100

        Args:
            transactions: List of transaction dicts with keys matching
                          process_transaction parameters.

        Returns:
            Batch processing result dict with counts.
        """
        result = TransactionResult()

        for txn_data in transactions:
            result.read_count += 1

            if result.error_count > MAX_ERRORS:
                logger.error("Maximum error count exceeded, stopping batch processing")
                break

            success, txn_result = self.process_transaction(
                portfolio_id=txn_data.get("portfolio_id", ""),
                transaction_type=txn_data.get("transaction_type", ""),
                investment_id=txn_data.get("investment_id"),
                quantity=txn_data.get("quantity"),
                price=txn_data.get("price"),
                amount=txn_data.get("amount"),
                currency=txn_data.get("currency", "USD"),
                user=txn_data.get("user", "SYSTEM"),
            )

            if success:
                result.process_count += 1
            else:
                result.add_error(
                    txn_data.get("portfolio_id", "UNKNOWN"),
                    txn_result.get("error", "Unknown error"),
                )

        logger.info(
            "Batch complete. Read: %d, Processed: %d, Errors: %d",
            result.read_count, result.process_count, result.error_count,
        )
        return result.to_dict()

    def _process_buy(
        self,
        portfolio: Portfolio,
        investment_id: Optional[str],
        quantity: Optional[Decimal],
        price: Optional[Decimal],
        amount: Optional[Decimal],
        currency: str,
        user: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a buy transaction.

        Mirrors COBOL 2210-PROCESS-BUY:
        1. Move TRN-PORTFOLIO-ID to PORT-ID
        2. READ PORTFOLIO-FILE (verify exists)
        3. ADD TRN-QUANTITY TO PORT-TOTAL-UNITS
        4. ADD TRN-AMOUNT TO PORT-TOTAL-COST
        5. REWRITE PORTFOLIO-RECORD
        """
        if not investment_id:
            return False, {"error": "Investment ID required for buy transaction"}
        if not quantity or quantity <= 0:
            return False, {"error": "Positive quantity required for buy transaction"}

        # Find or create position.
        # The COBOL program maintained a single position record per
        # portfolio/investment pair (PORT-ID + INVEST-ID as composite key).
        # First look for any existing active position regardless of date,
        # then fall back to creating a new one with today's date.  This
        # keeps buy and sell consistent — both operate on the same position.
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio.port_id,
            Position.investment_id == investment_id,
            Position.status == "A",
        ).first()

        if not position:
            position = Position(
                portfolio_id=portfolio.port_id,
                investment_id=investment_id,
                date=date.today(),
                quantity=Decimal("0.0000"),
                cost_basis=Decimal("0.00"),
                market_value=Decimal("0.00"),
                currency=currency,
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user=user,
            )
            self.db.add(position)

        # ADD TRN-QUANTITY TO PORT-TOTAL-UNITS
        position.quantity = (position.quantity or Decimal("0.0000")) + quantity
        # ADD TRN-AMOUNT TO PORT-TOTAL-COST
        if amount:
            position.cost_basis = (position.cost_basis or Decimal("0.00")) + amount
            position.market_value = (position.market_value or Decimal("0.00")) + amount

        position.last_maint_date = datetime.now()
        position.last_maint_user = user

        return True, {"message": "Buy processed"}

    def _process_sell(
        self,
        portfolio: Portfolio,
        investment_id: Optional[str],
        quantity: Optional[Decimal],
        price: Optional[Decimal],
        amount: Optional[Decimal],
        currency: str,
        user: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a sell transaction.

        Mirrors COBOL 2220-PROCESS-SELL:
        1. Move TRN-PORTFOLIO-ID to PORT-ID
        2. READ PORTFOLIO-FILE
        3. IF PORT-TOTAL-UNITS < TRN-QUANTITY -> 'Insufficient units for sale'
        4. SUBTRACT TRN-QUANTITY FROM PORT-TOTAL-UNITS
        5. SUBTRACT TRN-AMOUNT FROM PORT-TOTAL-COST
        6. REWRITE PORTFOLIO-RECORD
        """
        if not investment_id:
            return False, {"error": "Investment ID required for sell transaction"}
        if not quantity or quantity <= 0:
            return False, {"error": "Positive quantity required for sell transaction"}

        # Find position
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio.port_id,
            Position.investment_id == investment_id,
            Position.status == "A",
        ).first()

        if not position:
            return False, {"error": f"No active position found for investment: {investment_id}"}

        # Check sufficient units (mirrors COBOL: IF PORT-TOTAL-UNITS < TRN-QUANTITY)
        current_quantity = position.quantity or Decimal("0.0000")
        if current_quantity < quantity:
            return False, {"error": "Insufficient units for sale"}

        # SUBTRACT TRN-QUANTITY FROM PORT-TOTAL-UNITS
        position.quantity = current_quantity - quantity

        # Calculate proportional cost reduction
        if current_quantity > 0 and position.cost_basis:
            cost_per_unit = position.cost_basis / current_quantity
            cost_reduction = quantity * cost_per_unit
            position.cost_basis = (position.cost_basis or Decimal("0.00")) - cost_reduction

        if amount:
            position.market_value = (position.market_value or Decimal("0.00")) - amount

        position.last_maint_date = datetime.now()
        position.last_maint_user = user

        return True, {"message": "Sell processed"}

    def _process_transfer(
        self,
        portfolio: Portfolio,
        user: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a transfer transaction.

        Mirrors COBOL 2230-PROCESS-TRANSFER which was a placeholder:
        MOVE 'Transfer processing not implemented' TO ERR-TEXT
        PERFORM 9000-ERROR-ROUTINE
        """
        logger.warning("Transfer processing not yet implemented")
        return False, {"error": "Transfer processing not implemented"}

    def _process_fee(
        self,
        portfolio: Portfolio,
        amount: Optional[Decimal],
        user: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a fee transaction.

        Mirrors COBOL 2240-PROCESS-FEE:
        1. Move TRN-PORTFOLIO-ID to PORT-ID
        2. READ PORTFOLIO-FILE
        3. SUBTRACT TRN-AMOUNT FROM PORT-TOTAL-COST
        4. REWRITE PORTFOLIO-RECORD
        """
        if not amount or amount <= 0:
            return False, {"error": "Positive amount required for fee transaction"}

        # SUBTRACT TRN-AMOUNT FROM PORT-TOTAL-COST
        portfolio.cash_balance = (portfolio.cash_balance or Decimal("0.00")) - amount
        portfolio.last_maint = date.today()
        portfolio.last_user = user

        return True, {"message": "Fee processed"}

    def _update_audit_trail(
        self,
        portfolio_id: str,
        transaction_type: str,
        amount: Optional[Decimal],
        quantity: Optional[Decimal],
        user: str,
        status: str,
    ) -> None:
        """
        Write audit trail record.

        Mirrors COBOL 2300-UPDATE-AUDIT-TRAIL:
        - Set AUD-TIMESTAMP to CURRENT-DATE
        - Set AUD-PROGRAM to 'PORTTRAN'
        - Map transaction type to audit action:
          BU -> CREATE, SL -> DELETE, TR -> UPDATE, FE -> UPDATE
        - Set AUD-STATUS to SUCC or FAIL
        - Build message with transaction details
        - CALL 'AUDPROC' USING AUDIT-RECORD
        """
        # Map transaction type to audit action (mirrors COBOL EVALUATE TRN-TYPE)
        action_map = {
            TXN_BUY: "A",      # CREATE -> Add
            TXN_SELL: "D",     # DELETE -> Remove
            TXN_TRANSFER: "C", # UPDATE -> Change
            TXN_FEE: "C",     # UPDATE -> Change
        }
        action_code = action_map.get(transaction_type, "C")

        try:
            audit_record = History.create_audit_record(
                portfolio_id=portfolio_id,
                record_type="TR",
                action_code=action_code,
                after_data={
                    "transaction_type": transaction_type,
                    "amount": float(amount) if amount else 0.0,
                    "quantity": float(quantity) if quantity else 0.0,
                    "status": status,
                },
                reason_code="TRAN",
                user=user,
                db_session=self.db,
            )
            self.db.add(audit_record)
        except Exception as e:
            logger.error("Error writing audit record: %s", e)

    def close(self) -> None:
        """Close database session if we created one."""
        if self._db is not None:
            self._db.close()
