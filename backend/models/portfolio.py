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


class CreatePortfolioRequest(BaseModel):
    port_id: str
    account_no: str
    client_name: str
    client_type: str
    cash_balance: float = 0.0


class CreatePortfolioResponse(BaseModel):
    port_id: str
    account_no: str
    client_name: str
    client_type: str
    status: str
    cash_balance: float
    total_value: float
    create_date: Optional[str] = None
    last_maint: Optional[str] = None


class AddPositionRequest(BaseModel):
    investment_id: str
    quantity: float
    cost_basis: float
    currency: str = "USD"


class PositionResponse(BaseModel):
    portfolio_id: str
    date: Optional[str] = None
    investment_id: str
    quantity: float
    cost_basis: float
    market_value: float
    currency: str
    status: str
    gain_loss: float
    gain_loss_percent: float


class CreateTransactionRequest(BaseModel):
    portfolio_id: str
    investment_id: Optional[str] = None
    type: str
    quantity: Optional[float] = None
    price: Optional[float] = None
    currency: str = "USD"


class TransactionDBResponse(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    portfolio_id: str
    sequence_no: str
    investment_id: Optional[str] = None
    type: str
    quantity: float
    price: float
    amount: float
    currency: Optional[str] = None
    status: str
    process_date: Optional[str] = None
    process_user: Optional[str] = None


class UpdateTransactionStatusRequest(BaseModel):
    new_status: str
    user: str


class PortfolioPerformanceResponse(BaseModel):
    total_value: float
    total_cost_basis: float
    total_gain_loss: float
    positions_count: int
    active_positions: int
    cash_balance: float
