# Inventory-Aware Area Code Resolution System

**Version**: 5.0.0  
**Status**: Planning  
**Baseline**: `stable/textverified-only` @ `v4.5.0-stable`  
**Created**: April 17, 2026  
**Revised**: April 17, 2026 — corrected for actual TextVerified API capabilities

---

## Problem Statement

TextVerified treats `area_code_select_option` as a preference hint, not a hard filter. When the requested area code has no inventory, it silently assigns a random number. Users pay credits expecting a specific area code and receive something different with no warning.

**Current behavior**: User requests 213 → TextVerified has no 213 inventory → assigns 469 (Dallas) → user is confused and frustrated.

**Target behavior**: User types 213 → system tells them whether 213 is likely available for WhatsApp based on real purchase data → if unlikely, shows nearby alternatives → user picks 323 (same city) → purchase succeeds with the expected number.

---

## API Reality Check

TextVerified exposes exactly two relevant endpoints:

| Endpoint | Returns | Does NOT return |
|----------|---------|-----------------|
| `GET /api/pub/v2/area-codes` | Global list of `{area_code, state}` | Per-service availability, stock count, real-time inventory |
| `POST /verifications` | A purchased number (or error) | Pre-purchase availability check |

**There is no inventory query endpoint.** The only way to know if area code 213 has WhatsApp numbers is to attempt a purchase. This means our availability intelligence must be built from **our own purchase outcomes**, not from TextVerified's API.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                           │
│                                                         │
│  Area Code Input ──→ GET /area-code/check ──→ Show      │
│  [213]                                        results   │
│                                               inline    │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Area Code Check API                    │
│                                                         │
│  1. Query purchase history cache (Redis)                │
│  2. Score availability from success/fail ratio          │
│  3. If unlikely → rank alternatives via NANPA geo       │
│  4. Filter alternatives by TextVerified supported list  │
│  5. Return scored result + alternatives                 │
└──────┬──────────────────┬───────────────┬───────────────┘
       │                  │               │
       ▼                  ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐
│  Purchase    │  │  NANPA Geo   │  │  TextVerified        │
│  History     │  │  Data        │  │  Supported List      │
│  (Postgres)  │  │  (Static)    │  │  (Cached 24h)        │
│              │  │              │  │                       │
│  Every       │  │  area_code → │  │  Global area codes   │
│  purchase    │  │  city/state  │  │  that TV supports    │
│  outcome     │  │  lat/lng     │  │  (not availability)  │
│  logged      │  │  metro       │  │                       │
└──────┬───────┘  └──────────────┘  └───────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Purchase Enforcement                        │
│                                                          │
│  Purchase → validate area code → match? → proceed        │
│                                → mismatch? → cancel,     │
│                                  update history,         │
│                                  return alternatives     │
└──────────────────────────────────────────────────────────┘
```

---

## Phases

### Phase 1 — NANPA Geographic Data Layer

**Goal**: Static dataset mapping every US area code to city, state, coordinates, and metro cluster. Foundation for "find the closest alternative."

**Why first**: Zero external dependencies. Pure data. Testable in isolation. Everything else builds on this.

#### Tasks

- [ ] **1.1** Source NANPA area code dataset
  - Public domain, ~370 active US area codes
  - Fields per entry: `area_code`, `major_city`, `state`, `latitude`, `longitude`, `metro` (metro area name for clustering)
  - Store as Python dict in `app/services/area_code_geo.py` — no DB table, this data changes maybe once a year
  - Source: NANPA public records + FCC data

- [ ] **1.2** Build proximity ranking function
  - `get_nearby(area_code, max_results=8) → List[NearbyAreaCode]`
  - Uses haversine formula on lat/lng
  - Returns sorted by distance, tagged with tier:
    - `same_city`: shares the same `metro` value (e.g. 213, 323, 310 all = "Los Angeles")
    - `nearby`: < 50 miles, different metro
    - `same_state`: same state, > 50 miles
  - Stops expanding tiers once `max_results` reached

- [ ] **1.3** Build metro clustering
  - `get_metro_codes(area_code) → List[str]`
  - Returns all area codes in the same metro area
  - Example: `get_metro_codes("213")` → `["213", "323", "310", "818", "626", "424", "747", "562"]`

- [ ] **1.4** Filter by TextVerified supported list
  - `filter_supported(area_codes) → List[str]`
  - Cross-reference against the cached TextVerified global area codes list
  - Removes any NANPA area code that TextVerified doesn't carry at all
  - Uses existing `get_area_codes_list()` (already cached 24h)

- [ ] **1.5** Unit tests
  - `get_nearby("213")` → 323, 310, 818 appear before 916, 415
  - `get_metro_codes("213")` → returns all LA codes
  - `get_nearby("999")` → returns empty list (unknown code)
  - `filter_supported(["213", "999"])` → removes 999 if not in TV list
  - Haversine: known distance between two coordinates matches expected value

**Deliverable**: `app/services/area_code_geo.py` + `tests/unit/test_area_code_geo.py`  
**Risk**: None

---

### Phase 2 — Purchase Intelligence Tracker

**Goal**: Record the full profile of **every purchased number** — not just area-code-filtered ones. Every purchase is a data point. Over time this builds a complete picture of what TextVerified delivers: which carriers, which area codes, which cities, for which services.

**Why second**: The check API (Phase 3) needs data to score availability. Without purchase history, every area code is "unknown." This table starts collecting from day one.

#### Tasks

- [ ] **2.1** Create `purchase_outcomes` table
  ```
  purchase_outcomes
  ├── id                (serial PK)
  ├── service           (varchar, indexed) — e.g. "whatsapp"
  ├── requested_code    (varchar(10), nullable) — what user asked for (null if no filter)
  ├── assigned_code     (varchar(10), not null) — area code of the number TextVerified gave
  ├── assigned_carrier  (varchar(50)) — real carrier: "att", "tmobile", "verizon", etc.
  ├── carrier_type      (varchar(20)) — "mobile", "voip", "landline"
  ├── assigned_city     (varchar(100)) — city from NANPA lookup on assigned number
  ├── assigned_state    (varchar(2)) — state from NANPA lookup on assigned number
  ├── matched           (boolean) — did assigned code == requested code? (null if no filter)
  ├── sms_received      (boolean, default null) — did SMS actually arrive? (updated later by polling)
  ├── user_id           (varchar, FK users.id)
  ├── verification_id   (varchar, FK verifications.id)
  ├── created_at        (timestamp, indexed)
  ├── hour_utc          (smallint) — 0-23, for time-of-day patterns
  └── day_of_week       (smallint) — 0-6, for weekly patterns
  ```
  - Composite index on `(service, assigned_code, created_at)` — primary query path
  - Composite index on `(service, requested_code, created_at)` — area code availability scoring
  - Index on `(assigned_carrier, service)` — carrier analytics
  - Idempotent migration (guarded with existence check)

  **Every column earns its place:**
  | Column | What it answers |
  |--------|-----------------|
  | `service` + `assigned_code` | "Does 213 have WhatsApp numbers?" |
  | `service` + `assigned_carrier` | "Which carriers does TextVerified use for WhatsApp?" |
  | `assigned_carrier` + `sms_received` | "Do AT&T numbers actually receive SMS for Telegram?" |
  | `assigned_city` + `assigned_state` | "LA, CA — WhatsApp — AT&T" full profile per purchase |
  | `requested_code` + `matched` | "When users ask for 213, do they get it?" |
  | `hour_utc` + `day_of_week` | "Is 213 more available at 6am than 6pm?" |

- [ ] **2.2** Instrument the purchase flow — **ALL purchases, not just filtered ones**
  - After every `create_verification` call, log to `purchase_outcomes`
  - Log on success AND mismatch AND cancellation — all are valuable
  - Enrich with NANPA geo data: look up `assigned_city` and `assigned_state` from the assigned number's area code
  - Enrich with carrier data: `assigned_carrier` and `carrier_type` from the existing `CarrierLookupService` (already runs during purchase)
  - Non-blocking: fire-and-forget INSERT, purchase flow never waits on logging

- [ ] **2.3** Update `sms_received` after polling completes
  - When SMS polling finishes (success or timeout), update the matching `purchase_outcomes` row
  - `sms_received = true` if verification completed, `false` if timed out
  - This closes the loop: we know not just what number we got, but whether it actually worked
  - Enables future analysis: "AT&T numbers in 213 receive WhatsApp SMS 95% of the time"

- [ ] **2.4** Build availability scorer
  - `async def score_availability(service: str, area_code: str) → AvailabilityScore`
  - Queries recent outcomes (last 7 days) for this service + area code combo
  - Returns:
    ```python
    AvailabilityScore(
        available: bool | None,  # True/False/None (unknown)
        confidence: float,       # 0.0 to 1.0
        sample_size: int,        # how many data points
        success_rate: float,     # 0.0 to 1.0
        last_success: datetime | None,
        last_failure: datetime | None,
    )
    ```
  - Scoring logic:
    - 0 data points → `available=None, confidence=0.0` (unknown)
    - 1-2 data points → use result but `confidence=0.3` (low sample)
    - 3-9 data points → `confidence=0.6`
    - 10+ data points → `confidence=0.9`
    - Recency weight: outcomes from last 2 hours count 3x (inventory fluctuates)
    - `available=True` if success_rate ≥ 0.6
    - `available=False` if success_rate < 0.4
    - `available=None` if between 0.4-0.6 (uncertain)
  - **Bonus**: even unfiltered purchases contribute — if someone buys WhatsApp with no area code filter and gets a 213 number, that's a data point that 213 has WhatsApp inventory right now

- [ ] **2.5** Cache scored results in Redis
  - Key: `acscore:{service}:{area_code}` → serialized AvailabilityScore
  - TTL: 10 minutes (short — purchase data changes fast)
  - Invalidate on new outcome INSERT (so next check gets fresh score)
  - Cache miss → compute from DB, cache result

- [ ] **2.6** Unit tests
  - No history → returns `available=None, confidence=0.0`
  - 5 successes, 0 failures → `available=True, confidence=0.6`
  - 0 successes, 5 failures → `available=False, confidence=0.6`
  - 15 successes, 2 failures → `available=True, confidence=0.9`
  - Mixed results (50/50) → `available=None` (uncertain)
  - Recency: recent failure overrides older successes appropriately
  - Cache hit returns same result as fresh computation
  - Unfiltered purchase (no requested_code) still logged with full profile
  - `sms_received` update works after polling completes
  - Carrier and city fields populated from NANPA + CarrierLookup

**Deliverable**: `app/services/purchase_intelligence.py` + `app/models/purchase_outcome.py` + migration + `tests/unit/test_purchase_intelligence.py`  
**Risk**: Low — simple table + aggregation query  
**Dependency**: None (can build in parallel with Phase 1)

---

### Phase 3 — Area Code Check API

**Goal**: Single endpoint the frontend calls when user types an area code. Returns availability score + ranked alternatives.

**Why third**: Combines Phase 1 (geo data) + Phase 2 (purchase history) into a user-facing API.

#### Tasks

- [ ] **3.1** Create endpoint
  - `GET /api/verify/area-code/check?service=whatsapp&area_code=213`
  - Response when likely available:
    ```json
    {
      "area_code": "213",
      "service": "whatsapp",
      "status": "available",
      "confidence": 0.85,
      "message": "213 is available for WhatsApp based on recent activity."
    }
    ```
  - Response when likely unavailable:
    ```json
    {
      "area_code": "213",
      "service": "whatsapp",
      "status": "unavailable",
      "confidence": 0.78,
      "alternatives": [
        {"area_code": "323", "city": "Los Angeles", "state": "CA", "proximity": "same_city", "status": "available", "confidence": 0.90},
        {"area_code": "310", "city": "Los Angeles", "state": "CA", "proximity": "same_city", "status": "unknown", "confidence": 0.0},
        {"area_code": "818", "city": "Burbank", "state": "CA", "proximity": "same_city", "status": "available", "confidence": 0.65}
      ],
      "message": "213 is not available for WhatsApp. Select from nearby area codes."
    }
    ```
  - Response when unknown (no purchase data):
    ```json
    {
      "area_code": "213",
      "service": "whatsapp",
      "status": "unknown",
      "confidence": 0.0,
      "alternatives": [
        {"area_code": "323", "city": "Los Angeles", "state": "CA", "proximity": "same_city", "status": "unknown", "confidence": 0.0}
      ],
      "message": "No availability data yet for 213 + WhatsApp. You can proceed — if unavailable, you won't be charged."
    }
    ```

- [ ] **3.2** Build alternative ranking logic
  - Get nearby area codes from NANPA geo (Phase 1)
  - Filter by TextVerified supported list
  - Score each alternative via purchase history (Phase 2)
  - Sort by: `same_city available` → `same_city unknown` → `nearby available` → `same_state available`
  - Cap at 8 alternatives
  - Never include the originally requested code in alternatives

- [ ] **3.3** Handle edge cases
  - Area code not in NANPA data → `400: Invalid area code`
  - Area code not in TextVerified supported list → `400: Area code not supported`
  - Service not found → `400: Unknown service`
  - Redis down → compute from DB directly (slower but works)
  - DB down → return `status: unknown` for everything (graceful degradation)

- [ ] **3.4** Rate limiting
  - 30 requests/minute per user (frontend debounces, but protect against abuse)
  - No credit charge — read-only endpoint
  - No auth required for the check (reduces friction) — but rate limit by IP

- [ ] **3.5** Tests
  - Known available (history shows success) → `status: available`
  - Known unavailable (history shows failure) → `status: unavailable` + alternatives
  - Unknown (no history) → `status: unknown` + alternatives with unknown status
  - Alternatives sorted correctly: same_city before nearby before same_state
  - Unsupported area code → 400
  - Invalid input (letters, too short) → 400

**Deliverable**: `app/api/verification/area_code_endpoints.py` + `tests/unit/test_area_code_check.py`  
**Risk**: Low  
**Dependency**: Phase 1 + Phase 2

---

### Phase 4 — Frontend Integration

**Goal**: Live area code validation in the verification request form. User sees availability as they type.

#### Tasks

- [ ] **4.1** Debounced area code input
  - After user stops typing for 500ms → call `/area-code/check`
  - Show loading spinner while checking
  - Don't call if input < 3 digits
  - Cancel pending request if user types again

- [ ] **4.2** Available state UI
  - Green checkmark next to area code input
  - Text: "213 is available for WhatsApp ✓"
  - Continue button enabled

- [ ] **4.3** Unavailable state UI
  - Amber highlight on area code input (not red — it's guidance, not an error)
  - Message: "213 is not available for WhatsApp"
  - Below: clickable list of alternatives showing city name and proximity tier
  - Each alternative shows its own availability status (green dot = available, gray dot = unknown)
  - Clicking an alternative fills the area code input and triggers re-validation
  - Continue button disabled until user selects an alternative or clears the area code

- [ ] **4.4** Unknown state UI (no purchase data yet)
  - Neutral state — no checkmark, no warning
  - Text: "Availability will be confirmed on purchase. You won't be charged if unavailable."
  - Continue button enabled — don't block the user

- [ ] **4.5** Remove carrier dropdown
  - Remove the "Carrier" field from Advanced Options entirely
  - Update checkbox text: "Use Advanced Options above to filter by area code"
  - Clean removal — no hidden fields, no disabled state

- [ ] **4.6** Frontend tests
  - Type 213 → API returns available → green checkmark shown
  - Type 213 → API returns unavailable → alternatives list shown
  - Click alternative 323 → input updates to 323, re-validates
  - Type fast (multiple keystrokes) → only one API call fires (debounce)
  - API slow/timeout → spinner shown, then neutral state

**Deliverable**: Updated `static/js/verification.js` + `static/css/` updates  
**Risk**: Low — purely additive UI, doesn't change purchase flow  
**Dependency**: Phase 3

---

### Phase 5 — Purchase-Time Enforcement

**Goal**: Safety net. Never silently assign a mismatched number. Every purchase outcome feeds back into the history tracker.

#### Tasks

- [ ] **5.1** Strict area code validation post-purchase
  - After TextVerified returns a number, extract the assigned area code
  - Compare to requested area code
  - If match → proceed, log success to `purchase_outcomes`
  - If mismatch → cancel the number immediately, log failure to `purchase_outcomes`

- [ ] **5.2** Single informed retry
  - On mismatch, check purchase history score before retrying
  - If score says `unavailable` (confidence ≥ 0.6) → don't retry, return alternatives immediately
  - If score says `available` or `unknown` → retry once (could be transient)
  - Maximum 2 total attempts (1 original + 1 retry)
  - Both attempts logged to `purchase_outcomes` regardless of result

- [ ] **5.3** Mismatch response to frontend
  - No credits charged (number was cancelled)
  - Return alternatives from the check API (same ranking logic):
    ```json
    {
      "success": false,
      "error": "area_code_unavailable",
      "message": "213 is not available for WhatsApp right now.",
      "alternatives": [...],
      "credits_charged": false
    }
    ```
  - Frontend shows the alternatives list (same UI as Phase 4.3)
  - User can pick an alternative and retry without re-entering service details

- [ ] **5.4** Simplify create_verification
  - Remove the current 3-retry blind loop → replace with Phase 5.2 informed retry
  - Remove carrier matching logic (carrier feature removed)
  - Keep VOIP/landline checking as-is (working, out of scope for this roadmap)
  - Flow becomes: purchase → validate area code → accept or cancel+alternatives

- [ ] **5.5** Tests
  - Requested 213, got +1-213-xxx → success, outcome logged as matched
  - Requested 213, got +1-469-xxx → cancel, outcome logged as mismatched, retry
  - Retry succeeds with 213 → success, second outcome logged
  - Retry fails again → return alternatives, no credits charged
  - No area code requested → accept any number, no validation, no outcome logged
  - Outcome logging failure (DB error) → purchase still succeeds (logging is non-blocking)

**Deliverable**: Updated `app/services/textverified_service.py` + `app/api/verification/purchase_endpoints.py`  
**Risk**: Medium — modifies the purchase flow. Mitigated by keeping changes minimal and the stable branch as rollback.  
**Dependency**: Phase 2 (history tracker for informed retry)

---

### Phase 6 — Analytics & Admin Visibility

**Goal**: Admin dashboard showing the full intelligence picture — area code success rates, carrier distribution, SMS delivery rates by carrier, and system learning progress. Built on the data Phase 2 collects from every purchase.

#### Tasks

- [ ] **6.1** Admin analytics endpoint — area code intelligence
  - `GET /api/admin/analytics/area-codes?days=7`
  - Returns:
    ```json
    {
      "period": "7d",
      "total_purchases": 342,
      "match_rate": 0.78,
      "top_requested": [
        {"area_code": "213", "service": "whatsapp", "requests": 45, "success_rate": 0.82}
      ],
      "worst_performing": [
        {"area_code": "907", "service": "telegram", "requests": 12, "success_rate": 0.08}
      ],
      "data_coverage": 0.34
    }
    ```

- [ ] **6.2** Admin analytics endpoint — carrier intelligence
  - `GET /api/admin/analytics/carriers?days=7`
  - Returns:
    ```json
    {
      "period": "7d",
      "carrier_distribution": [
        {"carrier": "att", "count": 128, "pct": 0.37, "sms_delivery_rate": 0.94},
        {"carrier": "tmobile", "count": 95, "pct": 0.28, "sms_delivery_rate": 0.91},
        {"carrier": "verizon", "count": 72, "pct": 0.21, "sms_delivery_rate": 0.96}
      ],
      "carrier_by_service": [
        {"service": "whatsapp", "carrier": "att", "count": 45, "sms_delivery_rate": 0.96},
        {"service": "whatsapp", "carrier": "tmobile", "count": 38, "sms_delivery_rate": 0.89},
        {"service": "telegram", "carrier": "att", "count": 22, "sms_delivery_rate": 0.72}
      ],
      "voip_rate": 0.03,
      "landline_rate": 0.01
    }
    ```
  - Surfaces patterns like: "Telegram has low delivery on AT&T numbers" — actionable insight

- [ ] **6.3** Admin analytics endpoint — geographic intelligence
  - `GET /api/admin/analytics/geography?days=7`
  - Returns:
    ```json
    {
      "period": "7d",
      "top_cities": [
        {"city": "Los Angeles", "state": "CA", "purchases": 89, "sms_delivery_rate": 0.93},
        {"city": "New York", "state": "NY", "purchases": 76, "sms_delivery_rate": 0.91}
      ],
      "top_states": [
        {"state": "CA", "purchases": 142, "unique_area_codes": 18},
        {"state": "TX", "purchases": 98, "unique_area_codes": 12}
      ]
    }
    ```

- [ ] **6.4** Track alternative selection
  - When user picks an alternative from the list and purchases → log which alternative they chose
  - Frontend sends `selected_from_alternatives=true&original_request=213` on the purchase call
  - Enables: "Users who wanted 213 usually accepted 323" — future ML feature

- [ ] **6.5** Cold-start progress tracking
  - Admin can see: "System has purchase data for 120 of ~350 area codes for WhatsApp"
  - Shows learning velocity: "Added 15 new area code data points this week"

- [ ] **6.6** Tests
  - Analytics endpoints return correct aggregations
  - Empty data → returns zeros, not errors
  - Carrier distribution percentages sum to 1.0
  - SMS delivery rate only counts outcomes where `sms_received` is not null
  - Admin-only access enforced

**Deliverable**: `app/api/admin/area_code_analytics.py` + `tests/unit/test_area_code_analytics.py`  
**Risk**: None — read-only reporting on existing data  
**Dependency**: Phase 2 (reads from `purchase_outcomes`)

---

## Cold Start Strategy

On day one, the `purchase_outcomes` table is empty. Every area code returns `status: unknown`. This is honest and expected.

**How the system warms up:**

| Timeframe | State | User experience |
|-----------|-------|-----------------|
| Day 1 | 0 data points | All area codes show "unknown" — user can proceed, won't be charged on mismatch |
| Week 1 | ~50-100 outcomes | Popular combos (WhatsApp + major city codes) start showing available/unavailable. Carrier distribution emerging. |
| Month 1 | ~500-1000 outcomes | Most common service + area code combos have reliable scores. Carrier + SMS delivery patterns visible in admin. |
| Month 3 | ~2000+ outcomes | Time-of-day patterns emerge. Carrier reliability per service is statistically significant. Full city/state purchase profiles. |

**Key insight: unfiltered purchases warm the cache too.** A user who buys WhatsApp with no area code filter and gets a 213/AT&T/Los Angeles number — that's a data point proving 213 has WhatsApp inventory on AT&T right now. Every purchase teaches the system, not just filtered ones.

**The system never blocks a user due to lack of data.** Unknown = proceed, and the outcome feeds back into the system. Every purchase makes the system smarter for the next user.

---

## Build Order & Dependencies

```
Phase 1 (NANPA Geo)             ← No dependencies
    │                               Can build in parallel ──→ Phase 2 (Purchase History)
    │                                                              │
    └──────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
            Phase 3 (Check API)  ← Combines Phase 1 + 2
                   │
          ┌────────┴────────┐
          ▼                 ▼
   Phase 4 (Frontend)   Phase 5 (Purchase Enforcement)  ← Can build in parallel
          │                 │
          └────────┬────────┘
                   ▼
            Phase 6 (Analytics)  ← Reads from Phase 2 data
                   │
                   ▼
            Phase 7+ (ML)  ← Future, needs volume
```

---

## Success Criteria

| Metric | Day 1 | Month 1 | Month 3 (target) |
|--------|-------|---------|-------------------|
| Silent mismatch rate | 0% | 0% | 0% |
| Area code match rate (when data exists) | N/A | > 80% | > 95% |
| Pre-purchase check latency | < 200ms | < 200ms | < 200ms |
| Data coverage (combos with history) | 0% | ~30% | ~70% |
| Credits charged on mismatch | $0 | $0 | $0 |
| User dead-ends (no alternatives shown) | 0 | 0 | 0 |

The non-negotiable from day one: **zero silent mismatches, zero credits charged for wrong numbers.**

Everything else improves over time as purchase data accumulates.

---

## Rollback Plan

| Scenario | Action |
|----------|--------|
| Phase 1-4 breaks | Revert commits — these are purely additive, purchase flow unchanged |
| Phase 5 breaks | Revert Phase 5 — purchase flow falls back to current behavior |
| Everything breaks | Deploy `stable/textverified-only` branch on Render (`v4.5.0-stable`) |

Phase 5 is the only phase that modifies the purchase flow. Phases 1-4 and 6 are additive — they add new endpoints and UI but don't change how purchases work.

---

## Future: ML Prediction Layer (Phase 7+)

**Not built now.** Requires ~5,000 purchase outcomes to be useful. Phase 2 + 6 collect this data automatically.

When ready, the ML layer would:
- Predict availability before any purchase attempt (faster UX, fewer cancellations)
- Learn time-of-day inventory patterns ("213 restocks at 6am EST")
- Rank alternatives by historical user acceptance rate, not just distance
- Weight by recency: yesterday's data matters more than last month's
- **Carrier-aware routing**: "For Telegram, prefer T-Mobile numbers over AT&T (higher delivery rate)"
- **Service-carrier affinity**: learn which carrier + service combos have the best SMS delivery rates
- **Geographic demand prediction**: "LA area codes run out of WhatsApp inventory on weekday evenings"

Training features from `purchase_outcomes`:
- `service` + `assigned_code` + `hour_utc` + `day_of_week` → availability prediction
- `service` + `assigned_carrier` + `sms_received` → delivery rate prediction
- `assigned_city` + `assigned_state` + `service` → geographic demand patterns

The architecture is designed so ML slots in as an enhanced scorer in Phase 2's `score_availability` function — it doesn't replace the pipeline, it improves one function.
