"""
Data Validation Utility - Migrated from COBOL UTLVAL00.cbl

Performs comprehensive data validation across systems:
- Data integrity checks: verify required fields and referential integrity
- Cross-reference validation: ensure consistency between positions, transactions, and portfolios
- Format verification: validate data formats and field constraints
- Balance reconciliation: verify position totals match portfolio values

The COBOL program read validation control records that specified which
type of validation to perform (INTEGRITY, XREF, FORMAT, BALANCE),
then executed the appropriate checks against VSAM files and DB2 tables.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import Portfolio, Position, SessionLocal
from models.transactions import Transaction
from models.history import History

logger = logging.getLogger(__name__)


# Validation types (from COBOL WS-VALIDATION-TYPES)
VALIDATION_INTEGRITY = "INTEGRITY"
VALIDATION_XREF = "XREF"
VALIDATION_FORMAT = "FORMAT"
VALIDATION_BALANCE = "BALANCE"

VALID_VALIDATION_TYPES = {VALIDATION_INTEGRITY, VALIDATION_XREF, VALIDATION_FORMAT, VALIDATION_BALANCE}


class ValidationError:
    """Represents a single validation error (from COBOL WS-ERROR-LINE)."""

    def __init__(self, error_type: str, key: str, description: str):
        self.error_type = error_type
        self.key = key
        self.description = description

    def to_dict(self) -> Dict[str, str]:
        return {
            "error_type": self.error_type,
            "key": self.key,
            "description": self.description,
        }


class ValidationResult:
    """
    Tracks validation results.

    Mirrors COBOL WS-VALIDATION-TOTALS:
    - WS-RECORDS-READ
    - WS-RECORDS-VALID
    - WS-RECORDS-ERROR
    - WS-TOTAL-AMOUNT
    - WS-CONTROL-TOTAL
    """

    def __init__(self, validation_type: str):
        self.validation_type = validation_type
        self.records_read: int = 0
        self.records_valid: int = 0
        self.records_error: int = 0
        self.total_amount: Decimal = Decimal("0.00")
        self.control_total: Decimal = Decimal("0.00")
        self.errors: List[ValidationError] = []

    def add_error(self, error_type: str, key: str, description: str) -> None:
        """Add a validation error (mirrors COBOL 9999-ERROR-HANDLER)."""
        self.records_error += 1
        error = ValidationError(error_type, key, description)
        self.errors.append(error)
        logger.warning("Validation error [%s] key=%s: %s", error_type, key, description)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_type": self.validation_type,
            "records_read": self.records_read,
            "records_valid": self.records_valid,
            "records_error": self.records_error,
            "total_amount": float(self.total_amount),
            "control_total": float(self.control_total),
            "errors": [e.to_dict() for e in self.errors],
            "passed": self.records_error == 0,
        }


class DataValidator:
    """
    Cross-system data integrity validation service.

    Migrated from COBOL UTLVAL00 which:
    - Read validation control records from a sequential file
    - Dispatched to integrity, cross-reference, format, or balance checks
    - Validated positions against the Position Master VSAM file
    - Validated transactions against the Transaction History VSAM file
    - Accumulated totals and verified balance reconciliation
    - Wrote errors to an error report file
    """

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def validate(self, validation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute validation checks.

        Mirrors COBOL 2000-PROCESS which loops over validation control
        records and dispatches to the appropriate check via EVALUATE.

        Args:
            validation_types: List of validation types to run.
                              If None, runs all validation types.

        Returns:
            Dictionary with results for each validation type.
        """
        if validation_types is None:
            validation_types = [
                VALIDATION_INTEGRITY,
                VALIDATION_XREF,
                VALIDATION_FORMAT,
                VALIDATION_BALANCE,
            ]

        results: Dict[str, Any] = {}

        for val_type in validation_types:
            val_type = val_type.strip().upper()
            if val_type not in VALID_VALIDATION_TYPES:
                results[val_type] = {
                    "validation_type": val_type,
                    "error": "INVALID VALIDATION TYPE",
                    "passed": False,
                }
                continue

            result = self._process_validation(val_type)
            results[val_type] = result

        overall_passed = all(
            r.get("passed", False) for r in results.values()
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_passed": overall_passed,
            "results": results,
        }

    def _process_validation(self, validation_type: str) -> Dict[str, Any]:
        """Dispatch to the appropriate validation check (mirrors COBOL 2100-PROCESS-VALIDATION)."""
        dispatch = {
            VALIDATION_INTEGRITY: self._check_integrity,
            VALIDATION_XREF: self._check_xref,
            VALIDATION_FORMAT: self._check_format,
            VALIDATION_BALANCE: self._check_balance,
        }
        handler = dispatch[validation_type]
        return handler()

    def _check_integrity(self) -> Dict[str, Any]:
        """
        Check data integrity for positions and transactions.

        Mirrors COBOL 2200-CHECK-INTEGRITY:
        - 2210-CHECK-POSITION-INTEGRITY: Verify position records have required fields
        - 2220-CHECK-TRANSACTION-INTEGRITY: Verify transaction records have required fields
        """
        result = ValidationResult(VALIDATION_INTEGRITY)

        # Check position integrity (2210-CHECK-POSITION-INTEGRITY)
        positions = self.db.query(Position).all()
        result.records_read += len(positions)

        for pos in positions:
            key = f"{pos.portfolio_id}/{pos.investment_id}"
            has_error = False

            if not pos.portfolio_id:
                result.add_error("INTEGRITY", key, "Position missing portfolio_id")
                has_error = True

            if not pos.investment_id:
                result.add_error("INTEGRITY", key, "Position missing investment_id")
                has_error = True

            if pos.quantity is not None and pos.quantity < 0:
                result.add_error("INTEGRITY", key, "Position has negative quantity")
                has_error = True

            if not has_error:
                result.records_valid += 1

        # Check transaction integrity (2220-CHECK-TRANSACTION-INTEGRITY)
        transactions = self.db.query(Transaction).all()
        result.records_read += len(transactions)

        for txn in transactions:
            key = f"{txn.portfolio_id}/{txn.sequence_no}"
            has_error = False

            if not txn.portfolio_id:
                result.add_error("INTEGRITY", key, "Transaction missing portfolio_id")
                has_error = True

            if not txn.type:
                result.add_error("INTEGRITY", key, "Transaction missing type")
                has_error = True

            if txn.type in ("BU", "SL") and (txn.quantity is None or txn.quantity <= 0):
                result.add_error("INTEGRITY", key, "Buy/Sell transaction requires positive quantity")
                has_error = True

            if not has_error:
                result.records_valid += 1

        return result.to_dict()

    def _check_xref(self) -> Dict[str, Any]:
        """
        Cross-reference validation between positions, transactions, and portfolios.

        Mirrors COBOL 2300-CHECK-XREF:
        - 2310-CHECK-POSITION-XREF: Verify each position has a valid portfolio
        - 2320-CHECK-TRANSACTION-XREF: Verify each transaction references a valid portfolio
        """
        result = ValidationResult(VALIDATION_XREF)

        # Get all valid portfolio IDs
        portfolio_ids = {
            p.port_id for p in self.db.query(Portfolio.port_id).all()
        }

        # Check position cross-references (2310-CHECK-POSITION-XREF)
        positions = self.db.query(Position).all()
        result.records_read += len(positions)

        for pos in positions:
            key = f"{pos.portfolio_id}/{pos.investment_id}"
            if pos.portfolio_id not in portfolio_ids:
                result.add_error(
                    "XREF", key,
                    f"Position references non-existent portfolio: {pos.portfolio_id}"
                )
            else:
                result.records_valid += 1

        # Check transaction cross-references (2320-CHECK-TRANSACTION-XREF)
        transactions = self.db.query(Transaction).all()
        result.records_read += len(transactions)

        for txn in transactions:
            key = f"{txn.portfolio_id}/{txn.sequence_no}"
            if txn.portfolio_id not in portfolio_ids:
                result.add_error(
                    "XREF", key,
                    f"Transaction references non-existent portfolio: {txn.portfolio_id}"
                )
            else:
                result.records_valid += 1

        return result.to_dict()

    def _check_format(self) -> Dict[str, Any]:
        """
        Validate data formats and field constraints.

        Mirrors COBOL 2400-CHECK-FORMAT:
        - 2410-CHECK-POSITION-FORMAT: Verify position field formats
        - 2420-CHECK-TRANSACTION-FORMAT: Verify transaction field formats
        """
        result = ValidationResult(VALIDATION_FORMAT)

        valid_position_statuses = {"A", "C", "P"}
        valid_transaction_types = {"BU", "SL", "TR", "FE"}
        valid_transaction_statuses = {"P", "D", "F", "R"}

        # Check position formats (2410-CHECK-POSITION-FORMAT)
        positions = self.db.query(Position).all()
        result.records_read += len(positions)

        for pos in positions:
            key = f"{pos.portfolio_id}/{pos.investment_id}"
            has_error = False

            if pos.portfolio_id and len(pos.portfolio_id) != 8:
                result.add_error("FORMAT", key, "Portfolio ID must be 8 characters")
                has_error = True

            if pos.status and pos.status not in valid_position_statuses:
                result.add_error(
                    "FORMAT", key,
                    f"Invalid position status: {pos.status}. Must be one of {valid_position_statuses}"
                )
                has_error = True

            if pos.currency and len(pos.currency) != 3:
                result.add_error("FORMAT", key, "Currency must be 3 characters")
                has_error = True

            if not has_error:
                result.records_valid += 1

        # Check transaction formats (2420-CHECK-TRANSACTION-FORMAT)
        transactions = self.db.query(Transaction).all()
        result.records_read += len(transactions)

        for txn in transactions:
            key = f"{txn.portfolio_id}/{txn.sequence_no}"
            has_error = False

            if txn.type and txn.type not in valid_transaction_types:
                result.add_error(
                    "FORMAT", key,
                    f"Invalid transaction type: {txn.type}. Must be one of {valid_transaction_types}"
                )
                has_error = True

            if txn.status and txn.status not in valid_transaction_statuses:
                result.add_error(
                    "FORMAT", key,
                    f"Invalid transaction status: {txn.status}. Must be one of {valid_transaction_statuses}"
                )
                has_error = True

            if txn.sequence_no and len(txn.sequence_no) != 6:
                result.add_error("FORMAT", key, "Sequence number must be 6 characters")
                has_error = True

            if not has_error:
                result.records_valid += 1

        return result.to_dict()

    def _check_balance(self) -> Dict[str, Any]:
        """
        Verify balance reconciliation between positions and portfolio totals.

        Mirrors COBOL 2500-CHECK-BALANCE:
        - 2510-ACCUMULATE-POSITIONS: Sum up position values per portfolio
        - 2520-VERIFY-BALANCES: Compare accumulated totals against portfolio total_value
        """
        result = ValidationResult(VALIDATION_BALANCE)

        portfolios = self.db.query(Portfolio).filter(
            Portfolio.status == "A"
        ).all()
        result.records_read = len(portfolios)

        for portfolio in portfolios:
            key = f"{portfolio.port_id}/{portfolio.account_no}"

            # 2510-ACCUMULATE-POSITIONS: Sum position market values
            position_total = Decimal("0.00")
            positions = self.db.query(Position).filter(
                Position.portfolio_id == portfolio.port_id,
                Position.status == "A",
            ).all()

            for pos in positions:
                if pos.market_value:
                    position_total += pos.market_value

            # Add cash balance
            calculated_total = position_total + (portfolio.cash_balance or Decimal("0.00"))
            stored_total = portfolio.total_value or Decimal("0.00")

            result.total_amount += calculated_total
            result.control_total += stored_total

            # 2520-VERIFY-BALANCES: Compare totals
            difference = abs(calculated_total - stored_total)
            if difference > Decimal("0.01"):
                result.add_error(
                    "BALANCE", key,
                    f"Portfolio total mismatch: calculated={float(calculated_total):.2f}, "
                    f"stored={float(stored_total):.2f}, difference={float(difference):.2f}"
                )
            else:
                result.records_valid += 1

        return result.to_dict()

    def close(self) -> None:
        """Close database session if we created one."""
        if self._db is not None:
            self._db.close()
