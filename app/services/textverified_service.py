"""TextVerified API integration service."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger

try:
    import textverified
    from textverified.data import (
        NumberType,
        ReservationCapability,
        ReservationType,
    )
except ImportError:
    textverified = None

logger = get_logger(__name__)

# Redis cache key and TTL for the live area-code-by-state index
_AC_STATE_CACHE_KEY = "tv:area_codes_by_state"
_AC_STATE_TTL = 3600  # 1 hour
_SERVICES_CACHE_KEY = "tv:services_list"
_SERVICES_TTL = 1800  # 30 minutes


def _get_redis():
    """Lazy import to avoid circular deps."""
    from app.core.cache import get_redis
    return get_redis()


class TextVerifiedService:
    """Service for TextVerified API integration."""

    def __init__(self):
        self.api_key = os.getenv("TEXTVERIFIED_API_KEY")
        self.api_username = os.getenv("TEXTVERIFIED_USERNAME") or os.getenv("TEXTVERIFIED_EMAIL")
        self.enabled = textverified is not None and bool(self.api_key and self.api_username)

        if self.enabled:
            try:
                self.client = textverified.TextVerified(
                    api_key=self.api_key,
                    api_username=self.api_username,
                )
                logger.info("TextVerified client initialized successfully")
            except Exception as e:
                logger.error(f"TextVerified client initialization failed: {e}")
                self.enabled = False
                self.client = None
        else:
            logger.warning("TextVerified service disabled - missing credentials or library")
            self.client = None

    # ------------------------------------------------------------------
    # Live area code index — fetched from TextVerified, grouped by state
    # ------------------------------------------------------------------

    async def get_area_codes_list(self) -> List[Dict[str, Any]]:
        """Fetch live area codes from TextVerified API."""
        if not self.enabled:
            return []
        try:
            codes = await asyncio.wait_for(asyncio.to_thread(self.client.services.area_codes), timeout=8.0)
            return [{"area_code": c.area_code, "state": c.state} for c in codes]
        except Exception as e:
            logger.error(f"Failed to get area codes: {e}")
            return []

    async def _get_area_codes_by_state(self) -> Dict[str, List[str]]:
        """
        Return {state: [area_code, ...]} built entirely from the live
        TextVerified area-codes endpoint. Result is cached in Redis for 1 hour
        so every purchase doesn't hit the API.
        """
        # 1. Try Redis cache
        try:
            redis = _get_redis()
            cached = redis.get(_AC_STATE_CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # cache miss is fine

        # 2. Fetch live from TextVerified
        codes = await self.get_area_codes_list()
        if not codes:
            logger.warning("TextVerified returned no area codes — proximity chain unavailable")
            return {}

        # 3. Group by state
        by_state: Dict[str, List[str]] = {}
        for entry in codes:
            state = entry.get("state", "").strip().upper()
            ac = entry.get("area_code", "").strip()
            if state and ac:
                by_state.setdefault(state, []).append(ac)

        # 4. Cache
        try:
            redis = _get_redis()
            redis.setex(_AC_STATE_CACHE_KEY, _AC_STATE_TTL, json.dumps(by_state))
        except Exception:
            pass

        logger.info(
            f"Built live area-code-by-state index: {len(by_state)} states, "
            f"{sum(len(v) for v in by_state.values())} codes"
        )
        return by_state

    async def _build_area_code_preference(self, requested: str) -> List[str]:
        """
        Return an ordered preference list for TextVerified:
          [requested] + [other codes in the same state from the live index]

        If the live index is unavailable, returns [requested] only — still
        better than nothing, and TextVerified will do its best.
        """
        by_state = await self._get_area_codes_by_state()

        # Find which state owns the requested code
        state = next(
            (s for s, codes in by_state.items() if requested in codes),
            None,
        )

        if not state:
            logger.debug(f"Area code {requested} not found in live index — sending as sole preference")
            return [requested]

        siblings = [c for c in by_state[state] if c != requested]
        logger.debug(
            f"Proximity chain for {requested} ({state}): "
            f"{len(siblings)} same-state alternatives from live index"
        )
        return [requested] + siblings

    # ------------------------------------------------------------------
    # Core verification methods
    # ------------------------------------------------------------------

    async def get_balance(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"balance": 0.0, "currency": "USD", "error": "Service not available"}
        try:
            account = await asyncio.to_thread(lambda: self.client.account.balance)
            return {"balance": float(account), "currency": "USD"}
        except Exception as e:
            logger.error(f"Failed to get TextVerified balance: {e}")
            return {"balance": 0.0, "error": str(e)}

    async def get_services_list(self) -> List[Dict[str, Any]]:
        """Fetch live services from TextVerified API."""
        if not self.enabled:
            return self._mock_services()
        # Try cache first
        try:
            redis = _get_redis()
            cached = redis.get(_SERVICES_CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        try:
            services = await asyncio.wait_for(
                asyncio.to_thread(self.client.services.list, NumberType.MOBILE, ReservationType.VERIFICATION),
                timeout=8.0
            )
            result = []
            for s in services:
                try:
                    snapshot = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.client.verifications.pricing,
                            service_name=s.service_name,
                            area_code=False,
                            carrier=False,
                            number_type=NumberType.MOBILE,
                            capability=ReservationCapability.SMS,
                        ),
                        timeout=3.0
                    )
                    price = snapshot.price
                except Exception:
                    price = 2.50
                result.append({"id": s.service_name, "name": s.service_name.title(), "price": price})
            try:
                redis = _get_redis()
                redis.setex(_SERVICES_CACHE_KEY, _SERVICES_TTL, json.dumps(result))
            except Exception:
                pass
            return result
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return self._mock_services()

    def _mock_services(self) -> List[Dict[str, Any]]:
        return [
            {"id": "whatsapp", "name": "WhatsApp", "price": 2.50},
            {"id": "telegram", "name": "Telegram", "price": 2.00},
            {"id": "discord", "name": "Discord", "price": 2.25},
            {"id": "instagram", "name": "Instagram", "price": 2.75},
            {"id": "facebook", "name": "Facebook", "price": 2.50},
            {"id": "google", "name": "Google", "price": 2.00},
            {"id": "twitter", "name": "Twitter", "price": 2.50},
            {"id": "microsoft", "name": "Microsoft", "price": 2.25},
            {"id": "amazon", "name": "Amazon", "price": 2.50},
            {"id": "uber", "name": "Uber", "price": 2.75},
        ]

    async def create_verification(
        self,
        service: str,
        country: str = "US",
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
    ) -> Dict[str, Any]:
        """
        Purchase a verification number.

        When area_code is requested, builds a live proximity chain from
        TextVerified's own area-codes endpoint (same state, ordered).
        TextVerified tries each code in order — first available wins.
        """
        if not self.enabled:
            raise RuntimeError("TextVerified service not available")

        cap = ReservationCapability.SMS if capability == "sms" else ReservationCapability.VOICE

        # Build preference list from live TextVerified data
        area_code_options: Optional[List[str]] = None
        if area_code:
            area_code_options = await self._build_area_code_preference(area_code)
            logger.info(
                f"Area code preference chain for {area_code}: "
                f"{area_code_options[:5]}{'...' if len(area_code_options) > 5 else ''} "
                f"({len(area_code_options)} options)"
            )

        result = await asyncio.to_thread(
            self.client.verifications.create,
            service_name=service,
            capability=cap,
            area_code_select_option=area_code_options,
            carrier_select_option=self._build_carrier_preference(carrier) if carrier else None,
        )

        assigned_number = result.number
        assigned_area_code = assigned_number[2:5] if assigned_number.startswith("+1") else None
        fallback_applied = bool(area_code and assigned_area_code and assigned_area_code != area_code)

        # Determine same-state using the live index (already cached from above)
        same_state = True
        if fallback_applied and area_code and assigned_area_code:
            by_state = await self._get_area_codes_by_state()
            req_state = next((s for s, codes in by_state.items() if area_code in codes), None)
            asgn_state = next((s for s, codes in by_state.items() if assigned_area_code in codes), None)
            same_state = req_state is not None and req_state == asgn_state
            logger.warning(
                f"Area code fallback: requested={area_code}({req_state}), "
                f"assigned={assigned_area_code}({asgn_state}), same_state={same_state}"
            )

        return {
            "id": result.id,
            "phone_number": assigned_number,
            "cost": result.total_cost,
            "fallback_applied": fallback_applied,
            "requested_area_code": area_code,
            "assigned_area_code": assigned_area_code,
            "same_state": same_state,
        }

    # Backward compat alias used by verification_routes.py
    def _build_carrier_preference(self, carrier: str) -> List[str]:
        """Return ordered carrier preference list with fallbacks."""
        all_carriers = ["verizon", "att", "tmobile", "sprint", "us_cellular"]
        normalized = carrier.lower().replace(" ", "_").replace("&", "")
        # Put requested first, then remaining in default order
        others = [c for c in all_carriers if c != normalized]
        return [normalized] + others

    async def purchase_number(
        self,
        service: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            result = await self.create_verification(service=service, area_code=area_code, carrier=carrier)
            return {
                "success": True,
                "verification_id": result["id"],
                "phone_number": result["phone_number"],
                "service": service,
                "country": "US",
                "cost": result["cost"],
                "fallback_applied": result["fallback_applied"],
                "requested_area_code": result["requested_area_code"],
                "assigned_area_code": result["assigned_area_code"],
            }
        except Exception as e:
            logger.error(f"purchase_number failed: {e}")
            return {"success": False, "error": str(e), "verification_id": None}

    async def get_sms(self, verification_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"success": False, "error": "Service not available", "sms": None}
        try:
            sms_list = await asyncio.to_thread(
                lambda: list(self.client.sms.list(verification_id))
            )
            if sms_list:
                latest = sms_list[-1]
                return {
                    "success": True,
                    "sms": latest.sms_content,
                    "code": latest.parsed_code,
                    "received_at": latest.created_at.isoformat(),
                }
            return {"success": False, "sms": None, "code": None}
        except Exception as e:
            logger.error(f"Failed to get SMS: {e}")
            return {"success": False, "error": str(e), "sms": None}

    async def cancel_verification(self, verification_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"success": False, "error": "Service not available"}
        try:
            await asyncio.to_thread(self.client.verifications.cancel, verification_id)
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to cancel verification: {e}")
            return {"success": False, "error": str(e)}
