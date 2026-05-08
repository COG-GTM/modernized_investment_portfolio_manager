from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.inquiry import (
    PortfolioInquiryResponse,
    HistoryInquiryResponse,
    MenuResponse,
    ErrorResponse,
)
from services.inquiry_service import InquiryService

router = APIRouter(prefix="/api/inquiry", tags=["inquiry"])


@router.get("/menu", response_model=MenuResponse)
async def get_menu(db: Session = Depends(get_db)):
    service = InquiryService(db)
    return service.get_menu_options()


@router.get(
    "/portfolio/{account_number}",
    response_model=PortfolioInquiryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_portfolio_inquiry(
    account_number: str, db: Session = Depends(get_db)
):
    if not account_number or len(account_number) > 10:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error_code="INVALID_INPUT",
                message="Account number must be 1-10 characters",
                severity="ERROR",
                program="INQPORT",
            ).model_dump(),
        )

    service = InquiryService(db)
    result = service.get_portfolio_positions(account_number)

    if not result.positions and "not found" in result.message.lower():
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error_code="NOTFND",
                message=result.message,
                severity="WARNING",
                program="INQPORT",
            ).model_dump(),
        )

    return result


@router.get(
    "/history/{account_number}",
    response_model=HistoryInquiryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_history_inquiry(
    account_number: str, db: Session = Depends(get_db)
):
    if not account_number or len(account_number) > 10:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error_code="INVALID_INPUT",
                message="Account number must be 1-10 characters",
                severity="ERROR",
                program="INQONLN",
            ).model_dump(),
        )

    service = InquiryService(db)
    result = service.get_transaction_history(account_number)

    if "No portfolio found" in result.message:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error_code="NOTFND",
                message=result.message,
                severity="WARNING",
                program="INQONLN",
            ).model_dump(),
        )

    return result
