"""
Monitoring API Route - Migrated from COBOL UTLMON00.cbl

Exposes system monitoring statistics as an API endpoint.
"""

import logging
from fastapi import APIRouter

from app.utils.monitoring import MonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/stats")
async def get_monitoring_stats():
    """
    Get system monitoring statistics.

    Migrated from COBOL UTLMON00 which collected CPU, memory, DASD,
    and DB2 metrics, checked thresholds, and generated alerts.
    """
    service = MonitoringService()
    try:
        stats = service.collect_stats()
        return stats
    finally:
        service.close()
