import pytest
import json
from datetime import datetime
from models.history import History


class TestHistoryCreateAuditRecord:
    """Test History.create_audit_record class method."""

    def test_creates_record_with_required_fields(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="A",
        )
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "TR"
        assert record.action_code == "A"
        assert record.reason_code == "AUTO"
        assert record.process_user == "SYSTEM"
        assert record.process_date is not None

    def test_creates_record_with_before_and_after_data(self):
        before = {"status": "P", "amount": 100}
        after = {"status": "D", "amount": 100}
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PS",
            action_code="C",
            before_data=before,
            after_data=after,
        )
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)

    def test_creates_record_with_custom_user_and_reason(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="D",
            reason_code="FEE",
            user="ADMIN01",
        )
        assert record.reason_code == "FEE"
        assert record.process_user == "ADMIN01"

    def test_none_before_data_sets_null(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="A",
            before_data=None,
        )
        assert record.before_image is None

    def test_date_and_time_format(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="A",
        )
        assert len(record.date) == 8
        assert record.date.isdigit()
        assert len(record.time) == 8

    def test_seq_no_with_db_session(self, db_session):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="A",
            db_session=db_session,
        )
        assert record.seq_no == "0001"


class TestHistoryGetBeforeData:
    """Test History.get_before_data method."""

    def test_returns_parsed_json(self):
        h = History(before_image='{"key": "value"}')
        assert h.get_before_data() == {"key": "value"}

    def test_returns_none_for_null(self):
        h = History(before_image=None)
        assert h.get_before_data() is None

    def test_returns_none_for_invalid_json(self):
        h = History(before_image="not-valid-json{")
        assert h.get_before_data() is None


class TestHistoryGetAfterData:
    """Test History.get_after_data method."""

    def test_returns_parsed_json(self):
        h = History(after_image='{"status": "D"}')
        assert h.get_after_data() == {"status": "D"}

    def test_returns_none_for_null(self):
        h = History(after_image=None)
        assert h.get_after_data() is None

    def test_returns_none_for_invalid_json(self):
        h = History(after_image="{{invalid}}")
        assert h.get_after_data() is None


class TestHistoryToDict:
    """Test History.to_dict method."""

    def test_serializes_all_fields(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240615",
            time="09300000",
            seq_no="0001",
            record_type="TR",
            action_code="A",
            before_image='{"old": true}',
            after_image='{"new": true}',
            reason_code="PROC",
            process_date=datetime(2024, 6, 15, 9, 30),
            process_user="ADMIN",
        )
        d = h.to_dict()
        assert d["portfolio_id"] == "TEST0001"
        assert d["date"] == "20240615"
        assert d["time"] == "09300000"
        assert d["seq_no"] == "0001"
        assert d["record_type"] == "TR"
        assert d["action_code"] == "A"
        assert d["before_data"] == {"old": True}
        assert d["after_data"] == {"new": True}
        assert d["reason_code"] == "PROC"
        assert d["process_user"] == "ADMIN"

    def test_handles_none_process_date(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240615",
            time="09300000",
            seq_no="0001",
            process_date=None,
        )
        d = h.to_dict()
        assert d["process_date"] is None
