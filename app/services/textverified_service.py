"""TextVerified API integration service."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter

from app.core.config import get_settings
from app.core.exceptions import AreaCodeUnavailableException
from app.core.logging import get_logger
from app.services.area_code_geo import get_ranked_alternatives
from app.services.carrier_lookup import CarrierLookupService
from app.services.phone_validator import PhoneValidator
from app.services.purchase_intelligence import PurchaseIntelligenceService

settings = get_settings()

try:
    import textverified
    from textverified.data import NumberType, ReservationCapability, ReservationType
except ImportError:
    textverified = None

logger = get_logger(__name__)

# Cache keys and TTLs
_AC_STATE_CACHE_KEY = "tv:area_codes_by_state"
_AC_STATE_TTL = 7200  # 2 hours
_AREA_CODES_CACHE_KEY = "tv:area_codes_list"
_AREA_CODES_TTL = 7200  # 2 hours
_SERVICES_CACHE_KEY = "tv:services_list"
_SERVICES_TTL = 86400  # 24 hours
_SERVICES_NAMES_CACHE_KEY = "tv:services_names"
_SERVICES_NAMES_TTL = 86400  # 24 hours


def _get_redis():
    """Lazy import to avoid circular deps."""
    from app.core.cache import get_redis

    return get_redis()


class TextVerifiedService:
    """Service for TextVerified API integration."""

    def __init__(self):
        self.api_key = os.getenv("TEXTVERIFIED_API_KEY")
        self.api_username = os.getenv("TEXTVERIFIED_USERNAME") or os.getenv(
            "TEXTVERIFIED_EMAIL"
        )
        self.enabled = textverified is not None and bool(
            self.api_key and self.api_username
        )

        if self.enabled:
            try:
                self.client = textverified.TextVerified(
                    api_key=self.api_key,
                    api_username=self.api_username,
                )
                # Increase connection pool to handle concurrent polling
                adapter = HTTPAdapter(pool_connections=1, pool_maxsize=30)
                if hasattr(self.client, "_session"):
                    self.client._session.mount("https://", adapter)
                    self.client._session.mount("http://", adapter)
                logger.info("TextVerified client initialized successfully")
            except Exception as e:
                logger.error(f"TextVerified client initialization failed: {e}")
                self.enabled = False
                self.client = None
        else:
            logger.warning(
                "TextVerified service disabled - missing credentials or library"
            )
            self.client = None

    # ------------------------------------------------------------------
    # Live area code index — fetched from TextVerified, grouped by state
    # ------------------------------------------------------------------

    async def get_area_codes_list(self, service: str = None) -> List[Dict[str, Any]]:
        """Fetch live area codes from TextVerified API with aggressive caching."""
        if not self.enabled:
            return []

        from app.core.unified_cache import cache

        # Try cache first (accept stale cache during outages)
        try:
            cached = await cache.get(_AREA_CODES_CACHE_KEY)
            if cached:
                logger.debug(f"Area codes from cache: {len(cached)} codes")
                return cached
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

        # Fetch from API with retry
        for attempt in range(3):
            try:
                codes = await asyncio.wait_for(
                    asyncio.to_thread(self.client.services.area_codes), timeout=15.0
                )
                result = [{"area_code": c.area_code, "state": c.state} for c in codes]

                # Cache aggressively (24 hours instead of 2)
                try:
                    await cache.set(_AREA_CODES_CACHE_KEY, result, 86400)
                    logger.info(f"Cached {len(result)} area codes for 24h")
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")

                return result

            except asyncio.TimeoutError:
                logger.warning(f"Area codes API timeout (attempt {attempt + 1}/3)")
                if attempt < 2:
                    await asyncio.sleep(1)  # Brief delay before retry
                continue
            except Exception as e:
                logger.error(f"Failed to get area codes (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                continue

        # All retries failed
        logger.error("Area codes API failed after 3 attempts")
        return []

    async def _get_area_codes_by_state(self) -> Dict[str, List[str]]:
        """
        Return {state: [area_code, ...]} built entirely from the live
        TextVerified area-codes endpoint. Result is cached for 24 hours.
        """
        from app.core.unified_cache import cache

        # Try cache first
        try:
            cached = await cache.get(_AC_STATE_CACHE_KEY)
            if cached:
                logger.debug(f"Area codes by state from cache: {len(cached)} states")
                return cached
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

        # Fetch live from TextVerified
        codes = await self.get_area_codes_list()
        if not codes:
            logger.warning(
                "TextVerified returned no area codes — proximity chain unavailable"
            )
            return {}

        # Group by state
        by_state: Dict[str, List[str]] = {}
        for entry in codes:
            state = entry.get("state", "").strip().upper()
            ac = entry.get("area_code", "").strip()
            if state and ac:
                by_state.setdefault(state, []).append(ac)

        # Cache for 24 hours (same as area codes list)
        try:
            await cache.set(_AC_STATE_CACHE_KEY, by_state, 86400)
            logger.info(
                f"Cached area-code-by-state index: {len(by_state)} states, "
                f"{sum(len(v) for v in by_state.values())} codes (24h TTL)"
            )
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

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
            logger.debug(
                f"Area code {requested} not found in live index — sending as sole preference"
            )
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
        """Fetch live services from TextVerified API.

        CRITICAL: This MUST return live data from TextVerified.
        If API fails, return empty list - DO NOT use fallbacks.
        Frontend will show error and prevent purchases.
        """
        if not self.enabled:
            logger.error("TextVerified service is DISABLED - check API credentials")
            raise RuntimeError(
                "TextVerified API is not configured. "
                "Set TEXTVERIFIED_API_KEY and TEXTVERIFIED_USERNAME environment variables."
            )

        from app.core.unified_cache import cache

        # Return full cached result (names + prices) if available
        try:
            cached = await cache.get(_SERVICES_CACHE_KEY)
            if cached:
                # Deduplicate cached data (legacy cache may have dupes)
                seen = {}
                for s in cached:
                    if s["id"] not in seen:
                        seen[s["id"]] = s
                deduped = list(seen.values())
                logger.info(f"Returning {len(deduped)} services from cache")
                return deduped
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

        # Fast path: fetch only service names (no per-service pricing calls)
        try:
            cached_names = await cache.get(_SERVICES_NAMES_CACHE_KEY)
            if cached_names:
                seen = {}
                for s in cached_names:
                    if s["id"] not in seen:
                        seen[s["id"]] = s
                deduped = list(seen.values())
                logger.info(f"Returning {len(deduped)} services from names cache")
                return deduped
        except Exception as e:
            logger.warning(f"Names cache read failed: {e}")

        # Fetch from TextVerified API with retry
        last_error = None
        for attempt in range(3):
            try:
                logger.info(
                    f"Fetching services from TextVerified API (attempt {attempt + 1}/3)..."
                )
                services = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.services.list,
                        NumberType.MOBILE,
                        ReservationType.VERIFICATION,
                    ),
                    timeout=15.0,
                )

                if not services:
                    logger.error("TextVerified API returned empty services list")
                    raise RuntimeError("TextVerified API returned no services")

                # Deduplicate by service_name (API returns SMS + Voice variants)
                seen = {}
                for s in services:
                    if s.service_name not in seen:
                        seen[s.service_name] = s
                unique_services = list(seen.values())

                logger.info(
                    f"Fetched {len(services)} services, {len(unique_services)} unique after dedup"
                )

                # Try to fetch real prices inline (up to 12s)
                try:
                    priced = await asyncio.wait_for(
                        self._fetch_prices_inline(unique_services), timeout=12.0
                    )
                    try:
                        await cache.set(_SERVICES_CACHE_KEY, priced, _SERVICES_TTL)
                        await cache.set(
                            _SERVICES_NAMES_CACHE_KEY, priced, _SERVICES_NAMES_TTL
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache services: {e}")
                    return priced
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(
                        f"Inline pricing timed out/failed ({e}), returning names only"
                    )

                # Fallback: return without prices, background fetch
                result = [
                    {
                        "id": s.service_name,
                        "name": s.service_name.title(),
                        "price": None,
                        "cost": None,
                    }
                    for s in unique_services
                ]

                try:
                    await cache.set(
                        _SERVICES_NAMES_CACHE_KEY, result, _SERVICES_NAMES_TTL
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache services: {e}")

                asyncio.create_task(self._fetch_and_cache_pricing(unique_services))
                return result

            except asyncio.TimeoutError:
                last_error = "TextVerified API is not responding"
                logger.warning(f"TextVerified API timeout (attempt {attempt + 1}/3)")
                if attempt < 2:
                    await asyncio.sleep(1)
                continue
            except RuntimeError:
                raise  # Don't retry on empty response
            except Exception as e:
                last_error = str(e)
                logger.warning(f"TextVerified API error (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                continue

        logger.error(f"TextVerified API failed after 3 attempts: {last_error}")
        raise RuntimeError(
            f"TextVerified API failed after 3 attempts. Please try again in a few moments."
        )

    async def _fetch_prices_inline(self, services) -> list:
        """Fetch real prices for all services inline (called with timeout)."""
        sem = asyncio.Semaphore(10)

        async def _price(s) -> dict:
            async with sem:
                try:
                    snap = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.client.verifications.pricing,
                            service_name=s.service_name,
                            area_code=False,
                            carrier=False,
                            number_type=NumberType.MOBILE,
                            capability=ReservationCapability.SMS,
                        ),
                        timeout=8.0,
                    )
                    return {
                        "id": s.service_name,
                        "name": s.service_name.title(),
                        "price": float(snap.price),
                        "cost": float(snap.price),
                    }
                except Exception:
                    return {
                        "id": s.service_name,
                        "name": s.service_name.title(),
                        "price": None,
                        "cost": None,
                    }

        results = await asyncio.gather(*[_price(s) for s in services])
        logger.info(
            f"Inline pricing: {sum(1 for r in results if r['price'] is not None)}/{len(results)} priced"
        )
        return list(results)

    async def _fetch_and_cache_pricing(self, services) -> None:
        """Background task: fetch all service prices and update 24h cache."""
        from app.core.unified_cache import cache

        sem = asyncio.Semaphore(10)

        async def _price(service_name: str) -> float:
            async with sem:
                try:
                    snap = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.client.verifications.pricing,
                            service_name=service_name,
                            area_code=False,
                            carrier=False,
                            number_type=NumberType.MOBILE,
                            capability=ReservationCapability.SMS,
                        ),
                        timeout=8.0,
                    )
                    return snap.price
                except Exception:
                    return None

        try:
            prices = await asyncio.gather(*[_price(s.service_name) for s in services])
            result = [
                {
                    "id": s.service_name,
                    "name": s.service_name.title(),
                    "price": float(p) if p is not None else None,
                    "cost": float(p) if p is not None else None,
                }
                for s, p in zip(services, prices)
            ]
            await cache.set(_SERVICES_CACHE_KEY, result, _SERVICES_TTL)
            logger.info(f"Background pricing cache updated: {len(result)} services")
        except Exception as e:
            logger.error(f"Background pricing fetch failed: {e}")

    def _mock_services(self) -> List[Dict[str, Any]]:
        """DEPRECATED: Do not use. This method should never be called.
        All services must come from TextVerified API.
        """
        logger.error("_mock_services() called - this should never happen in production")
        raise RuntimeError(
            "Mock services are disabled. TextVerified API must be configured."
        )

    def _extract_carrier_from_number(self, phone_number: str) -> Optional[str]:
        """DEPRECATED: TextVerified does not return specific carrier info.

        This method always returns 'Mobile' for valid US numbers because TextVerified's
        API response does not include specific carrier information. Do not use this for
        carrier validation or decision-making.

        See: docs/TEXTVERIFIED_CARRIER_ANALYSIS.md
        """
        if not phone_number:
            return None
        clean = (
            str(phone_number)
            .replace("+", "")
            .replace("-", "")
            .replace(" ", "")
            .replace("(", "")
            .replace(")", "")
        )
        if len(clean) >= 10:
            return "Mobile"  # Always returns "Mobile" — TextVerified doesn't provide specific carrier
        return "Unknown"

    async def get_verification_status(self, activation_id: str) -> Dict[str, Any]:
        """Get the current status of a verification/activation."""
        if not self.enabled:
            return {"status": "error", "error": "Service disabled"}

        try:
            # Note: The textverified lib might use different method names
            # We'll try to get it via the client
            status = await asyncio.to_thread(
                self.client.verifications.get, activation_id
            )

            # Extract common fields
            return {
                "status": status.status,
                "sms_code": getattr(status, "sms_code", None),
                "sms_text": getattr(status, "sms_text", None),
                "carrier": getattr(status, "carrier", None),
            }
        except Exception as e:
            logger.error(f"Failed to get verification status for {activation_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def poll_sms_standard(
        self,
        tv_verification,
        timeout_seconds: float = 600.0,
    ) -> Dict[str, Any]:
        """Poll for SMS using TextVerified's standard sms.incoming() method.

        This is the correct way to poll — passes the VerificationExpanded
        object (not a string), uses TV's built-in since filter, deduplication,
        and timeout. Works identically for both SMS and voice capability.

        Args:
            tv_verification: VerificationExpanded object from verifications.create()
            timeout_seconds: How long to wait. Use ends_at delta for accuracy.

        Returns:
            {"success": True, "code": str, "sms": str} or
            {"success": False, "timed_out": True}
        """
        if not self.enabled:
            return {"success": False, "error": "Service not available"}

        def _blocking_poll():
            try:
                for sms in self.client.sms.incoming(
                    data=tv_verification,
                    since=tv_verification.created_at,
                    timeout=timeout_seconds,
                    polling_interval=3.0,
                ):
                    # Master Check: Ensure message is strictly fresh (v6.0 Institutional Grade)
                    from datetime import timezone

                    msg_time = sms.created_at
                    if msg_time.tzinfo is None:
                        msg_time = msg_time.replace(tzinfo=timezone.utc)

                    ref_time = tv_verification.created_at
                    if ref_time.tzinfo is None:
                        ref_time = ref_time.replace(tzinfo=timezone.utc)

                    if msg_time < ref_time:
                        logger.warning(
                            f"Rejected stale SMS from recycled number: {sms.sms_content}"
                        )
                        continue

                    parsed = sms.parsed_code or ""
                    # ... [rest as before]
                    if not parsed:
                        import re

                        text = sms.sms_content or ""
                        # TextVerified voice transcription often has codes in brackets or quotes
                        hyphen = re.findall(r"\b(\d{3}-\d{3})\b", text)
                        plain = re.findall(r"\b(\d{4,8})\b", text)
                        if hyphen:
                            parsed = hyphen[-1].replace("-", "")
                        elif plain:
                            parsed = plain[-1]

                    return {
                        "success": True,
                        "code": parsed,
                        "sms": sms.sms_content or "",
                        "received_at": msg_time.isoformat(),
                    }
                return {"success": False, "timed_out": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return await asyncio.to_thread(_blocking_poll)

    async def report_verification(self, verification_id: str) -> bool:
        """Report a failed verification to TextVerified.

        This triggers an automatic refund from TextVerified to the account
        balance. Always call this when a verification fails or times out
        so the platform recovers the cost from TextVerified.

        Returns True if report was submitted successfully.
        """
        if not self.enabled:
            return False
        try:
            await asyncio.to_thread(self.client.verifications.report, verification_id)
            logger.info(
                f"Reported verification {verification_id} to TextVerified — refund triggered"
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to report verification {verification_id}: {e}")
            return False

    async def get_verification_details(self, verification_id: str) -> Dict[str, Any]:
        """Get full VerificationExpanded details from TextVerified.

        Use this to read the real state, ends_at, and action flags.
        """
        if not self.enabled:
            return {}
        try:
            tv = await asyncio.to_thread(
                self.client.verifications.details, verification_id
            )
            return {
                "id": tv.id,
                "number": tv.number,
                "state": tv.state.value,
                "carrier": getattr(tv, "carrier", None)
                or getattr(tv, "carrier_name", None),
                "created_at": tv.created_at.isoformat(),
                "ends_at": tv.ends_at.isoformat(),
                "total_cost": tv.total_cost,
                "can_cancel": tv.cancel.can_cancel,
                "can_report": tv.report.can_report,
            }
        except Exception as e:
            logger.error(
                f"Failed to get verification details for {verification_id}: {e}"
            )
            return {}

    async def check_sms(self, activation_id: str, created_after=None) -> Dict[str, Any]:
        """
        Check for SMS messages for a specific activation.
        Used by SMSPollingService.

        Args:
            activation_id: TextVerified activation ID.
            created_after: datetime — only return SMS received after this time.
                           Pass verification.created_at to reject stale SMS.
        """
        if not self.enabled:
            return {"status": "ERROR", "messages": []}

        try:
            sms_data = await self.get_sms(activation_id, created_after=created_after)
            if sms_data.get("success"):
                return {
                    "status": "COMPLETED",
                    "messages": [
                        {
                            "text": sms_data.get("sms", ""),
                            "code": sms_data.get("code", ""),
                        }
                    ],
                }
            return {"status": "PENDING", "messages": []}
        except Exception as e:
            logger.error(f"check_sms failed for {activation_id}: {e}")
            return {"status": "ERROR", "messages": []}

    async def _cancel_safe(self, verification_id: str) -> bool:
        """Cancel verification without raising exceptions (v4.4.1).

        Returns True if cancellation succeeded, False otherwise.
        Never raises exceptions - failures are logged as warnings.
        """
        try:
            await asyncio.to_thread(self.client.verifications.cancel, verification_id)
            logger.info(f"Cancelled verification {verification_id}")
            return True
        except Exception as e:
            logger.warning(f"Cancel failed for {verification_id}: {e}")
            return False

    async def create_verification(
        self,
        service: str,
        country: str = "US",
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
        selected_from_alternatives: Optional[bool] = False,
        original_request: Optional[str] = None,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Purchase a verification number with Phase 5 logic.

        When area_code is requested, builds a live proximity chain from
        TextVerified's own area-codes endpoint.

        If area code doesn't match OR number is VOIP/landline, cancels.
        Uses informed retry: if mismatched area code score is unavailable,
        returns alternatives immediately. Otherwise retries once maximum (max 2 attempts).
        """
        if not self.enabled:
            raise RuntimeError("TextVerified service not available")

        cap = (
            ReservationCapability.SMS
            if capability == "sms"
            else ReservationCapability.VOICE
        )

        # Build preference list from live TextVerified data
        area_code_options: Optional[List[str]] = None
        if area_code:
            area_code_options = await self._build_area_code_preference(area_code)
            logger.info(
                f"Area code preference chain for {area_code}: "
                f"{area_code_options[:5]}{'...' if len(area_code_options) > 5 else ''} "
                f"({len(area_code_options)} options)"
            )

        # Build carrier preference if provided (Regression Fix)
        carrier_options: Optional[List[str]] = None
        if carrier:
            carrier_options = self._build_carrier_preference(carrier)

        # Initialize validators (Phase 5)
        phone_validator = PhoneValidator()

        # Retry loop (Phase 5: Single informed retry max_retries attempts)
        max_attempts = max_retries
        attempt_count = 0
        area_code_matched = False
        voip_rejected = False
        result = None

        while attempt_count < max_attempts:
            attempt_count += 1
            result = await asyncio.to_thread(
                self.client.verifications.create,
                service_name=service,
                capability=cap,
                area_code_select_option=area_code_options,
                carrier_select_option=carrier_options,
            )

            assigned_number = result.number
            assigned_area_code = (
                assigned_number[2:5] if assigned_number.startswith("+1") else None
            )

            # Check area code match (Honor preference chain for institutional flexibility)
            area_code_match = True
            if area_code:
                area_code_match = assigned_area_code in (
                    area_code_options or [area_code]
                )

            # Check VOIP/landline
            phone_validation = phone_validator.validate_mobile(assigned_number, country)
            is_mobile = phone_validation.get("is_mobile", True)
            is_voip = phone_validation.get("is_voip", False)

            # Phase 2 Instrumentation
            matched = area_code_match if area_code else None
            await PurchaseIntelligenceService.log_outcome(
                service=service,
                assigned_code=assigned_area_code,
                requested_code=area_code,
                assigned_carrier=None,
                carrier_type=phone_validation.get("number_type"),
                matched=matched,
                verification_id=result.id if result else None,
                selected_from_alternatives=selected_from_alternatives,
                original_request=original_request,
            )

            # Accept if all checks pass
            if area_code_match and is_mobile and not is_voip:
                area_code_matched = True
                break

            # Reject if not compatible
            reason = []
            if not area_code_match:
                reason.append(
                    f"area code mismatch (requested {area_code}, got {assigned_area_code})"
                )
            if not is_mobile or is_voip:
                reason.append("VOIP/Landline detected")
                voip_rejected = True

            # -- Informed Decision: Retry or Terminate --
            if not area_code_match:
                # If area code was the failure reason, we check if we should retry
                if attempt_count < max_attempts:
                    # Check score: if this combination is known to be dead, don't waste time/money on retry
                    score = await PurchaseIntelligenceService.score_availability(
                        service, area_code
                    )
                    if score.available is False and score.confidence >= 0.6:
                        logger.warning(
                            f"Availability score is poor ({score.confidence}), abandoning retry for {area_code}"
                        )
                        await self._cancel_safe(result.id)
                        alts = await get_ranked_alternatives(area_code, service)
                        raise AreaCodeUnavailableException(
                            area_code=area_code, service=service, alternatives=alts
                        )

                    # Score is okay or unknown, let's retry
                    logger.warning(
                        f"Rejecting number (attempt {attempt_count}/{max_attempts}) due to mismatch. Retrying..."
                    )
                    await self._cancel_safe(result.id)
                else:
                    # Final attempt failed area code match
                    logger.warning(
                        f"Failed to secure {area_code} after {max_attempts} attempts. Raising exception."
                    )
                    await self._cancel_safe(result.id)
                    alts = await get_ranked_alternatives(area_code, service)
                    raise AreaCodeUnavailableException(
                        area_code=area_code, service=service, alternatives=alts
                    )

            elif not is_mobile or is_voip:
                # VOIP failure but area code matched (or was not requested)
                if attempt_count < max_attempts:
                    logger.warning(
                        f"Rejecting number (attempt {attempt_count}/{max_attempts}) due to VOIP. Retrying..."
                    )
                    await self._cancel_safe(result.id)
                else:
                    # Final attempt is VOIP. Policy: Keep it to avoid infinite loops/billing overhead.
                    logger.warning(
                        f"Final attempt is VOIP. Keeping number {assigned_number} despite policy."
                    )
                    area_code_matched = area_code_match
                    break
            else:
                # Success!
                area_code_matched = True
                break

            await asyncio.sleep(0.5)

        assigned_number = result.number
        assigned_area_code = (
            assigned_number[2:5] if assigned_number.startswith("+1") else None
        )
        fallback_applied = bool(
            area_code and assigned_area_code and assigned_area_code != area_code
        )

        # Determine same-state using the live index (already cached from above)
        same_state = True
        if fallback_applied and area_code and assigned_area_code:
            by_state = await self._get_area_codes_by_state()
            req_state = next(
                (s for s, codes in by_state.items() if area_code in codes), None
            )
            asgn_state = next(
                (s for s, codes in by_state.items() if assigned_area_code in codes),
                None,
            )
            same_state = req_state is not None and req_state == asgn_state
            logger.warning(
                f"Area code fallback: requested={area_code}({req_state}), "
                f"assigned={assigned_area_code}({asgn_state}), same_state={same_state}"
            )

        return {
            "id": result.id,
            "phone_number": assigned_number,
            "cost": result.total_cost,
            "ends_at": result.ends_at.isoformat(),
            "tv_object": result,
            "attempt_count": attempt_count,
            "retry_attempts": attempt_count - 1,  # Legacy Phase 4 compatibility
            "area_code_matched": area_code_matched,
            "voip_rejected": voip_rejected,
            "fallback_applied": fallback_applied,
            "requested_area_code": area_code,
            "assigned_area_code": assigned_area_code,
            "same_state_fallback": same_state,
        }

    # Backward compat alias used by verification_routes.py
    def _build_carrier_preference(self, carrier: str) -> List[str]:
        """Return carrier preference list. Requested carrier is first and only option
        to ensure the assigned number matches the user's selection."""
        normalized = (
            carrier.lower().replace(" ", "_").replace("&", "").replace("-", "_")
        )
        return [normalized]

    async def purchase_number(
        self,
        service: str,
        country: str = "US",
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            from app.core.config import get_settings

            settings = get_settings()

            result = await self.create_verification(
                service=service, area_code=area_code
            )

            # Apply markup to cost
            raw_cost = result["cost"]
            marked_up_cost = round(raw_cost * settings.price_markup, 2)

            logger.info(
                f"Purchase cost: raw=${raw_cost:.2f}, marked_up=${marked_up_cost:.2f} (markup={settings.price_markup}x)"
            )

            return {
                "success": True,
                "verification_id": result["id"],
                "phone_number": result["phone_number"],
                "service": service,
                "country": "US",
                "cost": marked_up_cost,
                "raw_cost": raw_cost,
                "fallback_applied": result["fallback_applied"],
                "requested_area_code": result["requested_area_code"],
                "assigned_area_code": result["assigned_area_code"],
                "same_state_fallback": result["same_state_fallback"],
            }
        except Exception as e:
            logger.error(f"purchase_number failed: {e}")
            return {"success": False, "error": str(e), "verification_id": None}

    async def get_sms(self, verification_id: str, created_after=None) -> Dict[str, Any]:
        """Fetch SMS for a verification, filtering out stale messages.

        Args:
            verification_id: The TextVerified activation ID.
            created_after: datetime — only return SMS received after this time.
                           Prevents stale SMS from recycled numbers being delivered.
        """
        if not self.enabled:
            return {"success": False, "error": "Service not available", "sms": None}
        try:
            sms_list = await asyncio.to_thread(
                lambda: list(self.client.sms.list(verification_id))
            )
            if sms_list:
                # CRITICAL: Filter out stale SMS from recycled numbers.
                # TextVerified reuses numbers — sms.list() returns ALL historical
                # SMS on that activation, including codes from prior activations.
                # Only accept SMS received AFTER this verification was created.
                if created_after is not None:
                    from datetime import timezone

                    # Normalise created_after to UTC-aware
                    if created_after.tzinfo is None:
                        created_after = created_after.replace(tzinfo=timezone.utc)

                    fresh = []
                    for sms in sms_list:
                        sms_time = getattr(sms, "created_at", None)
                        if sms_time is None:
                            continue
                        if sms_time.tzinfo is None:
                            sms_time = sms_time.replace(tzinfo=timezone.utc)
                        if sms_time >= created_after:
                            fresh.append(sms)

                    if not fresh:
                        # No fresh SMS yet — still pending
                        return {"success": False, "sms": None, "code": None}
                    sms_list = fresh

                latest = sms_list[-1]
                sms_content = latest.sms_content or ""
                # CRITICAL: Use TextVerified's parsed_code first — it handles
                # hyphenated codes (e.g. 806-185), alphanumeric codes, etc.
                parsed = getattr(latest, "parsed_code", None) or ""
                if not parsed:
                    import re

                    hyphen = re.findall(r"\b(\d{3}-\d{3})\b", sms_content)
                    plain = re.findall(r"\b(\d{4,8})\b", sms_content)
                    if hyphen:
                        parsed = hyphen[-1].replace("-", "")
                    elif plain:
                        parsed = plain[-1]
                return {
                    "success": True,
                    "sms": sms_content,
                    "code": parsed,
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

    # --- RESERVATIONS (RENTALS) ---

    async def create_reservation(
        self, service: str, country: str = "US", duration_hours: float = 24.0
    ) -> Dict[str, Any]:
        """Create a long-term reservation (rental) for a service."""
        if not self.enabled:
            raise RuntimeError("TextVerified service disabled")

        try:
            # Map hours to minutes for the API
            duration_minutes = int(duration_hours * 60)

            # TextVerified reservations are US-only in standard API
            reservation = await asyncio.to_thread(
                self.client.reservations.create,
                service_name=service,
                duration=duration_minutes,
            )

            # Costs are marked up in the platform level (RentalService)
            # but we return raw cost here for accounting
            return {
                "id": reservation.id,
                "phone_number": reservation.number,
                "cost": float(reservation.total_cost),
                "ends_at": reservation.ends_at,
                "status": reservation.state.value,
                "tv_object": reservation,
            }
        except Exception as e:
            logger.error(f"TextVerified reservation creation failed: {e}")
            raise

    async def get_reservation_messages(
        self, reservation_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch all messages for an active reservation."""
        if not self.enabled:
            return []
        try:
            # Reservations use a different message retrieval endpoint
            messages = await asyncio.to_thread(
                self.client.reservations.messages, reservation_id
            )
            return [
                {
                    "id": m.id,
                    "text": m.sms_content,
                    "code": m.parsed_code,
                    "received_at": m.created_at.isoformat(),
                }
                for m in messages
            ]
        except Exception as e:
            logger.error(f"Failed to fetch reservation messages: {e}")
            return []

    async def extend_reservation(self, reservation_id: str, extra_hours: float) -> bool:
        """Extend an existing reservation."""
        if not self.enabled:
            return False
        try:
            extra_minutes = int(extra_hours * 60)
            await asyncio.to_thread(
                self.client.reservations.extend, reservation_id, extra_minutes
            )
            return True
        except Exception as e:
            logger.error(f"Failed to extend reservation: {e}")
            return False

    async def check_reservation_expiry(self, reservation_id: str) -> Dict[str, Any]:
        """Check if a reservation is nearing expiry (v6.0 Institutional Mastery)."""
        if not self.enabled:
            return {"status": "unknown"}
        try:
            res = await asyncio.to_thread(self.client.reservations.get, reservation_id)
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            ends_at = res.ends_at
            if ends_at.tzinfo is None:
                ends_at = ends_at.replace(tzinfo=timezone.utc)

            remaining_minutes = (ends_at - now).total_seconds() / 60

            return {
                "id": res.id,
                "status": res.state.value,
                "remaining_minutes": remaining_minutes,
                "is_critical": remaining_minutes < 15,
                "ends_at": ends_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to check reservation expiry: {e}")
            return {"status": "error"}

    def _set_balance_cache(self, balance: float) -> None:
        """Cache balance value (used in tests)."""
        try:
            redis = _get_redis()
            redis.setex("textverified:balance", 300, str(balance))
        except Exception:
            pass

    async def buy_number(self, country: str, service: str, **kwargs) -> Dict[str, Any]:
        """Alias for purchase_number used by tests."""
        return await self.purchase_number(service=service, country=country, **kwargs)

    async def get_health_status(self) -> Dict[str, Any]:
        """Return service health status."""
        if not self.enabled:
            return {
                "status": "error",
                "enabled": False,
                "error": "Service not configured",
            }
        try:
            balance_data = await self.get_balance()
            return {
                "status": "operational",
                "enabled": True,
                "balance": balance_data.get("balance", 0.0),
            }
        except Exception as e:
            return {"status": "error", "enabled": True, "error": str(e)}

    async def get_account_balance(self) -> float:
        """Legacy alias — returns balance as float."""
        data = await self.get_balance()
        return data.get("balance", 0.0)

    async def cancel_number(self, verification_id: str) -> bool:
        """Legacy alias for cancel_verification."""
        result = await self.cancel_verification(verification_id)
        return result.get("success", False)

    async def get_number(
        self, service: str, country: str = "US", **kwargs
    ) -> Dict[str, Any]:
        """Legacy alias for buy_number."""
        return await self.buy_number(country=country, service=service, **kwargs)
