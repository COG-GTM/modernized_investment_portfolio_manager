from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from enum import Enum


class InquiryFunction(str, Enum):
    MENU = "MENU"
    INQP = "INQP"
    INQH = "INQH"
    EXIT = "EXIT"


class InquiryRequest(BaseModel):
    function: InquiryFunction
    account_number: str = Field(..., max_length=10)


class PositionResponse(BaseModel):
    portfolio_id: str
    date: Optional[str] = None
    investment_id: str
    quantity: Decimal
    cost_basis: Decimal
    market_value: Decimal
    currency: str
    status: str
    gain_loss: Decimal
    gain_loss_percent: Decimal
    last_maint_date: Optional[str] = None
    last_maint_user: Optional[str] = None

    model_config = {"from_attributes": True}


class PortfolioSummaryInfo(BaseModel):
    portfolio_id: str
    client_name: Optional[str] = None
    total_value: Decimal
    cash_balance: Decimal
    status: Optional[str] = None


class PortfolioInquiryResponse(BaseModel):
    account_number: str
    positions: List[PositionResponse]
    portfolio_summary: Optional[PortfolioSummaryInfo] = None
    message: str


class TransactionDetail(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    portfolio_id: str
    sequence_no: str
    investment_id: Optional[str] = None
    type: str
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: str
    process_date: Optional[str] = None
    process_user: Optional[str] = None


class HistoryInquiryResponse(BaseModel):
    account_number: str
    transactions: List[TransactionDetail]
    message: str


class MenuOption(BaseModel):
    code: str
    description: str


class MenuResponse(BaseModel):
    options: List[MenuOption]


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    severity: str
    program: str
    paragraph: Optional[str] = None
