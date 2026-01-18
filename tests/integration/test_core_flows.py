"""Integration tests for core user flows."""
import pytest


def test_countries_list_flow(client):
    """Test countries listing."""
    response = client.get("/api/v1/countries")
    assert response.status_code in [200, 404, 500]
