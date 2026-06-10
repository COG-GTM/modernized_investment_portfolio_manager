import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestValidateAccount:

    async def test_validate_returns_bypassed(self, client):
        async with client as c:
            resp = await c.get("/api/accounts/1234567890/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["message"] == "Validation bypassed"

    async def test_validate_any_input_bypassed(self, client):
        async with client as c:
            resp = await c.get("/api/accounts/invalid/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True


@pytest.mark.asyncio
class TestHealthz:

    async def test_healthz(self, client):
        async with client as c:
            resp = await c.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
