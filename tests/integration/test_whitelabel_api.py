"""Integration tests for Whitelabel API endpoints"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.whitelabel_models import WhitelabelBranding, WhitelabelDomain
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def pro_user_token(client):
    """Create a Pro tier user and return auth token"""
    # Mock user creation and login
    with patch("app.api.core.auth.get_current_user") as mock_auth:
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "pro@example.com"
        mock_user.subscription_tier = "pro"
        mock_auth.return_value = mock_user
        yield "mock-token-pro"


@pytest.fixture
def freemium_user_token(client):
    """Create a Freemium tier user and return auth token"""
    with patch("app.api.core.auth.get_current_user") as mock_auth:
        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.email = "free@example.com"
        mock_user.subscription_tier = "freemium"
        mock_auth.return_value = mock_user
        yield "mock-token-free"


class TestWhitelabelSetup:
    """Test domain setup endpoint"""

    def test_setup_domain_success(self, client, pro_user_token):
        with patch(
            "app.services.whitelabel_service.whitelabel_service.create_domain"
        ) as mock_create:
            mock_domain = Mock(spec=WhitelabelDomain)
            mock_domain.id = 1
            mock_domain.domain = "example.com"
            mock_domain.verification_token = "test-token"
            mock_domain.verification_method = "txt_record"
            mock_domain.verified = False
            mock_create.return_value = (mock_domain, None)

            response = client.post(
                "/api/whitelabel/setup",
                json={"domain": "example.com", "verification_method": "txt_record"},
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["domain"] == "example.com"
            assert "verification_token" in data

    def test_setup_domain_invalid_format(self, client, pro_user_token):
        with patch(
            "app.services.whitelabel_service.whitelabel_service.create_domain"
        ) as mock_create:
            mock_create.return_value = (None, "Invalid domain format")

            response = client.post(
                "/api/whitelabel/setup",
                json={"domain": "invalid domain", "verification_method": "txt_record"},
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 400

    def test_setup_domain_tier_check(self, client, freemium_user_token):
        with patch(
            "app.services.whitelabel_service.whitelabel_service.create_domain"
        ) as mock_create:
            mock_create.return_value = (None, "Whitelabel requires Pro tier or higher")

            response = client.post(
                "/api/whitelabel/setup",
                json={"domain": "example.com", "verification_method": "txt_record"},
                headers={"Authorization": f"Bearer {freemium_user_token}"},
            )

            assert response.status_code == 402


class TestWhitelabelConfig:
    """Test configuration retrieval"""

    def test_get_config_success(self, client, pro_user_token):
        with patch("app.core.dependencies.get_db") as mock_db:
            mock_domain = Mock(spec=WhitelabelDomain)
            mock_domain.id = 1
            mock_domain.domain = "example.com"
            mock_domain.verified = True

            mock_db.return_value.query.return_value.filter.return_value.all.return_value = [
                mock_domain
            ]

            response = client.get(
                "/api/whitelabel/config",
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "domains" in data

    def test_get_config_no_domains(self, client, pro_user_token):
        with patch("app.core.dependencies.get_db") as mock_db:
            mock_db.return_value.query.return_value.filter.return_value.all.return_value = (
                []
            )

            response = client.get(
                "/api/whitelabel/config",
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["domains"] == []


class TestDomainVerification:
    """Test domain verification endpoint"""

    def test_verify_domain_success(self, client, pro_user_token):
        with patch(
            "app.services.whitelabel_service.whitelabel_service.verify_domain"
        ) as mock_verify:
            mock_verify.return_value = (True, None)

            response = client.post(
                "/api/whitelabel/verify-domain",
                json={"domain_id": 1},
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["verified"] is True

    def test_verify_domain_failed(self, client, pro_user_token):
        with patch(
            "app.services.whitelabel_service.whitelabel_service.verify_domain"
        ) as mock_verify:
            mock_verify.return_value = (False, "TXT record not found")

            response = client.post(
                "/api/whitelabel/verify-domain",
                json={"domain_id": 1},
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "not found" in data["detail"]


class TestBrandingManagement:
    """Test branding update endpoint"""

    def test_update_branding_success(self, client, pro_user_token):
        with patch(
            "app.services.whitelabel_service.whitelabel_service.update_branding"
        ) as mock_update:
            mock_branding = Mock(spec=WhitelabelBranding)
            mock_branding.company_name = "Test Company"
            mock_branding.primary_color = "#FF0000"
            mock_update.return_value = mock_branding

            response = client.put(
                "/api/whitelabel/branding",
                json={"company_name": "Test Company", "primary_color": "#FF0000"},
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["company_name"] == "Test Company"

    def test_update_branding_partial(self, client, pro_user_token):
        with patch(
            "app.services.whitelabel_service.whitelabel_service.update_branding"
        ) as mock_update:
            mock_branding = Mock(spec=WhitelabelBranding)
            mock_branding.company_name = "Updated Name"
            mock_update.return_value = mock_branding

            response = client.put(
                "/api/whitelabel/branding",
                json={"company_name": "Updated Name"},
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 200


class TestDomainRemoval:
    """Test domain removal endpoint"""

    def test_remove_domain_success(self, client, pro_user_token):
        with patch("app.core.dependencies.get_db") as mock_db:
            mock_domain = Mock(spec=WhitelabelDomain)
            mock_db.return_value.query.return_value.filter.return_value.first.return_value = (
                mock_domain
            )

            response = client.delete(
                "/api/whitelabel/domains/1",
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 200
            assert mock_db.return_value.delete.called

    def test_remove_domain_not_found(self, client, pro_user_token):
        with patch("app.core.dependencies.get_db") as mock_db:
            mock_db.return_value.query.return_value.filter.return_value.first.return_value = (
                None
            )

            response = client.delete(
                "/api/whitelabel/domains/999",
                headers={"Authorization": f"Bearer {pro_user_token}"},
            )

            assert response.status_code == 404


class TestVerificationInstructions:
    """Test verification instructions endpoint"""

    def test_get_instructions_txt_record(self, client, pro_user_token):
        response = client.get(
            "/api/whitelabel/verification-instructions?method=txt_record&domain=example.com&token=test-token",
            headers={"Authorization": f"Bearer {pro_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "txt_record"
        assert "_namaskah-verify" in data["instructions"]

    def test_get_instructions_meta_tag(self, client, pro_user_token):
        response = client.get(
            "/api/whitelabel/verification-instructions?method=meta_tag&domain=example.com&token=test-token",
            headers={"Authorization": f"Bearer {pro_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "meta_tag"
        assert "<meta" in data["instructions"]

    def test_get_instructions_file_upload(self, client, pro_user_token):
        response = client.get(
            "/api/whitelabel/verification-instructions?method=file_upload&domain=example.com&token=test-token",
            headers={"Authorization": f"Bearer {pro_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "file_upload"
        assert ".well-known" in data["instructions"]
