"""Tests for online/DB2 models translated from INQCOM, DB2REQ, ERRHND, DBPROC copybooks."""

import pytest
from pydantic import ValidationError

from app.models.inquiry_common import InquiryCommon
from app.models.db2_request import DB2Request
from app.models.online_error_handler import OnlineErrorHandler
from app.models.db2_procedure import DB2Procedure, SQL_STATUS_CODES


class TestInquiryCommon:
    def test_default_values(self) -> None:
        inq = InquiryCommon()
        assert inq.inq_function == "MENU"
        assert inq.inq_account_no == ""
        assert inq.inq_response_code == 0

    def test_all_function_values(self) -> None:
        for func in ["MENU", "INQP", "INQH", "EXIT"]:
            inq = InquiryCommon(inq_function=func)
            assert inq.inq_function == func

    def test_invalid_function(self) -> None:
        with pytest.raises(ValidationError):
            InquiryCommon(inq_function="XXXX")


class TestDB2Request:
    def test_default_values(self) -> None:
        req = DB2Request()
        assert req.db2_request_type == "C"
        assert req.db2_response_code == 0

    def test_all_request_types(self) -> None:
        for rtype in ["C", "D", "S"]:
            req = DB2Request(db2_request_type=rtype)
            assert req.db2_request_type == rtype

    def test_invalid_request_type(self) -> None:
        with pytest.raises(ValidationError):
            DB2Request(db2_request_type="X")


class TestOnlineErrorHandler:
    def test_default_values(self) -> None:
        err = OnlineErrorHandler()
        assert err.err_severity == "I"
        assert err.err_action == "R"
        assert err.err_sqlcode == 0

    def test_all_severity_values(self) -> None:
        for sev in ["F", "W", "I"]:
            err = OnlineErrorHandler(err_severity=sev)
            assert err.err_severity == sev

    def test_all_action_values(self) -> None:
        for action in ["R", "C", "A"]:
            err = OnlineErrorHandler(err_action=action)
            assert err.err_action == action

    def test_invalid_severity(self) -> None:
        with pytest.raises(ValidationError):
            OnlineErrorHandler(err_severity="X")


class TestDB2Procedure:
    def test_default_values(self) -> None:
        proc = DB2Procedure()
        assert proc.db2_max_retries == 3
        assert proc.db2_retry_wait == 100
        assert proc.db2_retry_count == 0

    def test_should_retry(self) -> None:
        proc = DB2Procedure(db2_retry_count=0, db2_max_retries=3)
        assert proc.should_retry() is True
        proc2 = DB2Procedure(db2_retry_count=3, db2_max_retries=3)
        assert proc2.should_retry() is False

    def test_format_error_message(self) -> None:
        proc = DB2Procedure(
            db2_sqlcode_txt="-803",
            db2_state="23505",
            db2_error_text="Duplicate key",
        )
        msg = proc.format_error_message()
        assert "-803" in msg
        assert "23505" in msg
        assert "Duplicate key" in msg


class TestSQLStatusCodes:
    def test_status_codes_exist(self) -> None:
        assert SQL_STATUS_CODES["SUCCESS"] == "00000"
        assert SQL_STATUS_CODES["NOT_FOUND"] == "02000"
        assert SQL_STATUS_CODES["DUP_KEY"] == "23505"
        assert SQL_STATUS_CODES["DEADLOCK"] == "40001"
        assert SQL_STATUS_CODES["TIMEOUT"] == "40003"
        assert SQL_STATUS_CODES["CONNECTION_ERROR"] == "08001"
        assert SQL_STATUS_CODES["DB_ERROR"] == "58004"
