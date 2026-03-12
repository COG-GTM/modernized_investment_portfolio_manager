"""
Centralized error processing utility.

Translated from COBOL program: src/programs/common/ERRPROC.cbl

The original COBOL program:
  1. Opens a sequential error log file (ERRLOG)
  2. Accepts an error request via LINKAGE SECTION
  3. Formats the error with timestamp, program, category, severity
  4. Writes to the log file and displays to console
  5. Returns the severity as the return code

Python equivalent uses the standard logging module with custom exception
classes for each error category defined in ERRHAND.cpy.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.error_record import ErrorMessage, ERROR_CATEGORIES, ERROR_CODES

logger = logging.getLogger("portfolio.error")


# ---------------------------------------------------------------------------
# Custom exception hierarchy (maps to ERR-CATEGORIES from ERRHAND.cpy)
# ---------------------------------------------------------------------------

class PortfolioError(Exception):
    """Base exception for portfolio system errors.

    Attributes:
        category: Error category code (VS, VL, PR, SY)
        error_code: Specific error code
        severity: Severity level (0=success, 4=warning, 8=error, 12=severe, 16=terminal)
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        category: str = "PR",
        error_code: str = "",
        severity: int = 8,
        details: str = "",
        program: str = "",
    ) -> None:
        super().__init__(message)
        self.category = category
        self.error_code = error_code
        self.severity = severity
        self.details = details
        self.program = program


class ValidationError(PortfolioError):
    """Validation error (category VL).

    Maps to ERR-CAT-VALID from ERRHAND.cpy.
    """

    def __init__(self, message: str, error_code: str = "", details: str = "", program: str = "") -> None:
        super().__init__(
            message,
            category=ERROR_CATEGORIES.validation,
            error_code=error_code,
            severity=ERROR_CODES.error,
            details=details,
            program=program,
        )


class DatabaseError(PortfolioError):
    """Database error (category SY - system).

    Maps to ERR-CAT-SYSTEM from ERRHAND.cpy for DB2-related errors.
    """

    def __init__(self, message: str, error_code: str = "", details: str = "", program: str = "") -> None:
        super().__init__(
            message,
            category=ERROR_CATEGORIES.system,
            error_code=error_code,
            severity=ERROR_CODES.severe,
            details=details,
            program=program,
        )


class FileError(PortfolioError):
    """File/VSAM error (category VS).

    Maps to ERR-CAT-VSAM from ERRHAND.cpy.
    """

    def __init__(self, message: str, error_code: str = "", details: str = "", program: str = "") -> None:
        super().__init__(
            message,
            category=ERROR_CATEGORIES.vsam,
            error_code=error_code,
            severity=ERROR_CODES.error,
            details=details,
            program=program,
        )


class SecurityError(PortfolioError):
    """Security error.

    No direct COBOL category; uses processing category with security code.
    """

    def __init__(self, message: str, error_code: str = "E006", details: str = "", program: str = "") -> None:
        super().__init__(
            message,
            category=ERROR_CATEGORIES.processing,
            error_code=error_code,
            severity=ERROR_CODES.severe,
            details=details,
            program=program,
        )


class ProcessingError(PortfolioError):
    """Processing error (category PR).

    Maps to ERR-CAT-PROC from ERRHAND.cpy.
    """

    def __init__(self, message: str, error_code: str = "", details: str = "", program: str = "") -> None:
        super().__init__(
            message,
            category=ERROR_CATEGORIES.processing,
            error_code=error_code,
            severity=ERROR_CODES.error,
            details=details,
            program=program,
        )


class ErrorProcessor:
    """Centralized error processing service.

    Translated from COBOL program ERRPROC.cbl.
    Replaces the sequential log file with Python logging.

    The COBOL program flow:
      0000-MAIN -> 1000-INITIALIZE -> 2000-PROCESS-ERROR -> 3000-TERMINATE
      2000-PROCESS-ERROR -> 2100-WRITE-LOG + 2200-DISPLAY-ERROR

    Usage:
        processor = ErrorProcessor(program_id="TRNVAL00")
        processor.process_error(error)
    """

    def __init__(self, program_id: str = "") -> None:
        self.program_id = program_id
        self._logger = logging.getLogger(f"portfolio.error.{program_id}" if program_id else "portfolio.error")

    def process_error(self, error: PortfolioError) -> int:
        """Process an error: log it and return the severity as return code.

        Mirrors COBOL paragraphs:
          2000-PROCESS-ERROR
          2100-WRITE-LOG
          2200-DISPLAY-ERROR

        Args:
            error: The portfolio error to process.

        Returns:
            The severity level (used as return code).
        """
        now = datetime.now(timezone.utc)

        error_msg = ErrorMessage(
            err_date=now.strftime("%Y-%m-%d"),
            err_time=now.strftime("%H:%M:%S"),
            err_program=(error.program or self.program_id)[:8],
            err_category=error.category[:2],
            err_code=error.error_code[:4],
            err_severity=error.severity,
            err_text=str(error)[:80],
            err_details=error.details[:256],
        )

        # 2100-WRITE-LOG equivalent
        self._write_log(error_msg)

        # 2200-DISPLAY-ERROR equivalent
        self._display_error(error_msg)

        # MOVE LS-SEVERITY TO LS-RETURN-CODE
        return error.severity

    def _write_log(self, error_msg: ErrorMessage) -> None:
        """Write error to log (replaces sequential file WRITE).

        Mirrors COBOL paragraph 2100-WRITE-LOG.
        """
        log_level = self._severity_to_log_level(error_msg.err_severity)
        self._logger.log(
            log_level,
            "[%s] %s/%s: %s | %s",
            error_msg.err_program,
            error_msg.err_category,
            error_msg.err_code,
            error_msg.err_text,
            error_msg.err_details,
        )

    def _display_error(self, error_msg: ErrorMessage) -> None:
        """Display error details (replaces COBOL DISPLAY statements).

        Mirrors COBOL paragraph 2200-DISPLAY-ERROR.
        """
        self._logger.info(
            "ERROR DETECTED: %s %s | PROGRAM: %s | CATEGORY: %s | "
            "CODE: %s | SEVERITY: %d | MESSAGE: %s",
            error_msg.err_date,
            error_msg.err_time,
            error_msg.err_program,
            error_msg.err_category,
            error_msg.err_code,
            error_msg.err_severity,
            error_msg.err_text,
        )

    @staticmethod
    def _severity_to_log_level(severity: int) -> int:
        """Map COBOL severity to Python logging level."""
        if severity >= 16:
            return logging.CRITICAL
        if severity >= 12:
            return logging.CRITICAL
        if severity >= 8:
            return logging.ERROR
        if severity >= 4:
            return logging.WARNING
        return logging.INFO
