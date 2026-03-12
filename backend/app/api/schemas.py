"""
Pydantic request/response schemas for the Portfolio Inquiry REST API.

Replaces BMS screen definitions from INQSET.bms:
- MENMAP (Main Menu)       -> Not needed (frontend handles navigation)
- POSMAP (Position Map)    -> PortfolioPositionResponse, PositionDetail
- HISMAP (History Map)     -> TransactionHistoryResponse, HistoryEntry
- ERRMAP (Error Map)       -> ErrorResponse

Replaces COBOL copybook structures:
- INQCOM.cpy              -> Various request/response models
- DB2REQ.cpy              -> Internal DB config (not exposed via API)
- ERRHND.cpy              -> ErrorResponse, ErrorDetail
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums (derived from COBOL 88-level values)
# ---------------------------------------------------------------------------

class ClientType(str, Enum):
    """Portfolio client types (from COBOL PIC X(1) with CHECK constraint)."""
    INDIVIDUAL = "I"
    CORPORATE = "C"
    TRUST = "T"


class PortfolioStatus(str, Enum):
    """Portfolio status codes."""
    ACTIVE = "A"
    CLOSED = "C"
    SUSPENDED = "S"


class PositionStatus(str, Enum):
    """Position status codes."""
    ACTIVE = "A"
    CLOSED = "C"
    PENDING = "P"


class TransactionType(str, Enum):
    """Transaction types (from COBOL WS-TRANS-TYPE PIC X(4) / DB constraint)."""
    BUY = "BU"
    SELL = "SL"
    TRANSFER = "TR"
    FEE = "FE"


class TransactionStatus(str, Enum):
    """Transaction processing status."""
    PENDING = "P"
    DONE = "D"
    FAILED = "F"
    REVERSED = "R"


class ErrorSeverity(str, Enum):
    """
    Mirrors ERRHND.cpy ERR-SEVERITY:
      88 ERR-FATAL   VALUE 'F'
      88 ERR-WARNING VALUE 'W'
      88 ERR-INFO    VALUE 'I'
    """
    FATAL = "fatal"
    WARNING = "warning"
    INFO = "info"


# ---------------------------------------------------------------------------
# Auth schemas (replacing SECMGR RACF/CICS auth)
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """
    Replaces SECMGR SEC-VALIDATE ('V') request.
    COBOL: SEC-USER-ID PIC X(8), validated via CICS ASSIGN USERID.
    """
    username: str = Field(..., min_length=1, max_length=50, description="User login name")
    password: str = Field(..., min_length=1, description="User password")


class TokenResponse(BaseModel):
    """JWT token response, replacing CICS session-based authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")
    user_id: str
    roles: List[str] = Field(default_factory=list)


class UserInfo(BaseModel):
    """Current user information extracted from JWT token."""
    user_id: str
    roles: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Portfolio schemas (replacing INQPORT / POSMAP screen fields)
# ---------------------------------------------------------------------------

class PositionDetail(BaseModel):
    """
    Single portfolio position — replaces BMS POSMAP fields:
      FUNDOUT  (Fund ID)      -> investment_id
      NAMEOUT  (Fund Name)    -> investment_name
      UNITOUT  (Units)        -> quantity
      COSTOUT  (Cost Basis)   -> cost_basis
      VALOUT   (Market Value) -> market_value

    Also replaces COBOL WS-POSITION-RECORD (POSREC copybook).
    """
    investment_id: str = Field(..., description="Investment/fund identifier")
    investment_name: Optional[str] = Field(None, description="Investment display name")
    quantity: float = Field(..., description="Number of units held")
    cost_basis: float = Field(..., description="Original cost basis")
    market_value: float = Field(..., description="Current market value")
    currency: str = Field("USD", description="Currency code")
    status: PositionStatus = Field(PositionStatus.ACTIVE, description="Position status")
    gain_loss: float = Field(0.0, description="Unrealized gain/loss")
    gain_loss_percent: float = Field(0.0, description="Gain/loss percentage")
    last_updated: Optional[str] = Field(None, description="Last maintenance date")


class PortfolioSummaryResponse(BaseModel):
    """
    Portfolio summary — replaces the POSMAP screen header section
    and INQCOM-ACCOUNT-NO field from INQCOM.cpy.
    """
    portfolio_id: str = Field(..., description="Portfolio identifier (8 chars)")
    account_number: str = Field(..., description="Account number (10 digits)")
    client_name: Optional[str] = Field(None, description="Client display name")
    client_type: Optional[ClientType] = Field(None, description="Client type")
    status: PortfolioStatus = Field(PortfolioStatus.ACTIVE)
    total_value: float = Field(0.0, description="Total portfolio value")
    cash_balance: float = Field(0.0, description="Available cash balance")
    create_date: Optional[str] = Field(None, description="Portfolio creation date")
    last_updated: Optional[str] = Field(None, description="Last maintenance date")


class PortfolioPositionsResponse(BaseModel):
    """
    Full portfolio positions response — replaces INQPORT P300-FORMAT-DISPLAY
    which sends POSMAP with position data via CICS SEND MAP.
    """
    portfolio_id: str
    account_number: str
    positions: List[PositionDetail] = Field(default_factory=list)
    total_positions: int = Field(0, description="Total number of positions")
    total_market_value: float = Field(0.0, description="Sum of all position market values")
    total_cost_basis: float = Field(0.0, description="Sum of all position cost bases")
    total_gain_loss: float = Field(0.0, description="Total unrealized gain/loss")


# ---------------------------------------------------------------------------
# Transaction history schemas (replacing INQHIST / HISMAP screen)
# ---------------------------------------------------------------------------

class HistoryEntry(BaseModel):
    """
    Single transaction history row — replaces BMS HISMAP ROW1-ROW10 fields:
      Date column   -> transaction_date
      Type column   -> transaction_type
      Units column  -> units
      Price column  -> price
      Amount column -> amount

    Maps to COBOL WS-HISTORY-ENTRY (OCCURS 10 TIMES in INQHIST).
    """
    transaction_date: str = Field(..., description="Transaction date")
    transaction_type: TransactionType = Field(..., description="Transaction type code")
    investment_id: Optional[str] = Field(None, description="Investment identifier")
    units: float = Field(0.0, description="Number of units transacted")
    price: float = Field(0.0, description="Price per unit")
    amount: float = Field(0.0, description="Total transaction amount")
    currency: str = Field("USD", description="Currency code")
    status: TransactionStatus = Field(TransactionStatus.DONE)
    sequence_no: Optional[str] = Field(None, description="Transaction sequence number")


class PaginationMeta(BaseModel):
    """Pagination metadata — replaces COBOL cursor-based scrolling (PF7/PF8 keys)."""
    total_count: int = Field(0, description="Total number of records")
    page: int = Field(1, description="Current page number (1-based)")
    per_page: int = Field(20, description="Records per page")
    total_pages: int = Field(0, description="Total number of pages")
    has_next: bool = Field(False, description="Whether more pages exist")
    has_previous: bool = Field(False, description="Whether previous pages exist")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page (cursor-based pagination)")
    previous_cursor: Optional[str] = Field(None, description="Cursor for previous page")


class TransactionHistoryResponse(BaseModel):
    """
    Paginated transaction history — replaces INQHIST P300-FORMAT-DISPLAY
    which sends HISMAP with WS-HISTORY-TABLE via CICS SEND MAP.

    The original COBOL program fetched 10 rows at a time via CURSMGR
    array fetch. This API supports both cursor-based and offset pagination.
    """
    portfolio_id: str
    account_number: str
    transactions: List[HistoryEntry] = Field(default_factory=list)
    pagination: PaginationMeta = Field(default_factory=PaginationMeta)


# ---------------------------------------------------------------------------
# Error schemas (replacing ERRHNDL / ERRMAP screen)
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """
    Structured error detail — replaces ERRHND.cpy fields:
      ERR-PROGRAM    -> source
      ERR-PARAGRAPH  -> detail
      ERR-MESSAGE    -> message
      ERR-TRACE-ID   -> trace_id
      ERR-SEVERITY   -> severity
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error context")
    source: Optional[str] = Field(None, description="Originating component")
    severity: ErrorSeverity = Field(ErrorSeverity.FATAL)
    trace_id: Optional[str] = Field(None, description="Error trace identifier for debugging")


class ErrorResponse(BaseModel):
    """
    Standard API error response — replaces BMS ERRMAP screen:
      ERRCOUT (Error Code)    -> error.code
      ERRDOUT (Error Details) -> error.message
    """
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Generic paginated response wrapper
# ---------------------------------------------------------------------------

DataT = TypeVar("DataT")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Generic paginated list response."""
    data: List[DataT] = Field(default_factory=list)  # type: ignore[assignment]
    pagination: PaginationMeta = Field(default_factory=PaginationMeta)


# ---------------------------------------------------------------------------
# Health check schema
# ---------------------------------------------------------------------------

class HealthCheckResponse(BaseModel):
    """Health check response — replaces DB2ONLN P300-CHECK-STATUS."""
    status: str = Field("ok", description="Service status")
    database: str = Field("ok", description="Database connection status")
    version: str = Field("1.0.0", description="API version")
    timestamp: str = Field(description="Current server timestamp")
