from pydantic import BaseModel
from typing import List


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
