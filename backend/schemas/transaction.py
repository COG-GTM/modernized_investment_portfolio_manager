from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from decimal import Decimal
from datetime import date, time, datetime
from typing import Optional


class TransactionBase(BaseModel):
    portfolio_id: str
    investment_id: Optional[str] = None
    type: str
    currency: Optional[str] = "USD"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("BU", "SL", "TR", "FE"):
            raise ValueError("type must be one of: BU, SL, TR, FE")
        return v


class TransactionCreate(TransactionBase):
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Optional[Decimal] = None

    @model_validator(mode="after")
    def validate_buy_sell_fields(self) -> "TransactionCreate":
        if self.type in ("BU", "SL"):
            if not self.investment_id:
                raise ValueError("investment_id required for buy/sell transactions")
            if not self.quantity or self.quantity <= 0:
                raise ValueError("positive quantity required for buy/sell transactions")
            if not self.price or self.price <= 0:
                raise ValueError("positive price required for buy/sell transactions")
        return self


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    date: Optional[date] = None
    time: Optional[time] = None
    sequence_no: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None
    process_date: Optional[datetime] = None
    process_user: Optional[str] = None
