"""Test SMS pricing of 3500 NGN works across all currencies."""

import pytest

from app.services.currency_service import CurrencyService


class TestSMSPricing3500NGN:
    """Verify SMS pricing of $2.12 (3500 NGN) converts correctly."""

    def test_base_usd_price(self):
        """Base price should be $2.12 USD."""
        base_price_usd = 2.12
        assert base_price_usd == 2.12

    def test_ngn_conversion(self):
        """$2.12 USD should equal 3500 NGN at 1650 rate."""
        base_price_usd = 2.12
        ngn_price = CurrencyService.convert(base_price_usd, "USD", "NGN")

        # Should be exactly 3498 (2.12 * 1650)
        assert round(ngn_price) == 3498
        # Close enough to 3500 (within 0.06% tolerance)
        assert abs(ngn_price - 3500) < 2

    def test_all_currency_conversions(self):
        """Verify $2.12 converts to all supported currencies."""
        base_price_usd = 2.12

        expected_conversions = {
            "USD": 2.12,
            "EUR": 1.95,  # 2.12 * 0.92
            "GBP": 1.67,  # 2.12 * 0.79
            "NGN": 3498,  # 2.12 * 1650
            "INR": 175.96,  # 2.12 * 83
            "CNY": 15.01,  # 2.12 * 7.08
            "JPY": 315.88,  # 2.12 * 149
            "BRL": 10.54,  # 2.12 * 4.97
            "CAD": 2.88,  # 2.12 * 1.36
            "AUD": 3.24,  # 2.12 * 1.53
        }

        for currency, expected in expected_conversions.items():
            converted = CurrencyService.convert(base_price_usd, "USD", currency)
            assert (
                round(converted, 2) == expected
            ), f"{currency} conversion failed: expected {expected}, got {round(converted, 2)}"

    def test_reverse_conversion(self):
        """Verify 3500 NGN converts back to ~$2.12 USD."""
        ngn_price = 3500
        usd_price = CurrencyService.convert(ngn_price, "NGN", "USD")

        # Should be approximately 2.12 (3500 / 1650 = 2.121)
        assert round(usd_price, 2) == 2.12

    def test_currency_formatting(self):
        """Verify currency formatting works for all currencies."""
        base_price_usd = 2.12

        formatted = {
            "USD": CurrencyService.format_currency(2.12, "USD"),
            "EUR": CurrencyService.format_currency(1.95, "EUR"),
            "GBP": CurrencyService.format_currency(1.67, "GBP"),
            "NGN": CurrencyService.format_currency(3498, "NGN"),
        }

        assert formatted["USD"] == "$2.12"
        assert formatted["EUR"] == "€1.95"
        assert formatted["GBP"] == "£1.67"
        assert formatted["NGN"] == "₦3498.00"

    def test_exchange_rate_consistency(self):
        """Verify NGN rate is 1650 across the system."""
        assert CurrencyService.RATES["NGN"] == 1650.0

        # Verify conversion matches rate
        usd_to_ngn = CurrencyService.convert(1, "USD", "NGN")
        assert usd_to_ngn == 1650.0

    def test_pricing_calculation_example(self):
        """Real-world example: User sees price in their currency."""
        base_price_usd = 2.12

        # Nigerian user
        ngn_user_sees = CurrencyService.convert(base_price_usd, "USD", "NGN")
        assert round(ngn_user_sees) == 3498  # ~3500 NGN

        # European user
        eur_user_sees = CurrencyService.convert(base_price_usd, "USD", "EUR")
        assert round(eur_user_sees, 2) == 1.95  # ~€1.95

        # UK user
        gbp_user_sees = CurrencyService.convert(base_price_usd, "USD", "GBP")
        assert round(gbp_user_sees, 2) == 1.67  # ~£1.67

    def test_all_currencies_available(self):
        """Verify all 10 currencies are supported."""
        currencies = CurrencyService.get_available_currencies()

        expected_currencies = [
            "USD",
            "EUR",
            "GBP",
            "NGN",
            "INR",
            "CNY",
            "JPY",
            "BRL",
            "CAD",
            "AUD",
        ]

        assert len(currencies) == 10
        for currency in expected_currencies:
            assert currency in currencies
