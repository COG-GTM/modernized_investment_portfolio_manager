"""
Process Sequence Manager.

Migrated from: PRCSEQ00.cbl, PRCSEQ.cpy
Defines and enforces process execution order, manages dependencies
between batch steps, and determines which process runs next.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from .return_codes import ProcessStatus, ReturnCode

logger = logging.getLogger(__name__)


class ProcessType(str, Enum):
    """Process type classifications from PRCSEQ.cpy PSR-TYPE."""

    INIT = "INI"
    PROCESS = "PRC"
    REPORT = "RPT"
    TERMINATE = "TRM"


class DependencyType(str, Enum):
    """Dependency strictness from PRCSEQ.cpy PSR-DEP-TYPE."""

    HARD = "H"
    SOFT = "S"


class Frequency(str, Enum):
    """Execution frequency from PRCSEQ.cpy PSR-FREQ."""

    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"


@dataclass
class Dependency:
    """
    A dependency on another process.

    Mirrors PRCSEQ.cpy PSR-DEP-ENTRY structure.
    """

    process_id: str
    dep_type: DependencyType = DependencyType.HARD
    max_return_code: int = 4


@dataclass
class ProcessDefinition:
    """
    Defines a single process in the batch sequence.

    Mirrors PRCSEQ.cpy PROCESS-SEQUENCE-RECORD structure including
    scheduling, dependency, control, and recovery information.
    """

    process_id: str
    description: str = ""
    process_type: ProcessType = ProcessType.PROCESS
    frequency: Frequency = Frequency.DAILY
    start_time: str = ""
    max_time: str = ""
    dependencies: List[Dependency] = field(default_factory=list)
    program_name: str = ""
    parameters: str = ""
    max_return_code: int = 4
    restartable: bool = True
    active_days: str = "YYYYYNN"  # Mon-Sun, Y=active
    month_end_only: bool = False
    run_on_holiday: bool = False
    recovery_program: str = ""
    recovery_parm: str = ""
    error_limit: int = 100


@dataclass
class ProcessEntry:
    """
    Runtime state of a process in the sequence table.

    Mirrors PRCSEQ00.cbl WS-PROCESS-TABLE / WS-PROC-ENTRY.
    """

    process_id: str
    sequence_no: int
    status: ProcessStatus = ProcessStatus.READY
    return_code: int = 0


# Standard process sequences from PRCSEQ.cpy STANDARD-SEQUENCES
SEQUENCE_START_OF_DAY = ["INITDAY", "CKPCLR", "DATEVAL"]
SEQUENCE_MAIN_PROCESS = ["TRNVAL00", "POSUPD00", "HISTLD00"]
SEQUENCE_END_OF_DAY = ["RPTGEN00", "BCKLOD00", "ENDDAY"]

# Default pipeline sequence for the investment portfolio system
DEFAULT_PIPELINE_SEQUENCE = [
    ProcessDefinition(
        process_id="TRNVAL00",
        description="Transaction Validation",
        process_type=ProcessType.PROCESS,
        program_name="transaction_validator",
        max_return_code=4,
        restartable=True,
    ),
    ProcessDefinition(
        process_id="POSUPD00",
        description="Position Updates",
        process_type=ProcessType.PROCESS,
        program_name="position_updater",
        dependencies=[Dependency(process_id="TRNVAL00", dep_type=DependencyType.HARD)],
        max_return_code=4,
        restartable=True,
    ),
    ProcessDefinition(
        process_id="HISTLD00",
        description="History Loading",
        process_type=ProcessType.PROCESS,
        program_name="history_loader",
        dependencies=[Dependency(process_id="POSUPD00", dep_type=DependencyType.HARD)],
        max_return_code=4,
        restartable=True,
    ),
    ProcessDefinition(
        process_id="RPTPOS00",
        description="Position Reports",
        process_type=ProcessType.REPORT,
        program_name="position_report",
        dependencies=[Dependency(process_id="HISTLD00", dep_type=DependencyType.HARD)],
        max_return_code=4,
        restartable=True,
    ),
    ProcessDefinition(
        process_id="RPTAUD00",
        description="Audit Reports",
        process_type=ProcessType.REPORT,
        program_name="audit_report",
        dependencies=[Dependency(process_id="HISTLD00", dep_type=DependencyType.SOFT)],
        max_return_code=4,
        restartable=True,
    ),
    ProcessDefinition(
        process_id="RPTSTA00",
        description="Statistics Reports",
        process_type=ProcessType.REPORT,
        program_name="stats_report",
        dependencies=[Dependency(process_id="HISTLD00", dep_type=DependencyType.SOFT)],
        max_return_code=4,
        restartable=True,
    ),
]


class ProcessSequencer:
    """
    Manages process execution order and dependency checking.

    Migrated from PRCSEQ00.cbl. The COBOL program reads a VSAM process
    sequence file and batch control file, builds an in-memory sequence table,
    and dispatches on function codes (INIT, NEXT, STAT, TERM).
    """

    def __init__(
        self, definitions: Optional[List[ProcessDefinition]] = None
    ) -> None:
        self._definitions: Dict[str, ProcessDefinition] = {}
        self._sequence: List[ProcessEntry] = []
        self._process_count = 0

        if definitions:
            self._build_sequence(definitions)
        logger.info("ProcessSequencer initialized with %d processes", self._process_count)

    def initialize(
        self,
        definitions: Optional[List[ProcessDefinition]] = None,
    ) -> int:
        """
        Initialize the process sequence.

        Mirrors PRCSEQ00.cbl 1000-INITIALIZE-SEQUENCE:
        opens files, builds the sequence table, and creates control records.
        """
        defs = definitions or DEFAULT_PIPELINE_SEQUENCE
        self._build_sequence(defs)
        logger.info("Sequence initialized with %d processes", self._process_count)
        return ReturnCode.SUCCESS

    def get_next_process(self) -> Optional[str]:
        """
        Get the next process that is ready to run.

        Mirrors PRCSEQ00.cbl 2000-GET-NEXT-PROCESS:
        finds the first READY process in sequence order, checks its
        dependencies, and marks it ACTIVE if all deps are satisfied.
        """
        for entry in self._sequence:
            if entry.status == ProcessStatus.READY:
                if self._check_dependencies(entry.process_id):
                    entry.status = ProcessStatus.ACTIVE
                    logger.info("Next process: %s (seq=%d)", entry.process_id, entry.sequence_no)
                    return entry.process_id
                else:
                    logger.debug(
                        "Process %s has unmet dependencies, skipping",
                        entry.process_id,
                    )
        logger.info("No more ready processes in sequence")
        return None

    def update_process_status(
        self, process_id: str, status: ProcessStatus, return_code: int = 0
    ) -> None:
        """
        Update the status and return code of a process.

        Mirrors PRCSEQ00.cbl 3200-UPDATE-SEQUENCE-TABLE:
        finds the process in the table and updates its status/RC.
        """
        for entry in self._sequence:
            if entry.process_id == process_id:
                entry.status = status
                entry.return_code = return_code
                logger.info(
                    "Process %s status updated: %s RC=%d",
                    process_id,
                    status.value,
                    return_code,
                )
                return
        logger.warning("Process %s not found in sequence", process_id)

    def check_completion(self) -> Dict[str, int]:
        """
        Check overall completion status of the sequence.

        Mirrors PRCSEQ00.cbl 3300-CHECK-COMPLETION:
        counts active and errored processes to determine overall state.
        """
        active_count = 0
        error_count = 0
        done_count = 0
        ready_count = 0

        for entry in self._sequence:
            if entry.status == ProcessStatus.ACTIVE:
                active_count += 1
            elif entry.status == ProcessStatus.ERROR:
                error_count += 1
            elif entry.status == ProcessStatus.DONE:
                done_count += 1
            elif entry.status == ProcessStatus.READY:
                ready_count += 1

        return {
            "total": self._process_count,
            "active": active_count,
            "error": error_count,
            "done": done_count,
            "ready": ready_count,
        }

    def terminate(self) -> int:
        """
        Terminate the sequence and return final status.

        Mirrors PRCSEQ00.cbl 4000-TERMINATE-SEQUENCE / 4100-CHECK-FINAL-STATUS:
        checks completion and returns appropriate RC.
        """
        status = self.check_completion()

        if status["error"] > 0:
            logger.info("Sequence terminated with errors: %d", status["error"])
            return ReturnCode.ERROR
        elif status["active"] > 0:
            logger.info("Sequence terminated with active processes: %d", status["active"])
            return ReturnCode.WARNING
        else:
            logger.info("Sequence terminated successfully")
            return ReturnCode.SUCCESS

    def get_process_definition(self, process_id: str) -> Optional[ProcessDefinition]:
        """Retrieve the definition for a specific process."""
        return self._definitions.get(process_id)

    def get_sequence(self) -> List[ProcessEntry]:
        """Return the current process sequence."""
        return list(self._sequence)

    def _build_sequence(self, definitions: List[ProcessDefinition]) -> None:
        """
        Build the sequence table from process definitions.

        Mirrors PRCSEQ00.cbl 1200-BUILD-SEQUENCE / 1210-ADD-TO-SEQUENCE.
        """
        self._definitions.clear()
        self._sequence.clear()
        self._process_count = 0

        for i, defn in enumerate(definitions):
            self._definitions[defn.process_id] = defn
            self._sequence.append(
                ProcessEntry(
                    process_id=defn.process_id,
                    sequence_no=i + 1,
                    status=ProcessStatus.READY,
                )
            )
            self._process_count += 1

    def _check_dependencies(self, process_id: str) -> bool:
        """
        Check if all dependencies for a process are satisfied.

        Mirrors PRCSEQ00.cbl 2200-CHECK-DEPENDENCIES / 2210-CHECK-DEP-STATUS:
        for each dependency, verifies the prerequisite is DONE and its RC
        is within the allowed threshold.
        """
        defn = self._definitions.get(process_id)
        if not defn:
            return True

        for dep in defn.dependencies:
            dep_entry = self._find_entry(dep.process_id)
            if not dep_entry:
                if dep.dep_type == DependencyType.HARD:
                    logger.warning(
                        "Hard dependency %s not found for %s",
                        dep.process_id,
                        process_id,
                    )
                    return False
                continue

            if dep_entry.status != ProcessStatus.DONE:
                if dep.dep_type == DependencyType.HARD:
                    return False
                continue

            if dep_entry.return_code > dep.max_return_code:
                logger.warning(
                    "Dependency %s RC=%d exceeds max=%d for %s",
                    dep.process_id,
                    dep_entry.return_code,
                    dep.max_return_code,
                    process_id,
                )
                return False

        return True

    def _find_entry(self, process_id: str) -> Optional[ProcessEntry]:
        """Find a process entry by ID."""
        for entry in self._sequence:
            if entry.process_id == process_id:
                return entry
        return None
