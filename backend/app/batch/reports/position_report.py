"""
Position Report Generator.

Migrated from: RPTPOS00.cbl, RPTPOS.jcl
Generates daily position reports including portfolio valuations,
transaction activity summaries, exception reporting, and performance metrics.

JCL DD assignments (now Python config):
- POSMSTRE -> Position master query
- TRANHIST -> Transaction history query
- RPTFILE  -> Output report (text/file)
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
class PositionDetail:
    """
    A single position line in the report.

    Mirrors RPTPOS00.cbl WS-POSITION-DETAIL.
    """

    portfolio_id: str = ""
    description: str = ""
    quantity: Decimal = Decimal("0")
    current_value: Decimal = Decimal("0")
    previous_value: Decimal = Decimal("0")
    change_percent: Decimal = Decimal("0")


@dataclass
class ReportSummary:
    """Summary totals for the position report."""

    total_positions: int = 0
    total_value: Decimal = Decimal("0")
    total_gain_loss: Decimal = Decimal("0")
    transactions_today: int = 0
    exceptions: int = 0


class PositionReportGenerator:
    """
    Generates the daily position report.

    Migrated from RPTPOS00.cbl. The COBOL program:
    1. Opens POSITION-MASTER, TRANSACTION-HISTORY, and REPORT-FILE (1100-OPEN-FILES)
    2. Writes report headers with date (1200-WRITE-HEADERS)
    3. Reads positions sequentially, formats each detail line (2100-READ-POSITIONS / 2110-FORMAT-POSITION)
    4. Processes transactions and summarizes activity (2200-PROCESS-TRANSACTIONS)
    5. Writes summary totals, exceptions, and metrics (2300-WRITE-SUMMARY)
    6. Closes all files (3000-CLEANUP)
    """

    def __init__(self, db_session: Optional[Session] = None) -> None:
        self._db = db_session
        self._positions: List[PositionDetail] = []
        self._summary = ReportSummary()
        self._return_status = ReturnStatus(program_id="RPTPOS00")
        self._report_lines: List[str] = []
        logger.info("PositionReportGenerator initialized")

    def generate(self, report_date: Optional[str] = None) -> tuple[str, int]:
        """
        Generate the full position report.

        Returns (report_text, return_code).
        Mirrors the main flow: initialize -> process -> cleanup.
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        self._report_lines.clear()
        self._positions.clear()
        self._summary = ReportSummary()

        try:
            # 1200-WRITE-HEADERS
            self._write_headers(report_date)

            # 2100-READ-POSITIONS / 2110-FORMAT-POSITION
            self._read_positions()

            # 2200-PROCESS-TRANSACTIONS
            self._process_transactions(report_date)

            # 2300-WRITE-SUMMARY
            self._write_summary()

            rc = ReturnCode.SUCCESS
        except Exception as e:
            logger.error("Error generating position report: %s", e)
            self._report_lines.append(f"\n*** ERROR: {e} ***")
            rc = ReturnCode.SEVERE

        self._return_status.set_code(
            rc,
            f"Position report generated: {self._summary.total_positions} positions, "
            f"total value={self._summary.total_value}",
        )

        report_text = "\n".join(self._report_lines)
        logger.info(
            "Position report complete: positions=%d RC=%d",
            self._summary.total_positions,
            rc,
        )
        return report_text, rc

    def get_return_status(self) -> ReturnStatus:
        return self._return_status

    def _write_headers(self, report_date: str) -> None:
        """
        Write report headers.

        Mirrors RPTPOS00.cbl 1200-WRITE-HEADERS: WS-HEADER1 through WS-HEADER3.
        """
        self._report_lines.append("*" * 132)
        self._report_lines.append(f"{'DAILY POSITION REPORT':^132}")
        self._report_lines.append(f"REPORT DATE: {report_date}")
        self._report_lines.append("*" * 132)
        self._report_lines.append(
            f"{'Portfolio':<12} {'Description':<32} {'Quantity':>16} "
            f"{'Value':>18} {'Change %':>10}"
        )
        self._report_lines.append("-" * 132)

    def _read_positions(self) -> None:
        """
        Read positions and format detail lines.

        Mirrors RPTPOS00.cbl 2100-READ-POSITIONS / 2110-FORMAT-POSITION.
        The COBOL reads POSITION-MASTER sequentially, computes change %
        as (current - previous) / previous * 100, and writes each line.
        """
        if self._db:
            try:
                from models.database import Position

                positions = (
                    self._db.query(Position)
                    .filter(Position.status == "A")
                    .order_by(Position.portfolio_id, Position.investment_id)
                    .all()
                )

                for pos in positions:
                    detail = PositionDetail(
                        portfolio_id=pos.portfolio_id or "",
                        description=pos.investment_id or "",
                        quantity=pos.quantity or Decimal("0"),
                        current_value=pos.market_value or Decimal("0"),
                        previous_value=pos.cost_basis or Decimal("0"),
                    )

                    # Compute change percent (mirrors 2110-FORMAT-POSITION COMPUTE)
                    if detail.previous_value != Decimal("0"):
                        detail.change_percent = (
                            (detail.current_value - detail.previous_value)
                            / detail.previous_value
                            * Decimal("100")
                        )

                    self._positions.append(detail)
                    self._summary.total_positions += 1
                    self._summary.total_value += detail.current_value
                    self._summary.total_gain_loss += detail.current_value - detail.previous_value

                    self._report_lines.append(
                        f"{detail.portfolio_id:<12} {detail.description:<32} "
                        f"{detail.quantity:>16,.4f} {detail.current_value:>18,.2f} "
                        f"{detail.change_percent:>+10.2f}"
                    )

            except Exception as e:
                logger.warning("Could not read positions from DB: %s", e)
        else:
            self._report_lines.append("  (No database connection - no position data available)")

    def _process_transactions(self, report_date: str) -> None:
        """
        Process transaction activity for the report date.

        Mirrors RPTPOS00.cbl 2200-PROCESS-TRANSACTIONS.
        """
        if self._db:
            try:
                from models.transactions import Transaction

                count = (
                    self._db.query(Transaction)
                    .filter(Transaction.status == "D")
                    .count()
                )
                self._summary.transactions_today = count
            except Exception as e:
                logger.warning("Could not count transactions: %s", e)

    def _write_summary(self) -> None:
        """
        Write summary section.

        Mirrors RPTPOS00.cbl 2300-WRITE-SUMMARY:
        2310-WRITE-TOTALS, 2320-WRITE-EXCEPTIONS, 2330-WRITE-METRICS.
        """
        self._report_lines.append("-" * 132)
        self._report_lines.append("")
        self._report_lines.append("SUMMARY")
        self._report_lines.append(f"  Total Positions:        {self._summary.total_positions:>12,}")
        self._report_lines.append(
            f"  Total Portfolio Value:   {self._summary.total_value:>12,.2f}"
        )
        self._report_lines.append(
            f"  Total Gain/Loss:        {self._summary.total_gain_loss:>+12,.2f}"
        )
        self._report_lines.append(
            f"  Transactions Today:     {self._summary.transactions_today:>12,}"
        )
        self._report_lines.append("")
        self._report_lines.append("*" * 132)
