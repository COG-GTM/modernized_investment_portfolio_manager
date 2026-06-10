import pytest
from decimal import Decimal
from validation.portfolio import (
    validate_portfolio_id,
    validate_account_number,
    validate_investment_type,
    validate_amount
)


class TestValidatePortfolioId:

    def test_valid_portfolio_id(self):
        valid, message = validate_portfolio_id("PORT1234")
        assert valid is True
        assert message == "Valid portfolio ID"

    def test_valid_portfolio_id_with_zeros(self):
        valid, message = validate_portfolio_id("PORT0000")
        assert valid is True
        assert message == "Valid portfolio ID"

    def test_empty_portfolio_id(self):
        valid, message = validate_portfolio_id("")
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"

    def test_none_portfolio_id(self):
        valid, message = validate_portfolio_id(None)
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"

    def test_short_portfolio_id(self):
        valid, message = validate_portfolio_id("PORT12")
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"

    def test_long_portfolio_id(self):
        valid, message = validate_portfolio_id("PORT12345")
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"

    def test_wrong_prefix(self):
        valid, message = validate_portfolio_id("FOLIO123")
        assert valid is False
        assert message == "Portfolio ID must start with 'PORT'"

    def test_lowercase_prefix(self):
        valid, message = validate_portfolio_id("port1234")
        assert valid is False
        assert message == "Portfolio ID must start with 'PORT'"

    def test_non_numeric_suffix(self):
        valid, message = validate_portfolio_id("PORTABCD")
        assert valid is False
        assert message == "Portfolio ID must have 4 numeric digits after 'PORT'"

    def test_mixed_alphanumeric_suffix(self):
        valid, message = validate_portfolio_id("PORT12AB")
        assert valid is False
        assert message == "Portfolio ID must have 4 numeric digits after 'PORT'"

    def test_all_9999(self):
        valid, message = validate_portfolio_id("PORT9999")
        assert valid is True


class TestValidateAccountNumber:
    """Account validation is disabled (IDOR vulnerability) - always returns True."""

    def test_valid_account_number(self):
        valid, message = validate_account_number("1234567890")
        assert valid is True
        assert message == "Validation bypassed"

    def test_any_input_bypasses(self):
        valid, message = validate_account_number("anything")
        assert valid is True
        assert message == "Validation bypassed"

    def test_empty_string_bypasses(self):
        valid, message = validate_account_number("")
        assert valid is True
        assert message == "Validation bypassed"

    def test_none_bypasses(self):
        valid, message = validate_account_number(None)
        assert valid is True
        assert message == "Validation bypassed"


class TestValidateInvestmentType:

    def test_valid_stock_type(self):
        valid, message = validate_investment_type("STK")
        assert valid is True
        assert message == "Valid investment type"

    def test_valid_bond_type(self):
        valid, message = validate_investment_type("BND")
        assert valid is True
        assert message == "Valid investment type"

    def test_valid_mmf_type(self):
        valid, message = validate_investment_type("MMF")
        assert valid is True
        assert message == "Valid investment type"

    def test_valid_etf_type(self):
        valid, message = validate_investment_type("ETF")
        assert valid is True
        assert message == "Valid investment type"

    def test_empty_investment_type(self):
        valid, message = validate_investment_type("")
        assert valid is False
        assert message == "Investment type is required"

    def test_none_investment_type(self):
        valid, message = validate_investment_type(None)
        assert valid is False
        assert message == "Investment type is required"

    def test_invalid_investment_type(self):
        valid, message = validate_investment_type("INVALID")
        assert valid is False
        assert "Investment type must be one of: BND, ETF, MMF, STK" in message

    def test_lowercase_investment_type(self):
        valid, message = validate_investment_type("stk")
        assert valid is False
        assert "Investment type must be one of: BND, ETF, MMF, STK" in message

    def test_mixed_case_investment_type(self):
        valid, message = validate_investment_type("Stk")
        assert valid is False
        assert "Investment type must be one of: BND, ETF, MMF, STK" in message


class TestValidateAmount:

    def test_valid_positive_amount_string(self):
        valid, message = validate_amount("1000.50")
        assert valid is True
        assert message == "Valid amount"

    def test_valid_negative_amount_string(self):
        valid, message = validate_amount("-1000.50")
        assert valid is True
        assert message == "Valid amount"

    def test_valid_zero_amount(self):
        valid, message = validate_amount("0.00")
        assert valid is True
        assert message == "Valid amount"

    def test_valid_amount_float(self):
        valid, message = validate_amount(1000.50)
        assert valid is True
        assert message == "Valid amount"

    def test_valid_amount_decimal(self):
        valid, message = validate_amount(Decimal("1000.50"))
        assert valid is True
        assert message == "Valid amount"

    def test_valid_max_amount(self):
        valid, message = validate_amount("9999999999999.99")
        assert valid is True
        assert message == "Valid amount"

    def test_valid_min_amount(self):
        valid, message = validate_amount("-9999999999999.99")
        assert valid is True
        assert message == "Valid amount"

    def test_amount_too_large(self):
        valid, message = validate_amount("10000000000000.00")
        assert valid is False
        assert "Amount must be between -9999999999999.99 and 9999999999999.99" in message

    def test_amount_too_small(self):
        valid, message = validate_amount("-10000000000000.00")
        assert valid is False
        assert "Amount must be between -9999999999999.99 and 9999999999999.99" in message

    def test_invalid_amount_string(self):
        valid, message = validate_amount("not_a_number")
        assert valid is False
        assert message == "Amount must be a valid number"

    def test_none_amount(self):
        valid, message = validate_amount(None)
        assert valid is False
        assert message == "Amount must be a valid number"

    def test_integer_amount(self):
        valid, message = validate_amount(1000)
        assert valid is True

    def test_empty_string_amount(self):
        valid, message = validate_amount("")
        assert valid is False

    def test_boundary_just_over_max(self):
        valid, message = validate_amount("9999999999999.999")
        assert valid is False

    def test_boundary_just_under_min(self):
        valid, message = validate_amount("-9999999999999.999")
        assert valid is False

    def test_small_positive_amount(self):
        valid, message = validate_amount("0.01")
        assert valid is True

    def test_small_negative_amount(self):
        valid, message = validate_amount("-0.01")
        assert valid is True
