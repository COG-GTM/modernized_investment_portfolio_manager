from fastapi import APIRouter, HTTPException, Query
from models.portfolio import AccountValidationResponse, AccountListResponse, AccountInfo, PaginationMeta
from validation.portfolio import validate_account_number
from typing import Optional
import re
import math

router = APIRouter(prefix="/api", tags=["accounts"])

MOCK_ACCOUNTS = [
    AccountInfo(accountNumber="1234567890", accountName="John Smith", accountType="Individual", totalValue=125750.50, status="Active"),
    AccountInfo(accountNumber="0987654321", accountName="Jane Doe", accountType="Joint", totalValue=245300.75, status="Active"),
    AccountInfo(accountNumber="1122334455", accountName="Robert Johnson", accountType="IRA", totalValue=89420.00, status="Active"),
    AccountInfo(accountNumber="5566778899", accountName="Emily Davis", accountType="401k", totalValue=312500.25, status="Active"),
    AccountInfo(accountNumber="9988776655", accountName="Michael Wilson", accountType="Individual", totalValue=67890.30, status="Inactive"),
    AccountInfo(accountNumber="1357924680", accountName="Sarah Brown", accountType="Joint", totalValue=198750.00, status="Active"),
    AccountInfo(accountNumber="2468013579", accountName="David Taylor", accountType="IRA", totalValue=145600.80, status="Active"),
    AccountInfo(accountNumber="1111222233", accountName="Lisa Anderson", accountType="Individual", totalValue=78900.45, status="Active"),
    AccountInfo(accountNumber="4444555566", accountName="James Thomas", accountType="401k", totalValue=267800.90, status="Inactive"),
    AccountInfo(accountNumber="7777888899", accountName="Jennifer Martinez", accountType="Joint", totalValue=189300.60, status="Active"),
    AccountInfo(accountNumber="3210987654", accountName="Chris Lee", accountType="Individual", totalValue=54320.15, status="Active"),
    AccountInfo(accountNumber="6543210987", accountName="Amanda Harris", accountType="IRA", totalValue=423100.00, status="Active"),
]


@router.get("/accounts", response_model=AccountListResponse)
async def list_accounts(
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    """List accounts with optional search and pagination"""
    filtered = MOCK_ACCOUNTS
    if search:
        filtered = [
            a for a in MOCK_ACCOUNTS
            if search.lower() in a.accountNumber.lower() or search.lower() in a.accountName.lower()
        ]

    total_items = len(filtered)
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    page_items = filtered[start:end]

    return AccountListResponse(
        accounts=page_items,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            totalItems=total_items,
            totalPages=total_pages,
        ),
    )


@router.get("/accounts/{account_number}/validate", response_model=AccountValidationResponse)
async def validate_account(account_number: str):
    """Validate account number format (10-digit numeric, not all zeros)"""
    is_valid, message = validate_account_number(account_number)
    
    return AccountValidationResponse(
        valid=is_valid,
        message=message
    )
