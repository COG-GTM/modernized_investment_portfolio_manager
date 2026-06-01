"""
Batch Pipeline Runner.

Orchestrates the batch processing pipeline:
  TRNVAL00 → POSUPDT → HISTLD00 → RPTPOS00 → RPTAUD00 → RPTSTA00

Replaces the JCL job control (RPTPOS.jcl, RPTAUD.jcl, RPTSTA.jcl) with
Python orchestration. Enforces RC ≤ 4 gating between steps, implements
checkpoint/restart, and logs each step's status and timing.

Usage:
    python -m app.batch.pipeline                 # Full run
    python -m app.batch.pipeline --resume        # Resume from checkpoint
    python -m app.batch.pipeline --step TRNVAL00 # Run single step
"""

import argparse
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Callable, Dict, List, Optional

from .checkpoint import CheckpointData, CheckpointManager, CheckpointStatus
from .process_sequencer import ProcessSequencer, DEFAULT_PIPELINE_SEQUENCE
from .return_codes import ProcessStatus, ReturnCode, can_continue_pipeline

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Result of running a single pipeline step."""

    step_name: str
    return_code: int = 0
    message: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    elapsed_seconds: Decimal = Decimal("0")
    records_processed: int = 0


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""

    overall_return_code: int = 0
    steps: List[StepResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    resumed: bool = False
    message: str = ""


class BatchPipeline:
    """
    Orchestrates the end-of-day batch processing pipeline.

    Replaces JCL orchestration with Python. The pipeline:
    1. Validates transactions (TRNVAL00)
    2. Updates positions (POSUPDT)
    3. Loads history (HISTLD00)
    4. Generates position reports (RPTPOS00)
    5. Generates audit reports (RPTAUD00)
    6. Generates statistics reports (RPTSTA00)

    Each step must complete with RC ≤ 4 for the next step to proceed.
    Checkpoint/restart allows resuming from the last successful step.
    """

    def __init__(self, db_session: Optional[object] = None) -> None:
        self._db = db_session
        self._sequencer = ProcessSequencer()
        self._checkpoint_mgr: Optional[CheckpointManager] = None
        self._program_id = "PIPELINE"
        self._run_date = datetime.now().strftime("%Y%m%d")
        self._step_handlers: Dict[str, Callable[[], StepResult]] = {}
        self._step_timings: List[Dict] = []
        self._transactions: List[Dict] = []
        self._valid_transactions: List[Dict] = []

        if db_session is not None:
            self._checkpoint_mgr = CheckpointManager(db_session=db_session)

        self._register_steps()
        logger.info("BatchPipeline initialized")

    def run_full(self) -> PipelineResult:
        """
        Run the complete pipeline from start to finish.

        Mirrors the JCL EXEC PGM= sequence with COND=(4,LT) gating.
        """
        result = PipelineResult(start_time=datetime.now())

        logger.info("=" * 60)
        logger.info("BATCH PIPELINE - FULL RUN")
        logger.info("Started: %s", result.start_time)
        logger.info("=" * 60)

        # Initialize the process sequencer
        self._sequencer.initialize()

        # Initialize checkpoint
        if self._checkpoint_mgr:
            self._checkpoint_mgr.initialize(self._program_id, self._run_date)

        # Run each step in sequence
        while True:
            process_id = self._sequencer.get_next_process()
            if process_id is None:
                break

            step_result = self._run_step(process_id)
            result.steps.append(step_result)

            # Update sequencer status
            if step_result.return_code <= ReturnCode.WARNING:
                self._sequencer.update_process_status(
                    process_id, ProcessStatus.DONE, step_result.return_code
                )
            else:
                self._sequencer.update_process_status(
                    process_id, ProcessStatus.ERROR, step_result.return_code
                )

            # RC gating: stop if RC > 4
            if not can_continue_pipeline(step_result.return_code):
                logger.error(
                    "Pipeline halted at %s: RC=%d exceeds threshold",
                    process_id,
                    step_result.return_code,
                )
                result.overall_return_code = step_result.return_code
                result.message = f"Pipeline halted at {process_id} with RC={step_result.return_code}"
                break

        # If we completed all steps normally
        if result.overall_return_code == 0:
            # Find the highest RC across all steps
            if result.steps:
                result.overall_return_code = max(s.return_code for s in result.steps)
            result.message = "Pipeline completed successfully"

        result.end_time = datetime.now()

        # Update checkpoint based on outcome
        if self._checkpoint_mgr:
            if result.overall_return_code <= ReturnCode.WARNING:
                self._checkpoint_mgr.complete(self._program_id, self._run_date)
            else:
                self._checkpoint_mgr.fail(self._program_id, self._run_date)

        # Final summary
        completion = self._sequencer.check_completion()
        logger.info("=" * 60)
        logger.info("BATCH PIPELINE - COMPLETE")
        logger.info("Overall RC: %d", result.overall_return_code)
        logger.info("Steps: %d done, %d errors", completion["done"], completion["error"])
        logger.info("Ended: %s", result.end_time)
        logger.info("=" * 60)

        return result

    def run_resume(self) -> PipelineResult:
        """
        Resume pipeline from last checkpoint.

        Reads the checkpoint to determine the last completed step,
        then continues from the next step.
        """
        result = PipelineResult(start_time=datetime.now(), resumed=True)

        logger.info("=" * 60)
        logger.info("BATCH PIPELINE - RESUME FROM CHECKPOINT")
        logger.info("=" * 60)

        # Initialize and check for existing checkpoint
        checkpoint_data = None
        if self._checkpoint_mgr:
            checkpoint_data = self._checkpoint_mgr.initialize(self._program_id, self._run_date)

        if checkpoint_data and checkpoint_data.status in (CheckpointStatus.ACTIVE, CheckpointStatus.RESTARTED):
            last_step = checkpoint_data.last_key
            if not last_step:
                logger.info("Checkpoint has no completed steps, starting from beginning")
                return self.run_full()
            logger.info("Resuming from after step: %s", last_step)
        else:
            logger.info("No active checkpoint found, starting from beginning")
            return self.run_full()

        # Initialize sequencer
        self._sequencer.initialize()

        # Skip past completed steps
        found_resume_point = False
        while True:
            process_id = self._sequencer.get_next_process()
            if process_id is None:
                break

            if not found_resume_point:
                if process_id == last_step:
                    # Mark this step as already done
                    self._sequencer.update_process_status(
                        process_id, ProcessStatus.DONE, 0
                    )
                    found_resume_point = True
                    logger.info("Skipping completed step: %s", process_id)
                    continue
                else:
                    # Mark prior steps as done
                    self._sequencer.update_process_status(
                        process_id, ProcessStatus.DONE, 0
                    )
                    logger.info("Skipping completed step: %s", process_id)
                    continue

            # Run remaining steps
            step_result = self._run_step(process_id)
            result.steps.append(step_result)

            if step_result.return_code <= ReturnCode.WARNING:
                self._sequencer.update_process_status(
                    process_id, ProcessStatus.DONE, step_result.return_code
                )
            else:
                self._sequencer.update_process_status(
                    process_id, ProcessStatus.ERROR, step_result.return_code
                )

            if not can_continue_pipeline(step_result.return_code):
                result.overall_return_code = step_result.return_code
                result.message = f"Pipeline halted at {process_id} with RC={step_result.return_code}"
                break

        # Check if resume point was found in the pipeline sequence
        if not found_resume_point:
            logger.error("Resume point '%s' not found in pipeline sequence", last_step)
            result.overall_return_code = ReturnCode.ERROR
            result.message = f"Resume point '{last_step}' not found in pipeline sequence"

        if result.overall_return_code == 0:
            if result.steps:
                result.overall_return_code = max(s.return_code for s in result.steps)
            result.message = "Pipeline resumed and completed successfully"

        result.end_time = datetime.now()
        if self._checkpoint_mgr:
            if result.overall_return_code <= ReturnCode.WARNING:
                self._checkpoint_mgr.complete(self._program_id, self._run_date)
            else:
                self._checkpoint_mgr.fail(self._program_id, self._run_date)

        return result

    def run_step(self, step_name: str) -> StepResult:
        """
        Run a single pipeline step by name.

        Useful for testing individual steps or re-running a failed step.
        """
        logger.info("=" * 60)
        logger.info("BATCH PIPELINE - SINGLE STEP: %s", step_name)
        logger.info("=" * 60)

        return self._run_step(step_name)

    def get_step_timings(self) -> List[Dict]:
        """Return timing data for all steps run in this session."""
        return list(self._step_timings)

    def _run_step(self, step_name: str) -> StepResult:
        """
        Execute a single pipeline step with timing and error handling.

        Mirrors JCL EXEC PGM=<program> with timing and RC capture.
        """
        result = StepResult(
            step_name=step_name,
            start_time=datetime.now(),
        )

        logger.info("-" * 40)
        logger.info("Step: %s - Starting at %s", step_name, result.start_time)

        handler = self._step_handlers.get(step_name)
        if not handler:
            logger.error("No handler registered for step: %s", step_name)
            result.return_code = ReturnCode.ERROR
            result.message = f"Unknown step: {step_name}"
            result.end_time = datetime.now()
            return result

        try:
            handler_result = handler()
            result.return_code = handler_result.return_code
            result.message = handler_result.message
            result.records_processed = handler_result.records_processed
        except Exception as e:
            logger.error("Step %s failed with exception: %s", step_name, e)
            result.return_code = ReturnCode.SEVERE
            result.message = str(e)

        result.end_time = datetime.now()
        elapsed = (result.end_time - result.start_time).total_seconds()
        result.elapsed_seconds = Decimal(str(elapsed))

        # Take checkpoint after successful step
        if result.return_code <= ReturnCode.WARNING and self._checkpoint_mgr:
            self._checkpoint_mgr.take_checkpoint(
                program_id=self._program_id,
                run_date=self._run_date,
                last_key=step_name,
            )
            self._checkpoint_mgr.commit_checkpoint(
                program_id=self._program_id,
                run_date=self._run_date,
            )

        # Record timing data for stats report
        self._step_timings.append({
            "step_name": step_name,
            "start_time": result.start_time.isoformat() if result.start_time else "",
            "end_time": result.end_time.isoformat() if result.end_time else "",
            "elapsed_seconds": float(result.elapsed_seconds),
            "records_processed": result.records_processed,
        })

        logger.info(
            "Step: %s - RC=%d elapsed=%.2fs records=%d",
            step_name,
            result.return_code,
            elapsed,
            result.records_processed,
        )
        logger.info("-" * 40)

        return result

    def _register_steps(self) -> None:
        """Register handler functions for each pipeline step."""
        self._step_handlers = {
            "TRNVAL00": self._step_validate_transactions,
            "POSUPD00": self._step_update_positions,
            "HISTLD00": self._step_load_history,
            "RPTPOS00": self._step_position_report,
            "RPTAUD00": self._step_audit_report,
            "RPTSTA00": self._step_stats_report,
        }

    def _step_validate_transactions(self) -> StepResult:
        """Step 1: Validate incoming transactions."""
        from .transaction_validator import TransactionValidator

        result = StepResult(step_name="TRNVAL00")
        validator = TransactionValidator(db_session=self._db)

        # In a real implementation, transactions would come from a file or queue
        # For now, use any transactions passed to the pipeline
        valid, invalid, rc = validator.validate_batch(self._transactions)
        self._valid_transactions = valid

        summary = validator.get_summary()
        result.return_code = rc
        result.message = (
            f"Validated {summary.total_transactions}: "
            f"{summary.valid_count} valid, {summary.error_count} errors"
        )
        result.records_processed = summary.total_transactions
        return result

    def _step_update_positions(self) -> StepResult:
        """Step 2: Update portfolio positions."""
        from .position_updater import PositionUpdater

        result = StepResult(step_name="POSUPD00")
        updater = PositionUpdater(db_session=self._db)

        updates, rc = updater.process_transactions(self._valid_transactions)

        summary = updater.get_summary()
        result.return_code = rc
        result.message = (
            f"Position updates: {len(updates)} applied, "
            f"{summary.positions_created} created, "
            f"{summary.errors} errors"
        )
        result.records_processed = len(updates)
        return result

    def _step_load_history(self) -> StepResult:
        """Step 3: Load transactions into history."""
        from .history_loader import HistoryLoader

        result = StepResult(step_name="HISTLD00")
        loader = HistoryLoader(db_session=self._db)

        stats, rc = loader.load_transactions(self._valid_transactions)

        result.return_code = rc
        result.message = (
            f"History load: {stats.records_written} written, "
            f"{stats.error_count} errors"
        )
        result.records_processed = stats.records_written
        return result

    def _step_position_report(self) -> StepResult:
        """Step 4: Generate position report."""
        from .reports.position_report import PositionReportGenerator

        result = StepResult(step_name="RPTPOS00")
        generator = PositionReportGenerator(db_session=self._db)

        report_text, rc = generator.generate()

        result.return_code = rc
        result.message = f"Position report generated ({len(report_text)} chars)"
        result.records_processed = 1
        return result

    def _step_audit_report(self) -> StepResult:
        """Step 5: Generate audit report."""
        from .reports.audit_report import AuditReportGenerator

        result = StepResult(step_name="RPTAUD00")
        generator = AuditReportGenerator(db_session=self._db)

        report_text, rc = generator.generate()

        result.return_code = rc
        result.message = f"Audit report generated ({len(report_text)} chars)"
        result.records_processed = 1
        return result

    def _step_stats_report(self) -> StepResult:
        """Step 6: Generate statistics report."""
        from .reports.stats_report import StatsReportGenerator

        result = StepResult(step_name="RPTSTA00")
        generator = StatsReportGenerator(db_session=self._db)

        report_text, rc = generator.generate(step_timings=self._step_timings)

        result.return_code = rc
        result.message = f"Stats report generated ({len(report_text)} chars)"
        result.records_processed = 1
        return result


def main() -> int:
    """CLI entry point for the batch pipeline."""
    parser = argparse.ArgumentParser(
        description="Investment Portfolio Batch Pipeline",
        prog="python -m app.batch.pipeline",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--step",
        type=str,
        help="Run a single step (e.g., TRNVAL00, POSUPD00, HISTLD00)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    pipeline = BatchPipeline()

    if args.step:
        result = pipeline.run_step(args.step)
        return result.return_code
    elif args.resume:
        pipeline_result = pipeline.run_resume()
        return pipeline_result.overall_return_code
    else:
        pipeline_result = pipeline.run_full()
        return pipeline_result.overall_return_code


if __name__ == "__main__":
    sys.exit(main())
