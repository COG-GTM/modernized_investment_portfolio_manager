"""
Return/Retry Handling data models.

Translated from COBOL copybook: src/copybook/common/RETHND.cpy

COBOL structures:
  - RETURN-HANDLING (01 level): return status, details, actions
  - STD-ERROR-CODES (01 level): standard error code constants
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ErrorLocation(BaseModel):
    """Error location within the program.

    Translated from RETHND.cpy - ERROR-LOCATION (10 level).
    """

    program_name: str = Field(
        default="", max_length=8,
        description="PROGRAM-NAME: Source program - PIC X(8)"
    )
    paragraph_name: str = Field(
        default="", max_length=8,
        description="PARAGRAPH-NAME: Source paragraph - PIC X(8)"
    )
    error_routine: str = Field(
        default="", max_length=8,
        description="ERROR-ROUTINE: Error handling routine - PIC X(8)"
    )


class ErrorInfo(BaseModel):
    """Detailed error information.

    Translated from RETHND.cpy - ERROR-INFO (10 level).

    Error types (88-level values):
      V = Validation, P = Processing, D = Database, F = File, S = Security
    """

    error_type: Literal["V", "P", "D", "F", "S"] = Field(
        default="P",
        description="ERROR-TYPE: V=Validation, P=Processing, D=Database, F=File, S=Security - PIC X(1)"
    )
    error_code: str = Field(
        default="", max_length=4,
        description="ERROR-CODE: Error code - PIC X(4)"
    )
    error_text: str = Field(
        default="", max_length=80,
        description="ERROR-TEXT: Error description - PIC X(80)"
    )


class SystemInfo(BaseModel):
    """System-level error information.

    Translated from RETHND.cpy - SYSTEM-INFO (10 level).
    """

    system_code: str = Field(
        default="", max_length=4,
        description="SYSTEM-CODE: System error code - PIC X(4)"
    )
    system_msg: str = Field(
        default="", max_length=80,
        description="SYSTEM-MSG: System error message - PIC X(80)"
    )


class ReturnActions(BaseModel):
    """Return action flags and retry control.

    Translated from RETHND.cpy - RETURN-ACTIONS (05 level).

    Action flags (88-level values):
      C = Continue, A = Abort, R = Retry
    """

    action_flag: Literal["C", "A", "R"] = Field(
        default="C",
        description="ACTION-FLAG: C=Continue, A=Abort, R=Retry - PIC X(1)"
    )
    retry_count: int = Field(
        default=0, ge=0, le=99,
        description="RETRY-COUNT: Current retry attempt - PIC 9(2) COMP"
    )
    max_retries: int = Field(
        default=3, ge=0, le=99,
        description="MAX-RETRIES: Maximum retry attempts - PIC 9(2) COMP VALUE 3"
    )

    def should_retry(self) -> bool:
        """Check if a retry should be attempted."""
        return self.action_flag == "R" and self.retry_count < self.max_retries

    def increment_retry(self) -> bool:
        """Increment retry counter. Returns True if retry is allowed."""
        if self.should_retry():
            self.retry_count += 1
            return True
        return False


class ReturnHandling(BaseModel):
    """Complete return/retry handling structure.

    Translated from COBOL copybook RETHND.cpy.
    Maps to RETURN-HANDLING (01 level).

    Return codes (88-level values):
      0 = Success, 4 = Warning, 8 = Error, 12 = Severe, 16 = Critical
    """

    # RETURN-STATUS fields
    return_code: int = Field(
        default=0,
        description="RETURN-CODE: PIC S9(4) COMP"
    )
    reason_code: int = Field(
        default=0,
        description="REASON-CODE: PIC S9(4) COMP"
    )
    module_id: str = Field(
        default="", max_length=8,
        description="MODULE-ID: Source module - PIC X(8)"
    )
    function_id: str = Field(
        default="", max_length=8,
        description="FUNCTION-ID: Source function - PIC X(8)"
    )

    # RETURN-DETAILS sub-structures
    error_location: ErrorLocation = Field(default_factory=ErrorLocation)
    error_info: ErrorInfo = Field(default_factory=ErrorInfo)
    system_info: SystemInfo = Field(default_factory=SystemInfo)

    # RETURN-ACTIONS
    return_actions: ReturnActions = Field(default_factory=ReturnActions)

    @property
    def is_success(self) -> bool:
        return self.return_code == 0

    @property
    def is_warning(self) -> bool:
        return self.return_code == 4

    @property
    def is_error(self) -> bool:
        return self.return_code == 8

    @property
    def is_severe(self) -> bool:
        return self.return_code == 12

    @property
    def is_critical(self) -> bool:
        return self.return_code == 16


class StandardErrorCodes(BaseModel):
    """Standard error code constants.

    Translated from COBOL copybook RETHND.cpy - STD-ERROR-CODES (01 level).
    """

    invalid_data: str = Field(default="E001", max_length=4, description="ERR-INVALID-DATA")
    not_found: str = Field(default="E002", max_length=4, description="ERR-NOT-FOUND")
    duplicate: str = Field(default="E003", max_length=4, description="ERR-DUPLICATE")
    file_error: str = Field(default="E004", max_length=4, description="ERR-FILE-ERROR")
    db_error: str = Field(default="E005", max_length=4, description="ERR-DB-ERROR")
    security: str = Field(default="E006", max_length=4, description="ERR-SECURITY")
    processing: str = Field(default="E007", max_length=4, description="ERR-PROCESSING")
    validation: str = Field(default="E008", max_length=4, description="ERR-VALIDATION")
    version: str = Field(default="E009", max_length=4, description="ERR-VERSION")
    timeout: str = Field(default="E010", max_length=4, description="ERR-TIMEOUT")


# Module-level constant instance
STD_ERROR_CODES = StandardErrorCodes()
