"""
Checkpoint/Restart Control data model.

Translated from COBOL copybook: src/copybook/batch/CKPRST.cpy

COBOL structures:
  - CHECKPOINT-CONTROL (01 level): program-level checkpoint state
  - CHECKPOINT-RECORD (01 level): VSAM checkpoint record

Standard checkpoint routines referenced:
  CKPINIT  - Initialize checkpoint
  CKPTAKE  - Take a checkpoint
  CKPCMIT  - Commit a checkpoint
  CKPRSTR  - Restart from checkpoint
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class FileStatus(BaseModel):
    """File status entry for checkpoint tracking.

    Translated from CKPRST.cpy - CK-FILE-STATUS OCCURS 5 TIMES.
    """

    file_name: str = Field(
        default="", max_length=8,
        description="CK-FILE-NAME: File name - PIC X(8)"
    )
    file_pos: str = Field(
        default="", max_length=50,
        description="CK-FILE-POS: File position marker - PIC X(50)"
    )
    file_status: str = Field(
        default="", max_length=2,
        description="CK-FILE-STATUS: File status code - PIC X(2)"
    )


class CheckpointControl(BaseModel):
    """Program-level checkpoint/restart control.

    Translated from COBOL copybook CKPRST.cpy.
    Maps to CHECKPOINT-CONTROL (01 level).

    Checkpoint statuses (88-level values):
      I = Initial, A = Active, C = Complete, F = Failed, R = Restarted

    Processing phases (88-level values):
      00 = Init, 10 = Read, 20 = Process, 30 = Update, 40 = Terminate

    Restart modes (88-level values):
      N = Normal, R = Restart, C = Recover
    """

    # CK-HEADER fields
    ck_program_id: str = Field(
        ..., max_length=8,
        description="CK-PROGRAM-ID: Program identifier - PIC X(8)"
    )
    ck_run_date: str = Field(
        default="", max_length=8,
        description="CK-RUN-DATE: Run date YYYYMMDD - PIC X(8)"
    )
    ck_run_time: str = Field(
        default="", max_length=6,
        description="CK-RUN-TIME: Run time HHMMSS - PIC X(6)"
    )
    ck_status: Literal["I", "A", "C", "F", "R"] = Field(
        default="I",
        description="CK-STATUS: I=Initial, A=Active, C=Complete, F=Failed, R=Restarted - PIC X(1)"
    )

    # CK-COUNTERS fields
    ck_records_read: int = Field(
        default=0, ge=0,
        description="CK-RECORDS-READ: Records read count - PIC 9(9) COMP"
    )
    ck_records_proc: int = Field(
        default=0, ge=0,
        description="CK-RECORDS-PROC: Records processed count - PIC 9(9) COMP"
    )
    ck_records_error: int = Field(
        default=0, ge=0,
        description="CK-RECORDS-ERROR: Records in error count - PIC 9(9) COMP"
    )
    ck_restart_count: int = Field(
        default=0, ge=0, le=99,
        description="CK-RESTART-COUNT: Restart attempt count - PIC 9(2) COMP"
    )

    # CK-POSITION fields
    ck_last_key: str = Field(
        default="", max_length=50,
        description="CK-LAST-KEY: Last processed key - PIC X(50)"
    )
    ck_last_time: str = Field(
        default="", max_length=26,
        description="CK-LAST-TIME: Last checkpoint timestamp - PIC X(26)"
    )
    ck_phase: Literal["00", "10", "20", "30", "40"] = Field(
        default="00",
        description="CK-PHASE: 00=Init, 10=Read, 20=Process, 30=Update, 40=Terminate - PIC X(2)"
    )

    # CK-RESOURCES
    ck_file_statuses: list[FileStatus] = Field(
        default_factory=lambda: [FileStatus() for _ in range(5)],
        description="CK-FILE-STATUS: OCCURS 5 TIMES - file tracking entries"
    )

    # CK-CONTROL-INFO fields
    ck_commit_freq: int = Field(
        default=1000, ge=0, le=99999,
        description="CK-COMMIT-FREQ: Commit frequency - PIC 9(5) COMP VALUE 1000"
    )
    ck_max_errors: int = Field(
        default=100, ge=0, le=999,
        description="CK-MAX-ERRORS: Maximum errors allowed - PIC 9(3) COMP VALUE 100"
    )
    ck_max_restarts: int = Field(
        default=3, ge=0, le=99,
        description="CK-MAX-RESTARTS: Maximum restart attempts - PIC 9(2) COMP VALUE 3"
    )
    ck_restart_mode: Literal["N", "R", "C"] = Field(
        default="N",
        description="CK-RESTART-MODE: N=Normal, R=Restart, C=Recover - PIC X(1)"
    )

    def should_commit(self) -> bool:
        """Check if a commit should be issued based on records processed."""
        return self.ck_records_proc > 0 and (self.ck_records_proc % self.ck_commit_freq == 0)

    def has_exceeded_errors(self) -> bool:
        """Check if the error threshold has been exceeded."""
        return self.ck_records_error >= self.ck_max_errors

    def can_restart(self) -> bool:
        """Check if another restart attempt is allowed."""
        return self.ck_restart_count < self.ck_max_restarts


class CheckpointRecord(BaseModel):
    """Checkpoint VSAM file record.

    Translated from CKPRST.cpy - CHECKPOINT-RECORD (01 level).
    """

    ckr_program_id: str = Field(
        ..., max_length=8,
        description="CKR-PROGRAM-ID: Program identifier - PIC X(8)"
    )
    ckr_run_date: str = Field(
        ..., max_length=8,
        description="CKR-RUN-DATE: Run date YYYYMMDD - PIC X(8)"
    )
    ckr_data: str = Field(
        default="", max_length=400,
        description="CKR-DATA: Checkpoint data blob - PIC X(400)"
    )
