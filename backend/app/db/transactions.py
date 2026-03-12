"""
Database transaction (commit/rollback) helpers.

Translated from COBOL program: src/programs/common/DB2CMT.cbl

The original COBOL program:
  - DB2 Commit Controller with functions: INIT, CMIT, RBAK, SAVE, REST, STAT
  - Tracks commit/rollback/savepoint counts
  - Supports frequency-based commits (LS-COMMIT-FREQ)
  - Supports savepoints with RETAIN CURSORS
  - Force commit option (LS-FORCE-FLAG = 'Y')

Python equivalent wraps SQLAlchemy session commit/rollback/savepoint
operations with the same semantics and statistics tracking.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger("portfolio.db.transactions")


class TransactionManager:
    """Database transaction commit/rollback controller.

    Translated from COBOL program DB2CMT.cbl.

    The COBOL program flow:
      0000-MAIN dispatches to:
        1000-INITIALIZE (FUNC-INIT) -> reset stats
        2000-COMMIT     (FUNC-CMIT) -> conditional commit based on frequency
        3000-ROLLBACK   (FUNC-RBACK) -> ROLLBACK WORK
        4000-SAVEPOINT  (FUNC-SAVE) -> SAVEPOINT with RETAIN CURSORS
        5000-RESTORE    (FUNC-REST) -> ROLLBACK TO SAVEPOINT
        6000-STATISTICS (FUNC-STAT) -> display stats

    Usage:
        txn = TransactionManager(session, commit_freq=1000)
        txn.initialize()
        # ... process records ...
        txn.commit(records_processed=count)
        txn.display_statistics()
    """

    def __init__(self, session: Session, commit_freq: int = 1000) -> None:
        self._session = session
        self._commit_freq = commit_freq

        # WS-COMMIT-STATS equivalents
        self._commit_count: int = 0
        self._rollback_count: int = 0
        self._savepoint_count: int = 0

    def initialize(self) -> int:
        """Initialize commit controller (mirrors 1000-INITIALIZE).

        Returns:
            0 on success.
        """
        self._commit_count = 0
        self._rollback_count = 0
        self._savepoint_count = 0
        return 0

    def commit(self, records_processed: int = 0, force: bool = False) -> int:
        """Commit transaction if threshold reached or forced (mirrors 2000-COMMIT).

        Args:
            records_processed: Number of records processed since last commit.
            force: If True, commit regardless of frequency (LS-FORCE-FLAG = 'Y').

        Returns:
            0 on success, 8 on failure.
        """
        if records_processed >= self._commit_freq or force:
            return self._issue_commit()
        return 0

    def _issue_commit(self) -> int:
        """Issue the actual commit (mirrors 2100-ISSUE-COMMIT).

        Returns:
            0 on success, 8 on failure.
        """
        try:
            self._session.commit()
            self._commit_count += 1
            return 0
        except Exception as exc:
            logger.error("Commit failed: %s", exc)
            return 8

    def rollback(self) -> int:
        """Rollback transaction (mirrors 3000-ROLLBACK).

        Returns:
            0 on success, 8 on failure.
        """
        try:
            self._session.rollback()
            self._rollback_count += 1
            return 0
        except Exception as exc:
            logger.error("Rollback failed: %s", exc)
            return 8

    def savepoint(self, name: str) -> int:
        """Create a savepoint (mirrors 4000-SAVEPOINT).

        Args:
            name: Savepoint name (maps to WS-SAVEPOINT-ID).

        Returns:
            0 on success, 8 on failure.
        """
        try:
            self._session.begin_nested()
            self._savepoint_count += 1
            logger.debug("Savepoint '%s' created.", name)
            return 0
        except Exception as exc:
            logger.error("Savepoint creation failed: %s", exc)
            return 8

    def restore(self, name: str) -> int:
        """Rollback to savepoint (mirrors 5000-RESTORE).

        Args:
            name: Savepoint name to restore to.

        Returns:
            0 on success, 8 on failure.
        """
        try:
            self._session.rollback()
            self._rollback_count += 1
            logger.debug("Rolled back to savepoint '%s'.", name)
            return 0
        except Exception as exc:
            logger.error("Savepoint restore failed: %s", exc)
            return 8

    def display_statistics(self) -> dict[str, int]:
        """Display commit controller statistics (mirrors 6000-STATISTICS).

        Returns:
            Dictionary of statistics.
        """
        stats = {
            "commits": self._commit_count,
            "rollbacks": self._rollback_count,
            "savepoints": self._savepoint_count,
        }
        logger.info(
            "DB2 Commit Controller Statistics: Commits=%d, Rollbacks=%d, Savepoints=%d",
            self._commit_count,
            self._rollback_count,
            self._savepoint_count,
        )
        return stats

    @property
    def commit_count(self) -> int:
        return self._commit_count

    @property
    def rollback_count(self) -> int:
        return self._rollback_count

    @property
    def savepoint_count(self) -> int:
        return self._savepoint_count
