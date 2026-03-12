"""
Transaction history endpoints — replaces INQHIST.cbl + CURSMGR.cbl.

COBOL INQHIST flow:
  P100-INIT-PROGRAM   — Copy DFHCOMMAREA, connect to DB2 via DB2ONLN
  P150-DB2-CONNECT    — EXEC CICS LINK PROGRAM('DB2ONLN'), with DB2RECV recovery
  P200-GET-HISTORY    — Declare/Open/Fetch/Close cursor via CURSMGR:
                          'D' -> Declare cursor for SELECT from POSHIST
                          'O' -> Open cursor
                          'F' -> Fetch rows (array fetch, 10 at a time)
                          'C' -> Close cursor
  P250-FETCH-HISTORY  — CURSMGR fetch with array result into WS-HISTORY-TABLE
  P300-FORMAT-DISPLAY — EXEC CICS SEND MAP('HISMAP') FROM(WS-HISTORY-TABLE)

CURSMGR cursor pattern (Declare -> Open -> Fetch -> Close):
  Replaced with SQLAlchemy .query().order_by().offset().limit() for offset pagination,
  and date-based cursor for cursor-based pagination.

DB2RECV retry logic:
  Replaced with tenacity @retry decorator with exponential backoff,
  matching COBOL WS-MAX-RETRIES=3, WS-RETRY-INTERVAL=2.

REST API:
  GET /api/v1/portfolios/{portfolio_id}/history?page=1&per_page=20
  GET /api/v1/portfolios/{portfolio_id}/history?cursor=xxx&per_page=20
"""

import base64
import logging
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import InterfaceError, OperationalError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.api.dependencies import PaginationParams, get_current_user, get_db
from app.api.schemas import (
    HistoryEntry,
    PaginationMeta,
    TransactionHistoryResponse,
    UserInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/portfolios", tags=["history"])


# ---------------------------------------------------------------------------
# DB retry decorator — replaces DB2RECV.cbl retry loop
# ---------------------------------------------------------------------------
# COBOL DB2RECV P100-RECOVER-CONNECTION:
#   WS-MAX-RETRIES = 3, WS-RETRY-INTERVAL = 2 seconds
#   PERFORM UNTIL WS-RETRY-COUNT >= WS-MAX-RETRIES
#     attempt reconnect, EXEC CICS DELAY INTERVAL(WS-RETRY-INTERVAL)

db_retry = retry(
    stop=stop_after_attempt(3),               # WS-MAX-RETRIES = 3
    wait=wait_exponential(multiplier=2, min=2, max=10),  # WS-RETRY-INTERVAL = 2
    retry=retry_if_exception_type((OperationalError, InterfaceError)),
    reraise=True,
)


# ---------------------------------------------------------------------------
# History query helper — replaces CURSMGR cursor operations
# ---------------------------------------------------------------------------

def _build_cursor_value(transaction_date: str, sequence_no: str) -> str:
    """Encode a pagination cursor from date + sequence."""
    raw = f"{transaction_date}|{sequence_no}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _parse_cursor_value(cursor: str) -> tuple:
    """Decode a pagination cursor back to (date, sequence_no)."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        parts = raw.split("|", 1)
        return (parts[0], parts[1] if len(parts) > 1 else "")
    except Exception:
        return ("", "")


@db_retry
def _fetch_history_page(
    db: Session,
    portfolio_id: str,
    offset: int,
    limit: int,
    cursor: Optional[str] = None,
    transaction_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> tuple:
    """
    Fetch a page of transaction history from the database.

    Replaces CURSMGR cursor lifecycle:
      CURS-DECLARE ('D') — Declare cursor for:
        SELECT TRANS_DATE, TRANS_TYPE, TRANS_UNITS, TRANS_PRICE, TRANS_AMOUNT
        FROM POSHIST WHERE ACCOUNT_NO = ? ORDER BY TRANS_DATE DESC
      CURS-OPEN ('O')    — Open cursor
      CURS-FETCH ('F')   — Fetch rows (array fetch via WS-MAX-ROWS=20)
      CURS-CLOSE ('C')   — Close cursor

    The SQLAlchemy query replaces the entire Declare->Open->Fetch->Close
    pattern with a single query using .offset()/.limit().

    Returns (transactions, total_count).
    """
    from models.transactions import Transaction

    # Base query — replaces CURSMGR SQL statement
    query = db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id)

    # Apply optional filters
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)

    # Get total count for pagination metadata (before cursor filter)
    total_count = query.count()

    # Cursor-based pagination — replaces PF7/PF8 scrolling
    if cursor:
        cursor_date, cursor_seq = _parse_cursor_value(cursor)
        if cursor_date:
            query = query.filter(
                (Transaction.date < cursor_date)
                | (
                    (Transaction.date == cursor_date)
                    & (Transaction.sequence_no > cursor_seq)
                )
            )

    # Fetch page — replaces CURSMGR array fetch (WS-MAX-ROWS at a time)
    # ORDER BY TRANS_DATE DESC matches COBOL: ORDER BY TRANS_DATE DESC
    # When cursor-based pagination is active, offset is 0 because the
    # cursor filter already handles positioning.
    effective_offset = 0 if cursor else offset

    # Fetch limit+1 to detect if more records exist (for cursor pagination)
    fetch_limit = limit + 1 if cursor else limit
    rows = (
        query
        .order_by(Transaction.date.desc(), Transaction.sequence_no.asc())
        .offset(effective_offset)
        .limit(fetch_limit)
        .all()
    )

    # Determine if there are more records beyond this page
    has_more = len(rows) > limit if cursor else None
    transactions = rows[:limit] if cursor and has_more else rows

    return transactions, total_count, has_more


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/{portfolio_id}/history",
    response_model=TransactionHistoryResponse,
    summary="Get transaction history",
    description=(
        "Retrieve paginated transaction history for a portfolio. "
        "Supports both offset-based (page/per_page) and cursor-based pagination. "
        "Replaces INQHIST.cbl DB2 cursor-based scrolling with CURSMGR array fetch."
    ),
)
async def get_transaction_history(
    portfolio_id: str,
    pagination: PaginationParams = Depends(),
    transaction_type: Optional[str] = Query(
        None, alias="type", description="Filter by transaction type (BU/SL/TR/FE)"
    ),
    date_from: Optional[str] = Query(
        None, description="Start date filter (YYYY-MM-DD)"
    ),
    date_to: Optional[str] = Query(
        None, description="End date filter (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> TransactionHistoryResponse:
    """
    Get paginated transaction history.

    Replaces INQHIST full flow:
      P100 -> P150-DB2-CONNECT (now handled by SQLAlchemy pool)
      P200 -> CURSMGR Declare/Open/Fetch/Close (now SQLAlchemy query)
      P300 -> CICS SEND MAP('HISMAP') (now JSON response)

    Pagination replaces BMS PF7=Previous / PF8=Next scrolling.
    """
    from models.database import Portfolio

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

    # Fetch history page — replaces CURSMGR array fetch
    try:
        transactions, total_count, has_more = _fetch_history_page(
            db=db,
            portfolio_id=portfolio_id,
            offset=pagination.offset,
            limit=pagination.per_page,
            cursor=pagination.cursor,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as exc:
        # Replaces INQHIST P999-ERROR-ROUTINE:
        # MOVE SQLCODE TO INQCOM-RESPONSE-CODE
        logger.error("History query failed for portfolio=%s: %s", portfolio_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction history",
        )

    # Build response — replaces INQHIST P300-FORMAT-DISPLAY
    history_entries = []
    for txn in transactions:
        history_entries.append(
            HistoryEntry(
                transaction_date=txn.date.isoformat() if txn.date else "",
                transaction_type=txn.type,
                investment_id=txn.investment_id,
                units=float(txn.quantity) if txn.quantity else 0.0,
                price=float(txn.price) if txn.price else 0.0,
                amount=float(txn.amount) if txn.amount else 0.0,
                currency=txn.currency or "USD",
                status=txn.status,
                sequence_no=txn.sequence_no,
            )
        )

    # Pagination metadata — replaces COBOL WS-MORE-HISTORY flag
    # For cursor-based pagination, use has_more from the fetch (limit+1 trick).
    # For offset-based pagination, use page-based arithmetic.
    if pagination.cursor:
        # Cursor mode: has_more from fetch, has_previous always true (cursor implies prior records)
        has_next = bool(has_more)
        has_previous = True  # a cursor implies there were previous records
        total_pages = 0  # not meaningful for cursor pagination
    else:
        # Offset mode: standard page-based calculations
        total_pages = math.ceil(total_count / pagination.per_page) if pagination.per_page > 0 else 0
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1

    # Build cursors for cursor-based pagination
    next_cursor = None
    previous_cursor = None
    if has_next and history_entries:
        last = history_entries[-1]
        next_cursor = _build_cursor_value(last.transaction_date, last.sequence_no or "")
    if has_previous and history_entries:
        first = history_entries[0]
        previous_cursor = _build_cursor_value(first.transaction_date, first.sequence_no or "")

    return TransactionHistoryResponse(
        portfolio_id=portfolio.port_id,
        account_number=portfolio.account_no,
        transactions=history_entries,
        pagination=PaginationMeta(
            total_count=total_count,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
        ),
    )
