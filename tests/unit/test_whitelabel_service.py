"""Unit tests for WhitelabelService"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.user import User
from app.models.whitelabel_models import WhitelabelBranding, WhitelabelDomain
from app.services.whitelabel_service import WhitelabelService


@pytest.fixture
def whitelabel_service():
    return WhitelabelService()


@pytest.fixture
def mock_db():
    return Mock()


class TestDomainValidation:
    """Test domain validation logic"""

    def test_valid_domain(self, whitelabel_service):
        is_valid, error = whitelabel_service.validate_domain("example.com")
        assert is_valid is True
        assert error is None

    def test_valid_subdomain(self, whitelabel_service):
        is_valid, error = whitelabel_service.validate_domain("app.example.com")
        assert is_valid is True
        assert error is None

    def test_invalid_format(self, whitelabel_service):
        is_valid, error = whitelabel_service.validate_domain("invalid domain")
        assert is_valid is False
        assert "Invalid domain format" in error

    def test_localhost_rejected(self, whitelabel_service):
        is_valid, error = whitelabel_service.validate_domain("localhost")
        assert is_valid is False
        assert error is not None

    def test_private_ip_rejected(self, whitelabel_service):
        is_valid, error = whitelabel_service.validate_domain("192.168.1.1")
        assert is_valid is False
        assert error is not None

    def test_domain_too_short(self, whitelabel_service):
        is_valid, error = whitelabel_service.validate_domain("a.b")
        assert is_valid is False
        assert error is not None

    def test_protocol_stripped(self, whitelabel_service):
        is_valid, error = whitelabel_service.validate_domain("https://example.com")
        assert is_valid is True


class TestVerificationToken:
    """Test verification token generation"""

    def test_token_generated(self, whitelabel_service):
        token = whitelabel_service.generate_verification_token()
        assert token is not None
        assert len(token) > 20

    def test_tokens_unique(self, whitelabel_service):
        token1 = whitelabel_service.generate_verification_token()
        token2 = whitelabel_service.generate_verification_token()
        assert token1 != token2


class TestDNSVerification:
    """Test DNS TXT record verification"""

    @pytest.mark.asyncio
    async def test_txt_record_found(self, whitelabel_service):
        mock_answer = Mock()
        mock_answer.to_text.return_value = '"test-token-123"'

        with patch.object(
            whitelabel_service.dns_resolver, "resolve", return_value=[mock_answer]
        ):
            verified, error = await whitelabel_service.verify_domain_txt_record(
                "example.com", "test-token-123"
            )
            assert verified is True
            assert error is None

    @pytest.mark.asyncio
    async def test_txt_record_not_found(self, whitelabel_service):
        import dns.resolver

        with patch.object(
            whitelabel_service.dns_resolver,
            "resolve",
            side_effect=dns.resolver.NXDOMAIN,
        ):
            verified, error = await whitelabel_service.verify_domain_txt_record(
                "example.com", "test-token-123"
            )
            assert verified is False
            assert "not found" in error


class TestMetaTagVerification:
    """Test HTML meta tag verification"""

    @pytest.mark.asyncio
    async def test_meta_tag_found(self, whitelabel_service):
        html = '<html><head><meta name="namaskah-verification" content="test-token-123"></head></html>'

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.text = html
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            verified, error = await whitelabel_service.verify_domain_meta_tag(
                "example.com", "test-token-123"
            )
            assert verified is True
            assert error is None

    @pytest.mark.asyncio
    async def test_meta_tag_not_found(self, whitelabel_service):
        html = "<html><head></head></html>"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.text = html
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            verified, error = await whitelabel_service.verify_domain_meta_tag(
                "example.com", "test-token-123"
            )
            assert verified is False
            assert "not found" in error


class TestFileVerification:
    """Test file upload verification"""

    @pytest.mark.asyncio
    async def test_file_content_matches(self, whitelabel_service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.text = "test-token-123"
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            verified, error = await whitelabel_service.verify_domain_file(
                "example.com", "test-token-123"
            )
            assert verified is True
            assert error is None

    @pytest.mark.asyncio
    async def test_file_content_mismatch(self, whitelabel_service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.text = "wrong-token"
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            verified, error = await whitelabel_service.verify_domain_file(
                "example.com", "test-token-123"
            )
            assert verified is False
            assert "does not match" in error


class TestCreateDomain:
    """Test domain creation"""

    def test_create_domain_success(self, whitelabel_service, mock_db):
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.subscription_tier = "pro"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            mock_user,
        ]

        domain_obj, error = whitelabel_service.create_domain(
            mock_db, user_id=1, domain="example.com"
        )

        assert error is None
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_create_domain_invalid_format(self, whitelabel_service, mock_db):
        domain_obj, error = whitelabel_service.create_domain(
            mock_db, user_id=1, domain="invalid domain"
        )

        assert domain_obj is None
        assert "Invalid domain format" in error

    def test_create_domain_already_exists(self, whitelabel_service, mock_db):
        mock_existing = Mock(spec=WhitelabelDomain)
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_existing
        )

        domain_obj, error = whitelabel_service.create_domain(
            mock_db, user_id=1, domain="example.com"
        )

        assert domain_obj is None
        assert "already registered" in error

    def test_create_domain_tier_check(self, whitelabel_service, mock_db):
        mock_user = Mock(spec=User)
        mock_user.subscription_tier = "freemium"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,
            mock_user,
        ]

        domain_obj, error = whitelabel_service.create_domain(
            mock_db, user_id=1, domain="example.com"
        )

        assert domain_obj is None
        assert "Pro tier" in error


class TestBranding:
    """Test branding management"""

    def test_get_or_create_existing(self, whitelabel_service, mock_db):
        mock_branding = Mock(spec=WhitelabelBranding)
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_branding
        )

        result = whitelabel_service.get_or_create_branding(mock_db, user_id=1)

        assert result == mock_branding
        assert not mock_db.add.called

    def test_get_or_create_new(self, whitelabel_service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = whitelabel_service.get_or_create_branding(mock_db, user_id=1)

        assert mock_db.add.called
        assert mock_db.commit.called

    def test_update_branding(self, whitelabel_service, mock_db):
        mock_branding = Mock(spec=WhitelabelBranding)
        mock_branding.company_name = "Old Name"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_branding
        )

        result = whitelabel_service.update_branding(
            mock_db, user_id=1, company_name="New Name", primary_color="#FF0000"
        )

        assert mock_db.commit.called
        assert mock_db.refresh.called

    def test_get_branding_by_domain(self, whitelabel_service, mock_db):
        mock_domain = Mock(spec=WhitelabelDomain)
        mock_domain.user_id = 1
        mock_branding = Mock(spec=WhitelabelBranding)

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_domain,
            mock_branding,
        ]

        result = whitelabel_service.get_branding_by_domain(mock_db, "example.com")

        assert result == mock_branding

    def test_get_branding_domain_not_found(self, whitelabel_service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = whitelabel_service.get_branding_by_domain(mock_db, "example.com")

        assert result is None
