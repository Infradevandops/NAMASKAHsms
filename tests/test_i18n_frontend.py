"""Tests for i18n and currency frontend integration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models.user import User
from app.models.user_preference import UserPreference
from app.core.database import get_db
from app.core.dependencies import get_current_user


client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        tier="freemium"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get auth headers for test user."""
    return {"Authorization": f"Bearer test_token_{test_user.id}"}


class TestPreferencesAPI:
    """Test user preferences API."""

    def test_get_default_preferences(self, test_user, db: Session):
        """Test getting default preferences."""
        # Mock current user
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        response = client.get("/api/user/preferences")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["language"] == "en"
        assert data["data"]["currency"] == "USD"

    def test_update_language_preference(self, test_user, db: Session):
        """Test updating language preference."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        response = client.put(
            "/api/user/preferences",
            json={"language": "es"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["language"] == "es"

    def test_update_currency_preference(self, test_user, db: Session):
        """Test updating currency preference."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        response = client.put(
            "/api/user/preferences",
            json={"currency": "EUR"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["currency"] == "EUR"

    def test_update_both_preferences(self, test_user, db: Session):
        """Test updating both language and currency."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        response = client.put(
            "/api/user/preferences",
            json={"language": "fr", "currency": "EUR"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["language"] == "fr"
        assert data["data"]["currency"] == "EUR"

    def test_invalid_language(self, test_user, db: Session):
        """Test invalid language code."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        response = client.put(
            "/api/user/preferences",
            json={"language": "invalid"}
        )
        
        assert response.status_code == 400

    def test_invalid_currency(self, test_user, db: Session):
        """Test invalid currency code."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        response = client.put(
            "/api/user/preferences",
            json={"currency": "INVALID"}
        )
        
        assert response.status_code == 400

    def test_all_supported_languages(self, test_user, db: Session):
        """Test all supported languages."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        languages = ['en', 'es', 'fr', 'de', 'pt', 'zh', 'ja', 'ar', 'hi', 'yo']
        
        for lang in languages:
            response = client.put(
                "/api/user/preferences",
                json={"language": lang}
            )
            assert response.status_code == 200
            assert response.json()["data"]["language"] == lang

    def test_all_supported_currencies(self, test_user, db: Session):
        """Test all supported currencies."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        currencies = ['USD', 'EUR', 'GBP', 'NGN', 'INR', 'CNY', 'JPY', 'BRL', 'CAD', 'AUD']
        
        for curr in currencies:
            response = client.put(
                "/api/user/preferences",
                json={"currency": curr}
            )
            assert response.status_code == 200
            assert response.json()["data"]["currency"] == curr

    def test_preferences_persistence(self, test_user, db: Session):
        """Test that preferences persist across requests."""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: db

        # Set preferences
        client.put(
            "/api/user/preferences",
            json={"language": "de", "currency": "EUR"}
        )
        
        # Get preferences
        response = client.get("/api/user/preferences")
        data = response.json()
        
        assert data["data"]["language"] == "de"
        assert data["data"]["currency"] == "EUR"


class TestCurrencyConversion:
    """Test currency conversion logic."""

    def test_usd_to_eur_conversion(self):
        """Test USD to EUR conversion."""
        from app.services.currency_service import CurrencyService
        
        amount = 100
        converted = CurrencyService.convert(amount, 'USD', 'EUR')
        
        assert converted > 0
        assert converted < amount  # EUR is stronger than USD

    def test_same_currency_conversion(self):
        """Test conversion to same currency."""
        from app.services.currency_service import CurrencyService
        
        amount = 100
        converted = CurrencyService.convert(amount, 'USD', 'USD')
        
        assert converted == amount

    def test_currency_formatting(self):
        """Test currency formatting."""
        from app.services.currency_service import CurrencyService
        
        formatted = CurrencyService.format_currency(100, 'USD')
        assert '$' in formatted
        assert '100.00' in formatted

    def test_currency_symbol_retrieval(self):
        """Test getting currency symbols."""
        from app.services.currency_service import CurrencyService
        
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'NGN': '₦',
            'INR': '₹'
        }
        
        for curr, symbol in symbols.items():
            assert CurrencyService.get_symbol(curr) == symbol

    def test_available_currencies(self):
        """Test getting available currencies."""
        from app.services.currency_service import CurrencyService
        
        currencies = CurrencyService.get_available_currencies()
        
        assert len(currencies) == 10
        assert 'USD' in currencies
        assert 'EUR' in currencies
        assert 'NGN' in currencies


class TestTranslationService:
    """Test translation service."""

    def test_translation_loading(self):
        """Test loading translations."""
        from app.services.translation_service import TranslationService
        
        service = TranslationService()
        translations = service.get_available_languages()
        
        assert len(translations) == 10
        assert 'en' in translations
        assert 'es' in translations

    def test_translation_retrieval(self):
        """Test retrieving translations."""
        from app.services.translation_service import TranslationService
        
        service = TranslationService()
        
        # Test English
        text = service.translate('common.welcome', 'en')
        assert text is not None
        assert len(text) > 0

    def test_translation_fallback(self):
        """Test translation fallback to English."""
        from app.services.translation_service import TranslationService
        
        service = TranslationService()
        
        # Non-existent key should return key itself
        text = service.translate('nonexistent.key', 'en')
        assert text == 'nonexistent.key'

    def test_all_language_translations(self):
        """Test translations for all languages."""
        from app.services.translation_service import TranslationService
        
        service = TranslationService()
        languages = service.get_available_languages()
        
        for lang in languages:
            text = service.translate('common.welcome', lang)
            assert text is not None


class TestI18nIntegration:
    """Test i18n and currency integration."""

    def test_tier_pricing_localization(self):
        """Test tier pricing with localization."""
        from app.services.currency_service import CurrencyService
        
        # Freemium pricing
        freemium_cost = 2.22
        formatted = CurrencyService.format_currency(freemium_cost, 'USD')
        assert '$' in formatted
        
        # Pro pricing
        pro_cost = 25
        formatted = CurrencyService.format_currency(pro_cost, 'USD')
        assert '$' in formatted

    def test_filter_charges_localization(self):
        """Test filter charges with localization."""
        from app.services.currency_service import CurrencyService
        
        charges = {
            'state': 0.25,
            'city': 0.25,
            'isp': 0.50
        }
        
        for charge_type, amount in charges.items():
            formatted = CurrencyService.format_currency(amount, 'USD')
            assert '$' in formatted

    def test_quota_display_localization(self):
        """Test quota display with localization."""
        from app.services.currency_service import CurrencyService
        
        quota_used = 10
        quota_total = 15
        
        percentage = (quota_used / quota_total) * 100
        assert percentage == pytest.approx(66.67, 0.1)

    def test_pricing_breakdown_with_currency(self):
        """Test pricing breakdown with currency conversion."""
        from app.services.currency_service import CurrencyService
        
        base_cost = 2.50
        filter_cost = 0.25
        total = base_cost + filter_cost
        
        # Format in different currencies
        usd_format = CurrencyService.format_currency(total, 'USD')
        eur_format = CurrencyService.format_currency(
            CurrencyService.convert(total, 'USD', 'EUR'),
            'EUR'
        )
        
        assert '$' in usd_format
        assert '€' in eur_format
