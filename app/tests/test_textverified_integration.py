"""Integration tests for TextVerified service.

These tests verify the complete integration of TextVerified service
with the application context.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime
import os


class TestTextVerifiedIntegration:
    """Integration tests for TextVerified service in application context.
    
    Validates: All Requirements
    """

    def test_service_initialization_in_app_context(self):
        """Test service initializes correctly in application context."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_tv.TextVerified = MagicMock()
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                assert service is not None
                assert service.api_key == 'test_key'
                assert service.api_username == 'test@example.com'

    def test_health_endpoint_integration(self):
        """Test health check endpoint in application context."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "operational",
                "balance": 50.0,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "operational"

    def test_balance_endpoint_integration(self):
        """Test balance endpoint in application context."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_balance = AsyncMock(return_value={
                "balance": 75.25,
                "currency": "USD",
                "cached": False
            })
            mock_service_class.return_value = mock_service
            
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/verification/textverified/balance")
            
            assert response.status_code == 200
            data = response.json()
            assert data["balance"] == 75.25

    def test_error_handling_integration(self):
        """Test error handling in application context."""
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
            
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/verification/textverified/health")
            
            assert response.status_code == 503


class TestTextVerifiedEndToEnd:
    """End-to-end tests for TextVerified integration.
    
    Validates: All Requirements
    """

    def test_complete_health_check_flow(self):
        """Test complete flow from request to response."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_health_status = AsyncMock(return_value={
                "status": "operational",
                "balance": 100.0,
                "currency": "USD",
                "timestamp": datetime.utcnow().isoformat()
            })
            mock_service_class.return_value = mock_service
            
            from app.main import app
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/verification/textverified/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required fields
            assert "status" in data
            assert "balance" in data
            assert "currency" in data
            assert "timestamp" in data
            
            # Verify data types
            assert isinstance(data["status"], str)
            assert isinstance(data["balance"], (int, float))
            assert isinstance(data["currency"], str)
            assert isinstance(data["timestamp"], str)

    def test_error_scenario_end_to_end(self):
        """Test error scenario from request to response."""
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_balance = AsyncMock(side_effect=Exception("Service unavailable"))
            mock_service_class.return_value = mock_service
            
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/verification/textverified/balance")
            
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]

    def test_status_endpoint_always_works(self):
        """Test status endpoint works regardless of service state."""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/verification/textverified/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
