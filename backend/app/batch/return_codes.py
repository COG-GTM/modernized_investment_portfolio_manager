"""
Return Code Constants and Handling.

Migrated from: RTNCDE00.cbl, RTNCODE.cpy, RETHND.cpy, BCHCON.cpy
Provides standardized return codes, status tracking, and code classification
used across the entire batch processing pipeline.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ReturnCode(IntEnum):
    """Standard return codes mirroring COBOL BCT-RC-THRESHOLDS from BCHCON.cpy."""

    SUCCESS = 0
    WARNING = 4
    ERROR = 8
    SEVERE = 12
    CRITICAL = 16


class StatusCode(str, Enum):
    """Status classification derived from RTNCODE.cpy RC-STATUS values."""

    SUCCESS = "S"
    WARNING = "W"
    ERROR = "E"
    SEVERE = "F"


class ProcessStatus(str, Enum):
    """Process status values from BCHCON.cpy BCT-STAT-VALUES."""

    READY = "R"
    ACTIVE = "A"
    WAITING = "W"
    DONE = "D"
    ERROR = "E"


class ErrorType(str, Enum):
    """Error type classifications from RETHND.cpy ERROR-TYPE."""

    VALIDATION = "V"
    PROCESSING = "P"
    DATABASE = "D"
    FILE = "F"
    SECURITY = "S"


class ActionFlag(str, Enum):
    """Recovery action flags from RETHND.cpy RETURN-ACTIONS."""

    CONTINUE = "C"
    ABORT = "A"
    RETRY = "R"


# Standard error codes from RETHND.cpy STD-ERROR-CODES
STANDARD_ERROR_CODES = {
    "E001": "Invalid data",
    "E002": "Not found",
    "E003": "Duplicate record",
    "E004": "File error",
    "E005": "Database error",
    "E006": "Security error",
    "E007": "Processing error",
    "E008": "Validation error",
    "E009": "Version error",
    "E010": "Timeout error",
}

# Maximum thresholds from BCHCON.cpy BCT-CTRL-VALUES
MAX_PREREQUISITES = 10
MAX_RESTARTS = 3
WAIT_INTERVAL_SECONDS = 300
MAX_WAIT_TIME_SECONDS = 3600


@dataclass
class ReturnStatus:
    """
    Tracks return code state for a program execution.

    Mirrors RTNCODE.cpy RETURN-CODE-AREA and RETHND.cpy RETURN-HANDLING.
    Manages current code, highest code seen, status classification,
    and error details.
    """

    program_id: str = ""
    current_code: int = 0
    highest_code: int = 0
    status: StatusCode = StatusCode.SUCCESS
    message: str = ""
    error_type: Optional[ErrorType] = None
    error_code: str = ""
    module_id: str = ""
    function_id: str = ""
    action: ActionFlag = ActionFlag.CONTINUE
    retry_count: int = 0
    max_retries: int = 3
    timestamp: Optional[datetime] = field(default=None)

    def set_code(self, code: int, message: str = "") -> None:
        """
        Set a new return code and update status classification.

        Mirrors RTNCDE00.cbl P200-SET-RETURN-CODE logic:
        0 = SUCCESS, 1-4 = WARNING, 5-8 = ERROR, 9+ = SEVERE.
        Always tracks the highest code seen.
        """
        if code > self.highest_code:
            self.highest_code = code

        self.current_code = code

        if code == 0:
            self.status = StatusCode.SUCCESS
        elif 1 <= code <= 4:
            self.status = StatusCode.WARNING
        elif 5 <= code <= 8:
            self.status = StatusCode.ERROR
        else:
            self.status = StatusCode.SEVERE

        if message:
            self.message = message

        self.timestamp = datetime.now()
        logger.info(
            "Return code set: program=%s code=%d status=%s message=%s",
            self.program_id,
            code,
            self.status.value,
            message,
        )

    def get_code(self) -> int:
        """Return the current return code."""
        return self.current_code

    def get_highest(self) -> int:
        """Return the highest return code seen."""
        return self.highest_code

    def is_success(self) -> bool:
        """Check if current status indicates success (RC=0)."""
        return self.current_code == ReturnCode.SUCCESS

    def is_warning(self) -> bool:
        """Check if current status indicates a warning (RC 1-4)."""
        return 1 <= self.current_code <= 4

    def is_error(self) -> bool:
        """Check if current status indicates an error (RC 5-8)."""
        return 5 <= self.current_code <= 8

    def is_severe(self) -> bool:
        """Check if current status indicates severe failure (RC > 8)."""
        return self.current_code > 8

    def can_continue(self) -> bool:
        """
        Check if processing should continue.

        Pipeline gating rule: RC <= 4 means continue.
        Mirrors the JCL COND=(4,LT) condition code checks.
        """
        return self.current_code <= ReturnCode.WARNING

    def should_retry(self) -> bool:
        """Check if a retry is appropriate based on action flag and retry count."""
        return self.action == ActionFlag.RETRY and self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment the retry counter."""
        self.retry_count += 1

    def reset(self) -> None:
        """
        Reset the return status for a new execution.

        Mirrors RTNCDE00.cbl P100-INIT-RETURN-CODES.
        """
        self.current_code = 0
        self.highest_code = 0
        self.status = StatusCode.SUCCESS
        self.message = ""
        self.error_type = None
        self.error_code = ""
        self.action = ActionFlag.CONTINUE
        self.retry_count = 0
        self.timestamp = None

    def to_dict(self) -> dict:
        """Serialize return status to a dictionary."""
        return {
            "program_id": self.program_id,
            "current_code": self.current_code,
            "highest_code": self.highest_code,
            "status": self.status.value,
            "message": self.message,
            "error_type": self.error_type.value if self.error_type else None,
            "error_code": self.error_code,
            "action": self.action.value,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


def classify_return_code(code: int) -> StatusCode:
    """
    Classify a numeric return code into a status category.

    Mirrors the EVALUATE in RTNCDE00.cbl P200-SET-RETURN-CODE.
    """
    if code == 0:
        return StatusCode.SUCCESS
    elif 1 <= code <= 4:
        return StatusCode.WARNING
    elif 5 <= code <= 8:
        return StatusCode.ERROR
    else:
        return StatusCode.SEVERE


def can_continue_pipeline(return_code: int) -> bool:
    """
    Determine if the pipeline should continue after a step.

    Mirrors the JCL COND parameter gating: RC <= 4 allows continuation.
    """
    return return_code <= ReturnCode.WARNING
