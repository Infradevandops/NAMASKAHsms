"""Currency conversion service."""


class CurrencyService:

    """Handle currency conversion and formatting."""

    RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "NGN": 411.0,
        "INR": 83.0,
        "CNY": 7.08,
        "JPY": 149.0,
        "BRL": 4.97,
        "CAD": 1.36,
        "AUD": 1.53,
    }

    SYMBOLS = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "NGN": "₦",
        "INR": "₹",
        "CNY": "¥",
        "JPY": "¥",
        "BRL": "R$",
        "CAD": "C$",
        "AUD": "A$",
    }

    @staticmethod
def convert(amount: float, from_currency: str, to_currency: str) -> float:

        """Convert amount between currencies."""
if from_currency == to_currency:
            return amount

        from_rate = CurrencyService.RATES.get(from_currency, 1.0)
        to_rate = CurrencyService.RATES.get(to_currency, 1.0)

        return (amount / from_rate) * to_rate

    @staticmethod
def format_currency(amount: float, currency: str) -> str:

        """Format amount with currency symbol."""
        symbol = CurrencyService.SYMBOLS.get(currency, currency)
        return f"{symbol}{amount:.2f}"

    @staticmethod
def get_symbol(currency: str) -> str:

        """Get currency symbol."""
        return CurrencyService.SYMBOLS.get(currency, currency)

    @staticmethod
def get_available_currencies() -> list:

        """List supported currencies."""
        return list(CurrencyService.RATES.keys())