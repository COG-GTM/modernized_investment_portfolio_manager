"""
Error Handling data models.

Translated from COBOL copybook: src/copybook/common/ERRHAND.cpy

COBOL structures:
  - ERR-CATEGORIES: error category codes (VS, VL, PR, SY)
  - ERR-RETURN-CODES: standard return codes (0, 4, 8, 12, 16)
  - ERR-MESSAGE: error message structure with timestamp, program, severity, etc.
  - ERR-VSAM-STATUSES: VSAM file status codes
  - ERR-VSAM-MSGS: VSAM error messages
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ErrorCategories(BaseModel):
    """Error category definitions.

    Translated from COBOL copybook ERRHAND.cpy - ERR-CATEGORIES (01 level).
    """

    vsam: str = Field(default="VS", max_length=2, description="ERR-CAT-VSAM: PIC X(2) VALUE 'VS'")
    validation: str = Field(default="VL", max_length=2, description="ERR-CAT-VALID: PIC X(2) VALUE 'VL'")
    processing: str = Field(default="PR", max_length=2, description="ERR-CAT-PROC: PIC X(2) VALUE 'PR'")
    system: str = Field(default="SY", max_length=2, description="ERR-CAT-SYSTEM: PIC X(2) VALUE 'SY'")


class ErrorRecord(BaseModel):
    """Standard error return codes.

    Translated from COBOL copybook ERRHAND.cpy - ERR-RETURN-CODES (01 level).
    """

    success: int = Field(default=0, description="ERR-SUCCESS: PIC S9(4) COMP VALUE +0")
    warning: int = Field(default=4, description="ERR-WARNING: PIC S9(4) COMP VALUE +4")
    error: int = Field(default=8, description="ERR-ERROR: PIC S9(4) COMP VALUE +8")
    severe: int = Field(default=12, description="ERR-SEVERE: PIC S9(4) COMP VALUE +12")
    terminal: int = Field(default=16, description="ERR-TERMINAL: PIC S9(4) COMP VALUE +16")


class ErrorMessage(BaseModel):
    """Error message structure.

    Translated from COBOL copybook ERRHAND.cpy - ERR-MESSAGE (01 level).
    """

    # ERR-TIMESTAMP sub-fields
    err_date: str = Field(
        default="", max_length=10,
        description="ERR-DATE: Error date - PIC X(10)"
    )
    err_time: str = Field(
        default="", max_length=8,
        description="ERR-TIME: Error time - PIC X(8)"
    )
    err_program: str = Field(
        default="", max_length=8,
        description="ERR-PROGRAM: Program name - PIC X(8)"
    )
    err_category: str = Field(
        default="", max_length=2,
        description="ERR-CATEGORY: Error category code - PIC X(2)"
    )
    err_code: str = Field(
        default="", max_length=4,
        description="ERR-CODE: Error code - PIC X(4)"
    )
    err_severity: int = Field(
        default=0,
        description="ERR-SEVERITY: Severity level - PIC S9(4) COMP"
    )
    err_text: str = Field(
        default="", max_length=80,
        description="ERR-TEXT: Error message text - PIC X(80)"
    )
    err_details: str = Field(
        default="", max_length=256,
        description="ERR-DETAILS: Detailed error information - PIC X(256)"
    )


class VsamStatuses(BaseModel):
    """VSAM file status codes and messages.

    Translated from COBOL copybook ERRHAND.cpy - ERR-VSAM-STATUSES (01 level).
    Maps VSAM file status codes to their Python equivalents.
    """

    success: str = Field(default="00", max_length=2, description="ERR-VSAM-SUCCESS: PIC X(2) VALUE '00'")
    duplicate_key: str = Field(default="22", max_length=2, description="ERR-VSAM-DUPKEY: PIC X(2) VALUE '22'")
    not_found: str = Field(default="23", max_length=2, description="ERR-VSAM-NOTFND: PIC X(2) VALUE '23'")
    end_of_file: str = Field(default="10", max_length=2, description="ERR-VSAM-EOF: PIC X(2) VALUE '10'")

    # VSAM error messages
    msg_duplicate_key: str = Field(
        default="Duplicate record key", max_length=80,
        description="ERR-VSAM-22: PIC X(80)"
    )
    msg_not_found: str = Field(
        default="Record not found", max_length=80,
        description="ERR-VSAM-23: PIC X(80)"
    )
    msg_other: str = Field(
        default="Unexpected VSAM error", max_length=80,
        description="ERR-OTHER: PIC X(80)"
    )


# Module-level constant instances
ERROR_CATEGORIES = ErrorCategories()
ERROR_CODES = ErrorRecord()
VSAM_STATUSES = VsamStatuses()
