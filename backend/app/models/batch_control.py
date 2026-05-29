"""
Batch Control Record data model.

Translated from COBOL copybook: src/copybook/batch/BCHCTL.cpy

COBOL structure: BATCH-CONTROL-RECORD (01 level)
  - BCT-KEY: composite key (job_name, process_date, sequence_no)
  - BCT-DATA: status, process control, dependencies, return info
  - BCT-STATISTICS: restart count, attempt/complete timestamps
  - BCT-FILLER: reserved space (PIC X(50))

Works with CKPRST.cpy for program-level checkpointing.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class PrerequisiteJob(BaseModel):
    """A single prerequisite job dependency.

    Translated from BCHCTL.cpy - BCT-PREREQ-JOBS OCCURS 10 TIMES.
    """

    prereq_name: str = Field(
        default="", max_length=8,
        description="BCT-PREREQ-NAME: Prerequisite job name - PIC X(8)"
    )
    prereq_seq: int = Field(
        default=0, ge=0, le=9999,
        description="BCT-PREREQ-SEQ: Prerequisite sequence number - PIC 9(4)"
    )
    prereq_rc: int = Field(
        default=0,
        description="BCT-PREREQ-RC: Required return code - PIC S9(4) COMP"
    )


class BatchControlRecord(BaseModel):
    """Batch job control record.

    Translated from COBOL copybook BCHCTL.cpy.
    Maps to BATCH-CONTROL-RECORD (01 level).

    Batch statuses (88-level values):
      R = Ready, A = Active, W = Waiting, D = Done, E = Error
    """

    # BCT-KEY fields
    bct_job_name: str = Field(
        ..., max_length=8,
        description="BCT-JOB-NAME: Job name - PIC X(8)"
    )
    bct_process_date: str = Field(
        ..., max_length=8,
        description="BCT-PROCESS-DATE: Process date YYYYMMDD - PIC X(8)"
    )
    bct_sequence_no: int = Field(
        ..., ge=0, le=9999,
        description="BCT-SEQUENCE-NO: Sequence number - PIC 9(4)"
    )

    # BCT-DATA fields
    bct_status: Literal["R", "A", "W", "D", "E"] = Field(
        default="R",
        description="BCT-STATUS: R=Ready, A=Active, W=Waiting, D=Done, E=Error - PIC X(1)"
    )

    # BCT-PROCESS-CONTROL fields
    bct_step_name: str = Field(
        default="", max_length=8,
        description="BCT-STEP-NAME: Step name - PIC X(8)"
    )
    bct_program_name: str = Field(
        default="", max_length=8,
        description="BCT-PROGRAM-NAME: Program name - PIC X(8)"
    )
    bct_start_time: str = Field(
        default="", max_length=8,
        description="BCT-START-TIME: Start time - PIC X(8)"
    )
    bct_end_time: str = Field(
        default="", max_length=8,
        description="BCT-END-TIME: End time - PIC X(8)"
    )

    # BCT-DEPENDENCIES
    bct_prereq_count: int = Field(
        default=0, ge=0, le=99,
        description="BCT-PREREQ-COUNT: Number of prerequisites - PIC 9(2) COMP"
    )
    bct_prereq_jobs: list[PrerequisiteJob] = Field(
        default_factory=list,
        description="BCT-PREREQ-JOBS: OCCURS 10 TIMES - prerequisite job list"
    )

    # BCT-RETURN-INFO fields
    bct_return_code: int = Field(
        default=0,
        description="BCT-RETURN-CODE: Return code - PIC S9(4) COMP"
    )
    bct_error_desc: str = Field(
        default="", max_length=80,
        description="BCT-ERROR-DESC: Error description - PIC X(80)"
    )

    # BCT-STATISTICS fields
    bct_restart_count: int = Field(
        default=0, ge=0, le=99,
        description="BCT-RESTART-COUNT: Restart count - PIC 9(2) COMP"
    )
    bct_attempt_ts: str = Field(
        default="", max_length=26,
        description="BCT-ATTEMPT-TS: Last attempt timestamp - PIC X(26)"
    )
    bct_complete_ts: str = Field(
        default="", max_length=26,
        description="BCT-COMPLETE-TS: Completion timestamp - PIC X(26)"
    )

    def are_prerequisites_met(self, completed_jobs: dict[str, int]) -> bool:
        """Check if all prerequisites are met.

        Args:
            completed_jobs: dict of job_name -> return_code for completed jobs

        Returns:
            True if all prerequisites are satisfied.
        """
        for prereq in self.bct_prereq_jobs[:self.bct_prereq_count]:
            if prereq.prereq_name not in completed_jobs:
                return False
            if completed_jobs[prereq.prereq_name] > prereq.prereq_rc:
                return False
        return True
