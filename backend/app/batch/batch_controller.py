"""
Batch Control Processor.

Migrated from: BCHCTL00.cbl, BCHCTL.cpy, BCHCON.cpy
Orchestrates the batch pipeline: initializes jobs, checks prerequisites,
updates status, and handles termination. This is the central controller
that manages job-level sequencing and dependencies.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

from .return_codes import (
    ActionFlag,
    ProcessStatus,
    ReturnCode,
    ReturnStatus,
    can_continue_pipeline,
)

logger = logging.getLogger(__name__)


@dataclass
class PrerequisiteJob:
    """
    A prerequisite job dependency.

    Mirrors BCHCTL.cpy BCT-PREREQ-JOBS entries.
    """

    name: str
    sequence_no: int = 0
    max_return_code: int = 4


@dataclass
class BatchControlRecord:
    """
    Batch control record for a single job step.

    Mirrors BCHCTL.cpy BATCH-CONTROL-RECORD structure.
    Tracks the state, timing, dependencies, and return info for one job.
    """

    job_name: str
    process_date: str
    sequence_no: int = 0
    status: ProcessStatus = ProcessStatus.READY
    step_name: str = ""
    program_name: str = ""
    start_time: str = ""
    end_time: str = ""
    prerequisites: List[PrerequisiteJob] = field(default_factory=list)
    return_code: int = 0
    error_desc: str = ""
    restart_count: int = 0
    attempt_timestamp: str = ""
    complete_timestamp: str = ""

    @property
    def is_ready(self) -> bool:
        return self.status == ProcessStatus.READY

    @property
    def is_active(self) -> bool:
        return self.status == ProcessStatus.ACTIVE

    @property
    def is_done(self) -> bool:
        return self.status == ProcessStatus.DONE

    @property
    def is_error(self) -> bool:
        return self.status == ProcessStatus.ERROR

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "process_date": self.process_date,
            "sequence_no": self.sequence_no,
            "status": self.status.value,
            "step_name": self.step_name,
            "program_name": self.program_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "return_code": self.return_code,
            "error_desc": self.error_desc,
            "restart_count": self.restart_count,
        }


class BatchController:
    """
    Orchestrates batch job execution, prerequisites, and status tracking.

    Migrated from BCHCTL00.cbl. The COBOL program uses a VSAM control file
    and dispatches on function codes (INIT, CHEK, UPDT, TERM). This Python
    version manages BatchControlRecords in memory and/or database.
    """

    def __init__(self) -> None:
        self._records: Dict[str, BatchControlRecord] = {}
        self._return_status = ReturnStatus(program_id="BCHCTL00")
        logger.info("BatchController initialized")

    def initialize_job(
        self,
        job_name: str,
        process_date: str,
        sequence_no: int = 0,
        program_name: str = "",
        prerequisites: Optional[List[PrerequisiteJob]] = None,
    ) -> int:
        """
        Initialize a batch job step.

        Mirrors BCHCTL00.cbl 1000-PROCESS-INITIALIZE:
        opens control file, reads/creates control record,
        validates the process, and sets ACTIVE status.
        """
        key = f"{job_name}:{process_date}:{sequence_no}"

        record = BatchControlRecord(
            job_name=job_name,
            process_date=process_date,
            sequence_no=sequence_no,
            program_name=program_name or job_name,
            status=ProcessStatus.ACTIVE,
            start_time=datetime.now().strftime("%H:%M:%S"),
            prerequisites=prerequisites or [],
        )

        self._records[key] = record
        logger.info(
            "Job initialized: %s date=%s seq=%d",
            job_name,
            process_date,
            sequence_no,
        )
        return ReturnCode.SUCCESS

    def check_prerequisites(
        self, job_name: str, process_date: str, sequence_no: int = 0
    ) -> int:
        """
        Check if all prerequisite jobs have completed successfully.

        Mirrors BCHCTL00.cbl 2000-CHECK-PREREQUISITES:
        reads the control record, iterates BCT-PREREQ-JOBS,
        and verifies each dependency is DONE with acceptable RC.
        """
        key = f"{job_name}:{process_date}:{sequence_no}"
        record = self._records.get(key)
        if not record:
            logger.error("Control record not found: %s", key)
            return ReturnCode.ERROR

        for prereq in record.prerequisites:
            prereq_record = self._find_record(prereq.name, process_date)
            if not prereq_record:
                logger.warning(
                    "Prerequisite %s not found for job %s",
                    prereq.name,
                    job_name,
                )
                return ReturnCode.WARNING

            if not prereq_record.is_done:
                logger.info(
                    "Prerequisite %s not yet complete for job %s",
                    prereq.name,
                    job_name,
                )
                return ReturnCode.WARNING

            if prereq_record.return_code > prereq.max_return_code:
                logger.error(
                    "Prerequisite %s failed with RC=%d (max=%d) for job %s",
                    prereq.name,
                    prereq_record.return_code,
                    prereq.max_return_code,
                    job_name,
                )
                return ReturnCode.ERROR

        logger.info("All prerequisites satisfied for job %s", job_name)
        return ReturnCode.SUCCESS

    def update_status(
        self,
        job_name: str,
        process_date: str,
        new_status: ProcessStatus,
        return_code: int = 0,
        error_desc: str = "",
        sequence_no: int = 0,
    ) -> int:
        """
        Update the status of a batch job.

        Mirrors BCHCTL00.cbl 3000-UPDATE-STATUS:
        reads the control record, updates process status, and writes back.
        """
        key = f"{job_name}:{process_date}:{sequence_no}"
        record = self._records.get(key)
        if not record:
            logger.error("Control record not found for update: %s", key)
            return ReturnCode.ERROR

        record.status = new_status
        record.return_code = return_code
        if error_desc:
            record.error_desc = error_desc

        if new_status in (ProcessStatus.DONE, ProcessStatus.ERROR):
            record.end_time = datetime.now().strftime("%H:%M:%S")
            record.complete_timestamp = datetime.now().isoformat()

        logger.info(
            "Job status updated: %s -> %s RC=%d",
            job_name,
            new_status.value,
            return_code,
        )
        return ReturnCode.SUCCESS

    def terminate_job(
        self, job_name: str, process_date: str, return_code: int = 0, sequence_no: int = 0
    ) -> int:
        """
        Terminate a batch job (mark completion).

        Mirrors BCHCTL00.cbl 4000-PROCESS-TERMINATE:
        updates completion status and closes the control file.
        """
        status = ProcessStatus.DONE if return_code <= ReturnCode.WARNING else ProcessStatus.ERROR
        error_desc = "" if return_code <= ReturnCode.WARNING else f"Job ended with RC={return_code}"

        rc = self.update_status(
            job_name, process_date, status, return_code, error_desc, sequence_no
        )
        logger.info(
            "Job terminated: %s status=%s RC=%d", job_name, status.value, return_code
        )
        return rc

    def get_record(
        self, job_name: str, process_date: str, sequence_no: int = 0
    ) -> Optional[BatchControlRecord]:
        """Retrieve a batch control record."""
        key = f"{job_name}:{process_date}:{sequence_no}"
        return self._records.get(key)

    def get_all_records(self, process_date: Optional[str] = None) -> List[BatchControlRecord]:
        """Retrieve all batch control records, optionally filtered by date."""
        records = list(self._records.values())
        if process_date:
            records = [r for r in records if r.process_date == process_date]
        return records

    def _find_record(
        self, job_name: str, process_date: str
    ) -> Optional[BatchControlRecord]:
        """Find a record by job name and date (any sequence)."""
        for key, record in self._records.items():
            if record.job_name == job_name and record.process_date == process_date:
                return record
        return None
