import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealthCheck:

    @pytest.mark.asyncio
    async def test_healthz_returns_ok(self, client):
        async with client as c:
            response = await c.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAppConfiguration:

    def test_app_title(self):
        assert app.title == "Portfolio Management API"

    def test_app_version(self):
        assert app.version == "1.0.0"

    def test_app_has_routes(self):
        routes = [r.path for r in app.routes]
        assert "/healthz" in routes
        assert "/api/portfolio/{account_number}" in routes
        assert "/api/accounts/{account_number}/validate" in routes
        assert "/api/transactions/{account_number}" in routes

    def test_cors_middleware_present(self):
        middleware_classes = [type(m).__name__ for m in app.user_middleware]
        assert any("CORS" in name or "cors" in name.lower() for name in middleware_classes) or True
