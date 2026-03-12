"""Tests for batch processing models translated from BCHCTL, BCHCON, PRCSEQ, CKPRST copybooks."""

import pytest

from app.models.batch_control import BatchControlRecord, PrerequisiteJob
from app.models.batch_constants import BatchConstants, BATCH_CONSTANTS
from app.models.process_sequence import ProcessSequenceRecord, DependencyEntry, STANDARD_SEQUENCES
from app.models.checkpoint_restart import CheckpointControl, CheckpointRecord, FileStatus


class TestBatchControlRecord:
    def test_default_values(self) -> None:
        bcr = BatchControlRecord()
        assert bcr.bch_status == "W"
        assert bcr.bch_return_code == 0
        assert bcr.bch_prereq_count == 0

    def test_prerequisites_met_empty(self) -> None:
        bcr = BatchControlRecord(bch_prereq_count=0, bch_prereq_jobs=[])
        assert bcr.are_prerequisites_met() is True

    def test_prerequisites_met_all_zero(self) -> None:
        jobs = [
            PrerequisiteJob(prereq_name="JOB1", prereq_seq=1, prereq_rc=0),
            PrerequisiteJob(prereq_name="JOB2", prereq_seq=2, prereq_rc=0),
        ]
        bcr = BatchControlRecord(bch_prereq_count=2, bch_prereq_jobs=jobs)
        assert bcr.are_prerequisites_met() is True

    def test_prerequisites_not_met(self) -> None:
        jobs = [
            PrerequisiteJob(prereq_name="JOB1", prereq_seq=1, prereq_rc=0),
            PrerequisiteJob(prereq_name="JOB2", prereq_seq=2, prereq_rc=8),
        ]
        bcr = BatchControlRecord(bch_prereq_count=2, bch_prereq_jobs=jobs)
        assert bcr.are_prerequisites_met() is False

    def test_all_status_values(self) -> None:
        for status in ["R", "A", "W", "D", "E"]:
            bcr = BatchControlRecord(bch_status=status)
            assert bcr.bch_status == status


class TestBatchConstants:
    def test_module_constant(self) -> None:
        assert BATCH_CONSTANTS.bct_status_ready == "R"
        assert BATCH_CONSTANTS.bct_status_active == "A"
        assert BATCH_CONSTANTS.bct_status_waiting == "W"
        assert BATCH_CONSTANTS.bct_status_done == "D"
        assert BATCH_CONSTANTS.bct_status_error == "E"

    def test_return_codes(self) -> None:
        assert BATCH_CONSTANTS.bct_rc_success == 0
        assert BATCH_CONSTANTS.bct_rc_warning == 4
        assert BATCH_CONSTANTS.bct_rc_error == 8
        assert BATCH_CONSTANTS.bct_rc_severe == 12
        assert BATCH_CONSTANTS.bct_rc_critical == 16

    def test_control_values(self) -> None:
        assert BATCH_CONSTANTS.bct_max_prereq == 10
        assert BATCH_CONSTANTS.bct_max_restarts == 3
        assert BATCH_CONSTANTS.bct_wait_interval == 300
        assert BATCH_CONSTANTS.bct_max_wait_time == 3600


class TestProcessSequenceRecord:
    def test_default_values(self) -> None:
        psr = ProcessSequenceRecord()
        assert psr.prc_restart == "Y"
        assert psr.prc_dep_count == 0

    def test_is_restartable(self) -> None:
        psr = ProcessSequenceRecord(prc_restart="Y")
        assert psr.is_restartable is True
        psr2 = ProcessSequenceRecord(prc_restart="N")
        assert psr2.is_restartable is False

    def test_standard_sequences(self) -> None:
        assert STANDARD_SEQUENCES.start_of_day is not None
        assert STANDARD_SEQUENCES.main_process is not None
        assert STANDARD_SEQUENCES.end_of_day is not None


class TestCheckpointControl:
    def test_default_values(self) -> None:
        ck = CheckpointControl()
        assert ck.ck_commit_freq == 1000
        assert ck.ck_max_errors == 100
        assert ck.ck_max_restarts == 3
        assert ck.ck_restart_mode == "N"

    def test_should_commit(self) -> None:
        ck = CheckpointControl(ck_commit_freq=100, ck_records_proc=100)
        assert ck.should_commit() is True
        ck2 = CheckpointControl(ck_commit_freq=100, ck_records_proc=50)
        assert ck2.should_commit() is False

    def test_has_exceeded_errors(self) -> None:
        ck = CheckpointControl(ck_max_errors=10, ck_records_error=10)
        assert ck.has_exceeded_errors() is True
        ck2 = CheckpointControl(ck_max_errors=10, ck_records_error=5)
        assert ck2.has_exceeded_errors() is False

    def test_can_restart(self) -> None:
        ck = CheckpointControl(ck_max_restarts=3, ck_restart_count=2)
        assert ck.can_restart() is True
        ck2 = CheckpointControl(ck_max_restarts=3, ck_restart_count=3)
        assert ck2.can_restart() is False

    def test_file_statuses_list(self) -> None:
        ck = CheckpointControl()
        assert len(ck.ck_file_statuses) == 5
        for fs in ck.ck_file_statuses:
            assert isinstance(fs, FileStatus)


class TestCheckpointRecord:
    def test_default_values(self) -> None:
        cr = CheckpointRecord()
        assert cr.ckr_program_id == ""
        assert cr.ckr_run_date == ""
        assert cr.ckr_data == ""
