"""
Audit trail processing utility.

Translated from COBOL program: src/programs/common/AUDPROC.cbl

The original COBOL program:
  1. Opens a sequential audit file (AUDFILE) in EXTEND mode
  2. Accepts audit request via LINKAGE SECTION (LS-AUDIT-REQUEST)
  3. Populates an AUDIT-RECORD (from AUDITLOG.cpy) with timestamp and request data
  4. Writes the record to the audit file
  5. Returns 0 on success, 8 on failure

Python equivalent uses the standard logging module with a dedicated audit
logger and produces structured AuditLogEntry records.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.audit_log import AuditLogEntry

audit_logger = logging.getLogger("portfolio.audit")


class AuditProcessor:
    """Audit trail processing service.

    Translated from COBOL program AUDPROC.cbl.

    The COBOL program flow:
      0000-MAIN -> 1000-INITIALIZE -> 2000-PROCESS-AUDIT -> 3000-TERMINATE

    Usage:
        auditor = AuditProcessor(system_id="PORTMGR", program="TRNVAL00")
        rc = auditor.log_event(
            user_id="USERA",
            audit_type="TRAN",
            action="CREATE",
            status="SUCC",
            portfolio_id="PORT0001",
            account_no="1234567890",
            message="Transaction created successfully",
        )
    """

    def __init__(
        self,
        system_id: str = "PORTMGR",
        program: str = "",
        terminal: str = "",
    ) -> None:
        self.system_id = system_id
        self.program = program
        self.terminal = terminal
        self._logger = audit_logger

    def log_event(
        self,
        user_id: str,
        audit_type: str,
        action: str,
        status: str,
        portfolio_id: str = "",
        account_no: str = "",
        before_image: str = "",
        after_image: str = "",
        message: str = "",
    ) -> int:
        """Log an audit event.

        Mirrors COBOL paragraph 2000-PROCESS-AUDIT.

        Args:
            user_id: User who performed the action.
            audit_type: TRAN, USER, or SYST.
            action: CREATE, UPDATE, DELETE, INQUIRE, LOGIN, LOGOUT, STARTUP, SHUTDOWN.
            status: SUCC, FAIL, or WARN.
            portfolio_id: Related portfolio ID.
            account_no: Related account number.
            before_image: Record state before change.
            after_image: Record state after change.
            message: Descriptive message.

        Returns:
            0 on success, 8 on failure.
        """
        try:
            now = datetime.now(timezone.utc)

            entry = AuditLogEntry(
                aud_timestamp=now.isoformat(),
                aud_system_id=self.system_id,
                aud_user_id=user_id,
                aud_program=self.program,
                aud_terminal=self.terminal,
                aud_type=audit_type,
                aud_action=action,
                aud_status=status,
                aud_portfolio_id=portfolio_id,
                aud_account_no=account_no,
                aud_before_image=before_image,
                aud_after_image=after_image,
                aud_message=message,
            )

            # Write audit record (replaces sequential file WRITE)
            self._write_audit_record(entry)
            return 0

        except Exception as exc:
            # Mirrors: DISPLAY 'Error writing audit record: ' WS-FILE-STATUS
            self._logger.error("Error writing audit record: %s", exc)
            return 8

    def _write_audit_record(self, entry: AuditLogEntry) -> None:
        """Write an audit record to the log.

        Replaces the COBOL WRITE AUDIT-RECORD statement.
        """
        self._logger.info(
            "AUDIT [%s] %s/%s %s | port=%s acct=%s | %s",
            entry.aud_timestamp,
            entry.aud_type,
            entry.aud_action,
            entry.aud_status,
            entry.aud_portfolio_id,
            entry.aud_account_no,
            entry.aud_message,
        )
