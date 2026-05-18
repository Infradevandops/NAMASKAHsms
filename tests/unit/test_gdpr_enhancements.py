"""Tests for GDPR enhancements (CSV/PDF export, consent management)"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.models.user import User
from main import app

client = TestClient(app)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id="test_user_gdpr",
        email="gdpr@test.com",
        hashed_password="hashed",
        credits=100.0,
        subscription_tier="pro",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create auth headers for test user"""
    # Mock the authentication
    from app.core.dependencies import get_current_user_id

    def override_get_current_user_id():
        return test_user.id

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    yield {"Authorization": "Bearer test_token"}
    app.dependency_overrides.clear()


class TestGDPRExportFormats:
    """Test GDPR export in multiple formats"""

    def test_export_json_format(self, auth_headers):
        """Test exporting user data in JSON format"""
        response = client.get("/api/gdpr/export?format=json", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "verifications" in data
        assert "audit_logs" in data
        assert "export_date" in data

    def test_export_csv_format(self, auth_headers):
        """Test exporting user data in CSV format"""
        response = client.get("/api/gdpr/export?format=csv", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]

    def test_export_pdf_format(self, auth_headers):
        """Test exporting user data in PDF format"""
        response = client.get("/api/gdpr/export?format=pdf", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert ".pdf" in response.headers["content-disposition"]

    def test_export_invalid_format_returns_error(self, auth_headers):
        """Test that invalid format returns validation error"""
        response = client.get("/api/gdpr/export?format=xml", headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_export_default_format_is_json(self, auth_headers):
        """Test that default format is JSON"""
        response = client.get("/api/gdpr/export", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "user" in data


class TestGDPRConsentManagement:
    """Test GDPR consent management"""

    def test_get_consent_returns_preferences(self, auth_headers):
        """Test getting user consent preferences"""
        response = client.get("/api/gdpr/consent", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "marketing_emails" in data
        assert "analytics_tracking" in data
        assert "data_sharing" in data
        assert "updated_at" in data

    def test_update_consent_marketing_emails(self, auth_headers):
        """Test updating marketing emails consent"""
        response = client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={"marketing_emails": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["marketing_emails"] is False

    def test_update_consent_analytics_tracking(self, auth_headers):
        """Test updating analytics tracking consent"""
        response = client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={"analytics_tracking": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["analytics_tracking"] is False

    def test_update_consent_data_sharing(self, auth_headers):
        """Test updating data sharing consent"""
        response = client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={"data_sharing": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data_sharing"] is True

    def test_update_multiple_consents(self, auth_headers):
        """Test updating multiple consent preferences at once"""
        response = client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={
                "marketing_emails": False,
                "analytics_tracking": False,
                "data_sharing": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["marketing_emails"] is False
        assert data["analytics_tracking"] is False
        assert data["data_sharing"] is False

    def test_update_consent_partial_update(self, auth_headers):
        """Test partial consent update (only some fields)"""
        response = client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={"marketing_emails": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert "analytics_tracking" in data  # Other fields still present


class TestGDPRRetentionPolicy:
    """Test GDPR retention policy endpoint"""

    def test_get_retention_policy_returns_info(self):
        """Test getting retention policy information"""
        response = client.get("/api/gdpr/retention-policy")

        assert response.status_code == 200
        data = response.json()
        assert "policy" in data
        assert "deletion_schedule" in data
        assert "last_updated" in data

    def test_retention_policy_includes_user_data(self):
        """Test retention policy includes user data category"""
        response = client.get("/api/gdpr/retention-policy")

        data = response.json()
        assert "user_data" in data["policy"]
        assert "retention_period" in data["policy"]["user_data"]
        assert "categories" in data["policy"]["user_data"]

    def test_retention_policy_includes_verification_data(self):
        """Test retention policy includes verification data category"""
        response = client.get("/api/gdpr/retention-policy")

        data = response.json()
        assert "verification_data" in data["policy"]
        assert "90 days" in data["policy"]["verification_data"]["retention_period"]

    def test_retention_policy_includes_transaction_data(self):
        """Test retention policy includes transaction data category"""
        response = client.get("/api/gdpr/retention-policy")

        data = response.json()
        assert "transaction_data" in data["policy"]
        assert "7 years" in data["policy"]["transaction_data"]["retention_period"]

    def test_retention_policy_includes_audit_logs(self):
        """Test retention policy includes audit logs category"""
        response = client.get("/api/gdpr/retention-policy")

        data = response.json()
        assert "audit_logs" in data["policy"]
        assert "1 year" in data["policy"]["audit_logs"]["retention_period"]

    def test_retention_policy_includes_deletion_schedule(self):
        """Test retention policy includes deletion schedule"""
        response = client.get("/api/gdpr/retention-policy")

        data = response.json()
        assert "automated" in data["deletion_schedule"]
        assert "manual" in data["deletion_schedule"]


class TestAcceptanceCriteria:
    """Test acceptance criteria for GDPR enhancements"""

    def test_ac1_users_can_export_data_in_json_csv_pdf(self, auth_headers):
        """AC-1: Users can export data in JSON/CSV/PDF"""
        # Test JSON
        json_response = client.get("/api/gdpr/export?format=json", headers=auth_headers)
        assert json_response.status_code == 200
        assert isinstance(json_response.json(), dict)

        # Test CSV
        csv_response = client.get("/api/gdpr/export?format=csv", headers=auth_headers)
        assert csv_response.status_code == 200
        assert "text/csv" in csv_response.headers["content-type"]

        # Test PDF
        pdf_response = client.get("/api/gdpr/export?format=pdf", headers=auth_headers)
        assert pdf_response.status_code == 200
        assert "application/pdf" in pdf_response.headers["content-type"]

    def test_ac2_users_can_manage_consent_preferences(self, auth_headers):
        """AC-2: Users can manage consent preferences"""
        # Get current consent
        get_response = client.get("/api/gdpr/consent", headers=auth_headers)
        assert get_response.status_code == 200

        # Update consent
        update_response = client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={"marketing_emails": False, "analytics_tracking": False},
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["marketing_emails"] is False
        assert data["analytics_tracking"] is False

    def test_ac3_data_retention_policy_is_visible(self):
        """AC-3: Data retention policy is visible"""
        response = client.get("/api/gdpr/retention-policy")

        assert response.status_code == 200
        data = response.json()

        # Verify all required sections are present
        assert "policy" in data
        assert "user_data" in data["policy"]
        assert "verification_data" in data["policy"]
        assert "transaction_data" in data["policy"]
        assert "audit_logs" in data["policy"]
        assert "deletion_schedule" in data


class TestCSVExportContent:
    """Test CSV export content structure"""

    def test_csv_export_includes_user_data(self, auth_headers):
        """Test CSV export includes user data section"""
        response = client.get("/api/gdpr/export?format=csv", headers=auth_headers)

        assert response.status_code == 200
        content = response.text
        assert "User Data" in content
        assert "Field" in content
        assert "Value" in content

    def test_csv_export_includes_verifications(self, auth_headers):
        """Test CSV export includes verifications section"""
        response = client.get("/api/gdpr/export?format=csv", headers=auth_headers)

        assert response.status_code == 200
        content = response.text
        assert "Verifications" in content

    def test_csv_export_includes_audit_logs(self, auth_headers):
        """Test CSV export includes audit logs section"""
        response = client.get("/api/gdpr/export?format=csv", headers=auth_headers)

        assert response.status_code == 200
        content = response.text
        assert "Audit Logs" in content


class TestPDFExportContent:
    """Test PDF export content structure"""

    def test_pdf_export_includes_header(self, auth_headers):
        """Test PDF export includes header"""
        response = client.get("/api/gdpr/export?format=pdf", headers=auth_headers)

        assert response.status_code == 200
        content = response.text
        assert "USER DATA EXPORT" in content

    def test_pdf_export_includes_user_information(self, auth_headers):
        """Test PDF export includes user information"""
        response = client.get("/api/gdpr/export?format=pdf", headers=auth_headers)

        assert response.status_code == 200
        content = response.text
        assert "User Information:" in content

    def test_pdf_export_includes_export_date(self, auth_headers):
        """Test PDF export includes export date"""
        response = client.get("/api/gdpr/export?format=pdf", headers=auth_headers)

        assert response.status_code == 200
        content = response.text
        assert "Export Date:" in content


class TestConsentPersistence:
    """Test consent preferences persistence"""

    def test_consent_persists_after_update(self, auth_headers):
        """Test that consent preferences persist after update"""
        # Update consent
        client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={"marketing_emails": False},
        )

        # Get consent again
        response = client.get("/api/gdpr/consent", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["marketing_emails"] is False

    def test_consent_update_timestamp_changes(self, auth_headers):
        """Test that updated_at timestamp changes on update"""
        # Get initial timestamp
        initial_response = client.get("/api/gdpr/consent", headers=auth_headers)
        initial_timestamp = initial_response.json()["updated_at"]

        # Update consent
        import time

        time.sleep(0.1)  # Ensure timestamp difference

        client.put(
            "/api/gdpr/consent",
            headers=auth_headers,
            json={"marketing_emails": False},
        )

        # Get new timestamp
        updated_response = client.get("/api/gdpr/consent", headers=auth_headers)
        updated_timestamp = updated_response.json()["updated_at"]

        # Timestamps should be different
        assert updated_timestamp != initial_timestamp
