"""Tests for i18n and currency frontend integration."""


import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from main import app
from app.services.currency_service import CurrencyService
from app.services.currency_service import CurrencyService
from app.services.translation_service import TranslationService
from app.services.translation_service import TranslationService

@pytest.fixture
def client():

    return TestClient(app)


@pytest.fixture
def test_user(db: Session):

    """Create test user."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"test_{uuid.uuid4()}@example.com",
        password_hash="hashed_password",
        subscription_tier="freemium",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestPreferencesAPI:

    """Test user preferences API."""

def test_get_default_preferences(self, client, test_user, auth_headers):

        """Test getting default preferences."""
        response = client.get("/api/user/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["language"] == "en"
        assert data["data"]["currency"] == "USD"

def test_update_language_preference(self, client, test_user, auth_headers):

        """Test updating language preference."""
        response = client.put("/api/user/preferences", json={"language": "es"}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["language"] == "es"

def test_update_currency_preference(self, client, test_user, auth_headers):

        """Test updating currency preference."""
        response = client.put("/api/user/preferences", json={"currency": "EUR"}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["currency"] == "EUR"

def test_invalid_language(self, client, test_user, auth_headers):

        """Test invalid language code."""
        response = client.put("/api/user/preferences", json={"language": "invalid"}, headers=auth_headers)
        assert response.status_code == 400

def test_all_supported_languages(self, client, test_user, auth_headers):

        """Test all supported languages."""
        languages = ["en", "es", "fr", "de", "pt", "zh", "ja", "ar", "hi", "yo"]
for lang in languages:
            response = client.put("/api/user/preferences", json={"language": lang}, headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["data"]["language"] == lang


class TestCurrencyConversion:

    """Test currency conversion logic."""

def test_usd_to_eur_conversion(self):

        """Test USD to EUR conversion."""

        amount = 100
        converted = CurrencyService.convert(amount, "USD", "EUR")
        assert converted == 92.0

def test_currency_formatting(self):

        """Test currency formatting."""

        formatted = CurrencyService.format_currency(100, "USD")
        assert "$100.00" in formatted


class TestTranslationService:

    """Test translation service."""

def test_translation_loading(self):

        """Test loading translations."""

        service = TranslationService(language="en")
        langs = service.get_available_languages()
        assert "en" in langs

def test_translation_retrieval(self):

        """Test retrieving translations."""

        # Initialize service with English
        service = TranslationService(language="en")
        # common.welcome might not exist in mock, but should return the key if missing
        text = service.translate("common.welcome")
        assert text is not None