# Smart Multi-Provider Routing — Production Implementation Plan

**Version**: 1.0.0  
**Status**: Planning  
**Priority**: Critical  
**Target**: Q2 2026  
**Risk Level**: HIGH — touches purchase flow, billing, polling, and refunds

---

## ⚠️ Why This Document Exists

A single misplan **will** break production. The purchase flow (`purchase_endpoints.py`) is the revenue-critical path — it handles:
- Balance checks and credit deduction
- TextVerified API calls
- Verification record creation
- SMS polling kickoff
- Refund processing
- Carrier analytics
- Idempotency
- Notifications

Adding a second provider means **every one of these steps** must work for both providers, or money is lost and users see errors.

---

## 🎯 Goal

Route SMS verification requests to the optimal provider automatically:
- **US requests** → TextVerified (existing, proven)
- **International requests** → SMSPool (new)
- **Failover** → If primary fails, try secondary
- **Zero downtime** — feature-flagged, gradual rollout

---

## 🧠 Current Architecture (What We're Changing)

```
purchase_endpoints.py
  └─→ TextVerifiedService.create_verification()
        └─→ textverified Python library
              └─→ TextVerified API
                    └─→ Phone number + activation_id

sms_polling_service.py
  └─→ TextVerifiedService.poll_sms_standard()
        └─→ textverified library sms.incoming()
              └─→ SMS code

refund flow
  └─→ TextVerifiedService.report_verification()
        └─→ TextVerified refund
```

**Problem**: Everything is hardcoded to TextVerified. There is no abstraction layer.

---

## 🏗️ Target Architecture

```
purchase_endpoints.py
  └─→ ProviderRouter.purchase_number()
        ├─→ [US]  TextVerifiedAdapter.purchase_number()
        │         └─→ TextVerified API (existing flow, unchanged)
        └─→ [INT] SMSPoolAdapter.purchase_number()
                  └─→ SMSPool API (new)

sms_polling_service.py
  └─→ ProviderRouter.check_messages()
        ├─→ [textverified] TextVerifiedAdapter.check_messages()
        │                   └─→ sms.incoming() (existing)
        └─→ [smspool]      SMSPoolAdapter.check_messages()
                            └─→ /sms/check (new)

refund flow
  └─→ ProviderRouter.report_failed()
        ├─→ [textverified] TextVerifiedService.report_verification()
        └─→ [smspool]      SMSPoolAdapter.cancel_order()
```

---

## 🚨 Production Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SMSPool API down on first deploy | International users get 503 | Feature flag `SMSPOOL_ENABLED=false` default. US flow untouched. |
| Polling service doesn't know which provider | SMS never received, user charged | `verification.provider` column already exists. Polling reads it. |
| Refund flow calls wrong provider | Money lost | Refund reads `verification.provider` and dispatches correctly. |
| SMSPool returns VOIP number | Service rejects code | Pre-purchase `paid_lookup` validates line type. Cancel + retry if VOIP. |
| SMSPool balance runs out | Purchases fail silently | Balance monitor alerts at $50. Auto-disable provider at $10. |
| Database migration fails | All purchases broken | Migration is additive only (new columns). No column drops. |
| Pricing mismatch | User overcharged or undercharged | SMSPool cost fetched BEFORE purchase. Markup applied same as TV. |
| Idempotency breaks | Duplicate charges | Idempotency key includes provider name. |
| SMS polling interval wrong for SMSPool | Codes missed or API hammered | SMSPool uses 5s interval (their recommendation). Separate config. |
| Carrier filter mapping wrong | Wrong operator selected, low success rate | Use SMSPool `/request/success_rate` (FREE) to auto-select best operator. |

---

## 📦 File Changes — Complete Inventory

### New Files (7)

| File | Purpose |
|------|---------|
| `app/services/providers/__init__.py` | Package init |
| `app/services/providers/base_provider.py` | Abstract interface — all providers implement this |
| `app/services/providers/textverified_adapter.py` | Wraps existing `TextVerifiedService` to match interface |
| `app/services/providers/smspool_adapter.py` | SMSPool API client + adapter |
| `app/services/providers/provider_router.py` | Routes requests to correct provider |
| `app/services/providers/smspool_filters.py` | Carrier/operator mapping for SMSPool |
| `tests/unit/test_provider_router.py` | Tests for routing logic |

### Modified Files (6)

| File | Change | Risk |
|------|--------|------|
| `app/core/config.py` | Add SMSPool config vars | LOW — additive only |
| `app/api/verification/purchase_endpoints.py` | Use `ProviderRouter` instead of direct `TextVerifiedService` | HIGH — revenue path |
| `app/services/sms_polling_service.py` | Dispatch polling by `verification.provider` | HIGH — SMS delivery |
| `app/models/verification.py` | Add `provider_order_id`, `provider_cost`, `routing_reason` columns | LOW — additive |
| `app/services/auto_refund_service.py` | Dispatch refund by provider | MEDIUM — money |
| `app/services/pricing_calculator.py` | Add SMSPool pricing tier | MEDIUM — billing |

### NOT Modified (Critical)

| File | Why |
|------|-----|
| `app/services/textverified_service.py` | **DO NOT TOUCH.** 18 bugs fixed in this file. Adapter wraps it. |
| `app/api/verification/outcome_endpoint.py` | Provider-agnostic already (reads from DB) |
| `templates/voice_verify_modern.html` | Frontend unchanged — same API contract |
| `templates/sms_verify_modern.html` | Frontend unchanged — same API contract |

---

## 📐 Interface Contract

```python
# app/services/providers/base_provider.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PurchaseResult:
    """Unified result from any provider."""
    phone_number: str
    order_id: str          # Provider-specific ID (TV activation_id or SMSPool order_id)
    cost: float            # Raw provider cost (before markup)
    expires_at: str        # ISO format
    provider: str          # "textverified" or "smspool"
    operator: Optional[str] = None
    area_code_matched: bool = True
    carrier_matched: bool = True
    real_carrier: Optional[str] = None
    voip_rejected: bool = False
    fallback_applied: bool = False
    requested_area_code: Optional[str] = None
    assigned_area_code: Optional[str] = None
    same_state_fallback: bool = True
    retry_attempts: int = 0
    tv_object: Any = None  # Only for TextVerified (needed by poll_sms_standard)

@dataclass
class MessageResult:
    """Unified SMS/voice message result."""
    text: str
    code: str
    received_at: str  # ISO format

class SMSProvider(ABC):
    """Every provider MUST implement these 4 methods. No exceptions."""

    @abstractmethod
    async def purchase_number(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
    ) -> PurchaseResult:
        """Buy a number. Returns unified PurchaseResult."""
        ...

    @abstractmethod
    async def check_messages(self, order_id: str, created_after=None) -> List[MessageResult]:
        """Check for received messages. Returns empty list if none."""
        ...

    @abstractmethod
    async def report_failed(self, order_id: str) -> bool:
        """Report failed verification for refund. Returns True if accepted."""
        ...

    @abstractmethod
    async def cancel(self, order_id: str) -> bool:
        """Cancel an active verification. Returns True if cancelled."""
        ...
```

---

## 🔀 Provider Router Logic

```python
# app/services/providers/provider_router.py

class ProviderRouter:
    """Routes to correct provider. Zero magic — explicit rules only."""

    def __init__(self):
        self._textverified = None  # Lazy init
        self._smspool = None       # Lazy init

    def get_provider(self, country: str) -> SMSProvider:
        """Determine provider for a country.

        Rules (in order):
        1. If SMSPOOL_ENABLED=false → always TextVerified
        2. If country == "US" → TextVerified
        3. If country is international → SMSPool
        4. If SMSPool balance < $10 → TextVerified (emergency fallback)
        """
        settings = get_settings()

        # Rule 1: Feature flag
        if not getattr(settings, 'smspool_enabled', False):
            return self._get_textverified()

        # Rule 2: US → TextVerified
        if country.upper() == "US":
            return self._get_textverified()

        # Rule 3: International → SMSPool
        return self._get_smspool()

    async def purchase_with_failover(
        self,
        service: str,
        country: str,
        area_code: Optional[str] = None,
        carrier: Optional[str] = None,
        capability: str = "sms",
    ) -> PurchaseResult:
        """Purchase with automatic failover.

        CRITICAL: Failover only happens if primary COMPLETELY fails
        (network error, 500, timeout). NOT for "no inventory" — that's
        expected and should surface to user.
        """
        primary = self.get_provider(country)
        routing_reason = f"country={country}"

        try:
            result = await primary.purchase_number(
                service=service,
                country=country,
                area_code=area_code,
                carrier=carrier,
                capability=capability,
            )
            result.routing_reason = routing_reason
            return result

        except Exception as e:
            logger.error(f"Primary provider failed for {country}: {e}")

            # Only failover for infrastructure errors, NOT business errors
            if "insufficient balance" in str(e).lower():
                raise  # Don't failover — provider is out of money
            if "no inventory" in str(e).lower():
                raise  # Don't failover — genuinely unavailable
            if "service not found" in str(e).lower():
                raise  # Don't failover — service doesn't exist

            # Infrastructure failure → try other provider
            if not getattr(get_settings(), 'enable_provider_failover', True):
                raise

            secondary = self._get_failover(country)
            if secondary is None:
                raise  # No failover available

            logger.warning(f"Failing over to {secondary.__class__.__name__}")
            result = await secondary.purchase_number(
                service=service,
                country=country,
                area_code=area_code,
                carrier=carrier,
                capability=capability,
            )
            result.routing_reason = f"failover from {primary.__class__.__name__}"
            return result
```

---

## 🔌 SMSPool Adapter — Critical Implementation Details

```python
# app/services/providers/smspool_adapter.py

class SMSPoolAdapter(SMSProvider):
    """SMSPool API adapter.

    CRITICAL API BEHAVIOR (from SMSPool docs):
    - /order/sms returns: {success: 1, number: str, order_id: str, cost: float}
    - /sms/check returns: {status: 1|2|3, sms: str, full_sms: str}
      - status 1 = waiting
      - status 2 = expired
      - status 3 = received
    - /sms/cancel returns: {success: 1}
    - /request/success_rate is FREE — use it to auto-select operators
    - /carrier/paid_lookup costs $0.005 — use sparingly, cache results

    GOTCHAS:
    - SMSPool uses POST for everything (not GET)
    - API key goes in request body as "key", not in headers
    - Order IDs are integers, not UUIDs
    - Phone numbers include country code (no +)
    - "operator" parameter is case-sensitive
    """

    async def purchase_number(self, service, country, area_code=None,
                              carrier=None, capability="sms") -> PurchaseResult:
        # 1. Auto-select best operator (FREE endpoint)
        operator = carrier or await self._auto_select_operator(country, service)

        # 2. Purchase number
        resp = await self._post("/order/sms", {
            "key": self.api_key,
            "country": self._map_country(country),
            "service": self._map_service(service),
            "operator": operator,
        })

        if resp.get("success") != 1:
            raise RuntimeError(f"SMSPool purchase failed: {resp.get('message')}")

        phone = resp["number"]
        order_id = str(resp["order_id"])

        # 3. Validate line type (costs $0.005, but prevents wasted purchases)
        if capability == "sms":
            lookup = await self._carrier_lookup(phone)
            if lookup.get("carrier_type", "").lower() in ("voip", "landline"):
                await self.cancel(order_id)
                raise RuntimeError(
                    f"SMSPool returned {lookup['carrier_type']} number, not mobile"
                )

        return PurchaseResult(
            phone_number=f"+{phone}",
            order_id=order_id,
            cost=float(resp.get("cost", 0)),
            expires_at=...,  # Calculate from now + 20min (SMSPool default)
            provider="smspool",
            operator=operator,
            area_code_matched=True,  # N/A for international
            carrier_matched=bool(operator),
            real_carrier=operator,
            voip_rejected=False,
            retry_attempts=0,
        )

    async def check_messages(self, order_id, created_after=None) -> list:
        resp = await self._post("/sms/check", {
            "key": self.api_key,
            "orderid": order_id,
        })

        if resp.get("status") == 3:  # Received
            sms_text = resp.get("full_sms", resp.get("sms", ""))
            code = self._extract_code(sms_text)
            return [MessageResult(
                text=sms_text,
                code=code,
                received_at=datetime.now(timezone.utc).isoformat(),
            )]

        return []  # Still waiting or expired

    async def report_failed(self, order_id) -> bool:
        # SMSPool: cancel = refund (no separate report endpoint)
        return await self.cancel(order_id)

    async def cancel(self, order_id) -> bool:
        resp = await self._post("/sms/cancel", {
            "key": self.api_key,
            "orderid": order_id,
        })
        return resp.get("success") == 1
```

---

## 🔧 Config Changes

```python
# app/core/config.py — ADD these fields (do not modify existing fields)

# SMSPool provider
smspool_api_key: Optional[str] = None
smspool_enabled: bool = False          # OFF by default — flip when ready
smspool_timeout: int = 30
smspool_max_retries: int = 3
smspool_polling_interval: float = 5.0  # SMSPool recommends 5s
smspool_min_balance_threshold: float = 10.0  # Auto-disable below this

# Multi-provider routing
enable_provider_failover: bool = True
routing_strategy: str = "country_based"  # Only strategy for now
```

---

## 📊 Database Migration

```sql
-- Additive only. No drops. No renames. Safe to run on live DB.

ALTER TABLE verifications ADD COLUMN IF NOT EXISTS provider_order_id VARCHAR(100);
ALTER TABLE verifications ADD COLUMN IF NOT EXISTS provider_cost FLOAT DEFAULT 0.0;
ALTER TABLE verifications ADD COLUMN IF NOT EXISTS routing_reason VARCHAR(200);
```

The `provider` column already exists (`default="textverified"`). No change needed.

---

## 🔄 Polling Service Changes

**Current** (`sms_polling_service.py`):
- Hardcoded to `TextVerifiedService`
- Uses `poll_sms_standard()` which requires TV's `VerificationExpanded` object
- Background service filters by `provider == "textverified"`

**Required changes**:

```python
# sms_polling_service.py — _poll_verification()

# BEFORE (line ~55):
tv_details = await self.textverified.get_verification_details(verification.activation_id)

# AFTER:
if verification.provider == "textverified":
    # Existing TextVerified flow — UNCHANGED
    tv_details = await self.textverified.get_verification_details(verification.activation_id)
    # ... rest of existing TV polling logic ...

elif verification.provider == "smspool":
    # SMSPool polling — simple check loop
    await self._poll_smspool(verification, db, timeout_seconds)
    return

# NEW METHOD:
async def _poll_smspool(self, verification, db, timeout_seconds):
    """Poll SMSPool for messages using /sms/check endpoint."""
    from app.services.providers.smspool_adapter import SMSPoolAdapter

    adapter = SMSPoolAdapter()
    elapsed = 0
    interval = settings.smspool_polling_interval  # 5s

    while elapsed < timeout_seconds:
        messages = await adapter.check_messages(
            verification.provider_order_id or verification.activation_id
        )

        if messages:
            msg = messages[0]
            verification.status = "completed"
            verification.outcome = "completed"
            verification.completed_at = datetime.now(timezone.utc)
            verification.sms_text = msg.text
            verification.sms_code = msg.code
            db.commit()

            # Notify + forward (same as TV flow)
            try:
                dispatcher = NotificationDispatcher(db)
                dispatcher.on_sms_received(verification)
            except Exception:
                pass

            logger.info(f"✅ SMSPool SMS received for {verification.id}")
            return

        await asyncio.sleep(interval)
        elapsed += interval

    # Timeout — cancel order for refund
    await self._handle_timeout(verification, db)
```

**Background service filter** — change from:
```python
.filter(Verification.provider == "textverified")
```
to:
```python
.filter(Verification.status == "pending")  # Poll ALL pending, regardless of provider
```

---

## 💰 Pricing Integration

```python
# app/services/pricing_calculator.py — ADD to calculate_sms_cost()

# After existing tier-based pricing:
if provider == "smspool":
    # SMSPool base cost comes from their API response
    # Apply same markup as TextVerified
    base_cost = smspool_cost  # From purchase response
    marked_up = base_cost * settings.price_markup  # Same 1.8x markup
    # No area_code_surcharge (not supported)
    # No carrier_surcharge (operator selection is free on SMSPool)
```

---

## 🔀 Purchase Endpoint Changes

The key change in `purchase_endpoints.py` is replacing the direct `TextVerifiedService` call with `ProviderRouter`:

```python
# BEFORE (line ~175):
textverified_result = await tv_service.create_verification(
    service=request.service,
    country=request.country,
    area_code=area_code,
    carrier=carrier,
)

# AFTER:
from app.services.providers.provider_router import ProviderRouter

provider_router = ProviderRouter()
purchase_result = await provider_router.purchase_with_failover(
    service=request.service,
    country=request.country,
    area_code=area_code,
    carrier=carrier,
    capability=request.capability,
)

# Map PurchaseResult to existing variable names (minimal change to rest of file)
textverified_result = {
    "id": purchase_result.order_id,
    "phone_number": purchase_result.phone_number,
    "cost": purchase_result.cost,
    "ends_at": purchase_result.expires_at,
    "tv_object": purchase_result.tv_object,
    "retry_attempts": purchase_result.retry_attempts,
    "area_code_matched": purchase_result.area_code_matched,
    "carrier_matched": purchase_result.carrier_matched,
    "real_carrier": purchase_result.real_carrier,
    "voip_rejected": purchase_result.voip_rejected,
    "fallback_applied": purchase_result.fallback_applied,
    "requested_area_code": purchase_result.requested_area_code,
    "assigned_area_code": purchase_result.assigned_area_code,
    "same_state_fallback": purchase_result.same_state_fallback,
}
provider_name = purchase_result.provider  # "textverified" or "smspool"
```

**Everything below this point in purchase_endpoints.py stays the same** — the verification record creation, balance deduction, transaction recording, notifications, and polling kickoff all work because they read from `textverified_result` dict (which we populated from `PurchaseResult`).

The only additional change:
```python
# When creating Verification record, also store:
provider_order_id=purchase_result.order_id,
provider_cost=purchase_result.cost,
routing_reason=purchase_result.routing_reason,
```

---

## 🧪 Testing Strategy

### Unit Tests (MUST pass before any deploy)

```
test_provider_router.py:
  ✓ US routes to TextVerified
  ✓ GB routes to SMSPool
  ✓ DE routes to SMSPool
  ✓ SMSPOOL_ENABLED=false → always TextVerified
  ✓ Failover on infrastructure error
  ✓ NO failover on "no inventory"
  ✓ NO failover on "insufficient balance"

test_smspool_adapter.py:
  ✓ Purchase returns PurchaseResult
  ✓ VOIP number rejected and cancelled
  ✓ check_messages returns MessageResult on status=3
  ✓ check_messages returns [] on status=1
  ✓ cancel sends correct payload
  ✓ Auto-select operator uses success_rate endpoint

test_textverified_adapter.py:
  ✓ Wraps existing TextVerifiedService correctly
  ✓ PurchaseResult includes tv_object
  ✓ All existing TV tests still pass (regression)

test_polling_dispatch.py:
  ✓ provider="textverified" → existing TV polling
  ✓ provider="smspool" → SMSPool polling loop
  ✓ Timeout triggers correct refund per provider
```

### Integration Tests (staging only)

```
test_smspool_live.py:
  ✓ Purchase real number from SMSPool (test service)
  ✓ Check messages returns data
  ✓ Cancel order works
  ✓ Balance check works

test_routing_live.py:
  ✓ US request → TextVerified number
  ✓ GB request → SMSPool number
  ✓ Full flow: purchase → poll → receive → complete
```

---

## 🚀 Deployment Plan — Zero Downtime

### Phase 1: Foundation (Week 1) — NO production impact

1. Create `app/services/providers/` package with all 7 files
2. Add config vars with `smspool_enabled: bool = False`
3. Run database migration (additive columns only)
4. Deploy — **nothing changes** because `smspool_enabled=false`

### Phase 2: Wire Up (Week 2) — Still no production impact

1. Modify `purchase_endpoints.py` to use `ProviderRouter`
2. Modify `sms_polling_service.py` to dispatch by provider
3. Deploy — **still nothing changes** because router returns TextVerified for everything when `smspool_enabled=false`

### Phase 3: Enable (Week 3) — Controlled rollout

1. Set `SMSPOOL_API_KEY` in production env
2. Set `SMSPOOL_ENABLED=true`
3. Test with ONE international request manually
4. Monitor for 24 hours
5. If stable → announce international support

### Phase 4: Optimize (Week 4)

1. Enable failover: `ENABLE_PROVIDER_FAILOVER=true`
2. Add balance monitoring alerts
3. Tune SMSPool polling interval based on real data
4. Add success rate dashboard

### Rollback at ANY phase

```bash
# Instant rollback — no deploy needed
SMSPOOL_ENABLED=false
# All requests route to TextVerified. SMSPool code is dead code.
```

---

## 📋 Implementation Checklist

### Phase 1: Foundation
- [ ] Create `app/services/providers/__init__.py`
- [ ] Create `app/services/providers/base_provider.py` with `SMSProvider`, `PurchaseResult`, `MessageResult`
- [ ] Create `app/services/providers/textverified_adapter.py` wrapping existing service
- [ ] Create `app/services/providers/smspool_adapter.py` with full API client
- [ ] Create `app/services/providers/smspool_filters.py` with operator mapping
- [ ] Create `app/services/providers/provider_router.py` with routing logic
- [ ] Add SMSPool config vars to `app/core/config.py`
- [ ] Run DB migration (3 additive columns)
- [ ] Write unit tests for router, adapters, filters
- [ ] All existing tests still pass (regression check)
- [ ] Deploy with `SMSPOOL_ENABLED=false`

### Phase 2: Integration
- [ ] Modify `purchase_endpoints.py` to use `ProviderRouter`
- [ ] Modify `sms_polling_service.py` to dispatch by provider
- [ ] Modify `auto_refund_service.py` to dispatch by provider
- [ ] Update `pricing_calculator.py` for SMSPool pricing
- [ ] Integration tests pass in staging
- [ ] Deploy with `SMSPOOL_ENABLED=false`

### Phase 3: Go Live
- [ ] Set `SMSPOOL_API_KEY` in production
- [ ] Set `SMSPOOL_ENABLED=true`
- [ ] Manual test: purchase GB number
- [ ] Manual test: receive SMS on GB number
- [ ] Manual test: timeout → refund on SMSPool
- [ ] Monitor 24h: no errors in `app.log`
- [ ] Monitor 24h: SMSPool balance stable

### Phase 4: Harden
- [ ] Enable failover
- [ ] Balance monitoring alerts ($50, $25, $10)
- [ ] Auto-disable at $10 balance
- [ ] Success rate tracking per country/operator
- [ ] Update README.md with international support

---

## 🗺️ Service/Country Mapping

### SMSPool Service ID Mapping

SMSPool uses numeric service IDs. We need a mapping:

```python
SMSPOOL_SERVICE_MAP = {
    "google": 1,
    "facebook": 2,
    "whatsapp": 3,
    "telegram": 4,
    "instagram": 5,
    "twitter": 6,
    "tiktok": 7,
    "discord": 8,
    "uber": 9,
    "amazon": 10,
    # ... fetch full list from /service/retrieve on startup
}
```

**CRITICAL**: This map must be fetched from SMSPool API on startup and cached. Hardcoding will break when they add/change services.

### Country Code Mapping

SMSPool uses numeric country IDs, not ISO codes:

```python
SMSPOOL_COUNTRY_MAP = {
    "US": 1,
    "GB": 2,
    "DE": 3,
    # ... fetch from /country/retrieve on startup
}
```

**Same rule**: Fetch on startup, cache for 24h.

---

## 💡 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Adapter pattern (not rewrite) | TextVerified service has 18 bug fixes. Wrapping it preserves all fixes. |
| Feature flag (not gradual %) | Simpler. Either SMSPool is on or off. No split-brain. |
| Country-based routing (not cost-based) | Cost optimization is premature. Get it working first. |
| No shared number pool | TextVerified and SMSPool numbers are completely separate. No cross-provider polling. |
| SMSPool polling is simple loop | SMSPool doesn't have a streaming/webhook API. Polling at 5s is their recommendation. |
| Carrier lookup is optional | $0.005/lookup adds up. Only use for mobile validation, not carrier matching. |
| Same markup for both providers | Users don't know/care which provider. Same price = simple. |

---

## 📞 Emergency Contacts

- **SMSPool API docs**: https://www.smspool.net/article/how-to-use-the-smspool-api
- **SMSPool support**: support@smspool.net
- **TextVerified** (existing): Already configured
- **Rollback command**: `SMSPOOL_ENABLED=false` (env var, no deploy needed)

---

**Owner**: Backend Team  
**Reviewer**: CTO  
**Estimated Effort**: 4 weeks  
**Confidence Level**: High (additive changes, feature-flagged, instant rollback)
