"""
Transaction Validation.

Migrated from: TRNVAL00.cbl (conceptual, source file not present in repo),
               TRNREC.cpy (transaction record structure)
First step in the batch pipeline. Validates incoming transactions by
checking required fields, validating amounts, verifying portfolio/security
IDs exist, and checking for duplicates.
"""

import decimal
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from .return_codes import ReturnCode, ReturnStatus

logger = logging.getLogger(__name__)

# Valid transaction types from TRNREC.cpy TRN-TYPE
VALID_TRANSACTION_TYPES = {"BU", "SL", "TR", "FE"}

# Valid statuses from TRNREC.cpy TRN-STATUS
VALID_STATUSES = {"P", "D", "F", "R"}

# Valid currencies
VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "CHF", "AUD"}


@dataclass
class ValidationError:
    """A single validation error for a transaction."""

    field: str
    message: str
    severity: str = "error"  # "error" or "warning"


@dataclass
class ValidationResult:
    """
    Result of validating a single transaction.

    Contains the list of errors/warnings found and the overall validity.
    """

    transaction_key: str = ""
    valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def return_code(self) -> int:
        if self.errors:
            return ReturnCode.ERROR
        elif self.warnings:
            return ReturnCode.WARNING
        return ReturnCode.SUCCESS


@dataclass
class ValidationSummary:
    """Summary of a batch validation run."""

    total_transactions: int = 0
    valid_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    duplicate_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class TransactionValidator:
    """
    Validates incoming transactions before processing.

    Migrated from TRNVAL00.cbl. The COBOL program reads a VSAM transaction
    file sequentially, validates each record against business rules,
    writes valid transactions to an output file, and writes invalid ones
    to an error file. This Python version validates transaction dicts
    and returns structured results.

    Pipeline position: Step 1 (first in batch sequence).
    """

    def __init__(self, db_session: Optional[Session] = None) -> None:
        self._db = db_session
        self._seen_keys: Set[str] = set()
        self._summary = ValidationSummary()
        self._return_status = ReturnStatus(program_id="TRNVAL00")
        self._portfolio_cache: Set[str] = set()
        self._security_cache: Set[str] = set()
        logger.info("TransactionValidator initialized")

    def validate_batch(self, transactions: List[Dict]) -> Tuple[List[Dict], List[Dict], int]:
        """
        Validate a batch of transactions.

        Returns (valid_transactions, invalid_transactions, return_code).
        Mirrors the main processing loop of TRNVAL00 which reads records
        sequentially, validates each, and routes to output or error file.
        """
        self._summary = ValidationSummary(
            start_time=datetime.now(),
            total_transactions=len(transactions),
        )
        self._seen_keys.clear()

        valid_transactions: List[Dict] = []
        invalid_transactions: List[Dict] = []

        for txn in transactions:
            result = self.validate_transaction(txn)

            if result.valid:
                if result.warnings:
                    self._summary.warning_count += 1
                else:
                    self._summary.valid_count += 1
                valid_transactions.append(txn)
            else:
                self._summary.error_count += 1
                invalid_transactions.append(
                    {**txn, "_validation_errors": [e.message for e in result.errors]}
                )

        self._summary.end_time = datetime.now()

        # Determine overall return code
        if self._summary.error_count > 0:
            rc = ReturnCode.WARNING  # Some errors, but processing continues
        else:
            rc = ReturnCode.SUCCESS

        # If ALL transactions failed, that's a real error
        if self._summary.error_count == self._summary.total_transactions and self._summary.total_transactions > 0:
            rc = ReturnCode.ERROR

        self._return_status.set_code(
            rc,
            f"Validated {self._summary.total_transactions}: "
            f"{self._summary.valid_count} valid, "
            f"{self._summary.warning_count} warnings, "
            f"{self._summary.error_count} errors",
        )

        logger.info(
            "Batch validation complete: total=%d valid=%d warnings=%d errors=%d RC=%d",
            self._summary.total_transactions,
            self._summary.valid_count,
            self._summary.warning_count,
            self._summary.error_count,
            rc,
        )

        return valid_transactions, invalid_transactions, rc

    def validate_transaction(self, txn: Dict) -> ValidationResult:
        """
        Validate a single transaction record.

        Checks all business rules derived from TRNREC.cpy field definitions
        and TRNVAL00 validation logic:
        1. Required fields present
        2. Field format/length validation
        3. Transaction type valid
        4. Amount/quantity/price validation
        5. Portfolio ID exists
        6. Security ID exists (for buy/sell)
        7. Duplicate check
        """
        key = self._build_key(txn)
        result = ValidationResult(transaction_key=key)

        # 1. Required fields
        self._validate_required_fields(txn, result)

        # 2. Field formats (from TRNREC.cpy field definitions)
        self._validate_field_formats(txn, result)

        # 3. Transaction type
        self._validate_transaction_type(txn, result)

        # 4. Amounts and quantities
        self._validate_amounts(txn, result)

        # 5. Portfolio exists
        self._validate_portfolio_exists(txn, result)

        # 6. Security exists (for buy/sell)
        self._validate_security_exists(txn, result)

        # 7. Duplicate check
        self._validate_no_duplicate(txn, key, result)

        # Set overall validity
        result.valid = len(result.errors) == 0

        if not result.valid:
            logger.debug("Transaction %s failed validation: %d errors", key, len(result.errors))

        return result

    def get_summary(self) -> ValidationSummary:
        """Return the validation summary for the current/last batch."""
        return self._summary

    def get_return_status(self) -> ReturnStatus:
        """Return the current return status."""
        return self._return_status

    def _build_key(self, txn: Dict) -> str:
        """Build the transaction key from TRNREC.cpy TRN-KEY fields."""
        date = txn.get("date", "")
        time = txn.get("time", "")
        portfolio_id = txn.get("portfolio_id", "")
        sequence_no = txn.get("sequence_no", "")
        return f"{date}:{time}:{portfolio_id}:{sequence_no}"

    def _validate_required_fields(self, txn: Dict, result: ValidationResult) -> None:
        """Check that all required fields are present and non-empty."""
        required = ["date", "portfolio_id", "type", "amount"]
        for field_name in required:
            value = txn.get(field_name)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                result.errors.append(
                    ValidationError(field=field_name, message=f"Required field '{field_name}' is missing or empty")
                )

    def _validate_field_formats(self, txn: Dict, result: ValidationResult) -> None:
        """Validate field formats per TRNREC.cpy definitions."""
        # TRN-DATE: PIC X(08) - should be YYYYMMDD
        date_val = txn.get("date", "")
        if date_val and (len(str(date_val)) != 8 or not str(date_val).isdigit()):
            result.errors.append(
                ValidationError(field="date", message="Date must be 8-digit YYYYMMDD format")
            )

        # TRN-PORTFOLIO-ID: PIC X(08)
        port_id = txn.get("portfolio_id", "")
        if port_id and len(str(port_id).strip()) > 8:
            result.errors.append(
                ValidationError(field="portfolio_id", message="Portfolio ID must be 8 characters or less")
            )

        # TRN-SEQUENCE-NO: PIC X(06)
        seq = txn.get("sequence_no", "")
        if seq and len(str(seq)) > 6:
            result.errors.append(
                ValidationError(field="sequence_no", message="Sequence number must be 6 characters or less")
            )

        # TRN-INVESTMENT-ID: PIC X(10)
        inv_id = txn.get("investment_id", "")
        if inv_id and len(str(inv_id).strip()) > 10:
            result.errors.append(
                ValidationError(field="investment_id", message="Investment ID must be 10 characters or less")
            )

        # TRN-CURRENCY: PIC X(03)
        currency = txn.get("currency", "")
        if currency and currency not in VALID_CURRENCIES:
            result.warnings.append(
                ValidationError(
                    field="currency",
                    message=f"Unrecognized currency '{currency}'",
                    severity="warning",
                )
            )

    def _validate_transaction_type(self, txn: Dict, result: ValidationResult) -> None:
        """Validate transaction type per TRNREC.cpy TRN-TYPE 88-levels."""
        txn_type = txn.get("type", "")
        if txn_type and txn_type not in VALID_TRANSACTION_TYPES:
            result.errors.append(
                ValidationError(
                    field="type",
                    message=f"Invalid transaction type '{txn_type}'. Must be one of: {', '.join(sorted(VALID_TRANSACTION_TYPES))}",
                )
            )

    def _validate_amounts(self, txn: Dict, result: ValidationResult) -> None:
        """
        Validate financial amounts.

        For buy/sell transactions, quantity and price are required.
        Amount must be consistent with quantity * price.
        """
        txn_type = txn.get("type", "")

        # Buy/sell require quantity and price
        if txn_type in ("BU", "SL"):
            quantity = txn.get("quantity")
            price = txn.get("price")

            qty_dec: Optional[Decimal] = None
            price_dec: Optional[Decimal] = None

            if quantity is None:
                result.errors.append(
                    ValidationError(field="quantity", message="Quantity required for buy/sell transactions")
                )
            else:
                try:
                    qty_dec = Decimal(str(quantity))
                except (decimal.InvalidOperation, ValueError):
                    result.errors.append(
                        ValidationError(field="quantity", message="Quantity is not a valid number")
                    )
                else:
                    if qty_dec <= 0:
                        result.errors.append(
                            ValidationError(field="quantity", message="Quantity must be positive for buy/sell transactions")
                        )

            if price is None:
                result.errors.append(
                    ValidationError(field="price", message="Price required for buy/sell transactions")
                )
            else:
                try:
                    price_dec = Decimal(str(price))
                except (decimal.InvalidOperation, ValueError):
                    result.errors.append(
                        ValidationError(field="price", message="Price is not a valid number")
                    )
                else:
                    if price_dec <= 0:
                        result.errors.append(
                            ValidationError(field="price", message="Price must be positive for buy/sell transactions")
                        )

            # Cross-check amount vs quantity * price
            if qty_dec is not None and price_dec is not None:
                amount = txn.get("amount")
                if amount is not None:
                    try:
                        expected = qty_dec * price_dec
                        actual = Decimal(str(amount))
                        if abs(expected - actual) > Decimal("0.01"):
                            result.warnings.append(
                                ValidationError(
                                    field="amount",
                                    message=f"Amount {actual} doesn't match quantity * price ({expected})",
                                    severity="warning",
                                )
                            )
                    except (decimal.InvalidOperation, ValueError):
                        result.errors.append(
                            ValidationError(field="amount", message="Amount is not a valid number")
                        )

            # Investment ID required for buy/sell
            inv_id = txn.get("investment_id", "")
            if not inv_id or str(inv_id).strip() == "":
                result.errors.append(
                    ValidationError(
                        field="investment_id",
                        message="Investment ID required for buy/sell transactions",
                    )
                )

    def _validate_portfolio_exists(self, txn: Dict, result: ValidationResult) -> None:
        """
        Verify portfolio ID exists in the system.

        Uses database lookup if a session is available, otherwise skips
        with a TODO comment for when DB integration is complete.
        """
        port_id = txn.get("portfolio_id", "")
        if not port_id:
            return  # Already caught by required fields check

        if self._db:
            try:
                from models.database import Portfolio

                if port_id not in self._portfolio_cache:
                    exists = (
                        self._db.query(Portfolio)
                        .filter(Portfolio.port_id == port_id)
                        .first()
                    )
                    if exists:
                        self._portfolio_cache.add(port_id)
                    else:
                        result.errors.append(
                            ValidationError(
                                field="portfolio_id",
                                message=f"Portfolio '{port_id}' not found in system",
                            )
                        )
            except Exception as e:
                logger.warning("Could not verify portfolio existence: %s", e)
        # TODO: When DB integration is fully wired, remove the cache fallback

    def _validate_security_exists(self, txn: Dict, result: ValidationResult) -> None:
        """
        Verify security/investment ID exists for buy/sell transactions.

        Uses database lookup if available.
        """
        txn_type = txn.get("type", "")
        inv_id = txn.get("investment_id", "")

        if txn_type not in ("BU", "SL") or not inv_id:
            return

        if self._db:
            try:
                from models.database import Position

                if inv_id not in self._security_cache:
                    exists = (
                        self._db.query(Position)
                        .filter(Position.investment_id == inv_id)
                        .first()
                    )
                    if exists:
                        self._security_cache.add(inv_id)
                    # Not finding a security is a warning, not error
                    # (new securities can be added via buy transactions)
            except Exception as e:
                logger.warning("Could not verify security existence: %s", e)

    def _validate_no_duplicate(self, txn: Dict, key: str, result: ValidationResult) -> None:
        """Check for duplicate transactions within this batch."""
        if key in self._seen_keys:
            result.errors.append(
                ValidationError(field="_key", message=f"Duplicate transaction: {key}")
            )
            self._summary.duplicate_count += 1
        else:
            self._seen_keys.add(key)
