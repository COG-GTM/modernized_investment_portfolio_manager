"""Tests for common models translated from COMMON.cpy."""

import pytest

from app.models.common import (
    CURRENCY_CODES,
    RETURN_CODES,
    STATUS_CODES,
    TRANSACTION_TYPES,
    CommonAuditFields,
    CommonDatetime,
    CommonErrorHandling,
    CurrencyCodes,
    ReturnCodeValues,
    StatusCodes,
    TransactionTypes,
)


class TestReturnCodeValues:
    def test_default_values(self) -> None:
        rc = ReturnCodeValues()
        assert rc.success == 0
        assert rc.warning == 4
        assert rc.error == 8
        assert rc.severe == 12
        assert rc.critical == 16

    def test_module_constant(self) -> None:
        assert RETURN_CODES.success == 0
        assert RETURN_CODES.critical == 16


class TestStatusCodes:
    def test_default_values(self) -> None:
        sc = StatusCodes()
        assert sc.active == "A"
        assert sc.closed == "C"
        assert sc.pending == "P"
        assert sc.suspended == "S"
        assert sc.failed == "F"
        assert sc.reversed == "R"


class TestTransactionTypes:
    def test_default_values(self) -> None:
        tt = TransactionTypes()
        assert tt.buy == "BU"
        assert tt.sell == "SL"
        assert tt.transfer == "TR"
        assert tt.fee == "FE"


class TestCurrencyCodes:
    def test_default_values(self) -> None:
        cc = CurrencyCodes()
        assert cc.usd == "USD"
        assert cc.eur == "EUR"
        assert cc.gbp == "GBP"
        assert cc.jpy == "JPY"
        assert cc.cad == "CAD"


class TestCommonDatetime:
    def test_default_empty(self) -> None:
        dt = CommonDatetime()
        assert dt.curr_year == ""
        assert dt.curr_month == ""

    def test_with_values(self) -> None:
        dt = CommonDatetime(
            curr_year="2024",
            curr_month="03",
            curr_day="20",
            curr_hour="14",
            curr_minute="30",
            curr_second="00",
            curr_msec="00",
        )
        assert dt.curr_year == "2024"
        assert dt.curr_day == "20"


class TestCommonErrorHandling:
    def test_default_empty(self) -> None:
        err = CommonErrorHandling()
        assert err.error_code == ""
        assert err.error_module == ""


class TestCommonAuditFields:
    def test_default_empty(self) -> None:
        aud = CommonAuditFields()
        assert aud.audit_timestamp == ""
        assert aud.audit_user == ""
