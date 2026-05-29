"""
Audit Log Entry data model.

Translated from COBOL copybook: src/copybook/common/AUDITLOG.cpy

COBOL structure: AUDIT-RECORD (01 level)
  - AUD-HEADER: timestamp, system/user/program/terminal IDs
  - AUD-TYPE: audit event type (TRAN, USER, SYST)
  - AUD-ACTION: action performed (CREATE, UPDATE, DELETE, etc.)
  - AUD-STATUS: result status (SUCC, FAIL, WARN)
  - AUD-KEY-INFO: portfolio/account reference
  - AUD-BEFORE-IMAGE / AUD-AFTER-IMAGE: record snapshots
  - AUD-MESSAGE: descriptive message
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Audit trail record.

    Translated from COBOL copybook AUDITLOG.cpy.
    Maps to AUDIT-RECORD (01 level).

    Audit types (88-level values):
      TRAN = Transaction, USER = User Action, SYST = System Event

    Audit actions (88-level values):
      CREATE, UPDATE, DELETE, INQUIRE, LOGIN, LOGOUT, STARTUP, SHUTDOWN

    Audit statuses (88-level values):
      SUCC = Success, FAIL = Failure, WARN = Warning
    """

    # AUD-HEADER fields
    aud_timestamp: str = Field(
        default="", max_length=26,
        description="AUD-TIMESTAMP: Event timestamp - PIC X(26)"
    )
    aud_system_id: str = Field(
        default="", max_length=8,
        description="AUD-SYSTEM-ID: System identifier - PIC X(8)"
    )
    aud_user_id: str = Field(
        default="", max_length=8,
        description="AUD-USER-ID: User identifier - PIC X(8)"
    )
    aud_program: str = Field(
        default="", max_length=8,
        description="AUD-PROGRAM: Program name - PIC X(8)"
    )
    aud_terminal: str = Field(
        default="", max_length=8,
        description="AUD-TERMINAL: Terminal ID - PIC X(8)"
    )

    # AUD-TYPE
    aud_type: Literal["TRAN", "USER", "SYST"] = Field(
        ...,
        description="AUD-TYPE: TRAN=Transaction, USER=User Action, SYST=System Event - PIC X(4)"
    )

    # AUD-ACTION (padded to 8 chars in COBOL, we strip trailing spaces)
    aud_action: Literal[
        "CREATE", "UPDATE", "DELETE", "INQUIRE",
        "LOGIN", "LOGOUT", "STARTUP", "SHUTDOWN"
    ] = Field(
        ...,
        description="AUD-ACTION: Action performed - PIC X(8)"
    )

    # AUD-STATUS
    aud_status: Literal["SUCC", "FAIL", "WARN"] = Field(
        ...,
        description="AUD-STATUS: SUCC=Success, FAIL=Failure, WARN=Warning - PIC X(4)"
    )

    # AUD-KEY-INFO fields
    aud_portfolio_id: str = Field(
        default="", max_length=8,
        description="AUD-PORTFOLIO-ID: Portfolio identifier - PIC X(8)"
    )
    aud_account_no: str = Field(
        default="", max_length=10,
        description="AUD-ACCOUNT-NO: Account number - PIC X(10)"
    )

    # Before/after images and message
    aud_before_image: str = Field(
        default="", max_length=100,
        description="AUD-BEFORE-IMAGE: Record image before change - PIC X(100)"
    )
    aud_after_image: str = Field(
        default="", max_length=100,
        description="AUD-AFTER-IMAGE: Record image after change - PIC X(100)"
    )
    aud_message: str = Field(
        default="", max_length=100,
        description="AUD-MESSAGE: Descriptive message - PIC X(100)"
    )
