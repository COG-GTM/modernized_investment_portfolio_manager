"""
System Statistics Report Generator.

Migrated from: RPTSTA00.cbl, RPTSTA.jcl
Generates system performance and processing statistics reports including
processing volume, error rates, timing metrics, and resource utilization.

JCL DD assignments (now Python config):
- SYSSTAT  -> System statistics query
- PRCSTAT  -> Process statistics query
- RPTFILE  -> Output report
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..return_codes import ReturnCode, ReturnStatus

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """
    Processing volume statistics.

    Mirrors RPTSTA00.cbl WS-PROCESSING-STATS.
    """

    transactions_processed: int = 0
    positions_updated: int = 0
    history_loaded: int = 0
    reports_generated: int = 0
    errors_encountered: int = 0


@dataclass
class TimingStats:
    """
    Timing metrics for batch steps.

    Mirrors RPTSTA00.cbl WS-TIMING-STATS.
    """

    step_name: str = ""
    start_time: str = ""
    end_time: str = ""
    elapsed_seconds: Decimal = Decimal("0")
    records_per_second: Decimal = Decimal("0")


@dataclass
class StatsSummary:
    """Summary of all statistics for the report."""

    processing: ProcessingStats = field(default_factory=ProcessingStats)
    timing: List[TimingStats] = field(default_factory=list)
    total_elapsed: Decimal = Decimal("0")
    overall_rate: Decimal = Decimal("0")
    error_rate: Decimal = Decimal("0")


class StatsReportGenerator:
    """
    Generates the system statistics report.

    Migrated from RPTSTA00.cbl. The COBOL program:
    1. Opens SYSTEM-STATS, PROCESS-STATS, and REPORT-FILE (1100-OPEN-FILES)
    2. Writes headers (1200-WRITE-HEADERS)
    3. Processes system statistics (2100-PROCESS-SYSTEM-STATS):
       reads stats records, aggregates counters
    4. Processes timing statistics (2200-PROCESS-TIMING-STATS):
       reads timing records, calculates rates
    5. Writes summary (2300-WRITE-SUMMARY):
       2310-WRITE-VOLUME-SUMMARY, 2320-WRITE-TIMING-SUMMARY, 2330-WRITE-RATE-SUMMARY
    6. Cleanup (3000-CLEANUP)
    """

    def __init__(self, db_session: Optional[Session] = None) -> None:
        self._db = db_session
        self._summary = StatsSummary()
        self._return_status = ReturnStatus(program_id="RPTSTA00")
        self._report_lines: List[str] = []
        logger.info("StatsReportGenerator initialized")

    def generate(
        self,
        report_date: Optional[str] = None,
        step_timings: Optional[List[Dict]] = None,
    ) -> tuple[str, int]:
        """
        Generate the full statistics report.

        Args:
            report_date: Date for the report (default: today).
            step_timings: List of dicts with step timing data from pipeline run.

        Returns (report_text, return_code).
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        self._report_lines.clear()
        self._summary = StatsSummary()

        try:
            self._write_headers(report_date)
            self._process_system_stats()
            self._process_timing_stats(step_timings or [])
            self._write_summary()
            rc = ReturnCode.SUCCESS
        except Exception as e:
            logger.error("Error generating stats report: %s", e)
            self._report_lines.append(f"\n*** ERROR: {e} ***")
            rc = ReturnCode.SEVERE

        self._return_status.set_code(
            rc,
            f"Stats report generated: "
            f"{self._summary.processing.transactions_processed} transactions processed",
        )

        report_text = "\n".join(self._report_lines)
        logger.info("Stats report complete: RC=%d", rc)
        return report_text, rc

    def get_return_status(self) -> ReturnStatus:
        return self._return_status

    def _write_headers(self, report_date: str) -> None:
        """Mirrors RPTSTA00.cbl 1200-WRITE-HEADERS."""
        self._report_lines.append("*" * 132)
        self._report_lines.append(f"{'SYSTEM STATISTICS REPORT':^132}")
        self._report_lines.append(f"REPORT DATE: {report_date}")
        self._report_lines.append("*" * 132)

    def _process_system_stats(self) -> None:
        """
        Process system statistics.

        Mirrors RPTSTA00.cbl 2100-PROCESS-SYSTEM-STATS:
        reads system stats records and aggregates.
        """
        self._report_lines.append("")
        self._report_lines.append("PROCESSING VOLUME")
        self._report_lines.append("-" * 132)

        if self._db:
            try:
                from models.transactions import Transaction
                from models.database import Position
                from models.history import History

                txn_count = self._db.query(Transaction).count()
                pos_count = self._db.query(Position).filter(Position.status == "A").count()
                hist_count = self._db.query(History).count()

                self._summary.processing.transactions_processed = txn_count
                self._summary.processing.positions_updated = pos_count
                self._summary.processing.history_loaded = hist_count
            except Exception as e:
                logger.warning("Could not query system stats: %s", e)

        self._report_lines.append(
            f"  Transactions Processed: {self._summary.processing.transactions_processed:>12,}"
        )
        self._report_lines.append(
            f"  Positions Active:       {self._summary.processing.positions_updated:>12,}"
        )
        self._report_lines.append(
            f"  History Records:        {self._summary.processing.history_loaded:>12,}"
        )
        self._report_lines.append(
            f"  Reports Generated:      {self._summary.processing.reports_generated:>12,}"
        )
        self._report_lines.append(
            f"  Errors Encountered:     {self._summary.processing.errors_encountered:>12,}"
        )

    def _process_timing_stats(self, step_timings: List[Dict]) -> None:
        """
        Process timing statistics from pipeline run data.

        Mirrors RPTSTA00.cbl 2200-PROCESS-TIMING-STATS.
        """
        self._report_lines.append("")
        self._report_lines.append("TIMING METRICS")
        self._report_lines.append("-" * 132)
        self._report_lines.append(
            f"{'Step':<20} {'Start':>20} {'End':>20} {'Elapsed (s)':>14} {'Rec/Sec':>12}"
        )
        self._report_lines.append("-" * 132)

        total_elapsed = Decimal("0")

        for timing in step_timings:
            elapsed = Decimal(str(timing.get("elapsed_seconds", 0)))
            records = timing.get("records_processed", 0)
            rate = Decimal(str(records)) / elapsed if elapsed > 0 else Decimal("0")

            stats = TimingStats(
                step_name=timing.get("step_name", ""),
                start_time=timing.get("start_time", ""),
                end_time=timing.get("end_time", ""),
                elapsed_seconds=elapsed,
                records_per_second=rate,
            )
            self._summary.timing.append(stats)
            total_elapsed += elapsed

            self._report_lines.append(
                f"{stats.step_name:<20} {stats.start_time:>20} {stats.end_time:>20} "
                f"{stats.elapsed_seconds:>14.2f} {stats.records_per_second:>12.1f}"
            )

        self._summary.total_elapsed = total_elapsed

        if not step_timings:
            self._report_lines.append("  No timing data available")

    def _write_summary(self) -> None:
        """
        Write summary section.

        Mirrors RPTSTA00.cbl 2300-WRITE-SUMMARY with sub-sections:
        2310-WRITE-VOLUME-SUMMARY, 2320-WRITE-TIMING-SUMMARY, 2330-WRITE-RATE-SUMMARY.
        """
        # Calculate error rate
        total = self._summary.processing.transactions_processed
        errors = self._summary.processing.errors_encountered
        if total > 0:
            self._summary.error_rate = Decimal(str(errors)) / Decimal(str(total)) * Decimal("100")

        # Calculate overall rate
        if self._summary.total_elapsed > 0 and total > 0:
            self._summary.overall_rate = (
                Decimal(str(total)) / self._summary.total_elapsed
            )

        self._report_lines.append("")
        self._report_lines.append("=" * 132)
        self._report_lines.append("SUMMARY")
        self._report_lines.append(
            f"  Total Elapsed Time:     {self._summary.total_elapsed:>12.2f} seconds"
        )
        self._report_lines.append(
            f"  Overall Processing Rate: {self._summary.overall_rate:>11.1f} rec/sec"
        )
        self._report_lines.append(
            f"  Error Rate:              {self._summary.error_rate:>11.2f}%"
        )
        self._report_lines.append("")
        self._report_lines.append("*" * 132)
