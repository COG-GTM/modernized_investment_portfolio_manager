"""
Unit tests for the return_codes module.

Tests return code classification, status tracking, and pipeline gating logic.
"""

import unittest

from app.batch.return_codes import (
    ReturnCode,
    ReturnStatus,
    StatusCode,
    classify_return_code,
    can_continue_pipeline,
)


class TestReturnCodeEnum(unittest.TestCase):
    """Test ReturnCode enum values."""

    def test_success_is_zero(self) -> None:
        self.assertEqual(ReturnCode.SUCCESS, 0)

    def test_warning_is_four(self) -> None:
        self.assertEqual(ReturnCode.WARNING, 4)

    def test_error_is_eight(self) -> None:
        self.assertEqual(ReturnCode.ERROR, 8)

    def test_severe_is_twelve(self) -> None:
        self.assertEqual(ReturnCode.SEVERE, 12)

    def test_critical_is_sixteen(self) -> None:
        self.assertEqual(ReturnCode.CRITICAL, 16)


class TestClassifyReturnCode(unittest.TestCase):
    """Test return code classification function."""

    def test_classify_success(self) -> None:
        self.assertEqual(classify_return_code(0), StatusCode.SUCCESS)

    def test_classify_warning(self) -> None:
        self.assertEqual(classify_return_code(4), StatusCode.WARNING)

    def test_classify_error(self) -> None:
        self.assertEqual(classify_return_code(8), StatusCode.ERROR)

    def test_classify_severe(self) -> None:
        self.assertEqual(classify_return_code(12), StatusCode.SEVERE)

    def test_classify_critical(self) -> None:
        self.assertEqual(classify_return_code(16), StatusCode.SEVERE)

    def test_classify_intermediate_values(self) -> None:
        # Values between thresholds: 0=SUCCESS, 1-4=WARNING, 5-8=ERROR, 9+=SEVERE
        self.assertEqual(classify_return_code(1), StatusCode.WARNING)
        self.assertEqual(classify_return_code(3), StatusCode.WARNING)
        self.assertEqual(classify_return_code(5), StatusCode.ERROR)
        self.assertEqual(classify_return_code(7), StatusCode.ERROR)
        self.assertEqual(classify_return_code(9), StatusCode.SEVERE)
        self.assertEqual(classify_return_code(11), StatusCode.SEVERE)


class TestCanContinuePipeline(unittest.TestCase):
    """Test pipeline continuation gating."""

    def test_success_continues(self) -> None:
        self.assertTrue(can_continue_pipeline(0))

    def test_warning_continues(self) -> None:
        self.assertTrue(can_continue_pipeline(4))

    def test_error_stops(self) -> None:
        self.assertFalse(can_continue_pipeline(8))

    def test_severe_stops(self) -> None:
        self.assertFalse(can_continue_pipeline(12))

    def test_critical_stops(self) -> None:
        self.assertFalse(can_continue_pipeline(16))

    def test_rc_1_continues(self) -> None:
        self.assertTrue(can_continue_pipeline(1))

    def test_rc_5_stops(self) -> None:
        self.assertFalse(can_continue_pipeline(5))


class TestReturnStatus(unittest.TestCase):
    """Test ReturnStatus tracking."""

    def test_initial_state(self) -> None:
        status = ReturnStatus(program_id="TEST")
        self.assertEqual(status.current_code, 0)
        self.assertEqual(status.highest_code, 0)
        self.assertEqual(status.program_id, "TEST")

    def test_set_code_updates_current(self) -> None:
        status = ReturnStatus(program_id="TEST")
        status.set_code(4, "Warning message")
        self.assertEqual(status.current_code, 4)
        self.assertEqual(status.message, "Warning message")

    def test_set_code_tracks_highest(self) -> None:
        status = ReturnStatus(program_id="TEST")
        status.set_code(4, "Warning")
        status.set_code(0, "Success")
        self.assertEqual(status.current_code, 0)
        self.assertEqual(status.highest_code, 4)

    def test_can_continue_with_success(self) -> None:
        status = ReturnStatus(program_id="TEST")
        status.set_code(0, "OK")
        self.assertTrue(status.can_continue())

    def test_can_continue_with_warning(self) -> None:
        status = ReturnStatus(program_id="TEST")
        status.set_code(4, "Warning")
        self.assertTrue(status.can_continue())

    def test_cannot_continue_with_error(self) -> None:
        status = ReturnStatus(program_id="TEST")
        status.set_code(8, "Error")
        self.assertFalse(status.can_continue())


if __name__ == "__main__":
    unittest.main()
