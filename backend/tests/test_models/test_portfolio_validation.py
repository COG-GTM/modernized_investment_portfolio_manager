"""Tests for PortfolioValidation model translated from PORTVAL.cpy."""

import pytest
from decimal import Decimal

from app.models.portfolio_validation import PortfolioValidation


class TestPortfolioValidation:
    def setup_method(self) -> None:
        self.validator = PortfolioValidation()

    def test_valid_portfolio_id(self) -> None:
        rc, msg = self.validator.validate_portfolio_id("PORT0001")
        assert rc == 0
        assert msg == ""

    def test_invalid_portfolio_id_empty(self) -> None:
        rc, msg = self.validator.validate_portfolio_id("")
        assert rc == 1
        assert msg == "Invalid Portfolio ID format"

    def test_invalid_portfolio_id_too_long(self) -> None:
        rc, msg = self.validator.validate_portfolio_id("PORT00001X")
        assert rc == 1

    def test_invalid_portfolio_id_prefix(self) -> None:
        rc, msg = self.validator.validate_portfolio_id("ABCD0001")
        assert rc == 1

    def test_valid_account_number(self) -> None:
        rc, msg = self.validator.validate_account_number("1234567890")
        assert rc == 0
        assert msg == ""

    def test_invalid_account_empty(self) -> None:
        rc, msg = self.validator.validate_account_number("")
        assert rc == 2
        assert msg == "Invalid Account Number format"

    def test_invalid_account_too_short(self) -> None:
        rc, msg = self.validator.validate_account_number("12345")
        assert rc == 2

    def test_invalid_account_non_numeric(self) -> None:
        rc, msg = self.validator.validate_account_number("123456789A")
        assert rc == 2

    def test_valid_amount(self) -> None:
        rc, msg = self.validator.validate_amount(Decimal("1000.00"))
        assert rc == 0
        assert msg == ""

    def test_valid_negative_amount(self) -> None:
        rc, msg = self.validator.validate_amount(Decimal("-1000.00"))
        assert rc == 0

    def test_invalid_amount_too_large(self) -> None:
        rc, msg = self.validator.validate_amount(Decimal("99999999999999.99"))
        assert rc == 4
        assert msg == "Amount outside valid range"

    def test_valid_max_boundary(self) -> None:
        rc, msg = self.validator.validate_amount(Decimal("9999999999999.99"))
        assert rc == 0

    def test_valid_min_boundary(self) -> None:
        rc, msg = self.validator.validate_amount(Decimal("-9999999999999.99"))
        assert rc == 0

    def test_default_constants(self) -> None:
        v = PortfolioValidation()
        assert v.val_id_prefix == "PORT"
        assert v.val_min_amount == Decimal("-9999999999999.99")
        assert v.val_max_amount == Decimal("9999999999999.99")
