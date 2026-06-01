from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


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


class PieChartData(BaseModel):
    symbol: str
    percentage: float


class LineGraphPoint(BaseModel):
    date: str
    value: float


class PerformanceMetrics(BaseModel):
    totalReturn: float
    totalReturnPercent: float
    annualizedReturn: float
    volatility: float
    sharpeRatio: float


class AssetAllocation(BaseModel):
    symbol: str
    name: str
    percentage: float
    marketValue: float


class RiskScores(BaseModel):
    overall: float
    market: float
    concentration: float
    volatility: float


class PortfolioAnalytics(BaseModel):
    accountNumber: str
    performance: PerformanceMetrics
    assetAllocation: List[AssetAllocation]
    riskScores: RiskScores
    pieChartData: List[PieChartData]
    lineGraphData: List[LineGraphPoint]
    lastUpdated: str


class AccountInfo(BaseModel):
    accountNumber: str
    accountName: str
    accountType: str
    totalValue: float
    status: str


class PaginationMeta(BaseModel):
    page: int
    limit: int
    totalItems: int
    totalPages: int


class AccountListResponse(BaseModel):
    accounts: List[AccountInfo]
    pagination: PaginationMeta


class TransactionItem(BaseModel):
    date: str
    time: str
    portfolioId: str
    sequenceNo: str
    investmentId: str
    type: str
    quantity: float
    price: float
    amount: float
    currency: str
    status: str


class TransactionFilterResponse(BaseModel):
    accountNumber: str
    transactions: List[TransactionItem]
    totalCount: int


class CompareRequest(BaseModel):
    accountNumbers: List[str]


class PortfolioComparisonItem(BaseModel):
    accountNumber: str
    totalValue: float
    totalGainLoss: float
    totalGainLossPercent: float
    holdingsCount: int
    topHolding: str


class PortfolioComparisonResponse(BaseModel):
    portfolios: List[PortfolioComparisonItem]
    holdingsOverlap: List[str]
    bestPerformer: str
    worstPerformer: str


class StockQuote(BaseModel):
    symbol: str
    price: float
    change: float
    changePercent: float
    timestamp: str
