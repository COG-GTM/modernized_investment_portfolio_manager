from fastapi import APIRouter, HTTPException
from models.portfolio import AccountValidationResponse
import re

router = APIRouter(prefix="/api", tags=["accounts"])


def validate_account_number(account_number: str) -> tuple[bool, str]:
    """Validate account number according to frontend schema rules"""
    if len(account_number) != 9:
        return False, "Account number must be exactly 9 digits"
    
    if not account_number.isdigit():
        return False, "Account number must contain only numeric characters"
    
    if "0" in account_number:
        return False, "Account number cannot contain zero digits"
    
    return True, "Valid account number"


@router.get("/accounts/{account_number}/validate", response_model=AccountValidationResponse)
async def validate_account(account_number: str):
    """Validate account number format (9-digit numeric without zeros)"""
    is_valid, message = validate_account_number(account_number)
    
    return AccountValidationResponse(
        valid=is_valid,
        message=message
    )
