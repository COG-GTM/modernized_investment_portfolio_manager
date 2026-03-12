"""
Position Record data model.

Translated from COBOL copybook: src/copybook/common/POSREC.cpy

COBOL structure: POSITION-RECORD (01 level)
  - POS-KEY: composite key (portfolio_id, date, investment_id)
  - POS-DATA: position details (quantity, cost basis, market value)
  - POS-AUDIT: audit trail fields
  - POS-FILLER: reserved space (PIC X(50))
"""

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PositionRecord(BaseModel):
    """Portfolio position record.

    Translated from COBOL copybook POSREC.cpy.
    Maps to POSITION-RECORD (01 level).

    Position statuses (88-level values):
      A = Active, C = Closed, P = Pending
    """

    # POS-KEY fields
    pos_portfolio_id: str = Field(
        ..., max_length=8,
        description="POS-PORTFOLIO-ID: Portfolio identifier - PIC X(08)"
    )
    pos_date: str = Field(
        ..., max_length=8,
        description="POS-DATE: Position date YYYYMMDD - PIC X(08)"
    )
    pos_investment_id: str = Field(
        ..., max_length=10,
        description="POS-INVESTMENT-ID: Investment identifier - PIC X(10)"
    )

    # POS-DATA fields
    pos_quantity: Decimal = Field(
        ...,
        description="POS-QUANTITY: Holding quantity - PIC S9(11)V9(4) COMP-3",
        decimal_places=4,
    )
    pos_cost_basis: Decimal = Field(
        ...,
        description="POS-COST-BASIS: Total cost basis - PIC S9(13)V9(2) COMP-3",
        decimal_places=2,
    )
    pos_market_value: Decimal = Field(
        ...,
        description="POS-MARKET-VALUE: Current market value - PIC S9(13)V9(2) COMP-3",
        decimal_places=2,
    )
    pos_currency: str = Field(
        default="USD", max_length=3,
        description="POS-CURRENCY: Currency code - PIC X(03)"
    )
    pos_status: Literal["A", "C", "P"] = Field(
        default="A",
        description="POS-STATUS: A=Active, C=Closed, P=Pending - PIC X(01)"
    )

    # POS-AUDIT fields
    pos_last_maint_date: str = Field(
        default="", max_length=26,
        description="POS-LAST-MAINT-DATE: Last maintenance timestamp - PIC X(26)"
    )
    pos_last_maint_user: str = Field(
        default="", max_length=8,
        description="POS-LAST-MAINT-USER: Last maintenance user ID - PIC X(08)"
    )

    @field_validator("pos_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if v and len(v) != 8:
            raise ValueError("Position date must be 8 characters (YYYYMMDD)")
        return v

    def calculate_gain_loss(self) -> Decimal:
        """Calculate unrealized gain/loss for this position."""
        return self.pos_market_value - self.pos_cost_basis

    def calculate_gain_loss_percent(self) -> Decimal:
        """Calculate gain/loss as a percentage of cost basis."""
        if self.pos_cost_basis == 0:
            return Decimal("0.00")
        return (self.calculate_gain_loss() / self.pos_cost_basis) * 100
