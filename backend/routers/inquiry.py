from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from models import SessionLocal
from models.inquiry import (
    InquiryMenuOption,
    InquiryMenuResponse,
    PortfolioInquiryResponse,
    TransactionHistoryResponse,
    InquiryErrorResponse,
)
from services.inquiry_service import InquiryService
from validation.inquiry import validate_inquiry_account

router = APIRouter(prefix="/api/inquiry", tags=["inquiry"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/menu", response_model=InquiryMenuResponse)
async def get_inquiry_menu():
    """Return available inquiry options (INQONLN menu dispatch)"""
    options = [
        InquiryMenuOption(
            id="INQP",
            label="Portfolio Inquiry",
            description="View portfolio positions and valuations",
            route="/api/inquiry/portfolio/{account_number}",
        ),
        InquiryMenuOption(
            id="INQH",
            label="Transaction History",
            description="View transaction history for a portfolio",
            route="/api/inquiry/history/{account_number}",
        ),
    ]
    return InquiryMenuResponse(
        title="Investment Portfolio Inquiry System",
        options=options,
    )


@router.get(
    "/portfolio/{account_number}",
    response_model=PortfolioInquiryResponse,
    responses={400: {"model": InquiryErrorResponse}, 404: {"model": InquiryErrorResponse}},
)
def get_portfolio_inquiry(account_number: str, db: Session = Depends(get_db)):
    """Portfolio position inquiry (INQPORT equivalent)"""
    is_valid, message = validate_inquiry_account(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    service = InquiryService(db)
    result = service.get_portfolio_positions(account_number)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No portfolio found for account number {account_number}",
        )

    return result


@router.get(
    "/history/{account_number}",
    response_model=TransactionHistoryResponse,
    responses={400: {"model": InquiryErrorResponse}, 404: {"model": InquiryErrorResponse}},
)
def get_transaction_history(
    account_number: str, limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)
):
    """Transaction history inquiry (INQHIST equivalent)"""
    is_valid, message = validate_inquiry_account(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    service = InquiryService(db)
    result = service.get_transaction_history(account_number, limit=limit)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No portfolio found for account number {account_number}",
        )

    return result
