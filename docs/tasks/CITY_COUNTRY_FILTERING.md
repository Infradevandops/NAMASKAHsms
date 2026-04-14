# City & Country Filtering — Implementation Task

Version 1.1.0 | Status: In Progress | Updated: April 13, 2026

---

## What This Is

Retiring carrier filtering entirely. Replacing with country + city level filtering
routed intelligently to the provider that can actually honour the request.

Users get two filter dimensions:
    country  ->  ISO code (US, GB, DE, FR, IN...)
    city     ->  city name (London, Berlin, New York, Mumbai...)

The platform decides which provider handles the request based on what was asked
and what tier the user is on. Users never see provider names. Ever.

---

## Hard Rules

1. Provider names (Telnyx, 5sim, TextVerified) never appear in any HTTP response body
2. "No inventory in city" is not an error — it is a routing signal. User gets a number.
3. "No inventory in country" triggers provider failover. User gets a number.
4. Only when ALL providers have no inventory does the user see an error.
5. routing_reason is internal only — never forwarded to API response.
6. Every failure has a category. Every category has a clean user message.

---

## Provider Capability Map

    TextVerified
        country: US only
        city: yes — via area code lookup (New York -> 212/646/718, LA -> 213/310/323)
        tiers: all (area code = PAYG+)

    Telnyx
        country: 190+ countries
        city: yes — filter[locality] globally (not US-only)
        tiers: Pro/Custom only
        notes: only provider with genuine city-level filtering internationally

    5sim
        country: 100+ countries
        city: no — country level only
        tiers: PAYG+

---

## Routing Logic

    country=US, any city
        ->  TextVerified
        ->  city translated to area codes via city_to_area_code.py
        ->  unknown city -> no area code, TextVerified picks any US number
        ->  city_honoured=True if assigned area code in city list, else False

    country=international, city provided, tier=Pro or Custom
        ->  Telnyx with filter[locality]=city
        ->  if Telnyx empty for city: retry without city, city_honoured=False
        ->  if Telnyx empty for country: failover to 5sim (country level)
        ->  if all fail: surface error

    country=international, city provided, tier=PAYG
        ->  5sim (city not sent to API)
        ->  city_honoured=False, city_note="Precise city filtering requires Pro tier"

    country=international, city provided, tier=Freemium
        ->  402 before purchase: "City filtering requires PAYG tier or higher"

    country=international, no city
        ->  5sim (cheapest, country level)
        ->  Telnyx as failover if 5sim unavailable

---

## Two-Level Rerouting (No Silent Failures)

    Level 1 — City fallback (within same provider):
        Telnyx returns empty for city=London
            -> retry Telnyx without city filter
            -> city_honoured=False, city_note="No numbers in London, country-level assigned"
            -> user gets a GB number, NOT an error

    Level 2 — Provider failover (across providers):
        Telnyx returns empty for country=GB entirely
            -> failover to 5sim for GB
            -> 5sim has inventory -> success
            -> routing_reason="failover telnyx->5sim, no inventory"

    Level 3 — All providers exhausted:
        Only then does user see an error
        Message: "No numbers available for this country right now. Please try again later."
        No provider names. No technical details.

---

## Error Message Map (Definitive)

    Category                  HTTP    User Message
    ─────────────────────────────────────────────────────────────────────────
    timeout                   503     "Verification is taking longer than expected. Please try again."
    no_inventory_city         200     city_honoured=False, city_note="No numbers in [city], country-level number assigned"
    no_inventory_country      503     "No numbers available for this country right now. Please try again later."
                                      (only after all providers tried)
    unsupported_country       400     "This country is not currently supported."
    unsupported_service       400     "This service is not currently supported."
    provider_unreachable      503     "Verification service is temporarily unavailable. Please try again."
    all_providers_failed      503     "Verification is temporarily unavailable. Your credits were not charged."
    insufficient_balance      402     "Insufficient balance. Available: $X.XX, Required: $Y.YY"
    city_filter_tier_gate     402     "Precise city filtering requires Pro tier or higher."
    city_best_effort          200     city_honoured=False, city_note="Precise city filtering requires Pro tier"

---

## Tier Access

    Freemium    country: yes | city: no (402 before purchase)
    PAYG        country: yes | city: best-effort (5sim, city_honoured=False)
    Pro         country: yes | city: precise (Telnyx filter[locality])
    Custom      country: yes | city: precise (Telnyx, priority routing)

---

## Files — Complete Change List

### New Files (3)

    app/services/providers/provider_errors.py
        ProviderError exception class
        Fields: category (str), internal (str — for logs only, never shown to user)
        Categories: timeout, no_inventory_city, no_inventory_country,
                    unsupported_country, unsupported_service,
                    provider_unreachable, all_providers_failed
        USER_MESSAGES dict: category -> clean user-facing string

    app/services/providers/city_to_area_code.py
        lookup(city: str) -> List[str]  (case-insensitive, returns [] if unknown)
        50 US cities mapped to area codes

    tests/unit/providers/test_city_filtering.py
        10 routing scenario tests

### Modified Files (6)

    app/services/providers/base_provider.py
        Add to PurchaseResult:
            city_honoured: bool = True
            city_note: Optional[str] = None

    app/schemas/verification.py
        Remove: carriers field and validate_carriers validator
        Add: city field (Optional[str], max_length=100)

    app/services/providers/telnyx_adapter.py
        Raise ProviderError(category=...) not RuntimeError("Telnyx...")
        filter[national_destination_code] fires for ANY country (remove US-only guard)
        filter[locality] wired when city provided
        Empty city result -> retry without city (not raise)
        Empty country result -> ProviderError(category="no_inventory_country")

    app/services/providers/fivesim_adapter.py
        Raise ProviderError(category=...) not RuntimeError("5sim...")
        unsupported_country -> ProviderError so router can try next provider

    app/services/providers/provider_router.py
        get_provider() gains city and user_tier params
        purchase_with_failover() gains city and user_tier params
        no_inventory_city -> retry within provider (drop city)
        no_inventory_country -> failover to next provider
        All ProviderError categories translated to clean user messages at boundary
        Provider names stripped from all errors before reaching endpoints

    app/api/verification/purchase_endpoints.py
        Remove: carrier extraction, isp_filtering gate, CarrierAnalytics block
        Remove: carrier preference logging, carrier_surcharge usage
        Add: city = request.city
        Add: city_filtering tier gate
        Pass city and user_tier to router
        Catch ProviderError by category -> clean HTTP response
        No provider names in any detail= string
        Add city_honoured, city_note, requested_city to response body
        Fix: raw validation error detail (was leaking field names)

    app/services/tier_manager.py
        Replace isp_filtering with city_filtering (PAYG+)
        Add precise_city_filtering (Pro/Custom)

    app/core/tier_config.py
        Replace has_isp_filtering with has_city_filtering
        Add has_precise_city_filtering

### Database Migration (1)

    alembic/versions/xxx_city_filtering_tier_columns.py
        ADD COLUMN has_city_filtering BOOLEAN DEFAULT FALSE
        ADD COLUMN has_precise_city_filtering BOOLEAN DEFAULT FALSE
        UPDATE payg/pro/custom: has_city_filtering=TRUE
        UPDATE pro/custom: has_precise_city_filtering=TRUE
        has_isp_filtering kept for backward compat

---

## Implementation Checklist

### Phase 1 — Error Foundation (1 hour)
    [ ]  Create provider_errors.py with ProviderError + USER_MESSAGES
    [ ]  Add city_honoured, city_note to PurchaseResult in base_provider.py

### Phase 2 — Schema & Config (1 hour)
    [ ]  Remove carriers from VerificationRequest
    [ ]  Add city field with validator
    [ ]  Update tier_config.py fallback configs
    [ ]  Update tier_manager.py feature keys
    [ ]  Write and run DB migration

### Phase 3 — City Map (30 min)
    [ ]  Create city_to_area_code.py with 50 US cities
    [ ]  lookup() function case-insensitive

### Phase 4 — Telnyx Adapter (1.5 hours)
    [ ]  Replace all RuntimeError("Telnyx...") with ProviderError(category=...)
    [ ]  Remove US-only guard on NDC filter
    [ ]  Wire filter[locality] when city provided
    [ ]  Locality retry pattern — empty city retries without city
    [ ]  Empty country -> ProviderError(category="no_inventory_country")

### Phase 5 — 5sim Adapter (30 min)
    [ ]  Replace all RuntimeError("5sim...") with ProviderError(category=...)
    [ ]  unsupported_country raises ProviderError so router can try next provider

### Phase 6 — Provider Router (2 hours)
    [ ]  get_provider() and purchase_with_failover() accept city + user_tier
    [ ]  no_inventory_city -> retry within provider without city
    [ ]  no_inventory_country -> failover to next provider
    [ ]  Translate ProviderError categories to clean user messages at boundary
    [ ]  routing_reason reflects city outcome

### Phase 7 — Purchase Endpoints (1 hour)
    [ ]  Remove all carrier code
    [ ]  Add city extraction + tier gate
    [ ]  Pass city + user_tier to router
    [ ]  Catch ProviderError -> clean HTTP response (no provider names)
    [ ]  Add city_honoured, city_note, requested_city to response
    [ ]  Fix raw validation error detail

### Phase 8 — Tests (2 hours)
    [ ]  test_us_city_translates_to_area_codes
    [ ]  test_international_city_pro_routes_telnyx_with_locality
    [ ]  test_international_city_payg_city_dropped_city_note_set
    [ ]  test_international_no_city_routes_fivesim
    [ ]  test_freemium_city_request_rejected_402
    [ ]  test_carriers_field_rejected_422
    [ ]  test_telnyx_empty_city_retries_without_city
    [ ]  test_telnyx_empty_country_failover_to_fivesim
    [ ]  test_no_provider_name_in_error_response
    [ ]  test_all_providers_failed_clean_message

---

## Acceptance Criteria

    [ ]  carriers=[...] returns 422 — no provider names in error
    [ ]  city="London" accepted at schema level
    [ ]  country=US + city=New York -> TextVerified with area codes [212,646,718,917,929]
    [ ]  country=GB + city=London + tier=pro -> Telnyx with filter[locality]=London
    [ ]  country=GB + city=London + tier=payg -> number returned, city_honoured=False
    [ ]  country=DE + no city -> 5sim
    [ ]  country=US + unknown city -> TextVerified, no area code, city_honoured=False
    [ ]  Freemium + city -> 402 "City filtering requires PAYG tier or higher"
    [ ]  Telnyx empty for city -> retry without city, city_honoured=False, number returned
    [ ]  Telnyx empty for country -> failover to 5sim, number returned
    [ ]  All providers empty -> 503 "No numbers available for this country right now"
    [ ]  No provider name in any HTTP response body under any condition
    [ ]  city_honoured + city_note + requested_city in every response
    [ ]  DB migration runs cleanly
    [ ]  All 10 new tests pass
    [ ]  All existing tests pass
    [ ]  CI green

---

## What Is NOT Changing

    TextVerifiedService — not touched
    Polling service — no changes
    Refund service — no changes
    Balance monitor — no changes
    5sim adapter country-level logic — no changes
    Pricing — no city surcharge, cost difference captured in tier pricing

---

Owner: Backend Team
Estimated effort: ~8.5 hours
Blocks: Phase 5 go-live

---

## What This Is

Retiring carrier filtering entirely. Replacing with country + city level filtering
routed intelligently to the provider that can actually honour the request.

Users get two filter dimensions:
    country  ->  ISO code (US, GB, DE, FR, IN...)
    city     ->  city name (London, Berlin, New York, Mumbai...)

The platform decides which provider handles the request based on what was asked
and what tier the user is on. Users never see provider names.

---

## Provider Capability Map

    TextVerified
        country: US only
        city: yes — via area code lookup (New York -> 212/646/718, LA -> 213/310/323)
        tiers: all (area code = PAYG+)
        notes: proven, battle-tested, 18 bug fixes in place

    Telnyx
        country: 190+ countries
        city: yes — filter[locality] + filter[national_destination_code] globally
        tiers: Pro/Custom only (enterprise cost, real city-level inventory)
        notes: only provider with genuine city-level filtering internationally

    5sim
        country: 100+ countries
        city: no — country level only
        tiers: PAYG+ (cost-effective)
        notes: operator selection but no city granularity

---

## Routing Logic

    country=US, any city
        ->  TextVerified
        ->  city translated to area codes via city_to_area_code.py map
        ->  existing proximity chain handles the rest

    country=GB/DE/FR/etc, city provided, tier=Pro or Custom
        ->  Telnyx (filter[locality]=city, filter[country_code]=country)
        ->  real city-level inventory
        ->  if Telnyx unavailable -> 5sim + notify user city could not be honoured

    country=GB/DE/FR/etc, city provided, tier=Freemium or PAYG
        ->  5sim (city silently dropped, country only)
        ->  user informed at request time: "precise city filtering requires Pro tier"

    country=GB/DE/FR/etc, no city
        ->  5sim (cheapest, country level)
        ->  Telnyx as fallback if 5sim unavailable

---

## Tier Access

    Freemium
        country: yes
        city: no — upgrade prompt shown

    PAYG
        country: yes
        city: yes — best effort (country-level routing, city shown as preference)

    Pro
        country: yes
        city: yes — precise (Telnyx city-level inventory)

    Custom
        country: yes
        city: yes — precise (Telnyx city-level inventory, priority routing)

---

## Files — Complete Change List

### New Files (2)

    app/services/providers/city_to_area_code.py
        Static map of US city names to area codes.
        New York -> [212, 646, 718, 917, 929]
        Los Angeles -> [213, 310, 323, 424, 747, 818]
        Chicago -> [312, 773, 872]
        Houston -> [281, 346, 713, 832]
        Phoenix -> [480, 602, 623]
        Philadelphia -> [215, 267, 445]
        San Antonio -> [210, 726]
        San Diego -> [619, 858]
        Dallas -> [214, 469, 972]
        San Jose -> [408, 669]
        Austin -> [512, 737]
        Jacksonville -> [904]
        Fort Worth -> [682, 817]
        Columbus -> [380, 614]
        Charlotte -> [704, 980]
        Indianapolis -> [317]
        San Francisco -> [415, 628]
        Seattle -> [206, 253, 360]
        Denver -> [303, 720]
        Nashville -> [615, 629]
        Oklahoma City -> [405]
        El Paso -> [915]
        Washington DC -> [202]
        Las Vegas -> [702, 725]
        Louisville -> [502]
        Memphis -> [901]
        Portland -> [503, 971]
        Baltimore -> [410, 443, 667]
        Milwaukee -> [262, 414]
        Albuquerque -> [505]
        Tucson -> [520]
        Fresno -> [559]
        Sacramento -> [279, 916]
        Mesa -> [480]
        Kansas City -> [816]
        Atlanta -> [404, 470, 678, 770]
        Omaha -> [402]
        Colorado Springs -> [719]
        Raleigh -> [919, 984]
        Long Beach -> [562]
        Virginia Beach -> [757]
        Minneapolis -> [612, 763, 952]
        Tampa -> [813]
        New Orleans -> [504]
        Arlington -> [682, 817]
        Wichita -> [316]
        Bakersfield -> [661]
        Aurora -> [303, 720]
        Anaheim -> [714]
        Miami -> [305, 786]
        Boston -> [339, 617, 857]

    tests/unit/providers/test_city_filtering.py
        Tests for all routing scenarios (see acceptance criteria)

### Modified Files (6)

    app/schemas/verification.py
        - Remove: carriers field and validate_carriers validator
        - Add: city field (Optional[str], max_length=100)
        - Update: area_codes validator comment — US only, internal use
        - Update: docstring to reflect new filter model

    app/services/providers/provider_router.py
        - get_provider() gains city (Optional[str]) and user_tier (str) params
        - purchase_with_failover() gains city and user_tier params
        - New routing logic per the map above
        - Notify when city filter cannot be honoured (non-premium + international)

    app/services/providers/telnyx_adapter.py
        - purchase_number() uses filter[locality] when city provided
        - filter[national_destination_code] fires for ANY country (remove US-only guard)
        - Remove carrier_matched=True hardcode -> city_matched based on locality filter

    app/api/verification/purchase_endpoints.py
        - Remove: carrier extraction (carrier = request.carriers[0]...)
        - Remove: isp_filtering tier gate
        - Remove: CarrierAnalytics recording block
        - Remove: carrier preference logging
        - Remove: carrier_surcharge from pricing_info usage
        - Add: city = request.city
        - Add: city_filtering tier gate (PAYG+ for any city, Pro/Custom for precise)
        - Pass city and user_tier to provider_router.purchase_with_failover()
        - Update Verification record: remove assigned_carrier/operator carrier fields

    app/services/tier_manager.py
        - check_feature_access(): replace isp_filtering with city_filtering
        - Add city_filtering: PAYG+ returns True
        - Add precise_city_filtering: Pro/Custom returns True

    app/core/tier_config.py
        - Fallback configs: replace has_isp_filtering with has_city_filtering
        - freemium: has_city_filtering=False
        - payg: has_city_filtering=True
        - pro: has_city_filtering=True, has_precise_city_filtering=True
        - custom: has_city_filtering=True, has_precise_city_filtering=True
        - DB query: add has_city_filtering, has_precise_city_filtering columns
        - Note: DB migration required for subscription_tiers table

### Database Migration (1)

    alembic/versions/xxx_city_filtering_tier_columns.py
        ALTER TABLE subscription_tiers
            ADD COLUMN has_city_filtering BOOLEAN DEFAULT FALSE,
            ADD COLUMN has_precise_city_filtering BOOLEAN DEFAULT FALSE;

        UPDATE subscription_tiers SET has_city_filtering=TRUE
            WHERE tier IN ('payg', 'pro', 'custom');

        UPDATE subscription_tiers SET has_precise_city_filtering=TRUE
            WHERE tier IN ('pro', 'custom');

        -- has_isp_filtering column kept for backward compat, not removed

---

## Implementation Checklist

### Phase 1 — Schema & Config (1.5 hours)
    [ ]  Remove carriers field from VerificationRequest
    [ ]  Add city field to VerificationRequest with validator
    [ ]  Update tier_config.py fallback configs (has_city_filtering, has_precise_city_filtering)
    [ ]  Update tier_manager.py check_feature_access() with new feature keys
    [ ]  Write DB migration for subscription_tiers columns
    [ ]  Run migration

### Phase 2 — City to Area Code Map (1 hour)
    [ ]  Create app/services/providers/city_to_area_code.py
    [ ]  50 US cities mapped to area codes
    [ ]  lookup(city) -> List[str] function (case-insensitive, returns [] if unknown)
    [ ]  Compile tests: New York -> [212, 646, 718, 917, 929], unknown city -> []

### Phase 3 — Telnyx Adapter (1 hour)
    [ ]  Remove US-only guard on filter[national_destination_code]
    [ ]  Wire filter[locality] when city provided
    [ ]  Update city_matched in PurchaseResult based on whether locality was sent
    [ ]  Remove carrier_matched=True hardcode

### Phase 4 — Provider Router (2 hours)
    [ ]  get_provider() accepts city and user_tier
    [ ]  purchase_with_failover() accepts city and user_tier
    [ ]  Routing logic per the map above
    [ ]  When city requested but cannot be honoured -> log warning, include in routing_reason
    [ ]  routing_reason field reflects city filter outcome

### Phase 5 — Purchase Endpoints (1 hour)
    [ ]  Remove all carrier-related code
    [ ]  Add city extraction from request
    [ ]  Add city_filtering tier gate
    [ ]  Pass city and user_tier to router
    [ ]  Update Verification record creation (remove carrier fields from new writes)

### Phase 6 — Tests (2 hours)
    [ ]  test_us_city_translates_to_area_codes
    [ ]  test_international_city_pro_routes_telnyx
    [ ]  test_international_city_payg_routes_fivesim_city_dropped
    [ ]  test_international_no_city_routes_fivesim
    [ ]  test_freemium_city_request_rejected
    [ ]  test_carriers_field_rejected_at_schema
    [ ]  test_city_field_accepted_at_schema
    [ ]  test_telnyx_locality_filter_sent
    [ ]  test_telnyx_ndc_fires_for_international
    [ ]  test_routing_reason_reflects_city_outcome

---

## Acceptance Criteria

Every item below must be true before this is considered done:

    [ ]  POST /api/verification/request with carriers=[...] returns 422 validation error
    [ ]  POST /api/verification/request with city="London" accepted at schema level
    [ ]  country=US + city=New York -> TextVerified called with area codes [212, 646, 718, 917, 929]
    [ ]  country=GB + city=London + tier=pro -> Telnyx called with filter[locality]=London
    [ ]  country=GB + city=London + tier=payg -> 5sim called, city not passed, routing_reason notes it
    [ ]  country=DE + no city -> 5sim called
    [ ]  country=US + unknown city -> TextVerified called with no area code (graceful)
    [ ]  Freemium user + city -> 402 with "precise city filtering requires PAYG or higher"
    [ ]  isp_filtering removed from all tier checks
    [ ]  has_city_filtering and has_precise_city_filtering in tier config
    [ ]  DB migration runs cleanly
    [ ]  All 10 new tests pass
    [ ]  All existing tests still pass (no regression)
    [ ]  CI green

---

## Risks

    Telnyx filter[locality] availability
        Not all cities have inventory in Telnyx.
        Mitigation: if Telnyx returns empty results for locality, retry without locality
        and notify user "no numbers available in [city], assigned country-level number"

    US city map coverage
        50 cities covers ~80% of US population but not all.
        Mitigation: unknown city -> no area code -> TextVerified handles it gracefully
        with its own proximity chain

    DB migration on live DB
        Additive only (new columns, no drops). Safe to run without downtime.

    Backward compat for existing API consumers
        carriers field removal is a breaking change for any API consumer sending it.
        Mitigation: schema returns 422 with clear message, not silent ignore.
        Document in changelog.

---

## What Is NOT Changing

    TextVerifiedService — not touched (18 bug fixes intact)
    Polling service — no changes needed (provider field already drives dispatch)
    Refund service — no changes needed
    Balance monitor — no changes needed
    Health checks — no changes needed
    5sim adapter — no changes needed (country-level already works)
    Pricing calculator — carrier_surcharge removed, no replacement surcharge for city

---

## Notes

City filtering is not a surcharge feature. It is a routing intelligence feature.
Pro/Custom users get better city accuracy because they route to Telnyx.
PAYG users get city as a best-effort preference because they route to 5sim.
The cost difference is already captured in the tier pricing, not per-request.

Carrier filtering is gone. No migration path, no soft deprecation.
Any request with carriers=[...] gets a 422. Document this in the changelog.

---

Owner: Backend Team
Estimated effort: ~8.5 hours
Blocks: Phase 5 go-live (Telnyx/5sim enablement)
