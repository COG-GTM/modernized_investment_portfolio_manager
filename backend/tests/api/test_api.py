"""
Tests for the Portfolio Inquiry REST API.

Tests cover all endpoints migrated from the COBOL CICS online inquiry system:
- Auth (SECMGR) - login, token validation
- Portfolio (INQPORT) - summary, positions
- History (INQHIST) - paginated transaction history
- Health (DB2ONLN) - status check
- Error handling (ERRHNDL) - error responses
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, time, datetime
from decimal import Decimal

from app.api.main import create_api_app
from app.api.dependencies import get_db
from models.database import Base, Portfolio, Position
from models.transactions import Transaction


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_URL = "sqlite:///./test_api.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def app():
    """Create test app with overridden DB dependency."""
    application = create_api_app()
    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture(scope="module")
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create tables and seed test data."""
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        # Create test portfolio
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_name="Test Client",
            client_type="I",
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            status="A",
            total_value=Decimal("125000.00"),
            cash_balance=Decimal("5000.00"),
            last_user="SYSTEM",
            last_trans="INIT0001",
        )
        db.add(portfolio)

        # Create test positions
        positions = [
            Position(
                portfolio_id="PORT0001",
                date=date(2024, 6, 1),
                investment_id="AAPL000001",
                quantity=Decimal("150.0000"),
                cost_basis=Decimal("25500.00"),
                market_value=Decimal("27787.50"),
                currency="USD",
                status="A",
                last_maint_date=datetime(2024, 6, 1),
                last_maint_user="SYSTEM",
            ),
            Position(
                portfolio_id="PORT0001",
                date=date(2024, 6, 1),
                investment_id="MSFT000001",
                quantity=Decimal("100.0000"),
                cost_basis=Decimal("34000.00"),
                market_value=Decimal("37885.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime(2024, 6, 1),
                last_maint_user="SYSTEM",
            ),
            Position(
                portfolio_id="PORT0001",
                date=date(2024, 6, 1),
                investment_id="CLOSED0001",
                quantity=Decimal("0.0000"),
                cost_basis=Decimal("0.00"),
                market_value=Decimal("0.00"),
                currency="USD",
                status="C",
                last_maint_date=datetime(2024, 5, 1),
                last_maint_user="SYSTEM",
            ),
        ]
        db.add_all(positions)

        # Create test transactions
        transactions = [
            Transaction(
                date=date(2024, 5, 15),
                time=time(10, 30, 0),
                portfolio_id="PORT0001",
                sequence_no="000001",
                investment_id="AAPL000001",
                type="BU",
                quantity=Decimal("50.0000"),
                price=Decimal("170.0000"),
                amount=Decimal("8500.00"),
                currency="USD",
                status="D",
                process_date=datetime(2024, 5, 15, 10, 30),
                process_user="SYSTEM",
            ),
            Transaction(
                date=date(2024, 6, 1),
                time=time(14, 0, 0),
                portfolio_id="PORT0001",
                sequence_no="000002",
                investment_id="MSFT000001",
                type="BU",
                quantity=Decimal("25.0000"),
                price=Decimal("378.8500"),
                amount=Decimal("9471.25"),
                currency="USD",
                status="D",
                process_date=datetime(2024, 6, 1, 14, 0),
                process_user="SYSTEM",
            ),
            Transaction(
                date=date(2024, 6, 10),
                time=time(9, 15, 0),
                portfolio_id="PORT0001",
                sequence_no="000003",
                investment_id="AAPL000001",
                type="SL",
                quantity=Decimal("10.0000"),
                price=Decimal("185.2500"),
                amount=Decimal("1852.50"),
                currency="USD",
                status="D",
                process_date=datetime(2024, 6, 10, 9, 15),
                process_user="SYSTEM",
            ),
        ]
        db.add_all(transactions)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("./test_api.db"):
        os.remove("./test_api.db")


def get_auth_token(client: TestClient) -> str:
    """Helper to get an auth token for protected endpoints."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# Auth tests (SECMGR)
# ---------------------------------------------------------------------------

class TestAuth:
    """Tests for auth endpoints — replaces SECMGR validation."""

    def test_login_success(self, client):
        """Test successful login — SECMGR SEC-RESPONSE-CODE = 0."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == "admin"
        assert "admin" in data["roles"]

    def test_login_invalid_password(self, client):
        """Test failed login — SECMGR SEC-RESPONSE-CODE = 8."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_invalid_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )
        assert response.status_code == 401

    def test_login_analyst_role(self, client):
        """Test analyst user gets correct roles."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "analyst", "password": "analyst"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_read" in data["roles"]
        assert "history_read" in data["roles"]
        assert "admin" not in data["roles"]


# ---------------------------------------------------------------------------
# Portfolio tests (INQPORT)
# ---------------------------------------------------------------------------

class TestPortfolio:
    """Tests for portfolio endpoints — replaces INQPORT."""

    def test_get_portfolio_summary(self, client):
        """Test portfolio summary — INQPORT successful position read."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_id"] == "PORT0001"
        assert data["account_number"] == "1234567890"
        assert data["client_name"] == "Test Client"
        assert data["status"] == "A"
        assert data["total_value"] == 125000.0

    def test_get_portfolio_not_found(self, client):
        """Test portfolio not found — INQPORT P900-NOT-FOUND."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/NOTFOUND",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_get_portfolio_positions(self, client):
        """Test portfolio positions — INQPORT full position display."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/positions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_id"] == "PORT0001"
        assert data["total_positions"] == 3
        assert len(data["positions"]) == 3
        assert data["total_market_value"] > 0

    def test_get_portfolio_positions_filter_status(self, client):
        """Test position filtering by status."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/positions?status=A",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_positions"] == 2
        for pos in data["positions"]:
            assert pos["status"] == "A"

    def test_get_portfolio_positions_filter_investment(self, client):
        """Test position filtering by investment ID."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/positions?investment_id=AAPL000001",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_positions"] == 1
        assert data["positions"][0]["investment_id"] == "AAPL000001"

    def test_get_positions_not_found(self, client):
        """Test positions for non-existent portfolio."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/NOTFOUND/positions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_portfolio_requires_auth(self, client):
        """Test that portfolio endpoints require authentication."""
        response = client.get("/api/v1/portfolios/PORT0001")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# History tests (INQHIST + CURSMGR)
# ---------------------------------------------------------------------------

class TestHistory:
    """Tests for history endpoints — replaces INQHIST + CURSMGR."""

    def test_get_transaction_history(self, client):
        """Test basic history retrieval — INQHIST P200-GET-HISTORY."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_id"] == "PORT0001"
        assert len(data["transactions"]) == 3
        assert "pagination" in data

    def test_history_pagination(self, client):
        """Test pagination — replaces CURSMGR array fetch + PF7/PF8 scrolling."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/history?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 2
        assert data["pagination"]["total_count"] == 3
        assert data["pagination"]["total_pages"] == 2
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is False

    def test_history_pagination_page2(self, client):
        """Test second page of history."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/history?page=2&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 1
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_previous"] is True

    def test_history_filter_by_type(self, client):
        """Test filtering by transaction type."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/history?type=BU",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 2
        for txn in data["transactions"]:
            assert txn["transaction_type"] == "BU"

    def test_history_not_found(self, client):
        """Test history for non-existent portfolio."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/NOTFOUND/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_history_requires_auth(self, client):
        """Test that history endpoints require authentication."""
        response = client.get("/api/v1/portfolios/PORT0001/history")
        assert response.status_code == 401

    def test_history_ordering(self, client):
        """Test that history is ordered by date descending (matching COBOL ORDER BY)."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/PORT0001/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        dates = [t["transaction_date"] for t in data["transactions"]]
        assert dates == sorted(dates, reverse=True)


# ---------------------------------------------------------------------------
# Health check tests (DB2ONLN status)
# ---------------------------------------------------------------------------

class TestHealth:
    """Tests for health endpoint — replaces DB2ONLN P300-CHECK-STATUS."""

    def test_health_check(self, client):
        """Test health check — DB2ONLN SQLCODE = 0."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Error handling tests (ERRHNDL)
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling — replaces ERRHNDL."""

    def test_not_found_error_format(self, client):
        """Test 404 error response includes trace_id — ERRHNDL ERR-TRACE-ID."""
        token = get_auth_token(client)
        response = client.get(
            "/api/v1/portfolios/NOTEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "trace_id" in data["error"]
        assert "code" in data["error"]
        assert "message" in data["error"]

    def test_unauthorized_error(self, client):
        """Test 401 error with invalid token."""
        response = client.get(
            "/api/v1/portfolios/PORT0001",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
