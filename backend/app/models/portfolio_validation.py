"""
Portfolio Validation Rules data model.

Translated from COBOL copybook: src/copybook/common/PORTVAL.cpy

COBOL structures:
  - VAL-RETURN-CODES: validation return codes
  - VAL-ERROR-MESSAGES: validation error messages
  - VAL-CONSTANTS: validation constants (min/max amounts, ID prefix)
  - VAL-WORK-AREAS: working storage for validation
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PortfolioValidation(BaseModel):
    """Portfolio validation rules and error messages.

    Translated from COBOL copybook PORTVAL.cpy.

    Validation return codes:
      0 = Success, 1 = Invalid ID, 2 = Invalid Account,
      3 = Invalid Type, 4 = Invalid Amount
    """

    # VAL-RETURN-CODES
    val_success: int = Field(default=0, description="VAL-SUCCESS: PIC S9(4) VALUE +0")
    val_invalid_id: int = Field(default=1, description="VAL-INVALID-ID: PIC S9(4) VALUE +1")
    val_invalid_acct: int = Field(default=2, description="VAL-INVALID-ACCT: PIC S9(4) VALUE +2")
    val_invalid_type: int = Field(default=3, description="VAL-INVALID-TYPE: PIC S9(4) VALUE +3")
    val_invalid_amt: int = Field(default=4, description="VAL-INVALID-AMT: PIC S9(4) VALUE +4")

    # VAL-ERROR-MESSAGES
    val_err_id: str = Field(
        default="Invalid Portfolio ID format", max_length=50,
        description="VAL-ERR-ID: PIC X(50)"
    )
    val_err_acct: str = Field(
        default="Invalid Account Number format", max_length=50,
        description="VAL-ERR-ACCT: PIC X(50)"
    )
    val_err_type: str = Field(
        default="Invalid Investment Type", max_length=50,
        description="VAL-ERR-TYPE: PIC X(50)"
    )
    val_err_amt: str = Field(
        default="Amount outside valid range", max_length=50,
        description="VAL-ERR-AMT: PIC X(50)"
    )

    # VAL-CONSTANTS
    val_min_amount: Decimal = Field(
        default=Decimal("-9999999999999.99"),
        description="VAL-MIN-AMOUNT: PIC S9(13)V99 VALUE -9999999999999.99",
        decimal_places=2,
    )
    val_max_amount: Decimal = Field(
        default=Decimal("9999999999999.99"),
        description="VAL-MAX-AMOUNT: PIC S9(13)V99 VALUE +9999999999999.99",
        decimal_places=2,
    )
    val_id_prefix: str = Field(
        default="PORT", max_length=4,
        description="VAL-ID-PREFIX: PIC X(4) VALUE 'PORT'"
    )

    # VAL-WORK-AREAS
    val_numeric_check: str = Field(
        default="", max_length=10,
        description="VAL-NUMERIC-CHECK: PIC X(10)"
    )
    val_temp_num: Decimal = Field(
        default=Decimal("0.00"),
        description="VAL-TEMP-NUM: PIC S9(13)V99",
        decimal_places=2,
    )
    val_error_code: int = Field(
        default=0,
        description="VAL-ERROR-CODE: PIC S9(4)"
    )
    val_error_msg: str = Field(
        default="", max_length=50,
        description="VAL-ERROR-MSG: PIC X(50)"
    )

    def validate_portfolio_id(self, port_id: str) -> tuple[int, str]:
        """Validate a portfolio ID format.

        Returns (return_code, error_message).
        """
        if not port_id or len(port_id) > 8:
            return self.val_invalid_id, self.val_err_id
        if not port_id.startswith(self.val_id_prefix):
            return self.val_invalid_id, self.val_err_id
        return self.val_success, ""

    def validate_account_number(self, account_no: str) -> tuple[int, str]:
        """Validate an account number format.

        Returns (return_code, error_message).
        """
        if not account_no or len(account_no) != 10:
            return self.val_invalid_acct, self.val_err_acct
        if not account_no.isdigit():
            return self.val_invalid_acct, self.val_err_acct
        return self.val_success, ""

    def validate_amount(self, amount: Decimal) -> tuple[int, str]:
        """Validate that an amount is within the allowed range.

        Returns (return_code, error_message).
        """
        if amount < self.val_min_amount or amount > self.val_max_amount:
            return self.val_invalid_amt, self.val_err_amt
        return self.val_success, ""
