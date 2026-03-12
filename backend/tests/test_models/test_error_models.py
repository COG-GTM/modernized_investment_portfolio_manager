"""Tests for error handling models translated from ERRHAND, RTNCODE, RETHND copybooks."""

import pytest

from app.models.error_record import (
    ERROR_CATEGORIES,
    ERROR_CODES,
    VSAM_STATUSES,
    ErrorCategories,
    ErrorMessage,
    ErrorRecord,
)
from app.models.return_code import ReturnCode
from app.models.retry_handler import (
    ErrorInfo,
    ErrorLocation,
    ReturnActions,
    ReturnHandling,
    STD_ERROR_CODES,
    StandardErrorCodes,
)


class TestErrorRecord:
    def test_default_severity_values(self) -> None:
        er = ErrorRecord()
        assert er.success == 0
        assert er.warning == 4
        assert er.error == 8
        assert er.severe == 12
        assert er.terminal == 16

    def test_module_constants(self) -> None:
        assert ERROR_CODES.success == 0
        assert ERROR_CODES.terminal == 16


class TestErrorCategories:
    def test_default_categories(self) -> None:
        ec = ErrorCategories()
        assert ec.vsam == "VS"
        assert ec.validation == "VL"
        assert ec.processing == "PR"
        assert ec.system == "SY"

    def test_module_constant(self) -> None:
        assert ERROR_CATEGORIES.vsam == "VS"


class TestErrorMessage:
    def test_creation(self) -> None:
        msg = ErrorMessage(
            err_date="2024-03-20",
            err_time="14:30:00",
            err_program="TRNVAL00",
            err_category="VL",
            err_code="E001",
            err_severity=8,
            err_text="Validation failed",
            err_details="Invalid portfolio ID",
        )
        assert msg.err_program == "TRNVAL00"
        assert msg.err_severity == 8


class TestReturnCode:
    def test_default_values(self) -> None:
        rc = ReturnCode()
        assert rc.rtc_current_code == 0
        assert rc.rtc_highest_code == 0

    def test_set_code(self) -> None:
        rc = ReturnCode()
        rc.set_code(8)
        assert rc.rtc_current_code == 8
        assert rc.rtc_highest_code == 8

    def test_set_code_tracks_highest(self) -> None:
        rc = ReturnCode()
        rc.set_code(4)
        rc.set_code(12)
        rc.set_code(8)
        assert rc.rtc_current_code == 8
        assert rc.rtc_highest_code == 12

    def test_get_code(self) -> None:
        rc = ReturnCode()
        rc.set_code(8)
        assert rc.get_code() == 8

    def test_initialize(self) -> None:
        rc = ReturnCode()
        rc.set_code(12)
        rc.initialize()
        assert rc.rtc_current_code == 0
        assert rc.rtc_highest_code == 0


class TestReturnHandling:
    def test_severity_properties(self) -> None:
        rh = ReturnHandling(rh_return_code=0)
        assert rh.is_success is True
        assert rh.is_warning is False

        rh2 = ReturnHandling(rh_return_code=4)
        assert rh2.is_warning is True
        assert rh2.is_error is False

        rh3 = ReturnHandling(rh_return_code=8)
        assert rh3.is_error is True

        rh4 = ReturnHandling(rh_return_code=12)
        assert rh4.is_severe is True

        rh5 = ReturnHandling(rh_return_code=16)
        assert rh5.is_critical is True


class TestReturnActions:
    def test_retry_logic(self) -> None:
        ra = ReturnActions(max_retries=3, retry_count=0)
        assert ra.should_retry() is True
        ra.increment_retry()
        assert ra.retry_count == 1
        assert ra.should_retry() is True
        ra.increment_retry()
        ra.increment_retry()
        assert ra.retry_count == 3
        assert ra.should_retry() is False

    def test_reset(self) -> None:
        ra = ReturnActions(max_retries=3, retry_count=2)
        ra.reset()
        assert ra.retry_count == 0


class TestStandardErrorCodes:
    def test_standard_codes_exist(self) -> None:
        assert STD_ERROR_CODES.e001 == "E001"
        assert STD_ERROR_CODES.e010 == "E010"
