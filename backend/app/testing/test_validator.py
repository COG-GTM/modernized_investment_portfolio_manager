"""
Test Validation Suite - Migrated from COBOL TSTVAL00.cbl

Validates test results and system behavior:
- Functional tests: verify individual operations work correctly
- Integration tests: verify cross-component interactions
- Performance tests: measure and benchmark operation timing
- Error tests: verify error handling and recovery

The COBOL program:
1. Read test case records from TEST-CASES file containing:
   TEST-ID, TEST-TYPE, TEST-DESCRIPTION, TEST-PARAMETERS
2. Read expected results from EXPECTED-RESULTS file
3. Read actual results from ACTUAL-RESULTS file
4. For each test case, dispatched based on TEST-TYPE:
   - FUNCTIONAL -> 2200-RUN-FUNCTIONAL-TEST
   - INTEGRATE  -> 2300-RUN-INTEGRATION-TEST
   - PERFORM    -> 2400-RUN-PERFORMANCE-TEST
   - ERROR      -> 2500-RUN-ERROR-TEST
5. Validated results (2600-VALIDATE-RESULTS)
6. Updated metrics (2700-UPDATE-METRICS)
7. Wrote test detail to report (2800-WRITE-TEST-DETAIL)
8. Wrote summary with totals and success rate (2900-WRITE-SUMMARY)

Test metrics tracked:
- WS-TOTAL-TESTS, WS-TESTS-PASSED, WS-TESTS-FAILED
- WS-START-TIME, WS-END-TIME, WS-ELAPSED-TIME
- Success rate computed as (PASSED / TOTAL) * 100
"""

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Test types (from COBOL WS-TEST-TYPES)
TEST_FUNCTIONAL = "FUNCTIONAL"
TEST_INTEGRATION = "INTEGRATE"
TEST_PERFORMANCE = "PERFORM"
TEST_ERROR = "ERROR"

VALID_TEST_TYPES = {TEST_FUNCTIONAL, TEST_INTEGRATION, TEST_PERFORMANCE, TEST_ERROR}


class TestCase:
    """
    Represents a single test case.

    Mirrors COBOL TEST-CASE-RECORD:
    - TEST-ID PIC X(10)
    - TEST-TYPE PIC X(10)
    - TEST-DESCRIPTION PIC X(50)
    - TEST-PARAMETERS PIC X(100)
    """

    def __init__(
        self,
        test_id: str,
        test_type: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        expected_result: Optional[Any] = None,
        test_function: Optional[Callable] = None,
    ):
        self.test_id = test_id
        self.test_type = test_type
        self.description = description
        self.parameters = parameters or {}
        self.expected_result = expected_result
        self.test_function = test_function


class TestResult:
    """
    Represents a single test execution result.

    Mirrors COBOL WS-TEST-DETAIL:
    - WS-TEST-ID-OUT
    - WS-TEST-TYPE-OUT
    - WS-TEST-DESC-OUT
    - WS-TEST-STATUS-OUT (PASS/FAIL)
    """

    def __init__(self, test_case: TestCase):
        self.test_id = test_case.test_id
        self.test_type = test_case.test_type
        self.description = test_case.description
        self.passed: bool = False
        self.actual_result: Optional[Any] = None
        self.error_message: Optional[str] = None
        self.elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_type": self.test_type,
            "description": self.description,
            "status": "PASS" if self.passed else "FAIL",
            "actual_result": str(self.actual_result) if self.actual_result is not None else None,
            "error_message": self.error_message,
            "elapsed_ms": self.elapsed_ms,
        }


class TestMetrics:
    """
    Tracks overall test metrics.

    Mirrors COBOL WS-TEST-METRICS:
    - WS-TOTAL-TESTS PIC 9(5)
    - WS-TESTS-PASSED PIC 9(5)
    - WS-TESTS-FAILED PIC 9(5)
    - WS-START-TIME PIC 9(8)
    - WS-END-TIME PIC 9(8)
    - WS-ELAPSED-TIME PIC 9(8)
    """

    def __init__(self):
        self.total_tests: int = 0
        self.tests_passed: int = 0
        self.tests_failed: int = 0
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    @property
    def elapsed_time(self) -> float:
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        """
        Compute success rate.

        Mirrors COBOL:
        COMPUTE WS-SUCCESS-RATE = (WS-TESTS-PASSED / WS-TOTAL-TESTS) * 100
        """
        if self.total_tests == 0:
            return 0.0
        return (self.tests_passed / self.total_tests) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "success_rate": round(self.success_rate, 2),
            "elapsed_seconds": round(self.elapsed_time, 3),
        }


class TestValidator:
    """
    Test validation suite.

    Migrated from COBOL TSTVAL00 which:
    1. Opened test case, expected, and actual result files
    2. Wrote report headers
    3. Read test cases sequentially, executing each
    4. Compared actual vs expected results
    5. Tracked metrics and wrote summary with success rate
    """

    def __init__(self):
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []
        self.metrics = TestMetrics()

    def add_test(self, test_case: TestCase) -> None:
        """Add a test case to the suite."""
        self.test_cases.append(test_case)

    def run_all(self) -> Dict[str, Any]:
        """
        Run all registered test cases.

        Mirrors COBOL 2000-PROCESS main loop:
        PERFORM UNTIL END-OF-TESTS
            READ TEST-CASES
                AT END SET END-OF-TESTS TO TRUE
                NOT AT END PERFORM 2100-EXECUTE-TEST
        END-PERFORM
        PERFORM 2900-WRITE-SUMMARY

        Returns:
            Complete test report with individual results and summary.
        """
        self.results.clear()
        self.metrics = TestMetrics()

        # 1300-INIT-METRICS: ACCEPT WS-START-TIME FROM TIME
        self.metrics.start_time = time.monotonic()

        # Process each test case
        for test_case in self.test_cases:
            result = self._execute_test(test_case)
            self.results.append(result)

        # 2900-WRITE-SUMMARY: ACCEPT WS-END-TIME FROM TIME
        self.metrics.end_time = time.monotonic()

        return self._generate_report()

    def _execute_test(self, test_case: TestCase) -> TestResult:
        """
        Execute a single test case.

        Mirrors COBOL 2100-EXECUTE-TEST:
        1. Dispatch by TEST-TYPE to appropriate runner
        2. PERFORM 2600-VALIDATE-RESULTS
        3. PERFORM 2700-UPDATE-METRICS
        4. PERFORM 2800-WRITE-TEST-DETAIL

        Args:
            test_case: The test case to execute.

        Returns:
            TestResult with pass/fail status.
        """
        result = TestResult(test_case)
        start = time.monotonic()

        try:
            # Dispatch by test type (mirrors COBOL EVALUATE TEST-TYPE)
            if test_case.test_type == TEST_FUNCTIONAL:
                actual = self._run_functional_test(test_case)
            elif test_case.test_type == TEST_INTEGRATION:
                actual = self._run_integration_test(test_case)
            elif test_case.test_type == TEST_PERFORMANCE:
                actual = self._run_performance_test(test_case)
            elif test_case.test_type == TEST_ERROR:
                actual = self._run_error_test(test_case)
            else:
                raise ValueError(f"Invalid test type: {test_case.test_type}")

            result.actual_result = actual

            # 2600-VALIDATE-RESULTS: Compare actual vs expected
            result.passed = self._validate_results(test_case.expected_result, actual)

        except Exception as e:
            result.passed = False
            result.error_message = str(e)

        result.elapsed_ms = (time.monotonic() - start) * 1000

        # 2700-UPDATE-METRICS
        self.metrics.total_tests += 1
        if result.passed:
            self.metrics.tests_passed += 1
        else:
            self.metrics.tests_failed += 1

        # Log test detail (mirrors 2800-WRITE-TEST-DETAIL)
        status_str = "PASS" if result.passed else "FAIL"
        logger.info("TEST [%s] %s: %s - %s", test_case.test_id, test_case.test_type,
                     test_case.description, status_str)

        return result

    def _run_functional_test(self, test_case: TestCase) -> Any:
        """
        Run a functional test.

        Mirrors COBOL 2200-RUN-FUNCTIONAL-TEST.
        Executes the test function with provided parameters.
        """
        if test_case.test_function is None:
            raise ValueError(f"No test function defined for {test_case.test_id}")
        return test_case.test_function(**test_case.parameters)

    def _run_integration_test(self, test_case: TestCase) -> Any:
        """
        Run an integration test.

        Mirrors COBOL 2300-RUN-INTEGRATION-TEST.
        """
        if test_case.test_function is None:
            raise ValueError(f"No test function defined for {test_case.test_id}")
        return test_case.test_function(**test_case.parameters)

    def _run_performance_test(self, test_case: TestCase) -> Any:
        """
        Run a performance test with timing.

        Mirrors COBOL 2400-RUN-PERFORMANCE-TEST.
        Returns execution time along with result.
        """
        if test_case.test_function is None:
            raise ValueError(f"No test function defined for {test_case.test_id}")

        iterations = test_case.parameters.get("iterations", 1)
        start = time.monotonic()
        result = None
        for _ in range(iterations):
            result = test_case.test_function(**{
                k: v for k, v in test_case.parameters.items() if k != "iterations"
            })
        elapsed = (time.monotonic() - start) * 1000

        return {"result": result, "elapsed_ms": elapsed, "iterations": iterations}

    def _run_error_test(self, test_case: TestCase) -> Any:
        """
        Run an error condition test.

        Mirrors COBOL 2500-RUN-ERROR-TEST.
        Expects the test function to raise an exception or return an error.
        """
        if test_case.test_function is None:
            raise ValueError(f"No test function defined for {test_case.test_id}")

        try:
            result = test_case.test_function(**test_case.parameters)
            return {"error_raised": False, "result": result}
        except Exception as e:
            return {"error_raised": True, "error_type": type(e).__name__, "error_message": str(e)}

    def _validate_results(self, expected: Any, actual: Any) -> bool:
        """
        Compare actual vs expected results.

        Mirrors COBOL 2600-VALIDATE-RESULTS which compared
        EXPECTED-RECORD to ACTUAL-RECORD.
        """
        if expected is None:
            # No expected result defined; test passes if it didn't throw
            return True

        if isinstance(expected, dict) and isinstance(actual, dict):
            return all(
                actual.get(k) == v for k, v in expected.items()
            )

        if isinstance(expected, (int, float, Decimal)):
            return abs(float(expected) - float(actual)) < 0.01

        return expected == actual

    def _generate_report(self) -> Dict[str, Any]:
        """
        Generate the test validation report.

        Mirrors COBOL report generation:
        - WS-HEADER1: Row of asterisks
        - WS-HEADER2: 'TEST VALIDATION REPORT'
        - Individual test detail lines
        - WS-SUMMARY-LINE with totals and success rate
        """
        return {
            "report_title": "TEST VALIDATION REPORT",
            "timestamp": datetime.now().isoformat(),
            "test_results": [r.to_dict() for r in self.results],
            "summary": self.metrics.to_dict(),
        }
