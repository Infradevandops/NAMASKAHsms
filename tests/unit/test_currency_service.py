

from app.services.currency_service import CurrencyService

class TestCurrencyService:

    def test_convert(self):
        # Same currency
        assert CurrencyService.convert(100, "USD", "USD") == 100

        # USD to NGN (1.0 -> 411.0)
        assert CurrencyService.convert(1, "USD", "NGN") == 411.0

        # NGN to USD (411.0 -> 1.0)
        assert CurrencyService.convert(411, "NGN", "USD") == 1.0

    def test_format_currency(self):

        assert CurrencyService.format_currency(10.5, "USD") == "$10.50"
        assert CurrencyService.format_currency(100, "EUR") == "€100.00"
        assert CurrencyService.format_currency(50, "NGN") == "₦50.00"
        assert CurrencyService.format_currency(10, "UNKNOWN") == "UNKNOWN10.00"

    def test_get_symbol(self):

        assert CurrencyService.get_symbol("USD") == "$"
        assert CurrencyService.get_symbol("XYZ") == "XYZ"

    def test_get_available_currencies(self):

        currencies = CurrencyService.get_available_currencies()
        assert "USD" in currencies
        assert "GBP" in currencies
        assert len(currencies) == 10
