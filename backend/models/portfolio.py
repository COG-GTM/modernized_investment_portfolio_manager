from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PortfolioHolding(BaseModel):
    symbol: str
    name: str
    shares: int
    currentPrice: float
    marketValue: float
    gainLoss: float
    gainLossPercent: float


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


class PortfolioPositionData(BaseModel):
    investment_id: str
    quantity: float
    cost_basis: float
    market_value: float
    currency: str
    status: str


class PortfolioPositionsResponse(BaseModel):
    portfolio_id: str
    positions: List[PortfolioPositionData]


class TransferRequest(BaseModel):
    sourcePortfolioId: str
    destPortfolioId: str
    investmentId: str
    quantity: float
    user: str


class TransferResponse(BaseModel):
    success: bool
    sourcePortfolioId: str
    destPortfolioId: str
    investmentId: str
    quantity: float
    transactionId: Optional[str] = None
    errors: List[str] = []
    message: str
