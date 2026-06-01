from fastapi import APIRouter
from models.portfolio import VisitorsHistoryResponse, VisitorRecord
from datetime import datetime

router = APIRouter(prefix="/api", tags=["visitors"])


def generate_mock_visitors() -> VisitorsHistoryResponse:
    visitors = [
        VisitorRecord(
            visitorId="VIS-001",
            accountNumber="1234567890",
            visitorName="John Smith",
            action="Portfolio Inquiry",
            ipAddress="192.168.1.42",
            timestamp="2026-04-30T14:23:15",
            duration="3m 12s",
        ),
        VisitorRecord(
            visitorId="VIS-002",
            accountNumber="9876543210",
            visitorName="Sarah Johnson",
            action="Transaction History",
            ipAddress="10.0.0.15",
            timestamp="2026-04-30T13:45:02",
            duration="1m 48s",
        ),
        VisitorRecord(
            visitorId="VIS-003",
            accountNumber="1234567890",
            visitorName="Michael Chen",
            action="Portfolio Inquiry",
            ipAddress="172.16.0.88",
            timestamp="2026-04-30T12:10:33",
            duration="5m 04s",
        ),
        VisitorRecord(
            visitorId="VIS-004",
            accountNumber="5555555555",
            visitorName="Emily Davis",
            action="Portfolio Inquiry",
            ipAddress="192.168.2.101",
            timestamp="2026-04-29T16:55:47",
            duration="2m 31s",
        ),
        VisitorRecord(
            visitorId="VIS-005",
            accountNumber="9876543210",
            visitorName="Robert Wilson",
            action="Transaction History",
            ipAddress="10.0.1.200",
            timestamp="2026-04-29T11:30:19",
            duration="4m 15s",
        ),
        VisitorRecord(
            visitorId="VIS-006",
            accountNumber="1111111111",
            visitorName="Amanda Torres",
            action="Portfolio Inquiry",
            ipAddress="192.168.0.55",
            timestamp="2026-04-28T09:12:58",
            duration="1m 05s",
        ),
        VisitorRecord(
            visitorId="VIS-007",
            accountNumber="1234567890",
            visitorName="David Park",
            action="Transaction History",
            ipAddress="10.10.10.42",
            timestamp="2026-04-28T08:45:11",
            duration="6m 22s",
        ),
        VisitorRecord(
            visitorId="VIS-008",
            accountNumber="5555555555",
            visitorName="Lisa Martinez",
            action="Portfolio Inquiry",
            ipAddress="172.16.5.33",
            timestamp="2026-04-27T15:20:44",
            duration="2m 58s",
        ),
    ]

    return VisitorsHistoryResponse(
        totalVisits=len(visitors),
        visitors=visitors,
        lastUpdated=datetime.now().strftime("%B %d, %Y, %I:%M %p"),
    )


@router.get("/visitors/history", response_model=VisitorsHistoryResponse)
async def get_visitors_history():
    """Get history of all portfolio visitors"""
    return generate_mock_visitors()
