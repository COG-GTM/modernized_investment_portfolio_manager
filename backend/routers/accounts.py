from fastapi import APIRouter, HTTPException
from models.portfolio import AccountValidationResponse
from validation.portfolio import validate_account_number
import re

router = APIRouter(prefix="/api", tags=["accounts"])


@router.get("/accounts/{account_number}/validate", response_model=AccountValidationResponse)
async def validate_account(account_number: str):
    """Validate account number format (10-digit numeric, not all zeros)"""
    is_valid, message = validate_account_number(account_number)
    
    return AccountValidationResponse(
        valid=is_valid,
        message=message
    )
