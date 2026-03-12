"""
Portfolio CRUD API Routes - Migrated from COBOL PORTMSTR, PORTADD, PORTREAD, PORTUPDT, PORTDEL

REST endpoints for portfolio management:
- POST   /api/v1/portfolios          - Create portfolio
- GET    /api/v1/portfolios/{id}     - Read portfolio
- GET    /api/v1/portfolios          - List portfolios
- PUT    /api/v1/portfolios/{id}     - Update portfolio
- DELETE /api/v1/portfolios/{id}     - Delete portfolio
"""

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import SessionLocal
from app.services.portfolio.portfolio_service import PortfolioCRUDService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


# ----------------------------------------------------------------
# Request/Response Models
# ----------------------------------------------------------------

class CreatePortfolioRequest(BaseModel):
    port_id: str = Field(..., min_length=8, max_length=8, description="Portfolio ID (starts with 'PORT')")
    account_no: str = Field(..., min_length=10, max_length=10, description="10-digit account number")
    client_name: str = Field(..., min_length=1, max_length=30, description="Client name")
    client_type: str = Field(default="I", description="Client type: I=Individual, C=Corporate, T=Trust")
    status: str = Field(default="A", description="Status: A=Active, C=Closed, S=Suspended")
    total_value: Optional[float] = Field(default=None, description="Initial total value")
    cash_balance: Optional[float] = Field(default=None, description="Initial cash balance")


class UpdatePortfolioRequest(BaseModel):
    client_name: Optional[str] = Field(default=None, max_length=30, description="New client name")
    status: Optional[str] = Field(default=None, description="New status: A=Active, C=Closed, S=Suspended")
    total_value: Optional[float] = Field(default=None, description="New total value")
    cash_balance: Optional[float] = Field(default=None, description="New cash balance")


class DeletePortfolioRequest(BaseModel):
    reason_code: str = Field(default="03", description="Reason: 01=closed, 02=transferred, 03=requested")


# ----------------------------------------------------------------
# Dependency
# ----------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------

@router.post("", status_code=201)
async def create_portfolio(request: CreatePortfolioRequest, db: Session = Depends(get_db)):
    """
    Create a new portfolio.

    Migrated from COBOL PORTADD / PORTMSTR 2000-CREATE-PORTFOLIO.
    """
    service = PortfolioCRUDService(db)

    success, result = service.create_portfolio(
        port_id=request.port_id,
        account_no=request.account_no,
        client_name=request.client_name,
        client_type=request.client_type,
        status=request.status,
        total_value=Decimal(str(request.total_value)) if request.total_value is not None else None,
        cash_balance=Decimal(str(request.cash_balance)) if request.cash_balance is not None else None,
    )

    if not success:
        errors = result.get("errors", ["Unknown error"])
        if any("already exists" in e for e in errors):
            raise HTTPException(status_code=409, detail=errors[0])
        raise HTTPException(status_code=400, detail=errors)

    return result


@router.get("/{port_id}")
async def get_portfolio(port_id: str, account_no: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Read a portfolio by ID.

    Migrated from COBOL PORTREAD / PORTMSTR 3000-READ-PORTFOLIO.
    """
    service = PortfolioCRUDService(db)

    success, result = service.get_portfolio(port_id=port_id, account_no=account_no)

    if not success:
        raise HTTPException(status_code=404, detail=result.get("errors", ["Portfolio not found"])[0])

    return result


@router.get("")
async def list_portfolios(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List all portfolios with optional filtering.

    Migrated from COBOL PORTREAD sequential read loop.
    """
    service = PortfolioCRUDService(db)

    success, result = service.list_portfolios(status=status, limit=limit, offset=offset)

    if not success:
        raise HTTPException(status_code=500, detail=result.get("errors", ["Error listing portfolios"])[0])

    return result


@router.put("/{port_id}")
async def update_portfolio(
    port_id: str,
    request: UpdatePortfolioRequest,
    account_no: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Update an existing portfolio.

    Migrated from COBOL PORTUPDT / PORTMSTR 4000-UPDATE-PORTFOLIO.
    """
    service = PortfolioCRUDService(db)

    success, result = service.update_portfolio(
        port_id=port_id,
        account_no=account_no,
        client_name=request.client_name,
        status=request.status,
        total_value=Decimal(str(request.total_value)) if request.total_value is not None else None,
        cash_balance=Decimal(str(request.cash_balance)) if request.cash_balance is not None else None,
    )

    if not success:
        errors = result.get("errors", ["Unknown error"])
        if any("not found" in e for e in errors):
            raise HTTPException(status_code=404, detail=errors[0])
        raise HTTPException(status_code=400, detail=errors)

    return result


@router.delete("/{port_id}")
async def delete_portfolio(
    port_id: str,
    account_no: Optional[str] = None,
    reason_code: str = Query(default="03", description="Reason: 01=closed, 02=transferred, 03=requested"),
    db: Session = Depends(get_db),
):
    """
    Delete a portfolio with audit trail.

    Migrated from COBOL PORTDEL / PORTMSTR 5000-DELETE-PORTFOLIO.
    """
    service = PortfolioCRUDService(db)

    success, result = service.delete_portfolio(
        port_id=port_id,
        account_no=account_no,
        reason_code=reason_code,
    )

    if not success:
        errors = result.get("errors", ["Unknown error"])
        if any("not found" in e for e in errors):
            raise HTTPException(status_code=404, detail=errors[0])
        raise HTTPException(status_code=400, detail=errors)

    return result
