"""
Portfolio inquiry endpoints — replaces INQPORT.cbl (Portfolio Position Inquiry Handler).

COBOL INQPORT flow:
  P100-INIT-PROGRAM  — Initialize, copy DFHCOMMAREA to WS-COMMAREA
  P200-GET-POSITION  — EXEC CICS READ FILE('POSFILE') INTO(WS-POSITION-RECORD)
                        using RIDFLD(POSITION-ACCOUNT)
  P300-FORMAT-DISPLAY — EXEC CICS SEND MAP('POSMAP') FROM(WS-POSITION-RECORD)
  P900-NOT-FOUND     — 'Position not found for account'
  P999-ERROR-ROUTINE  — 'Error accessing position data'

REST API replacements:
  GET /api/v1/portfolios/{portfolio_id}           -> Portfolio summary
  GET /api/v1/portfolios/{portfolio_id}/positions  -> Portfolio positions with filters

The CICS READ FILE('POSFILE') VSAM access is replaced with SQLAlchemy queries
against the portfolios and positions tables.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import PaginationParams, get_current_user, get_db
from app.api.schemas import (
    PaginationMeta,
    PortfolioPositionsResponse,
    PortfolioSummaryResponse,
    PositionDetail,
    UserInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioSummaryResponse,
    summary="Get portfolio summary",
    description=(
        "Retrieve portfolio summary by ID. "
        "Replaces INQONLN P300-PORTFOLIO-INQUIRY -> INQPORT initial screen display."
    ),
)
async def get_portfolio_summary(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> PortfolioSummaryResponse:
    """
    Get portfolio summary — replaces INQPORT P200-GET-POSITION (summary part).

    COBOL equivalent:
      MOVE WS-COMMAREA-ACCOUNT-NO TO POSITION-ACCOUNT OF WS-POSITION-RECORD
      EXEC CICS READ FILE('POSFILE')
               INTO(WS-POSITION-RECORD)
               RIDFLD(POSITION-ACCOUNT)
               RESP(WS-RESPONSE-CODE)
      END-EXEC
      IF WS-RESPONSE-CODE = DFHRESP(NORMAL) -> return data
      ELSE -> P900-NOT-FOUND
    """
    from models.database import Portfolio

    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.port_id == portfolio_id)
        .first()
    )

    if portfolio is None:
        # Replaces INQPORT P900-NOT-FOUND:
        # MOVE 'Position not found for account' TO INQCOM-ERROR-MSG
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio not found: {portfolio_id}",
        )

    return PortfolioSummaryResponse(
        portfolio_id=portfolio.port_id,
        account_number=portfolio.account_no,
        client_name=portfolio.client_name,
        client_type=portfolio.client_type,
        status=portfolio.status,
        total_value=float(portfolio.total_value) if portfolio.total_value else 0.0,
        cash_balance=float(portfolio.cash_balance) if portfolio.cash_balance else 0.0,
        create_date=portfolio.create_date.isoformat() if portfolio.create_date else None,
        last_updated=portfolio.last_maint.isoformat() if portfolio.last_maint else None,
    )


@router.get(
    "/{portfolio_id}/positions",
    response_model=PortfolioPositionsResponse,
    summary="Get portfolio positions",
    description=(
        "Retrieve all positions for a portfolio with optional filters. "
        "Replaces INQPORT full position display via BMS POSMAP."
    ),
)
async def get_portfolio_positions(
    portfolio_id: str,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by position status (A/C/P)"),
    investment_id: Optional[str] = Query(None, description="Filter by investment ID"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> PortfolioPositionsResponse:
    """
    Get portfolio positions — replaces INQPORT P200-GET-POSITION + P300-FORMAT-DISPLAY.

    COBOL equivalent:
      EXEC CICS READ FILE('POSFILE') INTO(WS-POSITION-RECORD) ...
      EXEC CICS SEND MAP('POSMAP') FROM(WS-POSITION-RECORD) ERASE

    The VSAM keyed read is replaced with a SQLAlchemy query that supports
    additional filters not available in the original COBOL program.
    """
    from models.database import Portfolio, Position

    # Verify portfolio exists
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.port_id == portfolio_id)
        .first()
    )

    if portfolio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio not found: {portfolio_id}",
        )

    # Build position query — replaces CICS READ FILE('POSFILE')
    query = db.query(Position).filter(Position.portfolio_id == portfolio_id)

    if status_filter:
        query = query.filter(Position.status == status_filter)
    if investment_id:
        query = query.filter(Position.investment_id == investment_id)

    positions = query.all()

    # Format response — replaces INQPORT P300-FORMAT-DISPLAY
    position_details = []
    total_market_value = 0.0
    total_cost_basis = 0.0

    for pos in positions:
        market_val = float(pos.market_value) if pos.market_value else 0.0
        cost_val = float(pos.cost_basis) if pos.cost_basis else 0.0
        gain_loss_data = pos.calculate_gain_loss()

        position_details.append(
            PositionDetail(
                investment_id=pos.investment_id,
                quantity=float(pos.quantity) if pos.quantity else 0.0,
                cost_basis=cost_val,
                market_value=market_val,
                currency=pos.currency or "USD",
                status=pos.status,
                gain_loss=float(gain_loss_data["gain_loss"]),
                gain_loss_percent=float(gain_loss_data["gain_loss_percent"]),
                last_updated=pos.last_maint_date.isoformat() if pos.last_maint_date else None,
            )
        )
        total_market_value += market_val
        total_cost_basis += cost_val

    total_gain_loss = total_market_value - total_cost_basis

    return PortfolioPositionsResponse(
        portfolio_id=portfolio.port_id,
        account_number=portfolio.account_no,
        positions=position_details,
        total_positions=len(position_details),
        total_market_value=round(total_market_value, 2),
        total_cost_basis=round(total_cost_basis, 2),
        total_gain_loss=round(total_gain_loss, 2),
    )
