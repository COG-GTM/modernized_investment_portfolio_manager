import pytest


class TestValidateAccount:
    def test_valid_account_number(self, client):
        response = client.get("/api/accounts/1234567890/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["message"] == "Valid account number"

    def test_too_short_account_number(self, client):
        response = client.get("/api/accounts/123/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_non_numeric_account_number(self, client):
        response = client.get("/api/accounts/abcdefghij/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_all_zeros_account_number(self, client):
        response = client.get("/api/accounts/0000000000/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_too_long_account_number(self, client):
        response = client.get("/api/accounts/12345678901/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
