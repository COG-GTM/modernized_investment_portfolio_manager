"""Tests for account validation API endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAccountValidation:
    """Tests for GET /api/accounts/{account_number}/validate"""

    def test_validate_valid_account(self):
        response = client.get("/api/accounts/1234567890/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_short_account(self):
        response = client.get("/api/accounts/12345/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_validate_non_numeric(self):
        response = client.get("/api/accounts/abcdefghij/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_validate_all_zeros(self):
        response = client.get("/api/accounts/0000000000/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_validate_empty_account(self):
        response = client.get("/api/accounts//validate")
        assert response.status_code in (404, 307)

    def test_validate_long_account(self):
        response = client.get("/api/accounts/12345678901/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
