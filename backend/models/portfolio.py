from pydantic import BaseModel, field_validator
from typing import List
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


class PortfolioUpdateRequest(BaseModel):
    portfolio_id: str
    account_no: str
    user: str = "SYSTEM"


class StatusUpdateRequest(PortfolioUpdateRequest):
    new_status: str
    
    @field_validator('new_status')
    def validate_status(cls, v):
        if v not in ['A', 'C', 'S']:
            raise ValueError('Status must be A, C, or S')
        return v


class ClientNameUpdateRequest(PortfolioUpdateRequest):
    new_client_name: str
    
    @field_validator('new_client_name')
    def validate_client_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Client name cannot be empty')
        if len(v) > 30:
            raise ValueError('Client name cannot exceed 30 characters')
        return v.strip()


class ValueUpdateRequest(PortfolioUpdateRequest):
    new_total_value: float
    
    @field_validator('new_total_value')
    def validate_value(cls, v):
        from validation.portfolio import validate_amount
        is_valid, message = validate_amount(v)
        if not is_valid:
            raise ValueError(message)
        return v


class PortfolioUpdateResponse(BaseModel):
    success: bool
    message: str
    portfolio_id: str = None
    errors: List[str] = []
