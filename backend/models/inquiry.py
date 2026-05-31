from pydantic import BaseModel
from typing import List, Optional


class InquiryMenuOption(BaseModel):
    id: str
    label: str
    description: str
    route: str


class InquiryMenuResponse(BaseModel):
    title: str
    options: List[InquiryMenuOption]


class PositionDetail(BaseModel):
    portfolioId: str
    investmentId: str
    positionDate: Optional[str]
    quantity: float
    costBasis: float
    marketValue: float
    currency: str
    status: str
    gainLoss: float
    gainLossPercent: float
    lastMaintDate: Optional[str]
    lastMaintUser: Optional[str]


class PortfolioInquiryResponse(BaseModel):
    accountNumber: str
    portfolioId: str
    portfolioName: Optional[str]
    clientName: Optional[str]
    clientType: Optional[str]
    status: Optional[str]
    totalValue: float
    totalCostBasis: float
    totalGainLoss: float
    totalGainLossPercent: float
    cashBalance: float
    currency: str
    positions: List[PositionDetail]
    lastUpdated: str


class HistoryEntry(BaseModel):
    transactionDate: Optional[str]
    transactionType: str
    quantity: float
    price: float
    amount: float
    investmentId: Optional[str]
    status: Optional[str]


class TransactionHistoryResponse(BaseModel):
    accountNumber: str
    portfolioId: str
    entries: List[HistoryEntry]
    totalEntries: int
    hasMore: bool
    message: str


class InquiryErrorResponse(BaseModel):
    errorCode: int
    errorMessage: str
    program: str
