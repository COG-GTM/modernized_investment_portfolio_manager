from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


class PositionBase(BaseModel):
    portfolio_id: str
    date: date
    investment_id: str
    currency: Optional[str] = "USD"
    status: Optional[str] = "A"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("A", "C", "P"):
            raise ValueError("status must be one of: A, C, P")
        return v


class PositionCreate(PositionBase):
    quantity: Decimal = Decimal("0.0000")
    cost_basis: Decimal = Decimal("0.00")
    market_value: Decimal = Decimal("0.00")


class PositionRead(PositionBase):
    model_config = ConfigDict(from_attributes=True)

    quantity: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    last_maint_date: Optional[datetime] = None
    last_maint_user: Optional[str] = None
