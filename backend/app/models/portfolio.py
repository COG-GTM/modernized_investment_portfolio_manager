"""
Portfolio Master Record data model.

Translated from COBOL copybook: src/copybook/common/PORTFLIO.cpy

COBOL structure: PORT-RECORD (01 level)
  - PORT-KEY: composite key (port_id, account_no)
  - PORT-CLIENT-INFO: client details
  - PORT-PORTFOLIO-INFO: portfolio metadata
  - PORT-FINANCIAL-INFO: financial totals
  - PORT-AUDIT-INFO: audit trail fields
  - PORT-FILLER: reserved space (PIC X(50))
"""

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Portfolio(BaseModel):
    """Portfolio master record.

    Translated from COBOL copybook PORTFLIO.cpy.
    Maps to PORT-RECORD (01 level).

    Client types (88-level values):
      I = Individual, C = Corporate, T = Trust

    Portfolio statuses (88-level values):
      A = Active, C = Closed, S = Suspended
    """

    # PORT-KEY fields
    port_id: str = Field(
        ..., max_length=8,
        description="PORT-ID: Portfolio identifier - PIC X(8)"
    )
    port_account_no: str = Field(
        ..., max_length=10,
        description="PORT-ACCOUNT-NO: Account number - PIC X(10)"
    )

    # PORT-CLIENT-INFO fields
    port_client_name: str = Field(
        default="", max_length=30,
        description="PORT-CLIENT-NAME: Client name - PIC X(30)"
    )
    port_client_type: Literal["I", "C", "T"] = Field(
        ...,
        description="PORT-CLIENT-TYPE: I=Individual, C=Corporate, T=Trust - PIC X(1)"
    )

    # PORT-PORTFOLIO-INFO fields
    port_create_date: str = Field(
        default="", max_length=8,
        description="PORT-CREATE-DATE: Creation date YYYYMMDD - PIC 9(8)"
    )
    port_last_maint: str = Field(
        default="", max_length=8,
        description="PORT-LAST-MAINT: Last maintenance date YYYYMMDD - PIC 9(8)"
    )
    port_status: Literal["A", "C", "S"] = Field(
        default="A",
        description="PORT-STATUS: A=Active, C=Closed, S=Suspended - PIC X(1)"
    )

    # PORT-FINANCIAL-INFO fields
    port_total_value: Decimal = Field(
        default=Decimal("0.00"),
        description="PORT-TOTAL-VALUE: Total portfolio value - PIC S9(13)V99 COMP-3",
        decimal_places=2,
    )
    port_cash_balance: Decimal = Field(
        default=Decimal("0.00"),
        description="PORT-CASH-BALANCE: Cash balance - PIC S9(13)V99 COMP-3",
        decimal_places=2,
    )

    # PORT-AUDIT-INFO fields
    port_last_user: str = Field(
        default="", max_length=8,
        description="PORT-LAST-USER: Last update user ID - PIC X(8)"
    )
    port_last_trans: str = Field(
        default="", max_length=8,
        description="PORT-LAST-TRANS: Last transaction date - PIC 9(8)"
    )

    @field_validator("port_account_no")
    @classmethod
    def validate_account_no(cls, v: str) -> str:
        if v and len(v) != 10:
            raise ValueError("Account number must be exactly 10 characters")
        return v

    @field_validator("port_id")
    @classmethod
    def validate_port_id(cls, v: str) -> str:
        if v and len(v) > 8:
            raise ValueError("Portfolio ID must be at most 8 characters")
        return v
