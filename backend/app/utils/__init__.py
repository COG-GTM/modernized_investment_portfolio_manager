"""
Common utility modules translated from COBOL programs.

- error_handler.py: from ERRPROC.cbl - centralized error processing
- audit.py: from AUDPROC.cbl - audit trail logging
"""

from app.utils.error_handler import (
    ErrorProcessor,
    PortfolioError,
    ValidationError,
    DatabaseError,
    FileError,
    SecurityError,
    ProcessingError,
)
from app.utils.audit import AuditProcessor

__all__ = [
    "ErrorProcessor",
    "PortfolioError",
    "ValidationError",
    "DatabaseError",
    "FileError",
    "SecurityError",
    "ProcessingError",
    "AuditProcessor",
]
