"""Tests for i18n and currency services."""

from app.services.currency_service import CurrencyService
from app.services.translation_service import TranslationService


class TestTranslationService:
    """Test translation service."""

    def test_get_available_languages(self):
        """Test getting available languages."""
        service = TranslationService()
        languages = service.get_available_languages()
        assert len(languages) == 10
        assert "en" in languages
        assert "es" in languages

    def test_translate_key(self):
        """Test translation key lookup."""
        service = TranslationService("en")
        # Should return key if translation not found
        result = service.translate("common.welcome")
        assert result is not None

    def test_translate_with_params(self):
        """Test translation with parameters."""
        service = TranslationService("en")
        result = service.translate("common.welcome", name="User")
        assert result is not None


class TestCurrencyService:
    """Test currency service."""

    def test_convert_same_currency(self):
        """Test converting same currency."""
        result = CurrencyService.convert(100, "USD", "USD")
        assert result == 100

    def test_convert_usd_to_eur(self):
        """Test USD to EUR conversion."""
        result = CurrencyService.convert(100, "USD", "EUR")
        assert result > 0
        assert result < 100

    def test_convert_usd_to_ngn(self):
        """Test USD to NGN conversion."""
        result = CurrencyService.convert(100, "USD", "NGN")
        assert result > 100

    def test_format_currency_usd(self):
        """Test USD formatting."""
        result = CurrencyService.format_currency(100.50, "USD")
        assert "$" in result
        assert "100.50" in result

    def test_format_currency_eur(self):
        """Test EUR formatting."""
        result = CurrencyService.format_currency(100.50, "EUR")
        assert "€" in result
        assert "100.50" in result

    def test_get_symbol(self):
        """Test getting currency symbol."""
        assert CurrencyService.get_symbol("USD") == "$"
        assert CurrencyService.get_symbol("EUR") == "€"
        assert CurrencyService.get_symbol("GBP") == "£"

    def test_get_available_currencies(self):
        """Test getting available currencies."""
        currencies = CurrencyService.get_available_currencies()
        assert len(currencies) == 10
        assert "USD" in currencies
        assert "EUR" in currencies
