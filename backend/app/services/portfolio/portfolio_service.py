"""
Portfolio Master Management Service - Migrated from COBOL PORTMSTR.cbl, PORTADD.cbl,
PORTREAD.cbl, PORTUPDT.cbl, PORTDEL.cbl

Orchestrates CRUD operations for Portfolio records:
- Create: Validate and write new portfolio records (PORTADD)
- Read: Retrieve portfolio by ID or list all (PORTREAD)
- Update: Modify existing portfolio fields (PORTUPDT)
- Delete: Remove portfolio with audit trail (PORTDEL)

The COBOL PORTMSTR program used a LINKAGE SECTION command area
(LS-COMMAND-AREA) with a single-char command ('C', 'R', 'U', 'D')
to dispatch to the appropriate operation. Portfolio data was stored
in a VSAM KSDS file with PORT-ID as the record key.

PORTADD read input records sequentially, validated each, and wrote
to the VSAM file, tracking add/duplicate/error counts.

PORTREAD opened the VSAM file for sequential reading and displayed
each record's fields.

PORTUPDT read update records with an action code (S=status, V=value,
N=name) and applied the change to the matching VSAM record.

PORTDEL read deletion requests with reason codes (01=closed,
02=transferred, 03=requested), deleted the record, and wrote
an audit trail.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import json

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from models.database import Portfolio, Position, SessionLocal
from models.history import History

logger = logging.getLogger(__name__)

# Valid portfolio statuses (from COBOL 88 VALID-STATUS VALUE 'A' 'I' 'C')
VALID_STATUSES = {"A", "C", "S"}

# Valid client types (from COBOL CheckConstraint)
VALID_CLIENT_TYPES = {"I", "C", "T"}

# Delete reason codes (from COBOL PORTDEL DEL-REASON-CODE)
REASON_CLOSED = "01"
REASON_TRANSFERRED = "02"
REASON_REQUESTED = "03"
VALID_REASON_CODES = {REASON_CLOSED, REASON_TRANSFERRED, REASON_REQUESTED}


class PortfolioCRUDService:
    """
    Main portfolio management service orchestrating CRUD operations.

    Migrated from COBOL PORTMSTR which used EVALUATE TRUE on the
    command area to dispatch to CREATE, READ, UPDATE, or DELETE paragraphs.
    Each operation opened the VSAM file I-O, performed the operation,
    and closed the file on completion or error.
    """

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    # ----------------------------------------------------------------
    # CREATE - Migrated from PORTADD.cbl / PORTMSTR 2000-CREATE-PORTFOLIO
    # ----------------------------------------------------------------

    def create_portfolio(
        self,
        port_id: str,
        account_no: str,
        client_name: str,
        client_type: str = "I",
        status: str = "A",
        total_value: Optional[Decimal] = None,
        cash_balance: Optional[Decimal] = None,
        user: str = "SYSTEM",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Create a new portfolio record.

        Mirrors COBOL PORTADD 2100-VALIDATE-AND-ADD:
        1. Validate input fields (PORT-ID not spaces, CLIENT-NAME not spaces,
           STATUS = 'A')
        2. Set PORT-CREATE-DATE and PORT-LAST-MAINT to current date
        3. WRITE PORT-RECORD
        4. Handle duplicate key (file status '22') and other errors

        Also mirrors PORTMSTR 2000-CREATE-PORTFOLIO:
        1. Move LS-PORTFOLIO to PORTFOLIO-RECORD
        2. Perform 2100-VALIDATE-PORTFOLIO
        3. WRITE PORTFOLIO-RECORD
        4. Check for PORT-DUP-KEY

        Args:
            port_id: Portfolio ID (8 chars, must start with 'PORT')
            account_no: Account number (10 numeric digits)
            client_name: Client name
            client_type: Client type ('I'=Individual, 'C'=Corporate, 'T'=Trust)
            status: Portfolio status ('A'=Active, 'C'=Closed, 'S'=Suspended)
            total_value: Initial total value
            cash_balance: Initial cash balance
            user: User performing the operation

        Returns:
            Tuple of (success, result_dict)
        """
        # Validate (mirrors PORTMSTR 2100-VALIDATE-PORTFOLIO and PORTADD validation)
        from .portfolio_validator import PortfolioValidator
        validator = PortfolioValidator()
        is_valid, errors = validator.validate_portfolio_data(
            port_id=port_id,
            account_no=account_no,
            client_name=client_name,
            client_type=client_type,
            status=status,
        )

        if not is_valid:
            logger.warning("Portfolio validation failed for %s: %s", port_id, errors)
            return False, {"errors": errors}

        try:
            now = date.today()
            portfolio = Portfolio(
                port_id=port_id,
                account_no=account_no,
                client_name=client_name,
                client_type=client_type,
                create_date=now,
                last_maint=now,
                status=status,
                total_value=total_value or Decimal("0.00"),
                cash_balance=cash_balance or Decimal("0.00"),
                last_user=user,
                last_trans="CREATE",
            )

            self.db.add(portfolio)
            self.db.flush()

            # Create audit record
            audit_record = History.create_audit_record(
                portfolio_id=port_id,
                record_type="PT",
                action_code="A",
                after_data=portfolio.to_dict(),
                reason_code="CREA",
                user=user,
                db_session=self.db,
            )
            self.db.add(audit_record)
            self.db.commit()

            logger.info("Portfolio created: %s", port_id)
            return True, {"portfolio": portfolio.to_dict()}

        except IntegrityError:
            # Mirrors COBOL PORT-DUP-KEY (file status '22')
            self.db.rollback()
            logger.warning("Portfolio ID already exists: %s", port_id)
            return False, {"errors": ["Portfolio ID already exists"]}

        except Exception as e:
            self.db.rollback()
            logger.error("Error creating portfolio %s: %s", port_id, e)
            return False, {"errors": [f"Error writing Portfolio record: {e}"]}

    # ----------------------------------------------------------------
    # READ - Migrated from PORTREAD.cbl / PORTMSTR 3000-READ-PORTFOLIO
    # ----------------------------------------------------------------

    def get_portfolio(
        self,
        port_id: str,
        account_no: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Read a portfolio record by ID.

        Mirrors COBOL PORTMSTR 3000-READ-PORTFOLIO:
        1. Move LS-PORTFOLIO to PORTFOLIO-RECORD (set key)
        2. READ PORTFOLIO-FILE
        3. Evaluate: PORT-SUCCESS -> return record,
           PORT-NOT-FOUND (status '23') -> error,
           OTHER -> error

        Also mirrors PORTREAD 2100-DISPLAY-RECORD which displayed
        PORT-ID, PORT-ACCOUNT-NO, PORT-CLIENT-NAME, PORT-STATUS,
        PORT-TOTAL-VALUE for each record read.

        Args:
            port_id: Portfolio ID to look up
            account_no: Optional account number for composite key lookup

        Returns:
            Tuple of (success, result_dict with portfolio data or errors)
        """
        try:
            query = self.db.query(Portfolio).filter(Portfolio.port_id == port_id)
            if account_no:
                query = query.filter(Portfolio.account_no == account_no)

            portfolio = query.first()

            if portfolio is None:
                # Mirrors COBOL PORT-NOT-FOUND (file status '23')
                logger.info("Portfolio not found: %s", port_id)
                return False, {"errors": ["Portfolio not found"]}

            return True, {"portfolio": portfolio.to_dict()}

        except Exception as e:
            logger.error("Error reading portfolio %s: %s", port_id, e)
            return False, {"errors": [f"Error reading Portfolio: {e}"]}

    def list_portfolios(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        List all portfolio records (sequential read).

        Mirrors COBOL PORTREAD 2000-PROCESS which read PORTFOLIO-FILE
        NEXT RECORD sequentially until END-OF-FILE, incrementing
        WS-RECORD-COUNT and displaying each record.

        Args:
            status: Optional filter by portfolio status
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            Tuple of (success, result_dict with list of portfolios)
        """
        try:
            query = self.db.query(Portfolio)
            if status:
                query = query.filter(Portfolio.status == status)

            total_count = query.count()
            portfolios = query.offset(offset).limit(limit).all()

            return True, {
                "portfolios": [p.to_dict() for p in portfolios],
                "total_count": total_count,
                "offset": offset,
                "limit": limit,
            }

        except Exception as e:
            logger.error("Error listing portfolios: %s", e)
            return False, {"errors": [f"Error reading Portfolios: {e}"]}

    # ----------------------------------------------------------------
    # UPDATE - Migrated from PORTUPDT.cbl / PORTMSTR 4000-UPDATE-PORTFOLIO
    # ----------------------------------------------------------------

    def update_portfolio(
        self,
        port_id: str,
        account_no: Optional[str] = None,
        client_name: Optional[str] = None,
        status: Optional[str] = None,
        total_value: Optional[Decimal] = None,
        cash_balance: Optional[Decimal] = None,
        user: str = "SYSTEM",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Update an existing portfolio record.

        Mirrors COBOL PORTUPDT 2100-PROCESS-UPDATE:
        1. Move UPDT-KEY to PORT-KEY
        2. READ PORTFOLIO-FILE (find existing record)
        3. If found, perform 2200-APPLY-UPDATE
        4. REWRITE PORT-RECORD

        2200-APPLY-UPDATE dispatched based on UPDT-ACTION:
        - 'S' (UPDT-STATUS): Move UPDT-NEW-VALUE to PORT-STATUS
        - 'N' (UPDT-NAME): Move UPDT-NEW-VALUE to PORT-CLIENT-NAME
        - 'V' (UPDT-VALUE): Move UPDT-NEW-VALUE to PORT-TOTAL-VALUE

        Also mirrors PORTMSTR 4000-UPDATE-PORTFOLIO:
        1. Validate portfolio data
        2. REWRITE PORTFOLIO-RECORD
        3. Check for PORT-NOT-FOUND
        4. Perform 2100-LOG-PORTFOLIO-UPDATE

        Args:
            port_id: Portfolio ID to update
            account_no: Optional account number for composite key
            client_name: New client name (if updating)
            status: New status (if updating)
            total_value: New total value (if updating)
            cash_balance: New cash balance (if updating)
            user: User performing the operation

        Returns:
            Tuple of (success, result_dict)
        """
        try:
            query = self.db.query(Portfolio).filter(Portfolio.port_id == port_id)
            if account_no:
                query = query.filter(Portfolio.account_no == account_no)

            portfolio = query.first()

            if portfolio is None:
                # Mirrors COBOL PORT-NOT-FOUND for update
                logger.warning("Portfolio not found for update: %s", port_id)
                return False, {"errors": ["Portfolio not found for update"]}

            # Save before-image for audit (mirrors COBOL WS-BEFORE-IMAGE)
            before_image = portfolio.to_dict()

            # Apply updates (mirrors COBOL 2200-APPLY-UPDATE)
            if client_name is not None:
                portfolio.client_name = client_name

            if status is not None:
                if status not in VALID_STATUSES:
                    return False, {"errors": [f"Invalid Portfolio Status: {status}"]}
                portfolio.status = status

            if total_value is not None:
                portfolio.total_value = total_value

            if cash_balance is not None:
                portfolio.cash_balance = cash_balance

            portfolio.last_maint = date.today()
            portfolio.last_user = user
            portfolio.last_trans = "UPDATE"

            # Create audit record (mirrors COBOL 2100-LOG-PORTFOLIO-UPDATE)
            audit_record = History.create_audit_record(
                portfolio_id=port_id,
                record_type="PT",
                action_code="C",
                before_data=before_image,
                after_data=portfolio.to_dict(),
                reason_code="UPDT",
                user=user,
                db_session=self.db,
            )
            self.db.add(audit_record)
            self.db.commit()

            logger.info("Portfolio updated: %s", port_id)
            return True, {"portfolio": portfolio.to_dict()}

        except Exception as e:
            self.db.rollback()
            logger.error("Error updating portfolio %s: %s", port_id, e)
            return False, {"errors": [f"Error updating Portfolio: {e}"]}

    # ----------------------------------------------------------------
    # DELETE - Migrated from PORTDEL.cbl / PORTMSTR 5000-DELETE-PORTFOLIO
    # ----------------------------------------------------------------

    def delete_portfolio(
        self,
        port_id: str,
        account_no: Optional[str] = None,
        reason_code: str = REASON_REQUESTED,
        user: str = "SYSTEM",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Delete a portfolio record with audit trail.

        Mirrors COBOL PORTDEL 2100-PROCESS-DELETE:
        1. Move DEL-KEY to PORT-KEY
        2. READ PORTFOLIO-FILE
        3. Evaluate: WS-SUCCESS-STATUS -> perform 2200-DELETE-RECORD,
           WS-REC-NOT-FND -> increment WS-NOT-FND-COUNT,
           OTHER -> increment WS-ERROR-COUNT

        2200-DELETE-RECORD:
        1. DELETE PORTFOLIO-FILE
        2. If success, increment WS-DELETE-COUNT and 2300-WRITE-AUDIT
        3. Otherwise, increment WS-ERROR-COUNT

        2300-WRITE-AUDIT wrote an audit record with:
        - AUD-TIMESTAMP, AUD-ACTION='DELETE', AUD-KEY=PORT-KEY,
          AUD-REASON=DEL-REASON-CODE, AUD-STATUS=PORT-STATUS

        Also mirrors PORTMSTR 5000-DELETE-PORTFOLIO:
        1. DELETE PORTFOLIO-FILE
        2. Check PORT-NOT-FOUND

        Args:
            port_id: Portfolio ID to delete
            account_no: Optional account number for composite key
            reason_code: Deletion reason ('01'=closed, '02'=transferred, '03'=requested)
            user: User performing the operation

        Returns:
            Tuple of (success, result_dict)
        """
        try:
            query = self.db.query(Portfolio).filter(Portfolio.port_id == port_id)
            if account_no:
                query = query.filter(Portfolio.account_no == account_no)

            portfolio = query.first()

            if portfolio is None:
                # Mirrors COBOL WS-REC-NOT-FND
                logger.warning("Portfolio not found for deletion: %s", port_id)
                return False, {"errors": ["Portfolio not found for deletion"]}

            # Save before-image for audit
            before_image = portfolio.to_dict()

            # Delete the portfolio record first (mirrors COBOL DELETE PORTFOLIO-FILE)
            # Note: cascade="all, delete-orphan" on the relationship will also
            # delete associated positions, transactions, and history records.
            self.db.delete(portfolio)
            self.db.flush()

            # Write audit record AFTER deletion using raw SQL to bypass the
            # ORM cascade that would delete it along with the portfolio.
            # This mirrors COBOL 2300-WRITE-AUDIT which wrote the audit trail
            # after the DELETE was successful.
            #
            # We temporarily disable FK enforcement because the History table
            # has a ForeignKeyConstraint on portfolio_id -> portfolios.port_id,
            # and the portfolio has already been deleted. The audit record
            # intentionally references the now-deleted portfolio as a permanent
            # deletion log. For PostgreSQL, use SET CONSTRAINTS ... DEFERRED.
            now = datetime.now()
            date_str = now.strftime("%Y%m%d")
            time_str = now.strftime("%H%M%S%f")[:8]

            dialect = self.db.bind.dialect.name if self.db.bind else "sqlite"
            if dialect == "sqlite":
                self.db.execute(text("PRAGMA foreign_keys = OFF"))
            elif dialect == "postgresql":
                self.db.execute(text("SET CONSTRAINTS ALL DEFERRED"))

            self.db.execute(
                text(
                    "INSERT INTO history (portfolio_id, date, time, seq_no, "
                    "record_type, action_code, before_image, after_image, "
                    "reason_code, process_date, process_user) "
                    "VALUES (:pid, :dt, :tm, :seq, :rt, :ac, :bi, :ai, :rc, :pd, :pu)"
                ),
                {
                    "pid": port_id,
                    "dt": date_str,
                    "tm": time_str,
                    "seq": "0001",
                    "rt": "PT",
                    "ac": "D",
                    "bi": json.dumps(before_image),
                    "ai": None,
                    "rc": reason_code,
                    "pd": now,
                    "pu": user,
                },
            )

            if dialect == "sqlite":
                self.db.execute(text("PRAGMA foreign_keys = ON"))

            self.db.commit()

            logger.info("Portfolio deleted: %s (reason: %s)", port_id, reason_code)
            return True, {
                "deleted_portfolio": before_image,
                "reason_code": reason_code,
            }

        except Exception as e:
            self.db.rollback()
            logger.error("Error deleting portfolio %s: %s", port_id, e)
            return False, {"errors": [f"Error deleting Portfolio: {e}"]}

    def close(self) -> None:
        """Close database session if we created one."""
        if self._db is not None:
            self._db.close()
