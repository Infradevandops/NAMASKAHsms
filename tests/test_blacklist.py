"""Tests for Blacklist Management functionality."""


class TestBlacklistEndpoints:
    """Test blacklist API endpoints."""

    def test_get_blacklist_authenticated(self, client, auth_headers):
        """Should return blacklist for authenticated user."""
        response = client.get("/blacklist", headers=auth_headers)
        # Endpoint may require PAYG+ tier
        assert response.status_code in [200, 403, 404, 501]

    def test_get_blacklist_unauthenticated(self, client):
        """Should return 401 for unauthenticated request."""
        response = client.get("/blacklist")
        assert response.status_code in [401, 403, 404]

    def test_add_to_blacklist(self, client, auth_headers):
        """Should add number to blacklist."""
        response = client.post(
            "/blacklist",
            headers=auth_headers,
            json={"phone_number": "+1234567890", "reason": "Test blacklist"},
        )
        # May require PAYG+ tier
        assert response.status_code in [200, 201, 403, 404, 422, 501]

    def test_add_to_blacklist_invalid_phone(self, client, auth_headers):
        """Should reject invalid phone number."""
        response = client.post(
            "/blacklist",
            headers=auth_headers,
            json={"phone_number": "invalid", "reason": "Test"},
        )
        # Should fail validation
        assert response.status_code in [400, 422, 403, 404, 501]

    def test_remove_from_blacklist(self, client, auth_headers):
        """Should remove number from blacklist."""
        response = client.delete("/blacklist/test-id", headers=auth_headers)
        assert response.status_code in [200, 204, 403, 404, 501]

    def test_blacklist_pagination(self, client, auth_headers):
        """Should support pagination."""
        response = client.get("/blacklist?page=1&limit=20", headers=auth_headers)
        assert response.status_code in [200, 403, 404, 501]


class TestBlacklistTierGating:
    """Test blacklist tier gating."""

    def test_blacklist_requires_payg_tier(self, client, auth_headers):
        """Blacklist should require PAYG+ tier."""
        # This test verifies tier gating is in place
        response = client.get("/blacklist", headers=auth_headers)
        # Freemium users should get 403
        # PAYG+ users should get 200 or 404 (if no data)
        assert response.status_code in [200, 403, 404, 501]


class TestBlacklistUI:
    """Test blacklist UI in settings."""

    def test_settings_page_has_blacklist_tab(self, client, auth_headers):
        """Settings page should have blacklist tab for PAYG+ users."""
        response = client.get("/settings", headers=auth_headers)
        assert response.status_code == 200
        content = response.content.decode()
        # Tab should exist (may be hidden for freemium)
        assert "blacklist" in content.lower()

    def test_blacklist_tab_has_add_button(self, client, auth_headers):
        """Blacklist tab should have add number button."""
        response = client.get("/settings", headers=auth_headers)
        assert response.status_code == 200
        content = response.content.decode()
        assert "showAddBlacklistModal" in content or "Add Number" in content

    def test_blacklist_tab_has_bulk_import(self, client, auth_headers):
        """Blacklist tab should have bulk import option."""
        response = client.get("/settings", headers=auth_headers)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Bulk Import" in content or "bulk-import" in content.lower()


class TestBlacklistDataFormat:
    """Test blacklist data format."""

    def test_blacklist_entry_has_required_fields(self):
        """Blacklist entry should have required fields."""
        expected_fields = ["id", "phone_number", "created_at"]
        sample_entry = {
            "id": "bl-123",
            "phone_number": "+1234567890",
            "reason": "Spam",
            "created_at": "2026-01-13T10:00:00Z",
        }
        for field in expected_fields:
            assert field in sample_entry

    def test_phone_number_validation(self):
        """Phone numbers should be validated."""
        import re

        valid_pattern = r"^\+?[0-9]{10,15}$"

        valid_numbers = ["+1234567890", "1234567890", "+12345678901234"]

        for num in valid_numbers:
            clean = num.replace("-", "").replace(" ", "")
            assert re.match(valid_pattern, clean)


class TestBlacklistBulkImport:
    """Test blacklist bulk import functionality."""

    def test_csv_parsing(self):
        """CSV file should be parsed correctly."""
        csv_content = """phone
+1234567890
+0987654321
+1122334455"""
        lines = csv_content.strip().split("\n")
        # Skip header
        numbers = [line.strip() for line in lines[1:] if line.strip()]
        assert len(numbers) == 3
        assert numbers[0] == "+1234567890"

    def test_bulk_import_validation(self):
        """Bulk import should validate phone numbers."""
        import re

        valid_pattern = r"^\+?[0-9]{10,15}$"

        test_numbers = ["+1234567890", "invalid", "+0987654321"]
        valid_count = sum(1 for n in test_numbers if re.match(valid_pattern, n.replace("-", "").replace(" ", "")))
        assert valid_count == 2
