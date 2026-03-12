"""
File Maintenance Utility - Migrated from COBOL UTLMNT00.cbl

Performs maintenance operations on system data:
- Archive processing: move old records to archive storage
- Cleanup: remove expired/obsolete records and reclaim space
- Reorganization: optimize database tables and indexes
- Analysis: collect statistics and generate maintenance reports
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from models.database import Portfolio, Position, Base, SessionLocal
from models.transactions import Transaction
from models.history import History

logger = logging.getLogger(__name__)


# Maintenance function constants (from COBOL WS-FUNCTIONS)
FUNCTION_ARCHIVE = "ARCHIVE"
FUNCTION_CLEANUP = "CLEANUP"
FUNCTION_REORG = "REORG"
FUNCTION_ANALYZE = "ANALYZE"

VALID_FUNCTIONS = {FUNCTION_ARCHIVE, FUNCTION_CLEANUP, FUNCTION_REORG, FUNCTION_ANALYZE}

# Maximum errors before aborting (from COBOL WS-ERROR-COUNT > 100 check)
MAX_ERRORS = 100


class MaintenanceResult:
    """Tracks results of a maintenance operation."""

    def __init__(self, function_name: str):
        self.function_name = function_name
        self.records_read: int = 0
        self.records_written: int = 0
        self.records_deleted: int = 0
        self.error_count: int = 0
        self.errors: List[str] = []
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None

    def add_error(self, message: str) -> None:
        self.error_count += 1
        self.errors.append(message)
        logger.error("Maintenance error [%s]: %s", self.function_name, message)

    def finalize(self) -> Dict[str, Any]:
        self.end_time = datetime.now()
        elapsed = (self.end_time - self.start_time).total_seconds()
        return {
            "function": self.function_name,
            "records_read": self.records_read,
            "records_written": self.records_written,
            "records_deleted": self.records_deleted,
            "error_count": self.error_count,
            "errors": self.errors,
            "elapsed_seconds": elapsed,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }


class MaintenanceService:
    """
    File/data maintenance service.

    Migrated from COBOL UTLMNT00 which performed:
    - ARCHIVE: Archive old records to history
    - CLEANUP: Remove expired records and reclaim space
    - REORG: Reorganize VSAM files (mapped to DB optimization)
    - ANALYZE: Collect statistics and generate reports
    """

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def execute(self, functions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Execute maintenance operations.

        Mirrors COBOL 2000-PROCESS which reads control records and
        dispatches to the appropriate function via EVALUATE.

        Args:
            functions: List of maintenance functions to execute.
                       If None, runs all functions.

        Returns:
            List of result dictionaries, one per function executed.
        """
        if functions is None:
            functions = [FUNCTION_ARCHIVE, FUNCTION_CLEANUP, FUNCTION_REORG, FUNCTION_ANALYZE]

        results: List[Dict[str, Any]] = []
        total_errors = 0

        for func_name in functions:
            func_name = func_name.strip().upper()
            if func_name not in VALID_FUNCTIONS:
                logger.error("Invalid function specified: %s", func_name)
                results.append({
                    "function": func_name,
                    "error": "INVALID FUNCTION SPECIFIED",
                })
                total_errors += 1
                continue

            if total_errors > MAX_ERRORS:
                logger.error("Maximum error count exceeded, aborting maintenance")
                break

            result = self._process_function(func_name)
            results.append(result)
            total_errors += result.get("error_count", 0)

        logger.info("Maintenance complete. Functions executed: %d", len(results))
        return results

    def _process_function(self, function_name: str) -> Dict[str, Any]:
        """Dispatch to the appropriate maintenance function (mirrors COBOL 2100-PROCESS-FUNCTION)."""
        dispatch = {
            FUNCTION_ARCHIVE: self._archive_process,
            FUNCTION_CLEANUP: self._cleanup_process,
            FUNCTION_REORG: self._reorg_process,
            FUNCTION_ANALYZE: self._analyze_process,
        }
        handler = dispatch[function_name]
        return handler()

    def _archive_process(self) -> Dict[str, Any]:
        """
        Archive old records to history.

        Mirrors COBOL 2200-ARCHIVE-PROCESS:
        - Opens VSAM file for the target dataset
        - Reads and archives qualifying records
        - Closes the VSAM file

        In the modernized version, this archives old transactions and
        positions to the history table and optionally removes them.
        """
        result = MaintenanceResult(FUNCTION_ARCHIVE)
        archive_cutoff = date.today() - timedelta(days=365)

        try:
            # Archive old transactions (older than 1 year)
            old_transactions = self.db.query(Transaction).filter(
                Transaction.date < archive_cutoff,
                Transaction.status == "D",
            ).all()

            result.records_read = len(old_transactions)

            for txn in old_transactions:
                if result.error_count > MAX_ERRORS:
                    result.add_error("Maximum error count exceeded during archival")
                    break
                try:
                    audit_record = History.create_audit_record(
                        portfolio_id=txn.portfolio_id,
                        record_type="TR",
                        action_code="D",
                        before_data=txn.to_dict(),
                        reason_code="ARCH",
                        user="MAINT",
                        db_session=self.db,
                    )
                    self.db.add(audit_record)
                    self.db.delete(txn)
                    result.records_written += 1
                except Exception as e:
                    result.add_error(f"Error archiving transaction: {e}")

            self.db.commit()
            logger.info("Archive process complete. Archived %d records.", result.records_written)

        except Exception as e:
            self.db.rollback()
            result.add_error(f"Archive process failed: {e}")

        return result.finalize()

    def _cleanup_process(self) -> Dict[str, Any]:
        """
        Clean up old records and reclaim space.

        Mirrors COBOL 2300-CLEANUP-PROCESS:
        - 2310-ANALYZE-SPACE: Check space utilization
        - 2320-DELETE-OLD: Remove expired records
        - 2330-UPDATE-CATALOG: Update system catalog

        In the modernized version, removes closed/cancelled positions
        and portfolios with status 'C' (Closed) that have no active positions.
        """
        result = MaintenanceResult(FUNCTION_CLEANUP)
        cleanup_cutoff = date.today() - timedelta(days=90)

        try:
            # Delete old closed positions
            closed_positions = self.db.query(Position).filter(
                Position.status == "C",
                Position.last_maint_date < datetime.combine(cleanup_cutoff, datetime.min.time()),
            ).all()

            result.records_read = len(closed_positions)

            for pos in closed_positions:
                if result.error_count > MAX_ERRORS:
                    result.add_error("Maximum error count exceeded during cleanup")
                    break
                try:
                    self.db.delete(pos)
                    result.records_deleted += 1
                except Exception as e:
                    result.add_error(f"Error deleting position: {e}")

            self.db.commit()
            logger.info("Cleanup process complete. Deleted %d records.", result.records_deleted)

        except Exception as e:
            self.db.rollback()
            result.add_error(f"Cleanup process failed: {e}")

        return result.finalize()

    def _reorg_process(self) -> Dict[str, Any]:
        """
        Reorganize database tables.

        Mirrors COBOL 2400-REORG-PROCESS:
        - 2410-EXPORT-DATA: Export current data
        - 2420-DELETE-DEFINE: Delete and redefine VSAM cluster
        - 2430-IMPORT-DATA: Import data back

        In the modernized version, this triggers database table
        optimization (VACUUM/ANALYZE for PostgreSQL, or VACUUM for SQLite).
        """
        result = MaintenanceResult(FUNCTION_REORG)

        try:
            # For SQLite: VACUUM to reclaim space and defragment
            # For PostgreSQL: would use VACUUM ANALYZE
            self.db.execute(text("VACUUM"))
            self.db.commit()
            result.records_written = 1
            logger.info("Reorg process complete. Database optimized.")

        except Exception as e:
            self.db.rollback()
            result.add_error(f"Reorg process failed: {e}")

        return result.finalize()

    def _analyze_process(self) -> Dict[str, Any]:
        """
        Collect statistics and generate analysis report.

        Mirrors COBOL 2500-ANALYZE-PROCESS:
        - 2510-COLLECT-STATS: Gather file/table statistics
        - 2520-GENERATE-REPORT: Produce analysis report

        Returns statistics about the database tables.
        """
        result = MaintenanceResult(FUNCTION_ANALYZE)

        try:
            portfolio_count = self.db.query(func.count(Portfolio.port_id)).scalar() or 0
            position_count = self.db.query(func.count(Position.portfolio_id)).scalar() or 0
            transaction_count = self.db.query(func.count(Transaction.portfolio_id)).scalar() or 0
            history_count = self.db.query(func.count(History.portfolio_id)).scalar() or 0

            active_portfolios = self.db.query(func.count(Portfolio.port_id)).filter(
                Portfolio.status == "A"
            ).scalar() or 0

            total_value = self.db.query(func.sum(Portfolio.total_value)).filter(
                Portfolio.status == "A"
            ).scalar() or Decimal("0.00")

            result.records_read = portfolio_count + position_count + transaction_count + history_count

            report = {
                "portfolio_count": portfolio_count,
                "active_portfolios": active_portfolios,
                "position_count": position_count,
                "transaction_count": transaction_count,
                "history_count": history_count,
                "total_portfolio_value": float(total_value),
                "analysis_date": datetime.now().isoformat(),
            }

            logger.info("Analyze process complete. Report: %s", report)
            analysis_result = result.finalize()
            analysis_result["report"] = report
            return analysis_result

        except Exception as e:
            result.add_error(f"Analyze process failed: {e}")
            return result.finalize()

    def close(self) -> None:
        """Close database session if we created one."""
        if self._db is not None:
            self._db.close()
