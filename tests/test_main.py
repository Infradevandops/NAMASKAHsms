"""Test main application routes."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


def test_landing_page_anonymous(client):
    """Test that the landing page is served for anonymous users."""
    response = client.get("/")
    assert response.status_code == 200
    assert "SMS Verification Made Simple & Secure" in response.text
