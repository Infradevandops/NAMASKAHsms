"""Unit tests for TextVerified health check endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.main import app
from app.services.textverified_service import TextVerifiedService


client = TestClient(app)


class TestHealthCheckEndpoint:
    """Tests for the health check endpoint.
    
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
    """

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check response."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "operational",
                "balance": 100.50,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "operational"
            assert data["balance"] == 100.50
            assert data["currency"] == "USD"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_check_invalid_credentials(self):
        """Test health check with invalid credentials."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "error",
                "error": "TextVerified not configured",
                "balance": None,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data["detail"]

    @pytest.mark.asyncio
    async def test_health_check_service_unavailable(self):
        """Test health check when service is unavailable."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "error",
                "error": "Connection timeout",
                "balance": None,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 503
            data = response.json()
            assert "error" in data["detail"]

    @pytest.mark.asyncio
    async def test_health_check_response_structure(self):
        """Test that health check response has correct structure."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "operational",
                "balance": 50.25,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required fields
            assert "status" in data
            assert "balance" in data
            assert "currency" in data
            assert "timestamp" in data
            
            # Verify data types
            assert isinstance(data["status"], str)
            assert isinstance(data["balance"], (float, int))
            assert isinstance(data["currency"], str)
            assert isinstance(data["timestamp"], str)

    @pytest.mark.asyncio
    async def test_health_check_balance_is_numeric(self):
        """Test that balance is returned as numeric value."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "operational",
                "balance": 123.45,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["balance"], (float, int))
            assert data["balance"] == 123.45

    @pytest.mark.asyncio
    async def test_health_check_currency_is_usd(self):
        """Test that currency is always USD."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "operational",
                "balance": 100.0,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_health_check_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            timestamp = datetime.utcnow().isoformat()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "operational",
                "balance": 100.0,
                "currency": "USD",
                "timestamp": timestamp
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["timestamp"] == timestamp
            # Verify it's a valid ISO format
            datetime.fromisoformat(data["timestamp"])


class TestBalanceEndpoint:
    """Tests for the balance endpoint.
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.5
    """

    @pytest.mark.asyncio
    async def test_balance_endpoint_success(self):
        """Test successful balance retrieval."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_balance = AsyncMock(return_value={
                "balance": 100.50,
                "currency": "USD",
                "cached": False
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/balance")
            
            assert response.status_code == 200
            data = response.json()
            assert data["balance"] == 100.50
            assert data["currency"] == "USD"
            assert data["cached"] is False

    @pytest.mark.asyncio
    async def test_balance_endpoint_cached(self):
        """Test balance endpoint returns cached data."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_balance = AsyncMock(return_value={
                "balance": 100.50,
                "currency": "USD",
                "cached": True
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/balance")
            
            assert response.status_code == 200
            data = response.json()
            assert data["cached"] is True

    @pytest.mark.asyncio
    async def test_balance_endpoint_error(self):
        """Test balance endpoint error handling."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_balance = AsyncMock(side_effect=Exception("API Error"))
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/balance")
            
            assert response.status_code == 503
            data = response.json()
            assert "error" in data["detail"]

    @pytest.mark.asyncio
    async def test_balance_is_float(self):
        """Test that balance is returned as float."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_balance = AsyncMock(return_value={
                "balance": 50.25,
                "currency": "USD",
                "cached": False
            })
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/verification/textverified/balance")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["balance"], (float, int))
            assert data["balance"] == 50.25


class TestStatusEndpoint:
    """Tests for the status endpoint (legacy)."""

    def test_status_endpoint(self):
        """Test status endpoint returns operational."""
        response = client.get("/api/verification/textverified/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
