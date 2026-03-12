"""
Common definitions and constants.

Translated from COBOL copybook: src/copybook/common/COMMON.cpy
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ReturnCodeValues(BaseModel):
    """Standard return codes used across the system.

    Source: COMMON.cpy - RETURN-CODES (01 level)
    """

    success: int = Field(default=0, description="RC-SUCCESS: PIC S9(4) VALUE +0")
    warning: int = Field(default=4, description="RC-WARNING: PIC S9(4) VALUE +4")
    error: int = Field(default=8, description="RC-ERROR: PIC S9(4) VALUE +8")
    severe: int = Field(default=12, description="RC-SEVERE: PIC S9(4) VALUE +12")
    critical: int = Field(default=16, description="RC-CRITICAL: PIC S9(4) VALUE +16")


class StatusCodes(BaseModel):
    """Status codes used across the system.

    Source: COMMON.cpy - STATUS-CODES (01 level)
    """

    active: str = Field(default="A", max_length=1, description="STATUS-ACTIVE: PIC X(01) VALUE 'A'")
    closed: str = Field(default="C", max_length=1, description="STATUS-CLOSED: PIC X(01) VALUE 'C'")
    pending: str = Field(default="P", max_length=1, description="STATUS-PENDING: PIC X(01) VALUE 'P'")
    suspended: str = Field(default="S", max_length=1, description="STATUS-SUSPENDED: PIC X(01) VALUE 'S'")
    failed: str = Field(default="F", max_length=1, description="STATUS-FAILED: PIC X(01) VALUE 'F'")
    reversed: str = Field(default="R", max_length=1, description="STATUS-REVERSED: PIC X(01) VALUE 'R'")


class TransactionTypes(BaseModel):
    """Transaction type codes.

    Source: COMMON.cpy - TRANSACTION-TYPES (01 level)
    """

    buy: str = Field(default="BU", max_length=2, description="TRN-TYPE-BUY: PIC X(02) VALUE 'BU'")
    sell: str = Field(default="SL", max_length=2, description="TRN-TYPE-SELL: PIC X(02) VALUE 'SL'")
    transfer: str = Field(default="TR", max_length=2, description="TRN-TYPE-TRANSFER: PIC X(02) VALUE 'TR'")
    fee: str = Field(default="FE", max_length=2, description="TRN-TYPE-FEE: PIC X(02) VALUE 'FE'")


class CommonDatetime(BaseModel):
    """Common date/time fields.

    Source: COMMON.cpy - COMMON-DATETIME (01 level)
    """

    curr_year: str = Field(default="", max_length=4, description="CURR-YEAR: PIC X(04)")
    curr_month: str = Field(default="", max_length=2, description="CURR-MONTH: PIC X(02)")
    curr_day: str = Field(default="", max_length=2, description="CURR-DAY: PIC X(02)")
    curr_hour: str = Field(default="", max_length=2, description="CURR-HOUR: PIC X(02)")
    curr_minute: str = Field(default="", max_length=2, description="CURR-MINUTE: PIC X(02)")
    curr_second: str = Field(default="", max_length=2, description="CURR-SECOND: PIC X(02)")
    curr_msec: str = Field(default="", max_length=2, description="CURR-MSEC: PIC X(02)")


class CommonErrorHandling(BaseModel):
    """Common error handling fields.

    Source: COMMON.cpy - ERROR-HANDLING (01 level)
    """

    error_code: str = Field(default="", max_length=4, description="ERROR-CODE: PIC X(04)")
    error_module: str = Field(default="", max_length=8, description="ERROR-MODULE: PIC X(08)")
    error_routine: str = Field(default="", max_length=8, description="ERROR-ROUTINE: PIC X(08)")
    error_message: str = Field(default="", max_length=80, description="ERROR-MESSAGE: PIC X(80)")


class CommonAuditFields(BaseModel):
    """Common audit fields.

    Source: COMMON.cpy - AUDIT-FIELDS (01 level)
    """

    audit_timestamp: str = Field(default="", max_length=26, description="AUDIT-TIMESTAMP: PIC X(26)")
    audit_user: str = Field(default="", max_length=8, description="AUDIT-USER: PIC X(08)")
    audit_terminal: str = Field(default="", max_length=8, description="AUDIT-TERMINAL: PIC X(08)")
    audit_program: str = Field(default="", max_length=8, description="AUDIT-PROGRAM: PIC X(08)")


class CurrencyCodes(BaseModel):
    """Common currency codes.

    Source: COMMON.cpy - CURRENCY-CODES (01 level)
    """

    usd: str = Field(default="USD", max_length=3, description="CURR-USD: PIC X(03) VALUE 'USD'")
    eur: str = Field(default="EUR", max_length=3, description="CURR-EUR: PIC X(03) VALUE 'EUR'")
    gbp: str = Field(default="GBP", max_length=3, description="CURR-GBP: PIC X(03) VALUE 'GBP'")
    jpy: str = Field(default="JPY", max_length=3, description="CURR-JPY: PIC X(03) VALUE 'JPY'")
    cad: str = Field(default="CAD", max_length=3, description="CURR-CAD: PIC X(03) VALUE 'CAD'")


# Module-level constant instances for convenient access
RETURN_CODES = ReturnCodeValues()
STATUS_CODES = StatusCodes()
TRANSACTION_TYPES = TransactionTypes()
CURRENCY_CODES = CurrencyCodes()
