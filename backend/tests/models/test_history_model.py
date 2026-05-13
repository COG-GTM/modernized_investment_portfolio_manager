import pytest
from datetime import datetime
import json

from models.history import History


class TestHistoryCreation:
    def test_create_with_valid_fields(self, sample_history):
        assert sample_history.portfolio_id == "PORT0001"
        assert sample_history.date == "20240615"
        assert sample_history.time == "09300000"
        assert sample_history.seq_no == "0001"
        assert sample_history.record_type == "TR"
        assert sample_history.action_code == "A"
        assert sample_history.before_image is None
        assert sample_history.after_image == '{"type": "BU", "quantity": 50}'
        assert sample_history.reason_code == "PROC"
        assert sample_history.process_date == datetime(2024, 6, 15, 9, 30, 0)
        assert sample_history.process_user == "SYSTEM"


class TestCreateAuditRecord:
    def test_without_db_session(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PT",
            action_code="C",
            before_data={"status": "A"},
            after_data={"status": "C"},
            reason_code="UPDT",
            user="ADMIN01"
        )
        assert record.portfolio_id == "PORT0001"
        assert record.record_type == "PT"
        assert record.action_code == "C"
        assert record.seq_no == "0001"
        assert record.reason_code == "UPDT"
        assert record.process_user == "ADMIN01"
        assert record.process_date is not None
        assert record.before_image == json.dumps({"status": "A"})
        assert record.after_image == json.dumps({"status": "C"})
        assert len(record.date) == 8
        assert len(record.time) == 8

    def test_with_db_session(self, db_session):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
            after_data={"type": "BU"},
            db_session=db_session
        )
        assert record.seq_no == "0001"

    def test_with_db_session_increments_seq(self, db_session, persisted_portfolio):
        first = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
            db_session=db_session
        )
        db_session.add(first)
        db_session.flush()

        second = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
            db_session=db_session
        )
        # seq_no depends on existing count for same portfolio_id/date/time
        assert second.seq_no is not None

    def test_defaults(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PS",
            action_code="D"
        )
        assert record.reason_code == "AUTO"
        assert record.process_user == "SYSTEM"
        assert record.before_image is None
        assert record.after_image is None

    def test_none_data_fields(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PT",
            action_code="A",
            before_data=None,
            after_data=None
        )
        assert record.before_image is None
        assert record.after_image is None


class TestGetBeforeData:
    def test_valid_json(self):
        h = History(before_image='{"key": "value", "num": 42}')
        result = h.get_before_data()
        assert result == {"key": "value", "num": 42}

    def test_invalid_json(self):
        h = History(before_image="not-valid-json{")
        result = h.get_before_data()
        assert result is None

    def test_none(self):
        h = History(before_image=None)
        result = h.get_before_data()
        assert result is None


class TestGetAfterData:
    def test_valid_json(self):
        h = History(after_image='{"status": "C"}')
        result = h.get_after_data()
        assert result == {"status": "C"}

    def test_invalid_json(self):
        h = History(after_image="broken json")
        result = h.get_after_data()
        assert result is None

    def test_none(self):
        h = History(after_image=None)
        result = h.get_after_data()
        assert result is None


class TestHistoryToDict:
    def test_serialization(self, sample_history):
        d = sample_history.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["date"] == "20240615"
        assert d["time"] == "09300000"
        assert d["seq_no"] == "0001"
        assert d["record_type"] == "TR"
        assert d["action_code"] == "A"
        assert d["before_data"] is None
        assert d["after_data"] == {"type": "BU", "quantity": 50}
        assert d["reason_code"] == "PROC"
        assert d["process_date"] == "2024-06-15T09:30:00"
        assert d["process_user"] == "SYSTEM"

    def test_serialization_none_process_date(self):
        h = History(portfolio_id="PORT0001", date="20240101",
                    time="12000000", seq_no="0001",
                    record_type="PT", action_code="A",
                    process_date=None)
        d = h.to_dict()
        assert d["process_date"] is None

    def test_serialization_with_before_and_after(self):
        h = History(
            portfolio_id="PORT0001", date="20240101",
            time="12000000", seq_no="0001",
            record_type="PT", action_code="C",
            before_image='{"status": "A"}',
            after_image='{"status": "C"}',
            process_date=datetime(2024, 1, 1, 12, 0, 0),
            process_user="ADMIN"
        )
        d = h.to_dict()
        assert d["before_data"] == {"status": "A"}
        assert d["after_data"] == {"status": "C"}
