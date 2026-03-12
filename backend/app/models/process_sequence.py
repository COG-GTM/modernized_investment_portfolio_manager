"""
Process Sequence data model.

Translated from COBOL copybook: src/copybook/batch/PRCSEQ.cpy

COBOL structures:
  - PROCESS-SEQUENCE-RECORD (01 level): process definition with timing,
    dependencies, control, schedule, recovery, and audit info
  - STANDARD-SEQUENCES (01 level): predefined process sequences
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class DependencyEntry(BaseModel):
    """A single process dependency entry.

    Translated from PRCSEQ.cpy - PSR-DEP-ENTRY OCCURS 10 TIMES.
    """

    dep_id: str = Field(
        default="", max_length=8,
        description="PSR-DEP-ID: Dependency process ID - PIC X(8)"
    )
    dep_type: Literal["H", "S"] = Field(
        default="H",
        description="PSR-DEP-TYPE: H=Hard, S=Soft dependency - PIC X(1)"
    )
    dep_rc: int = Field(
        default=0,
        description="PSR-DEP-RC: Max acceptable return code - PIC S9(4) COMP"
    )


class ProcessSequenceRecord(BaseModel):
    """Process sequence definition.

    Translated from COBOL copybook PRCSEQ.cpy.
    Maps to PROCESS-SEQUENCE-RECORD (01 level).

    Process types (88-level values):
      INI = Initialize, PRC = Process, RPT = Report, TRM = Terminate

    Frequency (88-level values):
      D = Daily, W = Weekly, M = Monthly

    Schedule flags:
      PSR-ACTIVE-DAYS (YYYYYNN = weekdays, NNNNNYY = weekend, YYYYYYY = all)
    """

    # PSR-KEY fields
    psr_process_id: str = Field(
        ..., max_length=8,
        description="PSR-PROCESS-ID: Process identifier - PIC X(8)"
    )
    psr_version: int = Field(
        default=1, ge=0, le=99,
        description="PSR-VERSION: Version number - PIC 9(2)"
    )

    # PSR-DATA fields
    psr_description: str = Field(
        default="", max_length=30,
        description="PSR-DESCRIPTION: Process description - PIC X(30)"
    )
    psr_type: Literal["INI", "PRC", "RPT", "TRM"] = Field(
        default="PRC",
        description="PSR-TYPE: INI=Init, PRC=Process, RPT=Report, TRM=Terminate - PIC X(3)"
    )

    # PSR-TIMING fields
    psr_freq: Literal["D", "W", "M"] = Field(
        default="D",
        description="PSR-FREQ: D=Daily, W=Weekly, M=Monthly - PIC X(1)"
    )
    psr_start_time: int = Field(
        default=0, ge=0, le=9999,
        description="PSR-START-TIME: Scheduled start time (HHMM) - PIC 9(4)"
    )
    psr_max_time: int = Field(
        default=0, ge=0, le=9999,
        description="PSR-MAX-TIME: Maximum run time (minutes) - PIC 9(4)"
    )

    # PSR-DEPENDENCIES
    psr_dep_count: int = Field(
        default=0, ge=0, le=99,
        description="PSR-DEP-COUNT: Number of dependencies - PIC 9(2) COMP"
    )
    psr_dep_entries: list[DependencyEntry] = Field(
        default_factory=list,
        description="PSR-DEP-ENTRY: OCCURS 10 TIMES - dependency list"
    )

    # PSR-CONTROL fields
    psr_program: str = Field(
        default="", max_length=8,
        description="PSR-PROGRAM: Program to execute - PIC X(8)"
    )
    psr_parm: str = Field(
        default="", max_length=50,
        description="PSR-PARM: Program parameters - PIC X(50)"
    )
    psr_max_rc: int = Field(
        default=0,
        description="PSR-MAX-RC: Maximum acceptable return code - PIC S9(4) COMP"
    )
    psr_restart: Literal["Y", "N"] = Field(
        default="Y",
        description="PSR-RESTART: Y=Restartable, N=No restart - PIC X(1)"
    )

    # PSR-SCHEDULE fields
    psr_active_days: str = Field(
        default="YYYYYYY", max_length=7,
        description="PSR-ACTIVE-DAYS: Day-of-week flags (Mon-Sun) - PIC X(7)"
    )
    psr_month_end: Literal["Y", "N"] = Field(
        default="N",
        description="PSR-MONTH-END: Run on last day of month - PIC X(1)"
    )
    psr_holiday_run: Literal["Y", "N"] = Field(
        default="N",
        description="PSR-HOLIDAY-RUN: Y=Run on holidays, N=Skip - PIC X(1)"
    )

    # PSR-RECOVERY fields
    psr_recovery_pgm: str = Field(
        default="", max_length=8,
        description="PSR-RECOVERY-PGM: Recovery program name - PIC X(8)"
    )
    psr_recovery_parm: str = Field(
        default="", max_length=50,
        description="PSR-RECOVERY-PARM: Recovery parameters - PIC X(50)"
    )
    psr_error_limit: int = Field(
        default=0, ge=0, le=9999,
        description="PSR-ERROR-LIMIT: Maximum errors before abort - PIC 9(4) COMP"
    )

    # PSR-AUDIT fields
    psr_create_date: str = Field(
        default="", max_length=10,
        description="PSR-CREATE-DATE: Creation date - PIC X(10)"
    )
    psr_create_user: str = Field(
        default="", max_length=8,
        description="PSR-CREATE-USER: Created by user - PIC X(8)"
    )
    psr_update_date: str = Field(
        default="", max_length=10,
        description="PSR-UPDATE-DATE: Last update date - PIC X(10)"
    )
    psr_update_user: str = Field(
        default="", max_length=8,
        description="PSR-UPDATE-USER: Last updated by user - PIC X(8)"
    )

    @property
    def is_restartable(self) -> bool:
        return self.psr_restart == "Y"


class StandardSequences(BaseModel):
    """Standard predefined process sequences.

    Translated from PRCSEQ.cpy - STANDARD-SEQUENCES (01 level).
    """

    start_of_day: list[str] = Field(
        default=["INITDAY", "CKPCLR", "DATEVAL"],
        description="SEQ-START-OF-DAY: Initialization sequence"
    )
    main_process: list[str] = Field(
        default=["TRNVAL00", "POSUPD00", "HISTLD00"],
        description="SEQ-MAIN-PROCESS: Main processing sequence"
    )
    end_of_day: list[str] = Field(
        default=["RPTGEN00", "BCKLOD00", "ENDDAY"],
        description="SEQ-END-OF-DAY: End-of-day sequence"
    )


# Module-level constant instance
STANDARD_SEQUENCES = StandardSequences()
