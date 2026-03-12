"""
Transaction Record data model.

Translated from COBOL copybook: src/copybook/common/TRNREC.cpy

COBOL structure: TRANSACTION-RECORD (01 level)
  - TRN-KEY: composite key (date, time, portfolio_id, sequence_no)
  - TRN-DATA: transaction details
  - TRN-AUDIT: audit trail fields
  - TRN-FILLER: reserved space (PIC X(50))
"""

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator


class TransactionRecord(BaseModel):
    """Investment transaction record.

    Translated from COBOL copybook TRNREC.cpy.
    Maps to TRANSACTION-RECORD (01 level).

    Transaction types (88-level values):
      BU = Buy, SL = Sell, TR = Transfer, FE = Fee

    Transaction statuses (88-level values):
      P = Pending, D = Done, F = Failed, R = Reversed
    """

    # TRN-KEY fields
    trn_date: str = Field(
        ..., max_length=8,
        description="TRN-DATE: Transaction date YYYYMMDD - PIC X(08)"
    )
    trn_time: str = Field(
        ..., max_length=6,
        description="TRN-TIME: Transaction time HHMMSS - PIC X(06)"
    )
    trn_portfolio_id: str = Field(
        ..., max_length=8,
        description="TRN-PORTFOLIO-ID: Portfolio identifier - PIC X(08)"
    )
    trn_sequence_no: str = Field(
        ..., max_length=6,
        description="TRN-SEQUENCE-NO: Sequence number - PIC X(06)"
    )

    # TRN-DATA fields
    trn_investment_id: str = Field(
        ..., max_length=10,
        description="TRN-INVESTMENT-ID: Investment identifier - PIC X(10)"
    )
    trn_type: Literal["BU", "SL", "TR", "FE"] = Field(
        ...,
        description="TRN-TYPE: BU=Buy, SL=Sell, TR=Transfer, FE=Fee - PIC X(02)"
    )
    trn_quantity: Decimal = Field(
        ...,
        description="TRN-QUANTITY: Transaction quantity - PIC S9(11)V9(4) COMP-3",
        decimal_places=4,
    )
    trn_price: Decimal = Field(
        ...,
        description="TRN-PRICE: Transaction price - PIC S9(11)V9(4) COMP-3",
        decimal_places=4,
    )
    trn_amount: Decimal = Field(
        ...,
        description="TRN-AMOUNT: Transaction amount - PIC S9(13)V9(2) COMP-3",
        decimal_places=2,
    )
    trn_currency: str = Field(
        default="USD", max_length=3,
        description="TRN-CURRENCY: Currency code - PIC X(03)"
    )
    trn_status: Literal["P", "D", "F", "R"] = Field(
        default="P",
        description="TRN-STATUS: P=Pending, D=Done, F=Failed, R=Reversed - PIC X(01)"
    )

    # TRN-AUDIT fields
    trn_process_date: str = Field(
        default="", max_length=26,
        description="TRN-PROCESS-DATE: Processing timestamp - PIC X(26)"
    )
    trn_process_user: str = Field(
        default="", max_length=8,
        description="TRN-PROCESS-USER: Processing user ID - PIC X(08)"
    )

    @validator("trn_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if v and len(v) != 8:
            raise ValueError("Transaction date must be 8 characters (YYYYMMDD)")
        return v

    @validator("trn_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if v and len(v) != 6:
            raise ValueError("Transaction time must be 6 characters (HHMMSS)")
        return v
