"""Tests for batch processing models translated from BCHCTL, BCHCON, PRCSEQ, CKPRST copybooks."""

import pytest

from app.models.batch_control import BatchControlRecord, PrerequisiteJob
from app.models.batch_constants import BatchConstants, BATCH_CONSTANTS
from app.models.process_sequence import ProcessSequenceRecord, DependencyEntry, STANDARD_SEQUENCES
from app.models.checkpoint_restart import CheckpointControl, CheckpointRecord, FileStatus


class TestBatchControlRecord:
    def test_with_required_fields(self) -> None:
        bcr = BatchControlRecord(
            bct_job_name="TRNVAL00",
            bct_process_date="20240320",
            bct_sequence_no=1,
        )
        assert bcr.bct_status == "R"
        assert bcr.bct_return_code == 0
        assert bcr.bct_prereq_count == 0

    def test_prerequisites_met_empty(self) -> None:
        bcr = BatchControlRecord(
            bct_job_name="TRNVAL00",
            bct_process_date="20240320",
            bct_sequence_no=1,
            bct_prereq_count=0,
            bct_prereq_jobs=[],
        )
        assert bcr.are_prerequisites_met({}) is True

    def test_prerequisites_met_all_zero(self) -> None:
        jobs = [
            PrerequisiteJob(prereq_name="JOB1", prereq_seq=1, prereq_rc=0),
            PrerequisiteJob(prereq_name="JOB2", prereq_seq=2, prereq_rc=0),
        ]
        bcr = BatchControlRecord(
            bct_job_name="TRNVAL00",
            bct_process_date="20240320",
            bct_sequence_no=1,
            bct_prereq_count=2,
            bct_prereq_jobs=jobs,
        )
        assert bcr.are_prerequisites_met({"JOB1": 0, "JOB2": 0}) is True

    def test_prerequisites_not_met(self) -> None:
        jobs = [
            PrerequisiteJob(prereq_name="JOB1", prereq_seq=1, prereq_rc=0),
            PrerequisiteJob(prereq_name="JOB2", prereq_seq=2, prereq_rc=0),
        ]
        bcr = BatchControlRecord(
            bct_job_name="TRNVAL00",
            bct_process_date="20240320",
            bct_sequence_no=1,
            bct_prereq_count=2,
            bct_prereq_jobs=jobs,
        )
        assert bcr.are_prerequisites_met({"JOB1": 0, "JOB2": 8}) is False

    def test_all_status_values(self) -> None:
        for status in ["R", "A", "W", "D", "E"]:
            bcr = BatchControlRecord(
                bct_job_name="TRNVAL00",
                bct_process_date="20240320",
                bct_sequence_no=1,
                bct_status=status,
            )
            assert bcr.bct_status == status


class TestBatchConstants:
    def test_module_constant_statuses(self) -> None:
        assert BATCH_CONSTANTS.stat_ready == "R"
        assert BATCH_CONSTANTS.stat_active == "A"
        assert BATCH_CONSTANTS.stat_waiting == "W"
        assert BATCH_CONSTANTS.stat_done == "D"
        assert BATCH_CONSTANTS.stat_error == "E"

    def test_return_codes(self) -> None:
        assert BATCH_CONSTANTS.rc_success == 0
        assert BATCH_CONSTANTS.rc_warning == 4
        assert BATCH_CONSTANTS.rc_error == 8
        assert BATCH_CONSTANTS.rc_severe == 12
        assert BATCH_CONSTANTS.rc_critical == 16

    def test_control_values(self) -> None:
        assert BATCH_CONSTANTS.max_prereq == 10
        assert BATCH_CONSTANTS.max_restarts == 3
        assert BATCH_CONSTANTS.wait_interval == 300
        assert BATCH_CONSTANTS.max_wait_time == 3600


class TestProcessSequenceRecord:
    def test_with_required_fields(self) -> None:
        psr = ProcessSequenceRecord(psr_process_id="TRNVAL00")
        assert psr.psr_restart == "Y"
        assert psr.psr_dep_count == 0

    def test_is_restartable(self) -> None:
        psr = ProcessSequenceRecord(psr_process_id="TRNVAL00", psr_restart="Y")
        assert psr.is_restartable is True
        psr2 = ProcessSequenceRecord(psr_process_id="TRNVAL00", psr_restart="N")
        assert psr2.is_restartable is False

    def test_standard_sequences(self) -> None:
        assert STANDARD_SEQUENCES.start_of_day is not None
        assert STANDARD_SEQUENCES.main_process is not None
        assert STANDARD_SEQUENCES.end_of_day is not None


class TestCheckpointControl:
    def test_with_required_fields(self) -> None:
        ck = CheckpointControl(ck_program_id="TRNVAL00")
        assert ck.ck_commit_freq == 1000
        assert ck.ck_max_errors == 100
        assert ck.ck_max_restarts == 3
        assert ck.ck_restart_mode == "N"

    def test_should_commit(self) -> None:
        ck = CheckpointControl(ck_program_id="TRNVAL00", ck_commit_freq=100, ck_records_proc=100)
        assert ck.should_commit() is True
        ck2 = CheckpointControl(ck_program_id="TRNVAL00", ck_commit_freq=100, ck_records_proc=50)
        assert ck2.should_commit() is False

    def test_has_exceeded_errors(self) -> None:
        ck = CheckpointControl(ck_program_id="TRNVAL00", ck_max_errors=10, ck_records_error=10)
        assert ck.has_exceeded_errors() is True
        ck2 = CheckpointControl(ck_program_id="TRNVAL00", ck_max_errors=10, ck_records_error=5)
        assert ck2.has_exceeded_errors() is False

    def test_can_restart(self) -> None:
        ck = CheckpointControl(ck_program_id="TRNVAL00", ck_max_restarts=3, ck_restart_count=2)
        assert ck.can_restart() is True
        ck2 = CheckpointControl(ck_program_id="TRNVAL00", ck_max_restarts=3, ck_restart_count=3)
        assert ck2.can_restart() is False

    def test_file_statuses_list(self) -> None:
        ck = CheckpointControl(ck_program_id="TRNVAL00")
        assert len(ck.ck_file_statuses) == 5
        for fs in ck.ck_file_statuses:
            assert isinstance(fs, FileStatus)


class TestCheckpointRecord:
    def test_with_required_fields(self) -> None:
        cr = CheckpointRecord(ckr_program_id="TRNVAL00", ckr_run_date="20240320")
        assert cr.ckr_program_id == "TRNVAL00"
        assert cr.ckr_run_date == "20240320"
        assert cr.ckr_data == ""
