"""
Return Code Management data model.

Translated from COBOL copybook: src/copybook/common/RTNCODE.cpy

COBOL structure: RETURN-CODE-AREA (01 level)
  - RC-REQUEST-TYPE: request type (I, S, G, L, A)
  - RC-PROGRAM-ID: program identifier
  - RC-CODES-AREA: current/highest/new codes and status
  - RC-MESSAGE: return message
  - RC-RESPONSE-CODE: response code
  - RC-ANALYSIS-DATA: timing and statistics
  - RC-RETURN-DATA: final return values
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReturnCode(BaseModel):
    """Return code management area.

    Translated from COBOL copybook RTNCODE.cpy.
    Maps to RETURN-CODE-AREA (01 level).

    Request types (88-level values):
      I = Initialize, S = Set Code, G = Get Code, L = Log Code, A = Analyze

    Status values (88-level values):
      S = Success, W = Warning, E = Error, F = Severe
    """

    # RC-REQUEST-TYPE
    rc_request_type: Literal["I", "S", "G", "L", "A"] = Field(
        default="I",
        description="RC-REQUEST-TYPE: I=Init, S=Set, G=Get, L=Log, A=Analyze - PIC X"
    )

    # RC-PROGRAM-ID
    rc_program_id: str = Field(
        default="", max_length=8,
        description="RC-PROGRAM-ID: Program identifier - PIC X(8)"
    )

    # RC-CODES-AREA fields
    rc_current_code: int = Field(
        default=0,
        description="RC-CURRENT-CODE: Current return code - PIC S9(4) COMP"
    )
    rc_highest_code: int = Field(
        default=0,
        description="RC-HIGHEST-CODE: Highest return code seen - PIC S9(4) COMP"
    )
    rc_new_code: int = Field(
        default=0,
        description="RC-NEW-CODE: New code to set - PIC S9(4) COMP"
    )
    rc_status: Literal["S", "W", "E", "F"] = Field(
        default="S",
        description="RC-STATUS: S=Success, W=Warning, E=Error, F=Severe - PIC X"
    )

    # RC-MESSAGE
    rc_message: str = Field(
        default="", max_length=80,
        description="RC-MESSAGE: Return message - PIC X(80)"
    )

    # RC-RESPONSE-CODE
    rc_response_code: int = Field(
        default=0,
        description="RC-RESPONSE-CODE: Response code - PIC S9(8) COMP"
    )

    # RC-ANALYSIS-DATA fields
    rc_start_time: str = Field(
        default="", max_length=26,
        description="RC-START-TIME: Analysis start time - PIC X(26)"
    )
    rc_end_time: str = Field(
        default="", max_length=26,
        description="RC-END-TIME: Analysis end time - PIC X(26)"
    )
    rc_total_codes: int = Field(
        default=0,
        description="RC-TOTAL-CODES: Total codes processed - PIC S9(8) COMP"
    )
    rc_max_code: int = Field(
        default=0,
        description="RC-MAX-CODE: Maximum code seen - PIC S9(4) COMP"
    )
    rc_min_code: int = Field(
        default=0,
        description="RC-MIN-CODE: Minimum code seen - PIC S9(4) COMP"
    )

    # RC-RETURN-DATA fields
    rc_return_value: int = Field(
        default=0,
        description="RC-RETURN-VALUE: Final return value - PIC S9(4) COMP"
    )
    rc_highest_return: int = Field(
        default=0,
        description="RC-HIGHEST-RETURN: Highest return value - PIC S9(4) COMP"
    )
    rc_return_status: str = Field(
        default="", max_length=1,
        description="RC-RETURN-STATUS: Final return status - PIC X"
    )

    def set_code(self, code: int, message: str = "") -> None:
        """Set a new return code and update tracking fields."""
        self.rc_current_code = code
        self.rc_new_code = code
        if code > self.rc_highest_code:
            self.rc_highest_code = code
        if message:
            self.rc_message = message

        # Update status based on code
        if code == 0:
            self.rc_status = "S"
        elif code <= 4:
            self.rc_status = "W"
        elif code <= 8:
            self.rc_status = "E"
        else:
            self.rc_status = "F"

    def get_code(self) -> int:
        """Get the current return code."""
        return self.rc_current_code

    def initialize(self, program_id: str) -> None:
        """Initialize the return code area for a program."""
        self.rc_program_id = program_id
        self.rc_current_code = 0
        self.rc_highest_code = 0
        self.rc_new_code = 0
        self.rc_status = "S"
        self.rc_message = ""
