def validate_inquiry_account(account_number: str) -> tuple[bool, str]:
    """Validate account number for inquiry: must be 10 chars, numeric, not all zeros"""
    if not account_number or len(account_number) != 10:
        return False, "Account number must be exactly 10 characters"
    if not account_number.isdigit():
        return False, "Account number must contain only numeric characters"
    if account_number == "0000000000":
        return False, "Account number cannot be all zeros"
    return True, "Valid account number"
