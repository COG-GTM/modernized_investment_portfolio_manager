"""
DB2 Standard Procedures configuration data model.

Translated from COBOL copybook: src/copybook/db2/DBPROC.cpy

COBOL structures:
  - DB2-ERROR-HANDLING (01 level): SQL error handling with retry support
  - Procedures: CONNECT-TO-DB2, DISCONNECT-FROM-DB2, DB2-ERROR-ROUTINE,
    CHECK-SQL-STATUS

Note on SQLCA.cpy mapping:
  The COBOL SQLCA (SQL Communication Area) copybook is not directly translated
  because SQLAlchemy handles SQL status/error communication natively.
  The SQLCA fields map conceptually as follows:
    - SQLCODE -> SQLAlchemy exception handling (IntegrityError, OperationalError, etc.)
    - SQLSTATE -> Exception type classification
    - SQL-STATUS-CODES from SQLCA.cpy:
        '00000' (SUCCESS)      -> Normal operation
        '02000' (NOT_FOUND)    -> NoResultFound exception
        '23505' (DUP_KEY)      -> IntegrityError exception
        '40001' (DEADLOCK)     -> OperationalError with deadlock detection
        '40003' (TIMEOUT)      -> OperationalError with timeout
        '08001' (CONN_ERROR)   -> OperationalError with connection failure
        '58004' (DB_ERROR)     -> DatabaseError exception
"""

from pydantic import BaseModel, Field


class DB2Procedure(BaseModel):
    """DB2 procedure configuration and error handling.

    Translated from COBOL copybook DBPROC.cpy.
    Maps to DB2-ERROR-HANDLING (01 level).
    """

    db2_sqlcode_txt: str = Field(
        default="", max_length=6,
        description="DB2-SQLCODE-TXT: Formatted SQL code - PIC X(6)"
    )
    db2_state: str = Field(
        default="", max_length=5,
        description="DB2-STATE: SQL state code - PIC X(5)"
    )
    db2_error_text: str = Field(
        default="", max_length=70,
        description="DB2-ERROR-TEXT: Error description - PIC X(70)"
    )
    db2_save_status: str = Field(
        default="", max_length=5,
        description="DB2-SAVE-STATUS: Saved SQL state - PIC X(5)"
    )
    db2_retry_count: int = Field(
        default=0,
        description="DB2-RETRY-COUNT: Current retry count - PIC S9(4) COMP VALUE 0"
    )
    db2_max_retries: int = Field(
        default=3,
        description="DB2-MAX-RETRIES: Maximum retries - PIC S9(4) COMP VALUE 3"
    )
    db2_retry_wait: int = Field(
        default=100,
        description="DB2-RETRY-WAIT: Wait between retries (ms) - PIC S9(4) COMP VALUE 100"
    )

    def should_retry(self) -> bool:
        """Check if a retry attempt should be made."""
        return self.db2_retry_count < self.db2_max_retries

    def format_error_message(self) -> str:
        """Format a DB2-style error message string."""
        return f"SQLCODE: {self.db2_sqlcode_txt} STATE: {self.db2_state} ERROR: {self.db2_error_text}"


# SQL status code constants (from SQLCA.cpy)
SQL_STATUS_CODES = {
    "SUCCESS": "00000",
    "NOT_FOUND": "02000",
    "DUP_KEY": "23505",
    "DEADLOCK": "40001",
    "TIMEOUT": "40003",
    "CONNECTION_ERROR": "08001",
    "DB_ERROR": "58004",
}
