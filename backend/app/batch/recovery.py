"""
Recovery Processing for Failed Batch Steps.

Migrated from: RCVPRC00.cbl
Handles recovery of failed batch processes by determining the appropriate
action (restart, bypass, or terminate) based on process definitions
and failure history.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .return_codes import ProcessStatus, ReturnCode, ReturnStatus

logger = logging.getLogger(__name__)


class RecoveryMode(str, Enum):
    """Recovery mode from RCVPRC00.cbl WS-RECOVERY-MODE."""

    PROCESS = "P"   # Recover a single process
    SEQUENCE = "S"  # Recover all processes in a sequence
    ALL = "A"       # Recover all failed processes


class RecoveryAction(str, Enum):
    """Recovery action from RCVPRC00.cbl WS-RECOVERY-ACTION."""

    RESTART = "R"    # Restart the failed process
    BYPASS = "B"     # Skip the process and mark as done with warning
    TERMINATE = "T"  # Mark as permanently failed


@dataclass
class RecoveryRequest:
    """
    A request to recover a failed process.

    Mirrors RCVPRC00.cbl LS-RECOVERY-REQUEST linkage structure.
    """

    process_date: str
    process_id: str = ""
    recovery_type: str = "P"
    recovery_parm: str = ""


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""

    process_id: str
    action_taken: RecoveryAction
    return_code: int
    message: str
    timestamp: str = ""


class RecoveryProcessor:
    """
    Handles recovery of failed batch steps.

    Migrated from RCVPRC00.cbl. The COBOL program dispatches on function
    codes (INIT, RECV, TERM), validates requests, determines the recovery
    action based on process definition, and executes recovery by updating
    the batch control records.
    """

    def __init__(self, max_restarts: int = 3) -> None:
        self._max_restarts = max_restarts
        self._results: list[RecoveryResult] = []
        self._return_status = ReturnStatus(program_id="RCVPRC00")
        logger.info("RecoveryProcessor initialized (max_restarts=%d)", max_restarts)

    def recover_process(
        self,
        process_id: str,
        process_date: str,
        current_status: ProcessStatus,
        restart_count: int = 0,
        restartable: bool = True,
    ) -> RecoveryResult:
        """
        Recover a single failed process.

        Mirrors RCVPRC00.cbl 2100-RECOVER-PROCESS which:
        1. Reads the batch control record (2100)
        2. Determines the recovery action (2110-DETERMINE-ACTION)
        3. Executes the chosen recovery (2120-EXECUTE-RECOVERY)
        """
        action = self._determine_action(restartable, restart_count)

        if action == RecoveryAction.RESTART:
            result = self._restart_process(process_id, restart_count)
        elif action == RecoveryAction.BYPASS:
            result = self._bypass_process(process_id)
        else:
            result = self._terminate_process(process_id)

        result.timestamp = datetime.now().isoformat()
        self._results.append(result)

        logger.info(
            "Recovery for %s: action=%s rc=%d msg=%s",
            process_id,
            action.value,
            result.return_code,
            result.message,
        )
        return result

    def recover_sequence(
        self,
        process_date: str,
        failed_processes: list[dict],
    ) -> list[RecoveryResult]:
        """
        Recover all failed processes in a sequence for a given date.

        Mirrors RCVPRC00.cbl 2200-RECOVER-SEQUENCE which iterates through
        batch control records for the date and recovers each failed one.
        """
        results: list[RecoveryResult] = []
        for proc in failed_processes:
            result = self.recover_process(
                process_id=proc.get("process_id", ""),
                process_date=process_date,
                current_status=ProcessStatus(proc.get("status", "E")),
                restart_count=proc.get("restart_count", 0),
                restartable=proc.get("restartable", True),
            )
            results.append(result)
        return results

    def recover_all(self, failed_processes: list[dict]) -> list[RecoveryResult]:
        """
        Recover all failed processes across all dates.

        Mirrors RCVPRC00.cbl 2300-RECOVER-ALL which iterates all batch
        control records and recovers each failed one.
        """
        results: list[RecoveryResult] = []
        for proc in failed_processes:
            result = self.recover_process(
                process_id=proc.get("process_id", ""),
                process_date=proc.get("process_date", ""),
                current_status=ProcessStatus(proc.get("status", "E")),
                restart_count=proc.get("restart_count", 0),
                restartable=proc.get("restartable", True),
            )
            results.append(result)
        return results

    def get_results(self) -> list[RecoveryResult]:
        """Return all recovery results from this session."""
        return list(self._results)

    def validate_request(self, request: RecoveryRequest) -> int:
        """
        Validate a recovery request.

        Mirrors RCVPRC00.cbl 1200-VALIDATE-REQUEST which checks that
        process_date is provided and recovery_type is valid.
        """
        if not request.process_date or request.process_date.strip() == "":
            logger.error("Process date required for recovery")
            return ReturnCode.ERROR

        if request.recovery_type not in ("P", "S", "A"):
            logger.error("Invalid recovery type: %s", request.recovery_type)
            return ReturnCode.ERROR

        if request.recovery_type == "P" and (
            not request.process_id or request.process_id.strip() == ""
        ):
            logger.error("Process ID required for single-process recovery")
            return ReturnCode.ERROR

        return ReturnCode.SUCCESS

    def _determine_action(self, restartable: bool, restart_count: int) -> RecoveryAction:
        """
        Determine the recovery action for a failed process.

        Mirrors RCVPRC00.cbl 2110-DETERMINE-ACTION:
        - If restartable -> RESTART
        - If restart count exceeded -> TERMINATE
        - Otherwise -> BYPASS
        """
        if restartable:
            if restart_count < self._max_restarts:
                return RecoveryAction.RESTART
            else:
                return RecoveryAction.TERMINATE
        else:
            return RecoveryAction.BYPASS

    def _restart_process(self, process_id: str, restart_count: int) -> RecoveryResult:
        """
        Execute restart recovery.

        Mirrors RCVPRC00.cbl 2121-RESTART-PROCESS:
        sets status back to READY, increments restart count.
        """
        return RecoveryResult(
            process_id=process_id,
            action_taken=RecoveryAction.RESTART,
            return_code=ReturnCode.SUCCESS,
            message=f"Process {process_id} queued for restart (attempt {restart_count + 1})",
        )

    def _bypass_process(self, process_id: str) -> RecoveryResult:
        """
        Execute bypass recovery.

        Mirrors RCVPRC00.cbl 2122-BYPASS-PROCESS:
        sets status to DONE with warning RC, adds bypass description.
        """
        return RecoveryResult(
            process_id=process_id,
            action_taken=RecoveryAction.BYPASS,
            return_code=ReturnCode.WARNING,
            message=f"Process {process_id} bypassed by recovery",
        )

    def _terminate_process(self, process_id: str) -> RecoveryResult:
        """
        Execute terminate recovery.

        Mirrors RCVPRC00.cbl 2123-TERMINATE-PROCESS:
        sets status to ERROR with error RC.
        """
        return RecoveryResult(
            process_id=process_id,
            action_taken=RecoveryAction.TERMINATE,
            return_code=ReturnCode.ERROR,
            message=f"Process {process_id} terminated by recovery (max restarts exceeded)",
        )
