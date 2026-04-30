from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal
from datetime import date
from typing import Optional, List
from .position import PositionRead


class PortfolioBase(BaseModel):
    port_id: str
    account_no: str
    client_name: Optional[str] = None
    client_type: Optional[str] = None
    status: Optional[str] = None

    @field_validator("client_type")
    @classmethod
    def validate_client_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("I", "C", "T"):
            raise ValueError("client_type must be one of: I, C, T")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("A", "C", "S"):
            raise ValueError("status must be one of: A, C, S")
        return v


class PortfolioCreate(PortfolioBase):
    cash_balance: Decimal = Decimal("0.00")


class PortfolioRead(PortfolioBase):
    model_config = ConfigDict(from_attributes=True)

    create_date: Optional[date] = None
    last_maint: Optional[date] = None
    total_value: Optional[Decimal] = None
    cash_balance: Optional[Decimal] = None
    last_user: Optional[str] = None
    last_trans: Optional[str] = None


class PortfolioHolding(BaseModel):
    symbol: str
    name: str
    shares: int
    currentPrice: float
    marketValue: float
    gainLoss: float
    gainLossPercent: float


class PortfolioSummary(PortfolioRead):
    """Extended read model that includes nested positions."""
    positions: list[PositionRead] = []


class MockPortfolioSummary(BaseModel):
    """Portfolio summary used by the mock router endpoints."""
    accountNumber: str
    totalValue: float
    totalGainLoss: float
    totalGainLossPercent: float
    holdings: List[PortfolioHolding]
    lastUpdated: str
