"""
Batch Control Constants data model.

Translated from COBOL copybook: src/copybook/batch/BCHCON.cpy

COBOL structure: BATCH-CONTROL-CONSTANTS (01 level)
  - BCT-STAT-VALUES: process status values
  - BCT-RC-THRESHOLDS: return code thresholds
  - BCT-CTRL-VALUES: process control values (max prereqs, restarts, etc.)
  - BCT-PROC-TYPES: process type codes
  - BCT-DEP-TYPES: dependency type codes
  - BCT-PROC-NAMES: special process names
  - BCT-REC-TYPES: control file record types
  - BCT-MESSAGES: standard messages
"""

from pydantic import BaseModel, Field


class BatchConstants(BaseModel):
    """Batch processing constants.

    Translated from COBOL copybook BCHCON.cpy.
    Maps to BATCH-CONTROL-CONSTANTS (01 level).
    """

    # BCT-STAT-VALUES: Process status values
    stat_ready: str = Field(default="R", max_length=1, description="BCT-STAT-READY: PIC X(1) VALUE 'R'")
    stat_active: str = Field(default="A", max_length=1, description="BCT-STAT-ACTIVE: PIC X(1) VALUE 'A'")
    stat_waiting: str = Field(default="W", max_length=1, description="BCT-STAT-WAITING: PIC X(1) VALUE 'W'")
    stat_done: str = Field(default="D", max_length=1, description="BCT-STAT-DONE: PIC X(1) VALUE 'D'")
    stat_error: str = Field(default="E", max_length=1, description="BCT-STAT-ERROR: PIC X(1) VALUE 'E'")

    # BCT-RC-THRESHOLDS: Return code thresholds
    rc_success: int = Field(default=0, description="BCT-RC-SUCCESS: PIC S9(4) COMP VALUE +0")
    rc_warning: int = Field(default=4, description="BCT-RC-WARNING: PIC S9(4) COMP VALUE +4")
    rc_error: int = Field(default=8, description="BCT-RC-ERROR: PIC S9(4) COMP VALUE +8")
    rc_severe: int = Field(default=12, description="BCT-RC-SEVERE: PIC S9(4) COMP VALUE +12")
    rc_critical: int = Field(default=16, description="BCT-RC-CRITICAL: PIC S9(4) COMP VALUE +16")

    # BCT-CTRL-VALUES: Process control values
    max_prereq: int = Field(default=10, description="BCT-MAX-PREREQ: PIC 9(2) COMP VALUE 10")
    max_restarts: int = Field(default=3, description="BCT-MAX-RESTARTS: PIC 9(2) COMP VALUE 3")
    wait_interval: int = Field(default=300, description="BCT-WAIT-INTERVAL: PIC 9(4) COMP VALUE 300 (seconds)")
    max_wait_time: int = Field(default=3600, description="BCT-MAX-WAIT-TIME: PIC 9(4) COMP VALUE 3600 (seconds)")

    # BCT-PROC-TYPES: Process type codes
    type_initial: str = Field(default="INI", max_length=3, description="BCT-TYPE-INITIAL: PIC X(3) VALUE 'INI'")
    type_update: str = Field(default="UPD", max_length=3, description="BCT-TYPE-UPDATE: PIC X(3) VALUE 'UPD'")
    type_report: str = Field(default="RPT", max_length=3, description="BCT-TYPE-REPORT: PIC X(3) VALUE 'RPT'")
    type_cleanup: str = Field(default="CLN", max_length=3, description="BCT-TYPE-CLEANUP: PIC X(3) VALUE 'CLN'")

    # BCT-DEP-TYPES: Dependency type codes
    dep_required: str = Field(default="R", max_length=1, description="BCT-DEP-REQUIRED: PIC X(1) VALUE 'R'")
    dep_optional: str = Field(default="O", max_length=1, description="BCT-DEP-OPTIONAL: PIC X(1) VALUE 'O'")
    dep_exclusive: str = Field(default="X", max_length=1, description="BCT-DEP-EXCLUSIVE: PIC X(1) VALUE 'X'")

    # BCT-PROC-NAMES: Special process names
    start_of_day: str = Field(default="STARTDAY", max_length=8, description="BCT-START-OF-DAY: PIC X(8)")
    end_of_day: str = Field(default="ENDDAY", max_length=8, description="BCT-END-OF-DAY: PIC X(8)")
    emergency: str = Field(default="EMERGENC", max_length=8, description="BCT-EMERGENCY: PIC X(8)")

    # BCT-REC-TYPES: Control file record types
    rec_control: str = Field(default="C", max_length=1, description="BCT-REC-CONTROL: PIC X(1) VALUE 'C'")
    rec_process: str = Field(default="P", max_length=1, description="BCT-REC-PROCESS: PIC X(1) VALUE 'P'")
    rec_depend: str = Field(default="D", max_length=1, description="BCT-REC-DEPEND: PIC X(1) VALUE 'D'")
    rec_history: str = Field(default="H", max_length=1, description="BCT-REC-HISTORY: PIC X(1) VALUE 'H'")

    # BCT-MESSAGES: Standard messages
    msg_starting: str = Field(
        default="Process starting...",
        max_length=30,
        description="BCT-MSG-STARTING: PIC X(30)"
    )
    msg_complete: str = Field(
        default="Process completed successfully",
        max_length=30,
        description="BCT-MSG-COMPLETE: PIC X(30)"
    )
    msg_failed: str = Field(
        default="Process failed - check errors",
        max_length=30,
        description="BCT-MSG-FAILED: PIC X(30)"
    )
    msg_waiting: str = Field(
        default="Waiting for prerequisites",
        max_length=30,
        description="BCT-MSG-WAITING: PIC X(30)"
    )


# Module-level constant instance
BATCH_CONSTANTS = BatchConstants()
