from decimal import Decimal
from typing import Union


def validate_portfolio_id(portfolio_id: str) -> tuple[bool, str]:
    """Validate portfolio ID must start with 'PORT' followed by 4 numeric digits"""
    if not portfolio_id or len(portfolio_id) != 8:
        return False, "Portfolio ID must be exactly 8 characters"
    
    if not portfolio_id.startswith("PORT"):
        return False, "Portfolio ID must start with 'PORT'"
    
    if not portfolio_id[4:8].isdigit():
        return False, "Portfolio ID must have 4 numeric digits after 'PORT'"
    
    return True, "Valid portfolio ID"


def validate_account_number(account_number: str) -> tuple[bool, str]:
    """Validate account number must be 10 numeric digits, not all zeros"""
    if not account_number:
        return False, "Account number must be exactly 10 digits"
    
    if not account_number.isdigit():
        return False, "Account number must contain only numeric characters"
    
    if len(account_number) != 10:
        return False, "Account number must be exactly 10 digits"
    
    if account_number == "0000000000":
        return False, "Account number cannot be all zeros"
    
    return True, "Valid account number"


def validate_investment_type(investment_type: str) -> tuple[bool, str]:
    """Validate investment type must be one of: STK, BND, MMF, ETF"""
    valid_types = {'STK', 'BND', 'MMF', 'ETF'}
    
    if not investment_type:
        return False, "Investment type is required"
    
    if investment_type not in valid_types:
        return False, f"Investment type must be one of: {', '.join(sorted(valid_types))}"
    
    return True, "Valid investment type"


def validate_amount(amount: Union[str, float, Decimal]) -> tuple[bool, str]:
    """Validate amount is within range -9,999,999,999,999.99 to +9,999,999,999,999.99"""
    if amount is None:
        return False, "Amount must be a valid number"
    
    try:
        decimal_amount = Decimal(str(amount))
    except (ValueError, TypeError, Exception):
        return False, "Amount must be a valid number"
    
    min_amount = Decimal('-9999999999999.99')
    max_amount = Decimal('9999999999999.99')
    
    if decimal_amount < min_amount or decimal_amount > max_amount:
        return False, f"Amount must be between {min_amount} and {max_amount}"
    
    return True, "Valid amount"
