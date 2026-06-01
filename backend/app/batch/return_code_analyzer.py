"""
Return Code Analysis Utility.

Migrated from: RTNANA00.cbl
Analyzes return codes across the system, generates trend analysis,
identifies error patterns, and produces analysis reports.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from .return_codes import ReturnCode, StatusCode, classify_return_code

logger = logging.getLogger(__name__)


@dataclass
class ProgramAnalysis:
    """Analysis results for a single program's return codes."""

    program_id: str = ""
    total_executions: int = 0
    success_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    severe_count: int = 0

    @property
    def success_rate(self) -> Decimal:
        """Calculate success rate as a percentage."""
        if self.total_executions == 0:
            return Decimal("0.00")
        return Decimal(str(self.success_count)) / Decimal(str(self.total_executions)) * Decimal("100")

    @property
    def error_rate(self) -> Decimal:
        """Calculate error rate as a percentage."""
        if self.total_executions == 0:
            return Decimal("0.00")
        return (
            Decimal(str(self.error_count + self.severe_count))
            / Decimal(str(self.total_executions))
            * Decimal("100")
        )


@dataclass
class ReturnCodeEntry:
    """A single return code log entry for analysis."""

    timestamp: datetime
    program_id: str
    return_code: int
    highest_code: int
    status: str
    message: str = ""


@dataclass
class AnalysisSummary:
    """
    Overall analysis summary across all programs.

    Mirrors RTNANA00.cbl WS-ANALYSIS-AREA accumulators.
    """

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_entries: int = 0
    success_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    severe_count: int = 0
    program_analyses: Dict[str, ProgramAnalysis] = field(default_factory=dict)


class ReturnCodeAnalyzer:
    """
    Analyzes return codes across the batch system.

    Migrated from RTNANA00.cbl. The COBOL program queries a DB2 RTNCODES
    table via cursor and aggregates counts by program. This Python version
    operates on in-memory log entries and/or database queries.
    """

    def __init__(self) -> None:
        self._entries: List[ReturnCodeEntry] = []
        self._summary = AnalysisSummary()
        logger.info("ReturnCodeAnalyzer initialized")

    def add_entry(
        self,
        program_id: str,
        return_code: int,
        message: str = "",
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Record a return code entry for later analysis.

        Mirrors the INSERT INTO RTNCODES in RTNCDE00.cbl P400-LOG-RETURN-CODE.
        """
        ts = timestamp or datetime.now()
        status = classify_return_code(return_code)

        entry = ReturnCodeEntry(
            timestamp=ts,
            program_id=program_id,
            return_code=return_code,
            highest_code=return_code,
            status=status.value,
            message=message,
        )
        self._entries.append(entry)
        logger.debug(
            "Logged return code: program=%s rc=%d status=%s",
            program_id,
            return_code,
            status.value,
        )

    def analyze(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        program_id: Optional[str] = None,
    ) -> AnalysisSummary:
        """
        Analyze return code entries and produce a summary.

        Mirrors RTNANA00.cbl P200-PROCESS-ANALYSIS which opens a cursor
        on RTNCODES grouped by PROGRAM_ID and accumulates counts.
        """
        self._summary = AnalysisSummary(start_time=start_time, end_time=end_time)

        filtered = self._entries
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        if program_id:
            filtered = [e for e in filtered if e.program_id == program_id]

        for entry in filtered:
            self._summary.total_entries += 1
            status = classify_return_code(entry.return_code)

            if status == StatusCode.SUCCESS:
                self._summary.success_count += 1
            elif status == StatusCode.WARNING:
                self._summary.warning_count += 1
            elif status == StatusCode.ERROR:
                self._summary.error_count += 1
            else:
                self._summary.severe_count += 1

            # Per-program analysis (mirrors the GROUP BY PROGRAM_ID query)
            if entry.program_id not in self._summary.program_analyses:
                self._summary.program_analyses[entry.program_id] = ProgramAnalysis(
                    program_id=entry.program_id
                )

            prog = self._summary.program_analyses[entry.program_id]
            prog.total_executions += 1
            if status == StatusCode.SUCCESS:
                prog.success_count += 1
            elif status == StatusCode.WARNING:
                prog.warning_count += 1
            elif status == StatusCode.ERROR:
                prog.error_count += 1
            else:
                prog.severe_count += 1

        logger.info(
            "Analysis complete: total=%d success=%d warning=%d error=%d severe=%d",
            self._summary.total_entries,
            self._summary.success_count,
            self._summary.warning_count,
            self._summary.error_count,
            self._summary.severe_count,
        )

        return self._summary

    def generate_report(self) -> str:
        """
        Generate a text report of return code analysis.

        Mirrors RTNANA00.cbl P210-WRITE-HEADERS through P300-GENERATE-REPORT
        which writes header lines, detail lines per program, and totals.
        """
        now = datetime.now()
        lines: List[str] = []

        # Header (mirrors WS-HEADER1 through WS-DETAIL-HDR)
        lines.append("-" * 133)
        lines.append(f"{'Return Code Analysis Report':^133}")
        lines.append(
            f"Report Date: {now.strftime('%Y-%m-%d')}     Report Time: {now.strftime('%H:%M:%S')}"
        )
        lines.append("-" * 133)
        lines.append(
            f"{'Program':<10} {'Total':>10} {'Success':>10} {'Warning':>10} {'Error':>10} {'Severe':>10}"
        )
        lines.append("-" * 133)

        # Detail lines per program (mirrors P220-PROCESS-DETAIL)
        for prog_id in sorted(self._summary.program_analyses.keys()):
            prog = self._summary.program_analyses[prog_id]
            lines.append(
                f"{prog.program_id:<10} {prog.total_executions:>10,} "
                f"{prog.success_count:>10,} {prog.warning_count:>10,} "
                f"{prog.error_count:>10,} {prog.severe_count:>10,}"
            )

        # Totals line (mirrors P300-GENERATE-REPORT)
        lines.append("-" * 133)
        lines.append(
            f"{'TOTALS':<10} {self._summary.total_entries:>10,} "
            f"{self._summary.success_count:>10,} {self._summary.warning_count:>10,} "
            f"{self._summary.error_count:>10,} {self._summary.severe_count:>10,}"
        )
        lines.append("-" * 133)

        return "\n".join(lines)

    def get_summary(self) -> AnalysisSummary:
        """Return the current analysis summary."""
        return self._summary

    def clear(self) -> None:
        """Clear all recorded entries and reset the summary."""
        self._entries.clear()
        self._summary = AnalysisSummary()
        logger.info("ReturnCodeAnalyzer cleared")
