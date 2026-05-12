"""Currency rates and conversion endpoint."""

import logging

from fastapi import APIRouter, HTTPException

from app.services.currency_service import CurrencyService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/currencies", tags=["Currencies"])


@router.get("")
def get_currencies():
    """Return supported currencies with rates (USD base) and symbols."""
    try:
        return {
            "base": "USD",
            "rates": CurrencyService.RATES,
            "symbols": CurrencyService.SYMBOLS,
        }
    except Exception as e:
        logger.error(f"Error fetching currencies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch currency data")
