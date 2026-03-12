"""
History Record data model.

Translated from COBOL copybook: src/copybook/common/HISTREC.cpy

COBOL structure: HISTORY-RECORD (01 level)
  - HIST-KEY: composite key (portfolio_id, date, time, seq_no)
  - HIST-DATA: history details (record type, action, before/after images)
  - HIST-AUDIT: audit trail fields
  - HIST-FILLER: reserved space (PIC X(50))
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class HistoryRecord(BaseModel):
    """Historical transaction/change record.

    Translated from COBOL copybook HISTREC.cpy.
    Maps to HISTORY-RECORD (01 level).

    Record types (88-level values):
      PT = Portfolio, PS = Position, TR = Transaction

    Action codes (88-level values):
      A = Add, C = Change, D = Delete
    """

    # HIST-KEY fields
    hist_portfolio_id: str = Field(
        ..., max_length=8,
        description="HIST-PORTFOLIO-ID: Portfolio identifier - PIC X(08)"
    )
    hist_date: str = Field(
        ..., max_length=8,
        description="HIST-DATE: History date YYYYMMDD - PIC X(08)"
    )
    hist_time: str = Field(
        ..., max_length=6,
        description="HIST-TIME: History time HHMMSS - PIC X(06)"
    )
    hist_seq_no: str = Field(
        ..., max_length=4,
        description="HIST-SEQ-NO: Sequence number - PIC X(04)"
    )

    # HIST-DATA fields
    hist_record_type: Literal["PT", "PS", "TR"] = Field(
        ...,
        description="HIST-RECORD-TYPE: PT=Portfolio, PS=Position, TR=Transaction - PIC X(02)"
    )
    hist_action_code: Literal["A", "C", "D"] = Field(
        ...,
        description="HIST-ACTION-CODE: A=Add, C=Change, D=Delete - PIC X(01)"
    )
    hist_before_image: str = Field(
        default="", max_length=400,
        description="HIST-BEFORE-IMAGE: Record image before change - PIC X(400)"
    )
    hist_after_image: str = Field(
        default="", max_length=400,
        description="HIST-AFTER-IMAGE: Record image after change - PIC X(400)"
    )
    hist_reason_code: str = Field(
        default="", max_length=4,
        description="HIST-REASON-CODE: Reason for change - PIC X(04)"
    )

    # HIST-AUDIT fields
    hist_process_date: str = Field(
        default="", max_length=26,
        description="HIST-PROCESS-DATE: Processing timestamp - PIC X(26)"
    )
    hist_process_user: str = Field(
        default="", max_length=8,
        description="HIST-PROCESS-USER: Processing user ID - PIC X(08)"
    )

    @field_validator("hist_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if v and len(v) != 8:
            raise ValueError("History date must be 8 characters (YYYYMMDD)")
        return v

    @field_validator("hist_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if v and len(v) != 6:
            raise ValueError("History time must be 6 characters (HHMMSS)")
        return v
