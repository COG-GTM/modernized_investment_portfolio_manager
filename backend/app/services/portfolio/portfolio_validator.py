"""
Portfolio Validation Subroutine - Migrated from COBOL PORTVALD.cbl

Validates portfolio data elements:
- Portfolio ID: Must start with 'PORT' followed by numeric digits
- Account number: Must be 10 numeric digits, not all zeros
- Investment type: Must be valid value (STK, BND, MMF, ETF)
- Amount: Must be within valid range

The COBOL program was a subroutine called via CALL with a LINKAGE
SECTION validation request containing:
- LS-VALIDATE-TYPE: 'I'=ID, 'A'=Account, 'T'=Type, 'M'=Amount
- LS-INPUT-VALUE: The value to validate (PIC X(50))
- LS-RETURN-CODE: Success (0) or specific error code
- LS-ERROR-MSG: Descriptive error message

It used EVALUATE TRUE on the validate type to dispatch to the
appropriate validation paragraph.
"""

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Validation return codes (from COBOL PORTVAL copybook)
VAL_SUCCESS = 0
VAL_INVALID_ID = 4
VAL_INVALID_ACCT = 8
VAL_INVALID_TYPE = 12
VAL_INVALID_AMT = 16

# Validation constants (from COBOL PORTVAL copybook)
VAL_ID_PREFIX = "PORT"
VAL_MIN_AMOUNT = Decimal("-9999999999999.99")
VAL_MAX_AMOUNT = Decimal("9999999999999.99")

# Valid values
VALID_INVESTMENT_TYPES = {"STK", "BND", "MMF", "ETF"}
VALID_PORTFOLIO_STATUSES = {"A", "C", "S"}
VALID_CLIENT_TYPES = {"I", "C", "T"}

# Error messages (from COBOL PORTVAL copybook)
ERR_ID = "Invalid Portfolio ID format"
ERR_ACCT = "Invalid Account Number"
ERR_TYPE = "Invalid Investment Type"
ERR_AMT = "Amount out of valid range"


class PortfolioValidator:
    """
    Portfolio validation service.

    Migrated from COBOL PORTVALD which was a callable subroutine
    that validated individual portfolio data fields. The COBOL
    version used PROCEDURE DIVISION USING LS-VALIDATION-REQUEST
    and dispatched based on LS-VALIDATE-TYPE.
    """

    def validate_id(self, portfolio_id: str) -> Tuple[int, str]:
        """
        Validate portfolio ID format.

        Mirrors COBOL 1000-VALIDATE-ID:
        - Portfolio ID must start with 'PORT' (VAL-ID-PREFIX)
        - Remaining characters must be numeric (VAL-NUMERIC-CHECK IS NUMERIC)

        The COBOL checked LS-INPUT-VALUE(1:4) NOT = VAL-ID-PREFIX
        and LS-INPUT-VALUE(5:4) IS NOT NUMERIC.

        Args:
            portfolio_id: The portfolio ID to validate

        Returns:
            Tuple of (return_code, error_message)
        """
        if not portfolio_id:
            return VAL_INVALID_ID, ERR_ID

        if not portfolio_id.startswith(VAL_ID_PREFIX):
            return VAL_INVALID_ID, ERR_ID

        # Check remaining characters are numeric (mirrors COBOL VAL-NUMERIC-CHECK)
        numeric_part = portfolio_id[len(VAL_ID_PREFIX):]
        if not numeric_part or not numeric_part.isdigit():
            return VAL_INVALID_ID, ERR_ID

        return VAL_SUCCESS, ""

    def validate_account(self, account_number: str) -> Tuple[int, str]:
        """
        Validate account number format.

        Mirrors COBOL 2000-VALIDATE-ACCOUNT:
        - Account number must be numeric (LS-INPUT-VALUE IS NOT NUMERIC)
        - Account number must not be all zeros (LS-INPUT-VALUE = ZEROS)

        The COBOL version checked for 10 numeric digits.

        Args:
            account_number: The account number to validate

        Returns:
            Tuple of (return_code, error_message)
        """
        if not account_number:
            return VAL_INVALID_ACCT, ERR_ACCT

        if not account_number.isdigit():
            return VAL_INVALID_ACCT, ERR_ACCT

        if len(account_number) != 10:
            return VAL_INVALID_ACCT, "Account number must be 10 digits"

        if account_number == "0" * 10:
            return VAL_INVALID_ACCT, ERR_ACCT

        return VAL_SUCCESS, ""

    def validate_type(self, investment_type: str) -> Tuple[int, str]:
        """
        Validate investment type.

        Mirrors COBOL 3000-VALIDATE-TYPE:
        - Investment type must be one of: 'STK', 'BND', 'MMF', 'ETF'

        The COBOL version checked:
        IF LS-INPUT-VALUE NOT = 'STK'
           AND NOT = 'BND'
           AND NOT = 'MMF'
           AND NOT = 'ETF'

        Args:
            investment_type: The investment type to validate

        Returns:
            Tuple of (return_code, error_message)
        """
        if not investment_type:
            return VAL_INVALID_TYPE, ERR_TYPE

        if investment_type not in VALID_INVESTMENT_TYPES:
            return VAL_INVALID_TYPE, ERR_TYPE

        return VAL_SUCCESS, ""

    def validate_amount(self, amount: Union[str, float, Decimal]) -> Tuple[int, str]:
        """
        Validate amount is within valid range.

        Mirrors COBOL 4000-VALIDATE-AMOUNT:
        - Move LS-INPUT-VALUE to VAL-TEMP-NUM
        - Check VAL-TEMP-NUM < VAL-MIN-AMOUNT OR VAL-TEMP-NUM > VAL-MAX-AMOUNT

        The valid range is -9,999,999,999,999.99 to +9,999,999,999,999.99
        (from COBOL PIC S9(13)V99).

        Args:
            amount: The amount to validate

        Returns:
            Tuple of (return_code, error_message)
        """
        if amount is None:
            return VAL_INVALID_AMT, "Amount is required"

        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError):
            return VAL_INVALID_AMT, "Amount must be a valid number"

        if decimal_amount < VAL_MIN_AMOUNT or decimal_amount > VAL_MAX_AMOUNT:
            return VAL_INVALID_AMT, ERR_AMT

        return VAL_SUCCESS, ""

    def validate_portfolio_data(
        self,
        port_id: str,
        account_no: str,
        client_name: Optional[str] = None,
        client_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate all portfolio data fields for creation or update.

        Mirrors COBOL PORTMSTR 2100-VALIDATE-PORTFOLIO which checked:
        - PORT-ID(1:4) NOT = 'PORT' OR PORT-ID(5:5) IS NOT NUMERIC
        - PORT-NAME = SPACES
        - PORT-STATUS not in VALID-STATUS ('A', 'I', 'C')

        And PORTADD 2100-VALIDATE-AND-ADD which checked:
        - PORT-ID EQUAL SPACES
        - PORT-CLIENT-NAME EQUAL SPACES
        - PORT-STATUS NOT EQUAL 'A' (for new portfolios)

        Args:
            port_id: Portfolio ID
            account_no: Account number
            client_name: Client name
            client_type: Client type
            status: Portfolio status

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors: List[str] = []

        # Validate portfolio ID
        rc, msg = self.validate_id(port_id)
        if rc != VAL_SUCCESS:
            errors.append(msg)

        # Validate account number
        rc, msg = self.validate_account(account_no)
        if rc != VAL_SUCCESS:
            errors.append(msg)

        # Validate client name (mirrors COBOL: PORT-NAME = SPACES check)
        if client_name is not None and (not client_name or client_name.isspace()):
            errors.append("Portfolio Name is required")

        # Validate client type
        if client_type is not None and client_type not in VALID_CLIENT_TYPES:
            errors.append(f"Invalid client type: {client_type}. Must be one of {VALID_CLIENT_TYPES}")

        # Validate status (mirrors COBOL: VALID-STATUS VALUE 'A' 'I' 'C')
        if status is not None and status not in VALID_PORTFOLIO_STATUSES:
            errors.append(f"Invalid Portfolio Status: {status}. Must be one of {VALID_PORTFOLIO_STATUSES}")

        return len(errors) == 0, errors

    def validate(self, validate_type: str, input_value: str) -> Tuple[int, str]:
        """
        Single-field validation dispatcher.

        Mirrors the COBOL PORTVALD main EVALUATE TRUE block:
        - LS-VAL-ID ('I') -> 1000-VALIDATE-ID
        - LS-VAL-ACCT ('A') -> 2000-VALIDATE-ACCOUNT
        - LS-VAL-TYPE ('T') -> 3000-VALIDATE-TYPE
        - LS-VAL-AMT ('M') -> 4000-VALIDATE-AMOUNT
        - OTHER -> Invalid validation type

        Args:
            validate_type: 'I'=ID, 'A'=Account, 'T'=Type, 'M'=Amount
            input_value: The value to validate

        Returns:
            Tuple of (return_code, error_message)
        """
        dispatch = {
            "I": self.validate_id,
            "A": self.validate_account,
            "T": self.validate_type,
            "M": self.validate_amount,
        }

        handler = dispatch.get(validate_type)
        if handler is None:
            return VAL_INVALID_ID, "Invalid validation type"

        return handler(input_value)
