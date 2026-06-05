import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime
from models.history import History


class TestHistoryCreateAuditRecord:

    def test_create_basic_audit_record(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            after_data={"field": "value"},
            reason_code="AUTO",
            user="SYSTEM",
        )
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.reason_code == "AUTO"
        assert record.process_user == "SYSTEM"
        assert record.seq_no == "0001"
        assert record.after_image == json.dumps({"field": "value"})
        assert record.before_image is None

    def test_create_with_before_and_after(self):
        before = {"status": "A"}
        after = {"status": "C"}
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            before_data=before,
            after_data=after,
        )
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)

    def test_create_with_no_data(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="D",
        )
        assert record.before_image is None
        assert record.after_image is None

    def test_seq_no_auto_increments_with_db_session(self):
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3

        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            db_session=mock_session,
        )
        assert record.seq_no == "0004"

    def test_seq_no_default_without_session(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
        )
        assert record.seq_no == "0001"

    def test_date_time_format(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
        )
        assert len(record.date) == 8
        assert record.date.isdigit()
        assert len(record.time) == 8


class TestHistoryGetData:

    def test_get_before_data_valid_json(self):
        h = History(before_image='{"key": "value"}')
        assert h.get_before_data() == {"key": "value"}

    def test_get_before_data_none(self):
        h = History(before_image=None)
        assert h.get_before_data() is None

    def test_get_before_data_invalid_json(self):
        h = History(before_image="not json")
        assert h.get_before_data() is None

    def test_get_after_data_valid_json(self):
        h = History(after_image='{"key": "value"}')
        assert h.get_after_data() == {"key": "value"}

    def test_get_after_data_none(self):
        h = History(after_image=None)
        assert h.get_after_data() is None

    def test_get_after_data_invalid_json(self):
        h = History(after_image="not json")
        assert h.get_after_data() is None


class TestHistoryToDict:

    def test_serialization(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240601",
            time="10300000",
            seq_no="0001",
            record_type="PT",
            action_code="A",
            before_image=None,
            after_image='{"status": "A"}',
            reason_code="AUTO",
            process_date=datetime(2024, 6, 1, 10, 30, 0),
            process_user="SYSTEM",
        )
        d = h.to_dict()
        assert d["portfolio_id"] == "TEST0001"
        assert d["date"] == "20240601"
        assert d["time"] == "10300000"
        assert d["seq_no"] == "0001"
        assert d["record_type"] == "PT"
        assert d["action_code"] == "A"
        assert d["before_data"] is None
        assert d["after_data"] == {"status": "A"}
        assert d["reason_code"] == "AUTO"
        assert d["process_user"] == "SYSTEM"

    def test_serialization_none_process_date(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240601",
            time="10300000",
            seq_no="0001",
            process_date=None,
        )
        d = h.to_dict()
        assert d["process_date"] is None
