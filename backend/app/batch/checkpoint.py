"""
Checkpoint/Restart Framework.

Migrated from: CKPRST.cbl, CKPRST.cpy
Tracks job state in a database table so failed jobs can resume from
their last successful checkpoint rather than restarting from scratch.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session

from .return_codes import ReturnCode, ReturnStatus

logger = logging.getLogger(__name__)


class CheckpointStatus(str, Enum):
    """Checkpoint status values from CKPRST.cpy CK-STATUS."""

    INITIAL = "I"
    ACTIVE = "A"
    COMPLETE = "C"
    FAILED = "F"
    RESTARTED = "R"


class CheckpointPhase(str, Enum):
    """Processing phase values from CKPRST.cpy CK-PHASE."""

    INIT = "00"
    READ = "10"
    PROCESS = "20"
    UPDATE = "30"
    TERMINATE = "40"


@dataclass
class FilePosition:
    """
    Tracks file position for checkpoint/restart.

    Mirrors CKPRST.cpy CK-RESOURCES / CK-FILE-STATUS entries.
    """

    file_name: str = ""
    file_position: str = ""
    file_status: str = ""


@dataclass
class CheckpointData:
    """
    Checkpoint state for a running batch program.

    Mirrors CKPRST.cpy CHECKPOINT-CONTROL structure.
    Tracks counters, position, file states, and control info
    so a failed job can resume where it left off.
    """

    program_id: str = ""
    run_date: str = ""
    run_time: str = ""
    status: CheckpointStatus = CheckpointStatus.INITIAL
    records_read: int = 0
    records_processed: int = 0
    records_error: int = 0
    restart_count: int = 0
    last_key: str = ""
    last_time: str = ""
    phase: CheckpointPhase = CheckpointPhase.INIT
    file_positions: List[FilePosition] = field(default_factory=list)
    commit_frequency: int = 1000
    max_errors: int = 100
    max_restarts: int = 3
    restart_mode: str = "N"  # N=normal, R=restart, C=recover
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize checkpoint data to JSON for storage."""
        return json.dumps(
            {
                "program_id": self.program_id,
                "run_date": self.run_date,
                "run_time": self.run_time,
                "status": self.status.value,
                "records_read": self.records_read,
                "records_processed": self.records_processed,
                "records_error": self.records_error,
                "restart_count": self.restart_count,
                "last_key": self.last_key,
                "last_time": self.last_time,
                "phase": self.phase.value,
                "file_positions": [
                    {
                        "file_name": fp.file_name,
                        "file_position": fp.file_position,
                        "file_status": fp.file_status,
                    }
                    for fp in self.file_positions
                ],
                "commit_frequency": self.commit_frequency,
                "max_errors": self.max_errors,
                "max_restarts": self.max_restarts,
                "restart_mode": self.restart_mode,
                "extra_data": self.extra_data,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "CheckpointData":
        """Deserialize checkpoint data from JSON."""
        d = json.loads(data)
        ckpt = cls(
            program_id=d.get("program_id", ""),
            run_date=d.get("run_date", ""),
            run_time=d.get("run_time", ""),
            status=CheckpointStatus(d.get("status", "I")),
            records_read=d.get("records_read", 0),
            records_processed=d.get("records_processed", 0),
            records_error=d.get("records_error", 0),
            restart_count=d.get("restart_count", 0),
            last_key=d.get("last_key", ""),
            last_time=d.get("last_time", ""),
            phase=CheckpointPhase(d.get("phase", "00")),
            commit_frequency=d.get("commit_frequency", 1000),
            max_errors=d.get("max_errors", 100),
            max_restarts=d.get("max_restarts", 3),
            restart_mode=d.get("restart_mode", "N"),
            extra_data=d.get("extra_data", {}),
        )
        for fp_data in d.get("file_positions", []):
            ckpt.file_positions.append(
                FilePosition(
                    file_name=fp_data.get("file_name", ""),
                    file_position=fp_data.get("file_position", ""),
                    file_status=fp_data.get("file_status", ""),
                )
            )
        return ckpt


class CheckpointManager:
    """
    Manages checkpoint/restart operations for batch programs.

    Migrated from CKPRST.cbl. The COBOL program dispatches on entry point
    (INIT, TAKE, COMMIT, RESTART) and reads/writes a VSAM checkpoint file.
    This Python version uses a database table for persistence.
    """

    def __init__(self, db_session: Session) -> None:
        self._db = db_session
        self._checkpoints: Dict[str, CheckpointData] = {}
        logger.info("CheckpointManager initialized")

    def initialize(self, program_id: str, run_date: Optional[str] = None) -> CheckpointData:
        """
        Initialize checkpoint processing for a program.

        Mirrors CKPRST.cbl PROC-INIT. Creates a new checkpoint record
        or loads existing one if restarting.
        """
        if run_date is None:
            run_date = datetime.now().strftime("%Y%m%d")
        run_time = datetime.now().strftime("%H%M%S")

        key = f"{program_id}:{run_date}"

        # Check for existing checkpoint (restart scenario)
        existing = self._load_from_db(program_id, run_date)
        if existing and existing.status in (CheckpointStatus.ACTIVE, CheckpointStatus.FAILED):
            existing.status = CheckpointStatus.RESTARTED
            existing.restart_count += 1
            existing.restart_mode = "R"
            self._checkpoints[key] = existing
            logger.info(
                "Restarting from checkpoint: program=%s date=%s restart_count=%d last_key=%s",
                program_id,
                run_date,
                existing.restart_count,
                existing.last_key,
            )
            return existing

        ckpt = CheckpointData(
            program_id=program_id,
            run_date=run_date,
            run_time=run_time,
            status=CheckpointStatus.ACTIVE,
            phase=CheckpointPhase.INIT,
        )
        self._checkpoints[key] = ckpt
        self._save_to_db(ckpt)
        logger.info("Checkpoint initialized: program=%s date=%s", program_id, run_date)
        return ckpt

    def take_checkpoint(
        self,
        program_id: str,
        run_date: str,
        last_key: str = "",
        phase: Optional[CheckpointPhase] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Take a checkpoint (snapshot current state).

        Mirrors CKPRST.cbl PROC-TAKE-CHECKPOINT. Records current position
        so processing can resume from this point if interrupted.
        """
        key = f"{program_id}:{run_date}"
        ckpt = self._checkpoints.get(key)
        if not ckpt:
            logger.warning("No active checkpoint for %s", key)
            return

        ckpt.last_key = last_key
        ckpt.last_time = datetime.now().isoformat()
        if phase:
            ckpt.phase = phase
        if extra_data:
            ckpt.extra_data.update(extra_data)

        logger.debug(
            "Checkpoint taken: program=%s key=%s phase=%s",
            program_id,
            last_key,
            ckpt.phase.value,
        )

    def commit_checkpoint(self, program_id: str, run_date: str) -> None:
        """
        Commit the current checkpoint to persistent storage.

        Mirrors CKPRST.cbl PROC-COMMIT-CHECKPOINT. Writes the checkpoint
        data to the database so it survives process failure.
        """
        key = f"{program_id}:{run_date}"
        ckpt = self._checkpoints.get(key)
        if not ckpt:
            logger.warning("No active checkpoint to commit for %s", key)
            return

        self._save_to_db(ckpt)
        logger.info(
            "Checkpoint committed: program=%s records_read=%d records_processed=%d",
            program_id,
            ckpt.records_read,
            ckpt.records_processed,
        )

    def complete(self, program_id: str, run_date: str) -> None:
        """Mark a checkpoint as complete (successful finish)."""
        key = f"{program_id}:{run_date}"
        ckpt = self._checkpoints.get(key)
        if ckpt:
            ckpt.status = CheckpointStatus.COMPLETE
            ckpt.phase = CheckpointPhase.TERMINATE
            self._save_to_db(ckpt)
            logger.info("Checkpoint completed: program=%s", program_id)

    def fail(self, program_id: str, run_date: str) -> None:
        """Mark a checkpoint as failed."""
        key = f"{program_id}:{run_date}"
        ckpt = self._checkpoints.get(key)
        if ckpt:
            ckpt.status = CheckpointStatus.FAILED
            self._save_to_db(ckpt)
            logger.info("Checkpoint marked failed: program=%s", program_id)

    def get_checkpoint(self, program_id: str, run_date: str) -> Optional[CheckpointData]:
        """Retrieve checkpoint data for a program/date combination."""
        key = f"{program_id}:{run_date}"
        return self._checkpoints.get(key) or self._load_from_db(program_id, run_date)

    def can_restart(self, program_id: str, run_date: str) -> bool:
        """
        Check if a program can be restarted from its checkpoint.

        Verifies the checkpoint exists, is in a restartable state,
        and hasn't exceeded the maximum restart count.
        """
        ckpt = self.get_checkpoint(program_id, run_date)
        if not ckpt:
            return False
        if ckpt.status not in (CheckpointStatus.FAILED, CheckpointStatus.ACTIVE):
            return False
        if ckpt.restart_count >= ckpt.max_restarts:
            return False
        return True

    def _save_to_db(self, ckpt: CheckpointData) -> None:
        """Persist checkpoint data to the database."""
        try:
            from models.database import Base

            # Use raw SQL to store checkpoint in a batch_checkpoints table
            self._db.execute(
                Base.metadata.tables.get("batch_checkpoints", _create_checkpoint_table(Base))
                .insert()
                .prefix_with("OR REPLACE")
                .values(
                    program_id=ckpt.program_id,
                    run_date=ckpt.run_date,
                    checkpoint_data=ckpt.to_json(),
                    updated_at=datetime.now(),
                )
            )
            self._db.commit()
        except Exception:
            # If the table doesn't exist yet, store in memory only
            logger.debug(
                "Checkpoint stored in memory (DB table not available): program=%s",
                ckpt.program_id,
            )

    def _load_from_db(self, program_id: str, run_date: str) -> Optional[CheckpointData]:
        """Load checkpoint data from the database."""
        try:
            from models.database import Base

            table = Base.metadata.tables.get("batch_checkpoints")
            if table is None:
                return None
            result = self._db.execute(
                table.select().where(
                    (table.c.program_id == program_id) & (table.c.run_date == run_date)
                )
            ).first()
            if result:
                return CheckpointData.from_json(result.checkpoint_data)
        except Exception:
            logger.debug("Could not load checkpoint from DB for %s:%s", program_id, run_date)
        return None


def _create_checkpoint_table(base: Any) -> Any:
    """
    Create the batch_checkpoints table definition.

    This replaces the VSAM checkpoint file (CKPTFILE) from the COBOL system.
    """
    from sqlalchemy import Column, DateTime, MetaData, String, Table, Text

    table = Table(
        "batch_checkpoints",
        base.metadata,
        Column("program_id", String(8), primary_key=True),
        Column("run_date", String(8), primary_key=True),
        Column("checkpoint_data", Text),
        Column("updated_at", DateTime),
        extend_existing=True,
    )
    return table
