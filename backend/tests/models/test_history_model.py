import pytest
import json
from datetime import datetime

from models.history import History


class TestHistoryCreation:
    def test_valid_creation(self, sample_history):
        assert sample_history.portfolio_id == "PORT0001"
        assert sample_history.date == "20240615"
        assert sample_history.time == "09300000"
        assert sample_history.seq_no == "0001"
        assert sample_history.record_type == "TR"
        assert sample_history.action_code == "A"
        assert sample_history.before_image is None
        assert sample_history.after_image == '{"type": "BU", "quantity": 100}'
        assert sample_history.reason_code == "PROC"
        assert sample_history.process_date == datetime(2024, 6, 15, 9, 30, 0)
        assert sample_history.process_user == "SYSTEM"


class TestHistoryCreateAuditRecord:
    def test_basic_creation(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PT",
            action_code="A",
        )
        assert record.portfolio_id == "PORT0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.seq_no == "0001"
        assert record.reason_code == "AUTO"
        assert record.process_user == "SYSTEM"
        assert record.process_date is not None
        assert len(record.date) == 8
        assert len(record.time) == 8

    def test_with_db_session_for_seq_no(self, db_session):
        record1 = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PT",
            action_code="A",
            db_session=db_session,
        )
        db_session.add(record1)
        db_session.flush()

        record2 = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PT",
            action_code="C",
            db_session=db_session,
        )
        assert record2.seq_no in ("0001", "0002")

    def test_with_before_after_data(self):
        before = {"status": "A", "total_value": 50000}
        after = {"status": "C", "total_value": 0}
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PS",
            action_code="C",
            before_data=before,
            after_data=after,
            reason_code="CLSE",
            user="ADMIN01",
        )
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)
        assert record.reason_code == "CLSE"
        assert record.process_user == "ADMIN01"


class TestHistoryGetData:
    def test_get_before_data_valid_json(self):
        history = History(before_image='{"key": "value", "num": 42}')
        result = history.get_before_data()
        assert result == {"key": "value", "num": 42}

    def test_get_before_data_invalid_json(self):
        history = History(before_image="not valid json {{")
        result = history.get_before_data()
        assert result is None

    def test_get_before_data_none(self):
        history = History(before_image=None)
        result = history.get_before_data()
        assert result is None

    def test_get_after_data_valid_json(self):
        history = History(after_image='{"type": "BU", "quantity": 100}')
        result = history.get_after_data()
        assert result == {"type": "BU", "quantity": 100}

    def test_get_after_data_invalid_json(self):
        history = History(after_image="corrupted data")
        result = history.get_after_data()
        assert result is None

    def test_get_after_data_none(self):
        history = History(after_image=None)
        result = history.get_after_data()
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
        assert d["after_data"] == {"type": "BU", "quantity": 100}
        assert d["reason_code"] == "PROC"
        assert d["process_date"] == "2024-06-15T09:30:00"
        assert d["process_user"] == "SYSTEM"

    def test_serialization_with_none_process_date(self):
        history = History(
            portfolio_id="PORT0002",
            date="20240701",
            time="12000000",
            seq_no="0001",
            record_type="PT",
            action_code="A",
            process_date=None,
            process_user="TEST",
        )
        d = history.to_dict()
        assert d["process_date"] is None
        assert d["before_data"] is None
        assert d["after_data"] is None
