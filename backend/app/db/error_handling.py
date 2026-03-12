"""
Database error handling utility.

Translated from COBOL program: src/programs/common/DB2ERR.cbl

The original COBOL program:
  - DB2 SQL Error Handler with functions: LOG, DIAG, RETR
  - Classifies SQLCODE errors by severity:
      -911 (deadlock), -913 (timeout) -> severity 2, should retry
      -30081 (connection) -> severity 4, no retry
      -803 (duplicate key) -> severity 1, no retry
      +100 (not found) -> severity 1, no retry
  - Logs errors to ERRLOG DB2 table
  - Diagnoses errors and returns appropriate messages

Python equivalent classifies SQLAlchemy exceptions similarly and provides
logging/diagnosis capabilities.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    OperationalError,
)

logger = logging.getLogger("portfolio.db.error")


# SQLCODE equivalents (from WS-ERROR-CATEGORIES in DB2ERR.cbl)
SQLCODE_DEADLOCK = -911
SQLCODE_TIMEOUT = -913
SQLCODE_CONNECTION_ERROR = -30081
SQLCODE_DUPLICATE_KEY = -803
SQLCODE_NOT_FOUND = 100


class DBErrorHandler:
    """Database error handler.

    Translated from COBOL program DB2ERR.cbl.

    The COBOL program flow:
      0000-MAIN dispatches to:
        1000-LOG-ERROR     (FUNC-LOG)  -> insert into ERRLOG table
        2000-DIAGNOSE-ERROR (FUNC-DIAG) -> classify and return message
        3000-RETRIEVE-ERROR (FUNC-RETR) -> query latest error from ERRLOG

    Usage:
        handler = DBErrorHandler(program_id="POSUPD00")
        severity, should_retry, message = handler.diagnose(exc)
        handler.log_error(exc, additional_info="Processing batch 42")
    """

    def __init__(self, program_id: str = "") -> None:
        self.program_id = program_id
        self._logger = logging.getLogger(
            f"portfolio.db.error.{program_id}" if program_id else "portfolio.db.error"
        )

    def log_error(
        self,
        exc: Exception,
        additional_info: str = "",
    ) -> int:
        """Log a database error (mirrors 1000-LOG-ERROR).

        Args:
            exc: The database exception.
            additional_info: Additional context information.

        Returns:
            0 on success, 12 on logging failure.
        """
        try:
            severity = self._classify_severity(exc)
            now = datetime.now(timezone.utc)

            self._logger.error(
                "DB ERROR [%s] program=%s severity=%d type=%s: %s | %s",
                now.isoformat(),
                self.program_id,
                severity,
                type(exc).__name__,
                str(exc),
                additional_info,
            )
            return 0
        except Exception as log_exc:
            self._logger.error("Error logging to ERRLOG: %s", log_exc)
            return 12

    def diagnose(self, exc: Exception) -> tuple[int, bool, str]:
        """Diagnose a database error (mirrors 2000-DIAGNOSE-ERROR).

        Classifies the exception and determines if a retry is appropriate.

        Args:
            exc: The database exception.

        Returns:
            Tuple of (return_code, should_retry, error_message).
        """
        if isinstance(exc, OperationalError):
            err_str = str(exc).lower()
            if "deadlock" in err_str:
                return 4, True, "Deadlock detected - retry transaction"
            if "timeout" in err_str or "timed out" in err_str:
                return 4, True, "Timeout occurred - retry transaction"
            if "connection" in err_str or "connect" in err_str:
                return 12, False, "DB2 connection error - check availability"
            return 12, False, f"Unhandled DB2 error: {exc}"

        if isinstance(exc, IntegrityError):
            return 8, False, "Duplicate key violation"

        if isinstance(exc, DatabaseError):
            return 12, False, f"Unhandled DB2 error: {exc}"

        # Non-DB exception
        return 12, False, f"Unexpected error: {exc}"

    def _classify_severity(self, exc: Exception) -> int:
        """Classify error severity (mirrors 1100-SET-SEVERITY).

        Severity levels:
          1 = Informational (not found, duplicate key)
          2 = Retryable (deadlock, timeout)
          3 = Unhandled negative SQLCODE
          4 = Connection error
        """
        if isinstance(exc, OperationalError):
            err_str = str(exc).lower()
            if "deadlock" in err_str or "timeout" in err_str:
                return 2
            if "connection" in err_str:
                return 4
            return 3

        if isinstance(exc, IntegrityError):
            return 1

        if isinstance(exc, DatabaseError):
            return 3

        return 3
