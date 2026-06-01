import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.history import History


class TestHistoryGetData:
    """Test History.get_before_data() and get_after_data()"""

    def test_get_before_data_valid_json(self):
        h = History(before_image='{"key": "value"}')
        result = h.get_before_data()
        assert result == {"key": "value"}

    def test_get_before_data_none(self):
        h = History(before_image=None)
        result = h.get_before_data()
        assert result is None

    def test_get_before_data_invalid_json(self):
        h = History(before_image="not valid json")
        result = h.get_before_data()
        assert result is None

    def test_get_after_data_valid_json(self):
        h = History(after_image='{"amount": 1000}')
        result = h.get_after_data()
        assert result == {"amount": 1000}

    def test_get_after_data_none(self):
        h = History(after_image=None)
        result = h.get_after_data()
        assert result is None

    def test_get_after_data_invalid_json(self):
        h = History(after_image="{bad json")
        result = h.get_after_data()
        assert result is None

    def test_get_before_data_complex_object(self):
        data = {"portfolio_id": "PORT0001", "positions": [{"id": 1}], "nested": {"a": "b"}}
        h = History(before_image=json.dumps(data))
        result = h.get_before_data()
        assert result == data


class TestHistoryCreateAuditRecord:
    """Test History.create_audit_record()"""

    def test_create_audit_record_basic(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
            after_data={"amount": 1000},
            reason_code="PROC",
            user="ADMIN01",
        )
        assert record.portfolio_id == "PORT0001"
        assert record.record_type == "TR"
        assert record.action_code == "A"
        assert record.reason_code == "PROC"
        assert record.process_user == "ADMIN01"
        assert record.before_image is None
        assert json.loads(record.after_image) == {"amount": 1000}

    def test_create_audit_record_with_before_data(self):
        before = {"status": "old"}
        after = {"status": "new"}
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="PS",
            action_code="C",
            before_data=before,
            after_data=after,
        )
        assert json.loads(record.before_image) == before
        assert json.loads(record.after_image) == after

    def test_create_audit_record_default_user(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
        )
        assert record.process_user == "SYSTEM"

    def test_create_audit_record_default_reason_code(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
        )
        assert record.reason_code == "AUTO"

    def test_create_audit_record_with_db_session(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3

        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
            db_session=mock_db,
        )
        assert record.seq_no == "0004"

    def test_create_audit_record_date_format(self):
        record = History.create_audit_record(
            portfolio_id="PORT0001",
            record_type="TR",
            action_code="A",
        )
        assert len(record.date) == 8
        assert record.date.isdigit()
        assert len(record.time) == 8


class TestHistoryToDict:
    """Test History.to_dict()"""

    def test_to_dict(self):
        h = History(
            portfolio_id="PORT0001",
            date="20240115",
            time="09300000",
            seq_no="0001",
            record_type="TR",
            action_code="A",
            before_image=None,
            after_image='{"amount": 1000}',
            reason_code="PROC",
            process_date=datetime(2024, 1, 15, 9, 30, 0),
            process_user="ADMIN01",
        )
        d = h.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["date"] == "20240115"
        assert d["time"] == "09300000"
        assert d["seq_no"] == "0001"
        assert d["record_type"] == "TR"
        assert d["action_code"] == "A"
        assert d["before_data"] is None
        assert d["after_data"] == {"amount": 1000}
        assert d["reason_code"] == "PROC"
        assert d["process_user"] == "ADMIN01"

    def test_to_dict_none_process_date(self):
        h = History(
            portfolio_id="PORT0001",
            date="20240115",
            time="09300000",
            seq_no="0001",
            record_type="TR",
            action_code="A",
            process_date=None,
        )
        d = h.to_dict()
        assert d["process_date"] is None
