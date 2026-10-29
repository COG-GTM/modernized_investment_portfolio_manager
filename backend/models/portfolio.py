from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PortfolioHolding(BaseModel):
    symbol: str
    name: str
    shares: int
    costBasis: float
    currentPrice: Optional[float]
    marketValue: Optional[float]
    gainLoss: Optional[float]
    gainLossPercent: Optional[float]


class PortfolioSummary(BaseModel):
    accountNumber: str
    totalValue: float
    totalGainLoss: float
    totalGainLossPercent: float
    holdings: List[PortfolioHolding]
    lastUpdated: str


class AccountValidationResponse(BaseModel):
    valid: bool
    message: str


class PortfolioValidationResponse(BaseModel):
    valid: bool
    message: str
    field: str


class ValidationErrorResponse(BaseModel):
    valid: bool
    errors: List[PortfolioValidationResponse]


class TransactionResponse(BaseModel):
    accountNumber: str
    transactions: List[dict]
    message: str
