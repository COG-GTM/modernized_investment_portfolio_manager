from pydantic import BaseModel
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
    account_number: str
    action_code: str
    new_value: str
    user: str = "SYSTEM"


class PortfolioStatusUpdateRequest(BaseModel):
    portfolio_id: str
    account_number: str
    status: str
    user: str = "SYSTEM"
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "PORT0001",
                "account_number": "1234567890",
                "status": "A",
                "user": "ADMIN"
            }
        }


class PortfolioNameUpdateRequest(BaseModel):
    portfolio_id: str
    account_number: str
    client_name: str
    user: str = "SYSTEM"
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "PORT0001", 
                "account_number": "1234567890",
                "client_name": "John Doe",
                "user": "ADMIN"
            }
        }


class PortfolioValueUpdateRequest(BaseModel):
    portfolio_id: str
    account_number: str
    total_value: float
    user: str = "SYSTEM"
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "PORT0001",
                "account_number": "1234567890", 
                "total_value": 125750.50,
                "user": "ADMIN"
            }
        }


class PortfolioUpdateResponse(BaseModel):
    success: bool
    message: str
    portfolio_id: str
    errors: List[str] = []
