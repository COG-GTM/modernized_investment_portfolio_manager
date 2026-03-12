"""
System Monitoring Utility - Migrated from COBOL UTLMON00.cbl

Monitors system health and performance:
- Resource utilization tracking (CPU, memory, disk, DB)
- Performance metrics collection (query times, connection pool)
- Threshold monitoring with configurable alert levels
- Alert generation when thresholds are exceeded

The COBOL program monitored mainframe resources (CPU, MEMORY, DASD, DB2)
with configurable thresholds (UTIL, RESPONSE, QUEUE, ERROR) and alert
levels (INFO, WARNING, CRITICAL). This modernized version monitors
the Python/FastAPI application and database equivalents.
"""

import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import Portfolio, Position, SessionLocal
from models.transactions import Transaction
from models.history import History

logger = logging.getLogger(__name__)


# Resource types (from COBOL WS-RESOURCE-TYPES)
RESOURCE_CPU = "CPU"
RESOURCE_MEMORY = "MEMORY"
RESOURCE_DISK = "DISK"
RESOURCE_DB = "DB"

# Threshold types (from COBOL WS-THRESHOLD-TYPES)
THRESHOLD_UTILIZATION = "UTIL"
THRESHOLD_RESPONSE = "RESPONSE"
THRESHOLD_QUEUE = "QUEUE"
THRESHOLD_ERROR = "ERROR"

# Alert levels (from COBOL WS-ALERT-LEVELS)
ALERT_INFO = "INFO"
ALERT_WARNING = "WARNING"
ALERT_CRITICAL = "CRITICAL"


class MonitoringThreshold:
    """Represents a monitoring threshold configuration (from COBOL CONFIG-RECORD)."""

    def __init__(
        self,
        resource_type: str,
        threshold_type: str,
        threshold_value: Decimal,
        alert_level: str = ALERT_WARNING,
        alert_action: str = "LOG",
    ):
        self.resource_type = resource_type
        self.threshold_type = threshold_type
        self.threshold_value = threshold_value
        self.alert_level = alert_level
        self.alert_action = alert_action


class MonitoringAlert:
    """Represents a monitoring alert (from COBOL ALERT-RECORD)."""

    def __init__(
        self,
        level: str,
        resource: str,
        message: str,
    ):
        self.timestamp = datetime.now()
        self.level = level
        self.resource = resource
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "resource": self.resource,
            "message": self.message,
        }


class MonitoringMetric:
    """Represents a collected metric (from COBOL LOG-RECORD)."""

    def __init__(
        self,
        resource_type: str,
        metric_name: str,
        metric_value: Decimal,
        status: str = "OK",
    ):
        self.timestamp = datetime.now()
        self.resource_type = resource_type
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "resource_type": self.resource_type,
            "metric_name": self.metric_name,
            "metric_value": float(self.metric_value),
            "status": self.status,
        }


# Default thresholds (mirrors COBOL 1300-READ-CONFIG)
DEFAULT_THRESHOLDS = [
    MonitoringThreshold(RESOURCE_CPU, THRESHOLD_UTILIZATION, Decimal("80.00"), ALERT_WARNING),
    MonitoringThreshold(RESOURCE_CPU, THRESHOLD_UTILIZATION, Decimal("95.00"), ALERT_CRITICAL),
    MonitoringThreshold(RESOURCE_MEMORY, THRESHOLD_UTILIZATION, Decimal("85.00"), ALERT_WARNING),
    MonitoringThreshold(RESOURCE_MEMORY, THRESHOLD_UTILIZATION, Decimal("95.00"), ALERT_CRITICAL),
    MonitoringThreshold(RESOURCE_DISK, THRESHOLD_UTILIZATION, Decimal("90.00"), ALERT_WARNING),
    MonitoringThreshold(RESOURCE_DISK, THRESHOLD_UTILIZATION, Decimal("98.00"), ALERT_CRITICAL),
    MonitoringThreshold(RESOURCE_DB, THRESHOLD_RESPONSE, Decimal("1000.00"), ALERT_WARNING),
    MonitoringThreshold(RESOURCE_DB, THRESHOLD_RESPONSE, Decimal("5000.00"), ALERT_CRITICAL),
    MonitoringThreshold(RESOURCE_DB, THRESHOLD_ERROR, Decimal("10.00"), ALERT_WARNING),
    MonitoringThreshold(RESOURCE_DB, THRESHOLD_ERROR, Decimal("50.00"), ALERT_CRITICAL),
]


class MonitoringService:
    """
    System monitoring service.

    Migrated from COBOL UTLMON00 which:
    - Read monitoring configuration thresholds from a config file
    - Collected CPU, memory, DASD, and DB2 metrics in a loop
    - Checked collected metrics against configured thresholds
    - Logged status to a monitor log file
    - Generated alerts when thresholds were exceeded
    - Ran continuously until hour 23 (end of business day)

    The modernized version collects equivalent metrics for the
    Python/FastAPI application environment.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        thresholds: Optional[List[MonitoringThreshold]] = None,
    ):
        self._db = db
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.metrics: List[MonitoringMetric] = []
        self.alerts: List[MonitoringAlert] = []
        self._current_metrics: Dict[str, Decimal] = {}

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def collect_stats(self) -> Dict[str, Any]:
        """
        Single-pass metric collection and threshold check.

        Mirrors the COBOL 2000-PROCESS loop body:
        - 2100-COLLECT-METRICS
        - 2200-CHECK-THRESHOLDS
        - 2300-LOG-STATUS
        - 2400-GENERATE-ALERTS

        Returns a snapshot of all current metrics and any alerts.
        """
        self.metrics.clear()
        self.alerts.clear()

        # 2100-COLLECT-METRICS
        self._collect_cpu_metrics()
        self._collect_memory_metrics()
        self._collect_disk_metrics()
        self._collect_db_metrics()

        # 2200-CHECK-THRESHOLDS
        self._check_thresholds()

        # 2300-LOG-STATUS
        self._log_status()

        # Build response
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {m.metric_name: m.to_dict() for m in self.metrics},
            "alerts": [a.to_dict() for a in self.alerts],
            "summary": {
                "cpu_utilization": float(self._current_metrics.get("cpu_util", Decimal("0"))),
                "memory_utilization": float(self._current_metrics.get("memory_util", Decimal("0"))),
                "disk_utilization": float(self._current_metrics.get("disk_util", Decimal("0"))),
                "db_response_ms": float(self._current_metrics.get("db_response", Decimal("0"))),
                "db_active_connections": float(self._current_metrics.get("db_connections", Decimal("0"))),
                "db_error_count": float(self._current_metrics.get("db_errors", Decimal("0"))),
                "total_alerts": len(self.alerts),
            },
        }

    def _collect_cpu_metrics(self) -> None:
        """
        Collect CPU utilization metrics.

        Mirrors COBOL 2110-GET-CPU-METRICS. The COBOL version read
        mainframe CPU utilization; this reads OS-level load average.
        """
        try:
            load_avg = os.getloadavg()
            cpu_count = os.cpu_count() or 1
            cpu_util = Decimal(str(min((load_avg[0] / cpu_count) * 100, 100.0)))
            self._current_metrics["cpu_util"] = cpu_util
            self.metrics.append(
                MonitoringMetric(RESOURCE_CPU, "cpu_util", cpu_util)
            )
        except (OSError, AttributeError):
            self._current_metrics["cpu_util"] = Decimal("0")
            self.metrics.append(
                MonitoringMetric(RESOURCE_CPU, "cpu_util", Decimal("0"), "UNAVAILABLE")
            )

    def _collect_memory_metrics(self) -> None:
        """
        Collect memory utilization metrics.

        Mirrors COBOL 2120-GET-MEMORY-METRICS. The COBOL version read
        mainframe memory utilization; this reads /proc/meminfo on Linux.
        """
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().split()[0]
                        meminfo[key] = int(value)

            total = meminfo.get("MemTotal", 1)
            available = meminfo.get("MemAvailable", total)
            used_pct = Decimal(str(((total - available) / total) * 100))
            self._current_metrics["memory_util"] = used_pct
            self.metrics.append(
                MonitoringMetric(RESOURCE_MEMORY, "memory_util", used_pct)
            )
        except (OSError, KeyError, ZeroDivisionError):
            self._current_metrics["memory_util"] = Decimal("0")
            self.metrics.append(
                MonitoringMetric(RESOURCE_MEMORY, "memory_util", Decimal("0"), "UNAVAILABLE")
            )

    def _collect_disk_metrics(self) -> None:
        """
        Collect disk utilization metrics.

        Mirrors COBOL 2130-GET-DASD-METRICS. The COBOL version read
        DASD (Direct Access Storage Device) utilization; this reads
        filesystem usage via os.statvfs.
        """
        try:
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            if total > 0:
                used_pct = Decimal(str(((total - free) / total) * 100))
            else:
                used_pct = Decimal("0")
            self._current_metrics["disk_util"] = used_pct
            self.metrics.append(
                MonitoringMetric(RESOURCE_DISK, "disk_util", used_pct)
            )
        except OSError:
            self._current_metrics["disk_util"] = Decimal("0")
            self.metrics.append(
                MonitoringMetric(RESOURCE_DISK, "disk_util", Decimal("0"), "UNAVAILABLE")
            )

    def _collect_db_metrics(self) -> None:
        """
        Collect database metrics.

        Mirrors COBOL 2140-GET-DB2-METRICS which collected DB2
        utilization, response time, queue depth, and error counts.

        This version measures query response time and counts records
        as a proxy for DB health.
        """
        # Measure DB response time
        try:
            start = time.monotonic()
            self.db.execute(text("SELECT 1"))
            elapsed_ms = Decimal(str((time.monotonic() - start) * 1000))
            self._current_metrics["db_response"] = elapsed_ms
            self.metrics.append(
                MonitoringMetric(RESOURCE_DB, "db_response", elapsed_ms)
            )
        except Exception:
            self._current_metrics["db_response"] = Decimal("-1")
            self.metrics.append(
                MonitoringMetric(RESOURCE_DB, "db_response", Decimal("-1"), "ERROR")
            )

        # Count active DB connections (approximation)
        try:
            connection_count = Decimal("1")  # Current session
            self._current_metrics["db_connections"] = connection_count
            self.metrics.append(
                MonitoringMetric(RESOURCE_DB, "db_connections", connection_count)
            )
        except Exception:
            self._current_metrics["db_connections"] = Decimal("0")

        # DB error count (check for failed transactions)
        try:
            failed_count = self.db.query(Transaction).filter(
                Transaction.status == "F"
            ).count()
            self._current_metrics["db_errors"] = Decimal(str(failed_count))
            self.metrics.append(
                MonitoringMetric(RESOURCE_DB, "db_errors", Decimal(str(failed_count)))
            )
        except Exception:
            self._current_metrics["db_errors"] = Decimal("0")

    def _check_thresholds(self) -> None:
        """
        Check all collected metrics against configured thresholds.

        Mirrors COBOL 2200-CHECK-THRESHOLDS:
        - 2210-CHECK-UTILIZATION
        - 2220-CHECK-RESPONSE
        - 2230-CHECK-QUEUES
        - 2240-CHECK-ERRORS
        """
        metric_to_threshold_map = {
            "cpu_util": (RESOURCE_CPU, THRESHOLD_UTILIZATION),
            "memory_util": (RESOURCE_MEMORY, THRESHOLD_UTILIZATION),
            "disk_util": (RESOURCE_DISK, THRESHOLD_UTILIZATION),
            "db_response": (RESOURCE_DB, THRESHOLD_RESPONSE),
            "db_errors": (RESOURCE_DB, THRESHOLD_ERROR),
        }

        for metric_name, (resource_type, threshold_type) in metric_to_threshold_map.items():
            current_value = self._current_metrics.get(metric_name, Decimal("0"))

            # Find applicable thresholds sorted by value (ascending)
            applicable = sorted(
                [
                    t for t in self.thresholds
                    if t.resource_type == resource_type and t.threshold_type == threshold_type
                ],
                key=lambda t: t.threshold_value,
            )

            for threshold in applicable:
                if current_value >= threshold.threshold_value:
                    self._generate_alert(
                        threshold.alert_level,
                        resource_type,
                        f"{metric_name} = {float(current_value):.2f} "
                        f"exceeds threshold {float(threshold.threshold_value):.2f}",
                    )

    def _generate_alert(self, level: str, resource: str, message: str) -> None:
        """
        Generate a monitoring alert.

        Mirrors COBOL 2400-GENERATE-ALERTS:
        - 2410-FORMAT-ALERT
        - 2420-WRITE-ALERT
        """
        alert = MonitoringAlert(level=level, resource=resource, message=message)
        self.alerts.append(alert)
        logger.warning("MONITORING ALERT [%s] %s: %s", level, resource, message)

    def _log_status(self) -> None:
        """
        Log current monitoring status.

        Mirrors COBOL 2300-LOG-STATUS:
        - 2310-LOG-RESOURCES
        - 2320-LOG-PERFORMANCE
        """
        for metric in self.metrics:
            logger.info(
                "MONITOR [%s] %s = %s (%s)",
                metric.resource_type,
                metric.metric_name,
                float(metric.metric_value),
                metric.status,
            )

    def close(self) -> None:
        """Close database session if we created one."""
        if self._db is not None:
            self._db.close()
