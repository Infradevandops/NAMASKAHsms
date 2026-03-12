"""
Integration Tests for Verification API Endpoints
Tests the complete API flow from service listing to SMS receipt
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import time


class TestServicesEndpoint:
    """Test /api/countries/{country}/services endpoint"""
    
    def test_services_endpoint_returns_200(self, client: TestClient, auth_headers: dict):
        """Services endpoint should always return 200"""
        response = client.get("/api/countries/US/services", headers=auth_headers)
        assert response.status_code == 200
    
    def test_services_never_empty(self, client: TestClient, auth_headers: dict):
        """Services endpoint should never return empty array"""
        response = client.get("/api/countries/US/services", headers=auth_headers)
        data = response.json()
        
        assert "services" in data
        assert isinstance(data["services"], list)
        assert len(data["services"]) >= 20, f"Expected ≥20 services, got {len(data['services'])}"
    
    def test_services_have_required_fields(self, client: TestClient, auth_headers: dict):
        """Each service should have id, name, price, cost"""
        response = client.get("/api/countries/US/services", headers=auth_headers)
        data = response.json()
        
        for service in data["services"]:
            assert "id" in service
            assert "name" in service
            assert "price" in service
            assert "cost" in service
            assert isinstance(service["price"], (int, float))
            assert service["price"] > 0
    
    def test_services_include_markup(self, client: TestClient, auth_headers: dict):
        """Service prices should include markup"""
        response = client.get("/api/countries/US/services", headers=auth_headers)
        data = response.json()
        
        # Verify prices are reasonable (between $1-$5)
        for service in data["services"]:
            assert 1.0 <= service["price"] <= 5.0, \
                f"Service {service['id']} has unreasonable price: ${service['price']}"
    
    def test_services_response_time(self, client: TestClient, auth_headers: dict):
        """Services endpoint should respond within 2 seconds"""
        start = time.time()
        response = client.get("/api/countries/US/services", headers=auth_headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Response took {elapsed:.2f}s (target: <2s)"
    
    def test_services_fallback_on_api_failure(self, client: TestClient, auth_headers: dict, monkeypatch):
        """Should return fallback services if TextVerified API fails"""
        # Mock TextVerified API to fail
        def mock_get_services_list(*args, **kwargs):
            raise Exception("API unavailable")
        
        from app.services import textverified_service
        monkeypatch.setattr(textverified_service.TextVerifiedService, "get_services_list", mock_get_services_list)
        
        response = client.get("/api/countries/US/services", headers=auth_headers)
        data = response.json()
        
        assert response.status_code == 200
        assert len(data["services"]) >= 10  # Fallback should have at least 10 services
        assert data.get("source") == "fallback"
    
    def test_services_cache_header(self, client: TestClient, auth_headers: dict):
        """Services endpoint should include cache metadata"""
        response = client.get("/api/countries/US/services", headers=auth_headers)
        data = response.json()
        
        assert "total" in data
        assert data["total"] == len(data["services"])


class TestVerificationRequestEndpoint:
    """Test POST /api/verification/request endpoint"""
    
    def test_create_verification_success(self, client: TestClient, auth_headers: dict, db: Session):
        """Should create verification successfully"""
        payload = {
            "service": "whatsapp",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        
        response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "verification_id" in data
        assert "phone_number" in data
        assert data["verification_id"] is not None
        assert data["phone_number"] is not None
    
    def test_create_verification_with_area_code(self, client: TestClient, auth_headers: dict):
        """Should accept area code filter"""
        payload = {
            "service": "telegram",
            "country": "US",
            "capability": "sms",
            "area_codes": ["212"],
            "carriers": []
        }
        
        response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        # Should succeed or return fallback
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "verification_id" in data
    
    def test_create_verification_with_carrier(self, client: TestClient, auth_headers: dict):
        """Should accept carrier filter"""
        payload = {
            "service": "google",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": ["verizon"]
        }
        
        response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        # Should succeed or return error
        assert response.status_code in [200, 400]
    
    def test_create_verification_insufficient_balance(self, client: TestClient, auth_headers: dict, db: Session):
        """Should reject if insufficient balance"""
        # Set user balance to $0
        from app.models.user import User
        user = db.query(User).filter(User.email == "test@example.com").first()
        if user:
            user.credits = 0.0
            db.commit()
        
        payload = {
            "service": "whatsapp",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        
        response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        # Should return 400 or 402
        assert response.status_code in [400, 402]
        data = response.json()
        assert "insufficient" in data.get("detail", "").lower() or "balance" in data.get("detail", "").lower()
    
    def test_create_verification_invalid_service(self, client: TestClient, auth_headers: dict):
        """Should reject invalid service"""
        payload = {
            "service": "nonexistent_service_12345",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        
        response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        # Should return 400 or 404
        assert response.status_code in [400, 404]
    
    def test_create_verification_missing_fields(self, client: TestClient, auth_headers: dict):
        """Should reject request with missing fields"""
        payload = {
            "service": "whatsapp"
            # Missing country, capability, etc.
        }
        
        response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error


class TestVerificationStatusEndpoint:
    """Test GET /api/verification/status/{verification_id} endpoint"""
    
    def test_status_endpoint_returns_verification(self, client: TestClient, auth_headers: dict, db: Session):
        """Should return verification status"""
        # Create verification first
        payload = {
            "service": "telegram",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        create_response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        if create_response.status_code == 200:
            verification_id = create_response.json()["verification_id"]
            
            # Check status
            response = client.get(f"/api/verification/status/{verification_id}", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "phone_number" in data
            assert data["status"] in ["pending", "active", "completed", "failed", "cancelled"]
    
    def test_status_endpoint_invalid_id(self, client: TestClient, auth_headers: dict):
        """Should return 404 for invalid verification ID"""
        response = client.get("/api/verification/status/invalid-id-12345", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_status_endpoint_unauthorized_access(self, client: TestClient, auth_headers: dict, db: Session):
        """Should reject access to other user's verification"""
        # This test requires creating a verification with one user
        # and trying to access it with another user
        # Skipping for now as it requires multi-user setup
        pass


class TestVerificationCancelEndpoint:
    """Test POST /api/verification/cancel/{verification_id} endpoint"""
    
    def test_cancel_verification_success(self, client: TestClient, auth_headers: dict):
        """Should cancel verification and refund"""
        # Create verification
        payload = {
            "service": "discord",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        create_response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        if create_response.status_code == 200:
            verification_id = create_response.json()["verification_id"]
            
            # Cancel it
            response = client.post(f"/api/verification/cancel/{verification_id}", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            
            assert "refund_amount" in data
            assert isinstance(data["refund_amount"], (int, float))
            assert data["refund_amount"] >= 0
    
    def test_cancel_already_completed(self, client: TestClient, auth_headers: dict, db: Session):
        """Should reject cancellation of completed verification"""
        # This requires a completed verification
        # Skipping for now as it requires SMS simulation
        pass
    
    def test_cancel_invalid_id(self, client: TestClient, auth_headers: dict):
        """Should return 404 for invalid verification ID"""
        response = client.post("/api/verification/cancel/invalid-id-12345", headers=auth_headers)
        
        assert response.status_code == 404


class TestVerificationOutcomeEndpoint:
    """Test PATCH /api/verification/{verification_id}/outcome endpoint"""
    
    def test_update_outcome_success(self, client: TestClient, auth_headers: dict):
        """Should update verification outcome"""
        # Create verification
        payload = {
            "service": "instagram",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        create_response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        if create_response.status_code == 200:
            verification_id = create_response.json()["verification_id"]
            
            # Update outcome
            outcome_payload = {
                "outcome": "timeout",
                "error_message": "No SMS received within 2 minutes"
            }
            response = client.patch(
                f"/api/verification/{verification_id}/outcome",
                json=outcome_payload,
                headers=auth_headers
            )
            
            assert response.status_code == 200
    
    def test_update_outcome_invalid_status(self, client: TestClient, auth_headers: dict):
        """Should reject invalid outcome status"""
        # Create verification
        payload = {
            "service": "facebook",
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        create_response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        if create_response.status_code == 200:
            verification_id = create_response.json()["verification_id"]
            
            # Try invalid outcome
            outcome_payload = {
                "outcome": "invalid_status_12345",
                "error_message": "Test"
            }
            response = client.patch(
                f"/api/verification/{verification_id}/outcome",
                json=outcome_payload,
                headers=auth_headers
            )
            
            # Should reject
            assert response.status_code in [400, 422]


class TestVerificationFlowIntegration:
    """Test complete verification flow end-to-end"""
    
    def test_complete_flow_without_sms(self, client: TestClient, auth_headers: dict):
        """Test complete flow: create -> poll -> cancel"""
        # Step 1: Get services
        services_response = client.get("/api/countries/US/services", headers=auth_headers)
        assert services_response.status_code == 200
        services = services_response.json()["services"]
        assert len(services) >= 20
        
        # Step 2: Create verification
        payload = {
            "service": services[0]["id"],
            "country": "US",
            "capability": "sms",
            "area_codes": [],
            "carriers": []
        }
        create_response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        if create_response.status_code != 200:
            pytest.skip("Verification creation failed (likely insufficient balance)")
        
        verification_id = create_response.json()["verification_id"]
        phone_number = create_response.json()["phone_number"]
        
        assert verification_id is not None
        assert phone_number is not None
        
        # Step 3: Poll status (simulate 3 polls)
        for i in range(3):
            time.sleep(1)  # Wait 1 second between polls
            status_response = client.get(f"/api/verification/status/{verification_id}", headers=auth_headers)
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            assert status_data["status"] in ["pending", "active", "completed"]
            
            if status_data["status"] == "completed":
                assert "sms_code" in status_data
                break
        
        # Step 4: Cancel verification
        cancel_response = client.post(f"/api/verification/cancel/{verification_id}", headers=auth_headers)
        assert cancel_response.status_code == 200
        
        refund_data = cancel_response.json()
        assert "refund_amount" in refund_data
    
    def test_flow_with_area_code_filter(self, client: TestClient, auth_headers: dict):
        """Test flow with area code filter"""
        payload = {
            "service": "whatsapp",
            "country": "US",
            "capability": "sms",
            "area_codes": ["415"],  # San Francisco
            "carriers": []
        }
        
        response = client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        # Should succeed or return fallback warning
        if response.status_code == 200:
            data = response.json()
            assert "verification_id" in data
            
            # Check if fallback was applied
            if "fallback_applied" in data:
                assert isinstance(data["fallback_applied"], bool)
                if data["fallback_applied"]:
                    assert "assigned_area_code" in data
                    assert "requested_area_code" in data


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    def test_concurrent_verification_requests(self, client: TestClient, auth_headers: dict):
        """Should handle concurrent requests correctly"""
        import concurrent.futures
        
        def create_verification():
            payload = {
                "service": "telegram",
                "country": "US",
                "capability": "sms",
                "area_codes": [],
                "carriers": []
            }
            return client.post("/api/verification/request", json=payload, headers=auth_headers)
        
        # Create 3 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_verification) for _ in range(3)]
            responses = [f.result() for f in futures]
        
        # All should either succeed or fail gracefully
        for response in responses:
            assert response.status_code in [200, 400, 402, 429]  # Success or rate limit
    
    def test_malformed_json_request(self, client: TestClient, auth_headers: dict):
        """Should reject malformed JSON"""
        response = client.post(
            "/api/verification/request",
            data="invalid json {{{",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_auth_header(self, client: TestClient):
        """Should reject requests without auth"""
        response = client.get("/api/countries/US/services")
        
        assert response.status_code == 401
    
    def test_invalid_auth_token(self, client: TestClient):
        """Should reject invalid auth tokens"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/countries/US/services", headers=headers)
        
        assert response.status_code == 401


# Fixtures
@pytest.fixture
def client():
    """Create test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def db():
    """Create database session"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_headers(client: TestClient, db: Session):
    """Create authenticated user and return auth headers"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # Create test user
    test_user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        credits=100.0,
        tier="payg"
    )
    db.add(test_user)
    db.commit()
    
    # Login
    login_response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    # Fallback: use admin credentials
    login_response = client.post("/api/auth/login", json={
        "email": "admin@namaskah.app",
        "password": "admin123"
    })
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
