"""
History Loader.

Migrated from: HISTLD00.cbl, HISTREC.cpy
Loads validated transactions into the history table for reporting.
Reads from the transaction source, maps fields to the DB2/history schema,
and inserts records with commit checkpointing.

Pipeline position: Step 3 (after position updates).
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .return_codes import ReturnCode, ReturnStatus

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal values."""

    def default(self, obj: object) -> object:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


@dataclass
class LoadStatistics:
    """
    Processing statistics for the history load.

    Mirrors HISTLD00.cbl WS-COUNTERS.
    """

    records_read: int = 0
    records_written: int = 0
    error_count: int = 0
    duplicate_count: int = 0
    commit_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class HistoryLoader:
    """
    Loads transaction data into the history table.

    Migrated from HISTLD00.cbl. The COBOL program:
    1. Opens VSAM transaction history file and batch control file (1000-INITIALIZE)
    2. Reads records sequentially (2100-READ-HISTORY)
    3. Maps VSAM fields to DB2 POSHIST columns (2200-LOAD-TO-DB2)
    4. Commits every N records (2300-CHECK-COMMIT with WS-COMMIT-THRESHOLD=1000)
    5. Updates checkpoint after each commit (2310-UPDATE-CHECKPOINT)
    6. Handles duplicate key errors (SQLCODE -803) by skipping
    7. Final commit and statistics display (3000-TERMINATE)
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        commit_threshold: int = 1000,
        max_errors: int = 100,
    ) -> None:
        self._db = db_session
        self._commit_threshold = commit_threshold
        self._max_errors = max_errors
        self._stats = LoadStatistics()
        self._return_status = ReturnStatus(program_id="HISTLD00")
        logger.info(
            "HistoryLoader initialized (commit_threshold=%d, max_errors=%d)",
            commit_threshold,
            max_errors,
        )

    def load_transactions(
        self, transactions: List[Dict]
    ) -> Tuple[LoadStatistics, int]:
        """
        Load a batch of transactions into the history table.

        Returns (statistics, return_code).
        Mirrors the main processing loop: read -> load -> check commit.
        Stops if error count exceeds max_errors (WS-ERROR-COUNT > 100).
        """
        self._stats = LoadStatistics(start_time=datetime.now())
        commit_counter = 0

        for txn in transactions:
            # Check error threshold (mirrors: OR WS-ERROR-COUNT > 100)
            if self._stats.error_count > self._max_errors:
                logger.error(
                    "Error threshold exceeded (%d > %d), stopping",
                    self._stats.error_count,
                    self._max_errors,
                )
                break

            self._stats.records_read += 1

            # Load to history (mirrors 2200-LOAD-TO-DB2)
            success = self._load_record(txn)
            if success:
                self._stats.records_written += 1

            # Check commit threshold (mirrors 2300-CHECK-COMMIT)
            commit_counter += 1
            if commit_counter >= self._commit_threshold:
                self._commit()
                commit_counter = 0

        # Final commit (mirrors 3100-FINAL-COMMIT)
        self._commit()
        self._stats.end_time = datetime.now()

        # Determine return code (mirrors: MOVE WS-ERROR-COUNT TO RETURN-CODE)
        if self._stats.error_count == 0:
            rc = ReturnCode.SUCCESS
        elif self._stats.error_count <= self._max_errors:
            rc = ReturnCode.WARNING
        else:
            rc = ReturnCode.ERROR

        self._return_status.set_code(
            rc,
            f"History load: read={self._stats.records_read} "
            f"written={self._stats.records_written} "
            f"errors={self._stats.error_count} "
            f"duplicates={self._stats.duplicate_count}",
        )

        # Display stats (mirrors 3400-DISPLAY-STATS)
        logger.info("HISTLD00 Processing Statistics:")
        logger.info("  Records Read:    %d", self._stats.records_read)
        logger.info("  Records Written: %d", self._stats.records_written)
        logger.info("  Errors:          %d", self._stats.error_count)
        logger.info("  Duplicates:      %d", self._stats.duplicate_count)

        return self._stats, rc

    def get_statistics(self) -> LoadStatistics:
        """Return current load statistics."""
        return self._stats

    def get_return_status(self) -> ReturnStatus:
        """Return the current return status."""
        return self._return_status

    def _load_record(self, txn: Dict) -> bool:
        """
        Load a single transaction into the history table.

        Mirrors HISTLD00.cbl 2200-LOAD-TO-DB2 which:
        1. Initializes POSHIST-RECORD
        2. Maps TH-* fields to PH-* fields
        3. Executes INSERT INTO POSHIST
        4. Handles SQLCODE 0 (success), -803 (duplicate, skip), other (error)
        """
        try:
            portfolio_id = str(txn.get("portfolio_id", ""))
            now = datetime.now()

            # Build the history record (maps TH-* to PH-* fields)
            history_data = {
                "portfolio_id": portfolio_id,
                "date": now.strftime("%Y%m%d"),
                "time": now.strftime("%H%M%S%f")[:8],
                "seq_no": str(txn.get("sequence_no", "0001"))[-4:].zfill(4),
                "record_type": "TR",  # Transaction history record
                "action_code": "A",   # Add action
                "before_image": None,
                "after_image": json.dumps(txn, cls=DecimalEncoder),
                "reason_code": "BATC",
                "process_date": now,
                "process_user": "BATCH",
            }

            if self._db:
                try:
                    from models.history import History

                    # Check for duplicate (mirrors SQLCODE -803 handling)
                    existing = (
                        self._db.query(History)
                        .filter(
                            History.portfolio_id == history_data["portfolio_id"],
                            History.date == history_data["date"],
                            History.time == history_data["time"],
                            History.seq_no == history_data["seq_no"],
                        )
                        .first()
                    )

                    if existing:
                        # Duplicate - skip (mirrors: IF SQLCODE = -803 CONTINUE)
                        self._stats.duplicate_count += 1
                        logger.debug("Duplicate history record skipped: %s", history_data["seq_no"])
                        return False

                    record = History(**history_data)
                    self._db.add(record)
                    return True

                except Exception as e:
                    self._stats.error_count += 1
                    logger.error("DB error loading history record: %s", e)
                    return False
            else:
                # No DB session - log the record for testing
                logger.debug("History record (no DB): %s", history_data["portfolio_id"])
                return True

        except Exception as e:
            self._stats.error_count += 1
            logger.error("Error loading history record: %s", e)
            return False

    def _commit(self) -> None:
        """
        Commit the current batch of records.

        Mirrors HISTLD00.cbl 2300-CHECK-COMMIT / 3100-FINAL-COMMIT
        which executes COMMIT WORK and updates the checkpoint.
        """
        if self._db:
            try:
                self._db.commit()
                self._stats.commit_count += 1
                logger.debug(
                    "Committed batch: records_written=%d",
                    self._stats.records_written,
                )
            except Exception as e:
                logger.error("Commit failed, rolling back: %s", e)
                self._db.rollback()
                self._stats.error_count += 1
