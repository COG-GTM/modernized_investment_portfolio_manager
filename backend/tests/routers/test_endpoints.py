import pytest
from validation.portfolio import (
    validate_account_number,
    validate_portfolio_id,
    validate_investment_type,
    validate_amount,
)


class TestValidateAccountNumberBypass:
    """Test the bypassed account validation (IDOR vulnerability)."""

    def test_always_returns_true(self):
        valid, message = validate_account_number("1234567890")
        assert valid is True
        assert message == "Validation bypassed"

    def test_bypassed_for_invalid_input(self):
        valid, message = validate_account_number("bad")
        assert valid is True

    def test_bypassed_for_empty_string(self):
        valid, message = validate_account_number("")
        assert valid is True

    def test_bypassed_for_none(self):
        valid, message = validate_account_number(None)
        assert valid is True


class TestValidatePortfolioId:
    """Test portfolio ID validation (additional coverage beyond existing tests)."""

    def test_valid_id(self):
        valid, message = validate_portfolio_id("PORT1234")
        assert valid is True

    def test_valid_id_with_all_nines(self):
        valid, message = validate_portfolio_id("PORT9999")
        assert valid is True

    def test_wrong_prefix_case(self):
        valid, message = validate_portfolio_id("port1234")
        assert valid is False
        assert "start with 'PORT'" in message

    def test_suffix_with_letters(self):
        valid, message = validate_portfolio_id("PORTABCD")
        assert valid is False
        assert "numeric digits" in message


class TestValidateInvestmentType:
    """Test investment type validation (additional coverage)."""

    def test_all_valid_types(self):
        for t in ["STK", "BND", "MMF", "ETF"]:
            valid, message = validate_investment_type(t)
            assert valid is True

    def test_partial_match(self):
        valid, message = validate_investment_type("ST")
        assert valid is False

    def test_extra_characters(self):
        valid, message = validate_investment_type("STKX")
        assert valid is False


class TestValidateAmount:
    """Test amount validation (additional coverage)."""

    def test_boundary_max(self):
        valid, _ = validate_amount("9999999999999.99")
        assert valid is True

    def test_boundary_min(self):
        valid, _ = validate_amount("-9999999999999.99")
        assert valid is True

    def test_just_over_max(self):
        valid, _ = validate_amount("10000000000000.00")
        assert valid is False

    def test_integer_amount(self):
        valid, _ = validate_amount(42)
        assert valid is True

    def test_special_characters(self):
        valid, _ = validate_amount("$100")
        assert valid is False
