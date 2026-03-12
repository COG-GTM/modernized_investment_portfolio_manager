"""
Database statistics tracking utility.

Translated from COBOL program: src/programs/common/DB2STAT.cbl

The original COBOL program:
  - DB2 Statistics Collector with functions: INIT, UPDT, TERM, DISP
  - Tracks rows read/inserted/updated/deleted, commits, rollbacks
  - Calculates CPU and elapsed time
  - Stores stats in a temporary DB2 table (SESSION.DBSTATS)

Python equivalent uses an in-memory stats structure with timing support.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

logger = logging.getLogger("portfolio.db.stats")


@dataclass
class DBStats:
    """Database operation statistics.

    Mirrors WS-STATS-RECORD from DB2STAT.cbl.
    """

    program_id: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    rows_read: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_deleted: int = 0
    commits: int = 0
    rollbacks: int = 0
    cpu_time: Decimal = Decimal("0.00")
    elapsed_time: Decimal = Decimal("0.00")


class DBStatsCollector:
    """Database statistics collector.

    Translated from COBOL program DB2STAT.cbl.

    The COBOL program flow:
      0000-MAIN dispatches to:
        1000-INITIALIZE  (FUNC-INIT) -> create temp table, insert initial row
        2000-UPDATE-STATS (FUNC-UPDT) -> update stats in temp table
        3000-TERMINATE   (FUNC-TERM) -> calculate times, finalize stats
        4000-DISPLAY-STATS (FUNC-DISP) -> display formatted statistics

    Usage:
        stats = DBStatsCollector(program_id="TRNVAL00")
        stats.initialize()
        # ... processing ...
        stats.update(rows_read=100, rows_inserted=50, commits=5)
        stats.terminate()
        stats.display()
    """

    def __init__(self, program_id: str = "") -> None:
        self._stats = DBStats(program_id=program_id)
        self._start_monotonic: float = 0.0
        self._logger = logging.getLogger(
            f"portfolio.db.stats.{program_id}" if program_id else "portfolio.db.stats"
        )

    def initialize(self) -> int:
        """Initialize statistics collection (mirrors 1000-INITIALIZE).

        Returns:
            0 on success, 12 on failure.
        """
        try:
            self._stats = DBStats(program_id=self._stats.program_id)
            self._stats.start_time = datetime.now(timezone.utc)
            self._start_monotonic = time.monotonic()

            self._logger.info("Statistics collection initialized for %s", self._stats.program_id)
            return 0
        except Exception as exc:
            self._logger.error("Error initializing stats: %s", exc)
            return 12

    def update(
        self,
        rows_read: int = 0,
        rows_inserted: int = 0,
        rows_updated: int = 0,
        rows_deleted: int = 0,
        commits: int = 0,
        rollbacks: int = 0,
    ) -> int:
        """Update statistics (mirrors 2000-UPDATE-STATS).

        Args:
            rows_read: Total rows read.
            rows_inserted: Total rows inserted.
            rows_updated: Total rows updated.
            rows_deleted: Total rows deleted.
            commits: Total commits.
            rollbacks: Total rollbacks.

        Returns:
            0 on success, 12 on failure.
        """
        try:
            self._stats.rows_read = rows_read
            self._stats.rows_inserted = rows_inserted
            self._stats.rows_updated = rows_updated
            self._stats.rows_deleted = rows_deleted
            self._stats.commits = commits
            self._stats.rollbacks = rollbacks
            return 0
        except Exception as exc:
            self._logger.error("Error updating stats: %s", exc)
            return 12

    def terminate(self) -> int:
        """Terminate statistics collection and calculate times (mirrors 3000-TERMINATE).

        Returns:
            0 on success, 12 on failure.
        """
        try:
            self._stats.end_time = datetime.now(timezone.utc)
            elapsed = time.monotonic() - self._start_monotonic
            self._stats.elapsed_time = Decimal(str(round(elapsed, 2)))
            # CPU time approximation (mirrors: MULTIPLY 0.65 BY WS-CPU-TIME)
            self._stats.cpu_time = Decimal(str(round(elapsed * 0.65, 2)))

            self.display()
            return 0
        except Exception as exc:
            self._logger.error("Error finalizing stats: %s", exc)
            return 12

    def display(self) -> dict[str, object]:
        """Display statistics (mirrors 4000-DISPLAY-STATS).

        Returns:
            Dictionary of statistics values.
        """
        stats_dict = {
            "program_id": self._stats.program_id,
            "start_time": self._stats.start_time.isoformat() if self._stats.start_time else None,
            "end_time": self._stats.end_time.isoformat() if self._stats.end_time else None,
            "rows_read": self._stats.rows_read,
            "rows_inserted": self._stats.rows_inserted,
            "rows_updated": self._stats.rows_updated,
            "rows_deleted": self._stats.rows_deleted,
            "commits": self._stats.commits,
            "rollbacks": self._stats.rollbacks,
            "cpu_time_seconds": float(self._stats.cpu_time),
            "elapsed_time_seconds": float(self._stats.elapsed_time),
        }

        self._logger.info("DB2 Statistics for %s:", self._stats.program_id)
        self._logger.info("  Records Read:     %d", self._stats.rows_read)
        self._logger.info("  Records Inserted: %d", self._stats.rows_inserted)
        self._logger.info("  Records Updated:  %d", self._stats.rows_updated)
        self._logger.info("  Records Deleted:  %d", self._stats.rows_deleted)
        self._logger.info("  Commits:          %d", self._stats.commits)
        self._logger.info("  Rollbacks:        %d", self._stats.rollbacks)
        self._logger.info("  CPU Time:         %.2f seconds", self._stats.cpu_time)
        self._logger.info("  Elapsed Time:     %.2f seconds", self._stats.elapsed_time)

        return stats_dict

    @property
    def stats(self) -> DBStats:
        """Access the current statistics."""
        return self._stats
