import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock

from models.history import History


class TestHistoryCreateAuditRecord:

    def test_creates_record_without_session(self):
        record = History.create_audit_record(
            portfolio_id="PORT1234",
            record_type="PT",
            action_code="A",
            after_data={"key": "value"},
            reason_code="AUTO",
            user="ADMIN"
        )
        assert record.portfolio_id == "PORT1234"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.after_image == '{"key": "value"}'
        assert record.before_image is None
        assert record.reason_code == "AUTO"
        assert record.process_user == "ADMIN"
        assert record.seq_no == "0001"
        assert record.process_date is not None

    def test_creates_record_with_before_data(self):
        record = History.create_audit_record(
            portfolio_id="PORT1234",
            record_type="PS",
            action_code="C",
            before_data={"old": "data"},
            after_data={"new": "data"},
        )
        assert record.before_image == '{"old": "data"}'
        assert record.after_image == '{"new": "data"}'

    def test_creates_record_with_no_data(self):
        record = History.create_audit_record(
            portfolio_id="PORT1234",
            record_type="TR",
            action_code="D",
        )
        assert record.before_image is None
        assert record.after_image is None

    def test_seq_no_increments_with_session(self):
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3

        record = History.create_audit_record(
            portfolio_id="PORT1234",
            record_type="PT",
            action_code="A",
            db_session=mock_session,
        )
        assert record.seq_no == "0004"

    def test_default_user_and_reason(self):
        record = History.create_audit_record(
            portfolio_id="PORT1234",
            record_type="PT",
            action_code="A",
        )
        assert record.process_user == "SYSTEM"
        assert record.reason_code == "AUTO"

    def test_date_and_time_format(self):
        record = History.create_audit_record(
            portfolio_id="PORT1234",
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

    def test_to_dict_with_values(self):
        h = History(
            portfolio_id="PORT1234",
            date="20240601",
            time="09300000",
            seq_no="0001",
            record_type="PT",
            action_code="A",
            before_image='{"old": "data"}',
            after_image='{"new": "data"}',
            reason_code="AUTO",
            process_date=datetime(2024, 6, 1, 9, 30),
            process_user="ADMIN"
        )
        d = h.to_dict()
        assert d["portfolio_id"] == "PORT1234"
        assert d["date"] == "20240601"
        assert d["time"] == "09300000"
        assert d["seq_no"] == "0001"
        assert d["record_type"] == "PT"
        assert d["action_code"] == "A"
        assert d["before_data"] == {"old": "data"}
        assert d["after_data"] == {"new": "data"}
        assert d["reason_code"] == "AUTO"
        assert d["process_user"] == "ADMIN"

    def test_to_dict_with_none_process_date(self):
        h = History(
            portfolio_id="PORT1234", date="20240601", time="09300000",
            seq_no="0001", record_type="PT", action_code="A", process_date=None
        )
        d = h.to_dict()
        assert d["process_date"] is None
