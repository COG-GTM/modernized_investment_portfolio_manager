"""
Online Error Handling data model.

Translated from COBOL copybook: src/copybook/online/ERRHND.cpy

COBOL structure: ERROR-HANDLING (01 level)
  - ERR-PROGRAM: originating program
  - ERR-PARAGRAPH: originating paragraph
  - ERR-SQLCODE: SQL return code
  - ERR-CICS-RESP / ERR-CICS-RESP2: CICS response codes
  - ERR-SEVERITY: error severity (F, W, I)
  - ERR-MESSAGE: error message
  - ERR-ACTION: recovery action (R, C, A)
  - ERR-TRACE: trace ID and timestamp
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class OnlineErrorHandler(BaseModel):
    """Online (CICS) error handling structure.

    Translated from COBOL copybook ERRHND.cpy (online).
    Maps to ERROR-HANDLING (01 level).

    Severity levels (88-level values):
      F = Fatal, W = Warning, I = Info

    Recovery actions (88-level values):
      R = Return, C = Continue, A = Abend
    """

    err_program: str = Field(
        default="", max_length=8,
        description="ERR-PROGRAM: Originating program - PIC X(8)"
    )
    err_paragraph: str = Field(
        default="", max_length=30,
        description="ERR-PARAGRAPH: Originating paragraph - PIC X(30)"
    )
    err_sqlcode: int = Field(
        default=0,
        description="ERR-SQLCODE: SQL return code - PIC S9(9) COMP"
    )
    err_cics_resp: int = Field(
        default=0,
        description="ERR-CICS-RESP: CICS response code - PIC S9(8) COMP"
    )
    err_cics_resp2: int = Field(
        default=0,
        description="ERR-CICS-RESP2: CICS secondary response code - PIC S9(8) COMP"
    )
    err_severity: Literal["F", "W", "I"] = Field(
        default="I",
        description="ERR-SEVERITY: F=Fatal, W=Warning, I=Info - PIC X"
    )
    err_message: str = Field(
        default="", max_length=80,
        description="ERR-MESSAGE: Error message text - PIC X(80)"
    )
    err_action: Literal["R", "C", "A"] = Field(
        default="R",
        description="ERR-ACTION: R=Return, C=Continue, A=Abend - PIC X"
    )

    # ERR-TRACE fields
    err_trace_id: str = Field(
        default="", max_length=16,
        description="ERR-TRACE-ID: Trace identifier - PIC X(16)"
    )
    err_timestamp: str = Field(
        default="", max_length=26,
        description="ERR-TIMESTAMP: Error timestamp - PIC X(26)"
    )
