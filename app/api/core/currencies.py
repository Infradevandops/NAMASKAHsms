"""Currency rates and conversion endpoint."""

from fastapi import APIRouter

from app.services.currency_service import CurrencyService

router = APIRouter(prefix="/api/currencies", tags=["Currencies"])


@router.get("")
def get_currencies():
    """Return supported currencies with rates (USD base) and symbols."""
    return {
        "base": "USD",
        "rates": CurrencyService.RATES,
        "symbols": CurrencyService.SYMBOLS,
    }
