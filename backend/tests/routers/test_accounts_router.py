import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestValidateAccountEndpoint:

    @pytest.mark.asyncio
    async def test_validate_account_returns_200(self, client):
        async with client as c:
            response = await c.get("/api/accounts/1234567890/validate")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_validate_account_bypassed(self, client):
        async with client as c:
            response = await c.get("/api/accounts/anything/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["message"] == "Validation bypassed"

    @pytest.mark.asyncio
    async def test_validate_account_empty_string(self, client):
        async with client as c:
            response = await c.get("/api/accounts//validate")
        # Empty string path segment may result in 404 or redirect
        assert response.status_code in [200, 307, 404]
