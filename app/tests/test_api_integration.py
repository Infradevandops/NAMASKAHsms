"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient
from main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_register_user(self, client):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "Test123!@#",
                "username": "testuser"
            }
        )
        assert response.status_code in [200, 201, 409]

    @pytest.mark.asyncio
    async def test_login_user(self, client):
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        assert response.status_code in [200, 401]


class TestVerificationAPI:
    @pytest.mark.asyncio
    async def test_get_countries(self, client):
        response = await client.get("/api/countries/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_services(self, client):
        response = await client.get("/api/countries/US/services")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_create_verification(self, client):
        response = await client.post(
            "/api/verify/create",
            json={
                "country": "US",
                "service": "telegram"
            }
        )
        assert response.status_code in [200, 400, 401]


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
