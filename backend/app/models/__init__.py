"""
Pydantic data models translated from COBOL copybooks.

Each model preserves the semantics of the original COBOL data structures.
COBOL PIC clause mappings:
  - PIC X(n)         -> str (max_length=n)
  - PIC 9(n)         -> int
  - PIC S9(n)V9(m)   -> Decimal
  - PIC S9(n) COMP   -> int
  - 88-level values   -> Literal types or Enum
"""

from app.models.common import (
    ReturnCodeValues,
    StatusCodes,
    TransactionTypes,
    CommonDatetime,
    CommonErrorHandling,
    CommonAuditFields,
    CurrencyCodes,
)
from app.models.transaction_record import TransactionRecord
from app.models.position_record import PositionRecord
from app.models.history_record import HistoryRecord
from app.models.portfolio import Portfolio
from app.models.portfolio_validation import PortfolioValidation
from app.models.audit_log import AuditLogEntry
from app.models.error_record import ErrorRecord, ErrorCategories, ErrorMessage
from app.models.return_code import ReturnCode
from app.models.retry_handler import ReturnHandling, StandardErrorCodes
from app.models.batch_control import BatchControlRecord
from app.models.batch_constants import BatchConstants
from app.models.process_sequence import ProcessSequenceRecord, StandardSequences
from app.models.checkpoint_restart import CheckpointControl, CheckpointRecord
from app.models.inquiry_common import InquiryCommon
from app.models.db2_request import DB2Request
from app.models.online_error_handler import OnlineErrorHandler
from app.models.db2_procedure import DB2Procedure

__all__ = [
    "ReturnCodeValues",
    "StatusCodes",
    "TransactionTypes",
    "CommonDatetime",
    "CommonErrorHandling",
    "CommonAuditFields",
    "CurrencyCodes",
    "TransactionRecord",
    "PositionRecord",
    "HistoryRecord",
    "Portfolio",
    "PortfolioValidation",
    "AuditLogEntry",
    "ErrorRecord",
    "ErrorCategories",
    "ErrorMessage",
    "ReturnCode",
    "ReturnHandling",
    "StandardErrorCodes",
    "BatchControlRecord",
    "BatchConstants",
    "ProcessSequenceRecord",
    "StandardSequences",
    "CheckpointControl",
    "CheckpointRecord",
    "InquiryCommon",
    "DB2Request",
    "OnlineErrorHandler",
    "DB2Procedure",
]
