# Smart Multi-Provider Routing

Version 1.1.0 | Status: In Progress | Last Updated: April 13, 2026

See architecture diagrams -> docs/tasks/MULTI_PROVIDER_ARCHITECTURE.md

---

## What This Does

Routes every SMS verification request to the best available provider automatically.

    US request  ->  TextVerified  (proven, area code support)
    GB request  ->  Telnyx or 5sim  (international)
    Any failure ->  Auto-failover to next provider

Users never see which provider handled their request. Same API, same price, same experience.

---

## Why It Was Built

The original codebase was hardcoded to TextVerified only. No abstraction, no fallback. If TextVerified went down or didn't support a country, the user got an error and lost credits.

This adds Telnyx (enterprise, 190+ countries) and 5sim (cost-effective, 100+ countries) behind a single router that picks the right one automatically.

---

## How Routing Works

    Request comes in
        |
        v
    Is country == US?
        Yes  ->  TextVerified
        No   ->  Is TELNYX_ENABLED?
                    Yes + prefer_enterprise=true  ->  Telnyx
                    No  ->  Is FIVESIM_ENABLED?
                                Yes  ->  5sim
                                No   ->  Telnyx
                                No   ->  TextVerified (last resort)

    If primary fails with a network/infra error:
        ->  Try failover provider
        ->  If failover also fails  ->  Raise error to user

    If primary fails with a business error (no inventory, insufficient balance):
        ->  Raise immediately, no failover

---

## Failover Rules

Failover only triggers on infrastructure errors, not business errors.

Infrastructure errors (DO failover):
- Network timeout
- Connection refused
- HTTP 500 from provider

Business errors (DO NOT failover):
- "No inventory available"
- "Insufficient balance"
- "Service not found"
- "Invalid API key"

Failover chain:
    TextVerified fails  ->  try Telnyx  ->  try 5sim
    Telnyx fails        ->  try 5sim    ->  try TextVerified
    5sim fails          ->  try Telnyx  ->  try TextVerified

---

## Files

New files added:

    app/services/providers/__init__.py          package init
    app/services/providers/base_provider.py     abstract interface all providers implement
    app/services/providers/textverified_adapter.py  wraps existing TextVerifiedService
    app/services/providers/telnyx_adapter.py    Telnyx API client
    app/services/providers/fivesim_adapter.py   5sim API client
    app/services/providers/provider_router.py   routing + failover logic

Modified files:

    app/core/config.py                          added TELNYX_API_KEY, FIVESIM_API_KEY, etc.
    app/api/verification/purchase_endpoints.py  uses ProviderRouter instead of TextVerifiedService directly
    app/services/sms_polling_service.py         dispatches polling by verification.provider field

Do not touch:

    app/services/textverified_service.py        has 18 bug fixes, adapter wraps it
    app/api/verification/outcome_endpoint.py    already provider-agnostic

---

## Provider Interface

Every provider implements the same 4 methods:

    purchase_number(service, country, area_code, carrier, capability)
        ->  PurchaseResult

    check_messages(order_id, created_after)
        ->  list of MessageResult

    report_failed(order_id)
        ->  bool (True if refund accepted)

    cancel(order_id)
        ->  bool (True if cancelled)

PurchaseResult carries: phone_number, order_id, cost, expires_at, provider, area_code_matched, carrier_matched, real_carrier, voip_rejected, fallback_applied, retry_attempts, routing_reason.

MessageResult carries: text, code, received_at.

---

## Purchase Flow (Before vs After)

Before:
    purchase_endpoints.py
        ->  TextVerifiedService.create_verification()
        ->  TextVerified API
        ->  phone number

After:
    purchase_endpoints.py
        ->  ProviderRouter.purchase_with_failover()
        ->  get_provider(country)  ->  correct adapter
        ->  adapter.purchase_number()
        ->  provider API
        ->  PurchaseResult  ->  mapped back to existing dict format

The rest of purchase_endpoints.py (balance deduction, DB record, notifications, polling kickoff) is unchanged. The PurchaseResult is mapped to the same dict shape the rest of the file already expects.

---

## Polling Flow (Before vs After)

Before:
    sms_polling_service.py
        ->  always TextVerified
        ->  poll_sms_standard()

After:
    sms_polling_service.py
        ->  read verification.provider from DB
        ->  "textverified"  ->  _poll_textverified()  (existing, unchanged)
        ->  "telnyx"        ->  _poll_telnyx()         (5s loop)
        ->  "5sim"          ->  _poll_fivesim()        (5s loop)
        ->  unknown         ->  _handle_timeout()

Timeout handling also dispatches by provider:
    "textverified"  ->  textverified.report_verification()  (TV refunds automatically)
    "telnyx"        ->  telnyx.report_failed()
    "5sim"          ->  fivesim.report_failed()
    any failure     ->  platform AutoRefundService as fallback

---

## Configuration

All new providers are disabled by default. Nothing changes until you set the keys.

    TELNYX_API_KEY=           your Telnyx API key
    TELNYX_ENABLED=false      flip to true when ready
    TELNYX_TIMEOUT=30

    FIVESIM_API_KEY=          your 5sim API key
    FIVESIM_ENABLED=false     flip to true when ready
    FIVESIM_TIMEOUT=30

    ENABLE_PROVIDER_FAILOVER=true
    PREFER_ENTERPRISE_PROVIDER=false   true = Telnyx first, false = 5sim first

Rollback at any time without a deploy:
    TELNYX_ENABLED=false
    FIVESIM_ENABLED=false
    -> all traffic goes back to TextVerified

---

## Production Risks

    Provider API down on deploy
        ->  feature flags default to false, US flow untouched

    Polling doesn't know which provider
        ->  verification.provider column stores it, polling reads it

    Refund goes to wrong provider
        ->  _handle_timeout() dispatches by verification.provider

    Provider balance runs out
        ->  balance monitor (outstanding) alerts at $50/$25, disables at $10

    HTTP client connection leaks
        ->  fixed, lazy singleton client per adapter (commit ee8f376e)

    Broad exception handlers swallow errors
        ->  outstanding, 17 still need replacing (Issue 8)

---

## Implementation Checklist

Phase 1 - Foundation  (done, commit 0bcace42)
    [x]  base_provider.py with SMSProvider, PurchaseResult, MessageResult
    [x]  textverified_adapter.py wrapping existing service
    [x]  telnyx_adapter.py
    [x]  fivesim_adapter.py
    [x]  provider_router.py with routing + failover
    [x]  config.py updated with new provider settings
    [x]  all new providers disabled by default

Phase 2 - Integration  (done, commit 0bcace42)
    [x]  purchase_endpoints.py uses ProviderRouter
    [x]  sms_polling_service.py dispatches by provider
    [x]  _handle_timeout() dispatches refund by provider
    [x]  HTTP client leaks fixed (commit ee8f376e)

Phase 3 - Tests  (done, commit ee8f376e)
    [x]  Telnyx adapter: 23 tests
    [x]  5sim adapter: 25 tests
    [x]  Provider router: 23 tests
    [x]  SMS polling dispatch: 15 tests
    [x]  Medium priority services: 30 tests
    [x]  CI provider gate at 90% coverage

Phase 4 - Harden  (done, commit b98571a2 + d0e53a5d)
    [x]  Startup health checks  ->  app/services/providers/health_check.py
    [x]  Error handling  ->  replaced 17 broad except Exception with specific handlers
    [x]  Balance monitoring  ->  app/services/providers/balance_monitor.py, alerts + auto-disable
    [x]  Purchase endpoint integration tests  ->  5 tests with DB assertions
    [x]  TextVerified regression tests  ->  10 tests covering 18 bug fixes
    [x]  Load tests  ->  ProviderRoutingUser added to locustfile.py

Phase 5 - Go Live  (ready — needs API keys)
    [ ]  Set TELNYX_API_KEY + TELNYX_ENABLED=true in production
    [ ]  Set FIVESIM_API_KEY + FIVESIM_ENABLED=true in production
    [ ]  Run load test against staging: locust -f tests/load/locustfile.py ProviderRoutingUser
    [ ]  Manual test: GB number via Telnyx
    [ ]  Manual test: DE number via 5sim
    [ ]  Manual test: timeout -> refund on each provider
    [ ]  Monitor 24h, no errors
    [ ]  Enable ENABLE_PROVIDER_FAILOVER=true

---

## Key Decisions

Adapter pattern, not rewrite
    TextVerifiedService has 18 bug fixes. Wrapping it keeps all fixes intact.

Feature flags, not gradual percentage rollout
    Simpler. Provider is either on or off. No split-brain state.

Country-based routing, not cost-based
    Cost optimization is premature. Get it working reliably first.

Same markup for all providers
    Users don't know or care which provider handled their request.

Lazy singleton HTTP client
    One client per adapter instance, reused across requests. Prevents connection leaks.

---

## Provider API Notes

TextVerified
    Library: textverified Python package
    Polling: sms.incoming() with VerificationExpanded object (not string ID)
    Refund: verifications.report() triggers automatic refund

Telnyx
    Auth: Bearer token in Authorization header
    Numbers: search available_phone_numbers -> order via number_orders
    Polling: GET /messages (webhook preferred in production)
    Refund: DELETE /number_orders/{id}

5sim
    Auth: Bearer token in Authorization header
    Numbers: GET /user/buy/activation/{country}/{operator}/{service}
    Polling: GET /user/check/{order_id}  ->  status PENDING / RECEIVED / CANCELED / TIMEOUT
    Refund: GET /user/cancel/{order_id}
    Note: uses country names not ISO codes (GB -> "unitedkingdom")

---

Owner: Backend Team
Reviewer: CTO
Architecture diagrams: docs/tasks/MULTI_PROVIDER_ARCHITECTURE.md
