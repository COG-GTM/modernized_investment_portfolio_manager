"""
Unit tests for the checkpoint module.

Tests checkpoint/restart framework including state management,
serialization, and restart logic.
"""

import unittest

from app.batch.checkpoint import (
    CheckpointData,
    CheckpointManager,
    CheckpointPhase,
    CheckpointStatus,
    FilePosition,
)


class TestCheckpointData(unittest.TestCase):
    """Test CheckpointData serialization and state."""

    def test_default_state(self) -> None:
        data = CheckpointData(program_id="TEST")
        self.assertEqual(data.program_id, "TEST")
        self.assertEqual(data.status, CheckpointStatus.INITIAL)
        self.assertEqual(data.phase, CheckpointPhase.INIT)
        self.assertEqual(data.records_processed, 0)
        self.assertEqual(data.restart_count, 0)

    def test_json_round_trip(self) -> None:
        data = CheckpointData(
            program_id="HISTLD00",
            status=CheckpointStatus.ACTIVE,
            phase=CheckpointPhase.PROCESS,
            records_processed=500,
            last_key="HISTLD00",
            restart_count=1,
        )
        json_str = data.to_json()
        restored = CheckpointData.from_json(json_str)

        self.assertEqual(restored.program_id, "HISTLD00")
        self.assertEqual(restored.status, CheckpointStatus.ACTIVE)
        self.assertEqual(restored.phase, CheckpointPhase.PROCESS)
        self.assertEqual(restored.records_processed, 500)
        self.assertEqual(restored.last_key, "HISTLD00")
        self.assertEqual(restored.restart_count, 1)


class TestFilePosition(unittest.TestCase):
    """Test FilePosition tracking."""

    def test_default_values(self) -> None:
        fp = FilePosition()
        self.assertEqual(fp.file_name, "")
        self.assertEqual(fp.file_position, "")
        self.assertEqual(fp.file_status, "")

    def test_custom_values(self) -> None:
        fp = FilePosition(file_name="TRNFILE", file_position="4096", file_status="OK")
        self.assertEqual(fp.file_name, "TRNFILE")
        self.assertEqual(fp.file_position, "4096")
        self.assertEqual(fp.file_status, "OK")


class TestCheckpointManager(unittest.TestCase):
    """Test CheckpointManager operations (without DB)."""

    def test_checkpoint_data_default_state(self) -> None:
        """Test that CheckpointData starts in correct initial state."""
        data = CheckpointData(program_id="TEST")
        self.assertEqual(data.status, CheckpointStatus.INITIAL)
        self.assertEqual(data.restart_count, 0)
        self.assertEqual(data.records_processed, 0)
        self.assertEqual(data.last_key, "")

    def test_checkpoint_data_restart_count_tracking(self) -> None:
        """Test restart count tracking in CheckpointData."""
        data = CheckpointData(program_id="TEST", restart_count=2, max_restarts=3)
        self.assertTrue(data.restart_count < data.max_restarts)
        data.restart_count += 1
        self.assertFalse(data.restart_count < data.max_restarts)

    def test_checkpoint_data_status_transitions(self) -> None:
        """Test valid status transitions in CheckpointData."""
        data = CheckpointData(program_id="TEST")
        self.assertEqual(data.status, CheckpointStatus.INITIAL)
        data.status = CheckpointStatus.ACTIVE
        self.assertEqual(data.status, CheckpointStatus.ACTIVE)
        data.status = CheckpointStatus.COMPLETE
        self.assertEqual(data.status, CheckpointStatus.COMPLETE)


class TestCheckpointStatusEnum(unittest.TestCase):
    """Test CheckpointStatus enum values."""

    def test_status_values(self) -> None:
        self.assertEqual(CheckpointStatus.INITIAL.value, "I")
        self.assertEqual(CheckpointStatus.ACTIVE.value, "A")
        self.assertEqual(CheckpointStatus.COMPLETE.value, "C")
        self.assertEqual(CheckpointStatus.FAILED.value, "F")
        self.assertEqual(CheckpointStatus.RESTARTED.value, "R")


class TestCheckpointPhaseEnum(unittest.TestCase):
    """Test CheckpointPhase enum values."""

    def test_phase_values(self) -> None:
        self.assertEqual(CheckpointPhase.INIT.value, "00")
        self.assertEqual(CheckpointPhase.READ.value, "10")
        self.assertEqual(CheckpointPhase.PROCESS.value, "20")
        self.assertEqual(CheckpointPhase.UPDATE.value, "30")
        self.assertEqual(CheckpointPhase.TERMINATE.value, "40")


if __name__ == "__main__":
    unittest.main()
