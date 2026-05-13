import pytest
from starlette.middleware.cors import CORSMiddleware

from app.main import app
import models
import services


class TestAppConfiguration:

    def test_app_title(self):
        assert app.title == "Portfolio Management API"

    def test_app_version(self):
        assert app.version == "1.0.0"

    def test_cors_middleware_present(self):
        middleware_classes = [m.cls for m in app.user_middleware if hasattr(m, 'cls')]
        assert CORSMiddleware in middleware_classes

    def test_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert "/healthz" in route_paths
        assert "/api/accounts/{account_number}/validate" in route_paths
        assert "/api/portfolio/{account_number}" in route_paths
        assert "/api/transactions/{account_number}" in route_paths


class TestModuleExports:

    def test_models_init_exports(self):
        expected = ["Portfolio", "Position", "Transaction", "History", "Base", "engine", "SessionLocal"]
        assert hasattr(models, "__all__")
        for name in expected:
            assert name in models.__all__

    def test_services_init_exports(self):
        expected = ["PortfolioService"]
        assert hasattr(services, "__all__")
        for name in expected:
            assert name in services.__all__
