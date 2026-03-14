# TextVerified Alignment Roadmap

**Version**: 1.0  
**Date**: March 14, 2026  
**Status**: Active  
**Owner**: Engineering Team

---

## Executive Summary

This roadmap addresses the fundamental misalignment between Namaskah's verification system and the TextVerified API. The core issues are:

1. **Carrier validation is broken** — TextVerified returns generic types ("Mobile") not specific carriers ("Verizon"), causing 409 Conflict errors
2. **Carrier data is fabricated** — `_extract_carrier_from_number()` always returns "Mobile", making the `assigned_carrier` field meaningless
3. **Service loading has no recovery** — when the API fails, users are stuck with an empty modal and no retry path
4. **Receipts are inaccurate** — they show requested filters, not what was actually assigned
5. **Carrier list is fictional** — frontend shows Verizon/AT&T/T-Mobile but TextVerified cannot guarantee any of them

**Estimated Total Effort**: 3–4 weeks across 5 milestones

---

## Milestone 1: Stop the Bleeding (Critical Fixes)

**Timeline**: Days 1–3  
**Goal**: Eliminate user-facing failures caused by carrier mismatch logic

---

### Task 1.1: Fix Carrier Validation Logic

**File**: `app/api/verification/purchase_endpoints.py` (Lines 223–248)

**Problem**: The current "mobile fallback" fix only accepts `assigned_carrier` values containing "mobile", "cellular", or "wireless". But `_extract_carrier_from_number()` always returns "Mobile" for any valid number, so the `assigned_carrier` field in `textverified_result` is always "Mobile". The validation is comparing a user-selected carrier like "us_cellular" against "Mobile" — which passes the mobile fallback check only because "cellular" is a substring of "us_cellular". For carriers like "verizon" or "att", the fallback check fails because they don't contain "mobile", "cellular", or "wireless".

**Root Cause**: `textverified_service.py:_extract_carrier_from_number()` is a stub that always returns "Mobile". TextVerified's API response does not include a specific carrier name.

**Fix**: Since TextVerified does not return specific carrier information, carrier validation after purchase is impossible. Remove post-purchase carrier validation entirely. The `carrier_select_option` parameter sent to TextVerified is a best-effort preference — not a guarantee.

**Changes**:

```python
# purchase_endpoints.py — REMOVE the entire carrier validation block (lines ~223-248)
# Replace with a simple log:
if carrier:
    assigned_carrier = textverified_result.get("assigned_carrier")
    logger.info(
        f"Carrier preference applied: requested={carrier}, "
        f"assigned_type={assigned_carrier} (TextVerified best-effort)"
    )
```

```python
# textverified_service.py — Mark _extract_carrier_from_number as deprecated
def _extract_carrier_from_number(self, phone_number: str) -> Optional[str]:
    """DEPRECATED: TextVerified does not return specific carrier info.
    Always returns 'Mobile' for valid US numbers. Do not use for validation."""
    if not phone_number:
        return None
    clean = str(phone_number).replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    return "Mobile" if len(clean) >= 10 else "Unknown"
```

**Acceptance Criteria**:
- [ ] No 409 Conflict errors for carrier-filtered verification requests
- [ ] Carrier preference is still sent to TextVerified API via `carrier_select_option`
- [ ] Log entry records requested carrier and assigned type for every carrier-filtered request
- [ ] Existing tests pass (no regression)
- [ ] Manual test: create verification with carrier=verizon → succeeds (no 409)
- [ ] Manual test: create verification with carrier=us_cellular → succeeds (no 409)

---

### Task 1.2: Fix Service Loading Error Recovery

**File**: `templates/verify_modern.html`

**Problem**: When TextVerified API fails, the service dropdown shows "Services unavailable" but the modal can still be opened (showing empty "No results found"), filter settings button remains visible, and there's no retry mechanism.

**Changes**:

1. Prevent modal from opening when services are empty
2. Hide filter settings button when no services loaded
3. Add retry button in error state
4. Disable input click handler on error with visual feedback

**Acceptance Criteria**:
- [ ] Clicking service input when API is down shows error toast, does NOT open modal
- [ ] Filter settings (sliders) button is hidden when services array is empty
- [ ] Error state in modal shows "Unable to load services" with a Retry button
- [ ] Retry button re-fetches services from API and re-enables input
- [ ] Input shows `cursor: not-allowed` when in error state
- [ ] After successful retry, modal opens normally with services

---

### Task 1.3: Honest Carrier UX — Rename "Select Carrier" to "Prefer Carrier"

**Files**: `templates/verify_modern.html`, `app/api/verification/carrier_endpoints.py`

**Problem**: UI says "Select Carrier" implying a guarantee. TextVerified treats it as a preference.

**Changes**:

1. Rename label from "Carrier Filter" → "Carrier Preference"
2. Add tooltip: "We'll request this carrier from our provider. Subject to availability."
3. Update carrier endpoint response to include `guarantee: false`

**Acceptance Criteria**:
- [ ] UI label reads "Carrier Preference" (not "Carrier Filter" or "Select Carrier")
- [ ] Tooltip/help text explains best-effort nature
- [ ] API response includes `"guarantee": false` field
- [ ] No user-facing language implies carrier is guaranteed

---

## Milestone 2: Data Integrity (Schema & Receipt Fixes)

**Timeline**: Days 4–7  
**Goal**: Ensure database records and receipts reflect reality

---

### Task 2.1: Clean Up Verification Model — Remove Redundant `operator` Field

**Files**: `app/models/verification.py`, `app/api/verification/purchase_endpoints.py`

**Problem**: The `Verification` model has both `operator` and `assigned_carrier` columns. In `purchase_endpoints.py` line ~260, `operator` is set to `textverified_result.get("assigned_carrier") or carrier` — mixing assigned type with requested carrier. The `assigned_carrier` field is also set from the same source. This is redundant and confusing.

**Changes**:

1. Stop writing to `operator` in new verifications (keep column for historical data)
2. Use `requested_carrier` for what the user asked for
3. Use `assigned_carrier` for what TextVerified returned (always "Mobile" for now)
4. Document that `operator` is legacy and should not be used for new code

```python
# purchase_endpoints.py — Fix the verification record creation
verification = Verification(
    ...
    requested_carrier=carrier,                                    # What user asked for
    assigned_carrier=textverified_result.get("assigned_carrier"), # What TV returned ("Mobile")
    operator=carrier,                                             # Legacy — keep for backward compat
    ...
)
```

**Acceptance Criteria**:
- [ ] `requested_carrier` always contains the user's original selection (or None)
- [ ] `assigned_carrier` always contains TextVerified's response value (or None)
- [ ] `operator` is populated for backward compatibility but not used in new logic
- [ ] Historical data is not modified
- [ ] Query `SELECT requested_carrier, assigned_carrier FROM verifications WHERE requested_carrier IS NOT NULL LIMIT 10` returns sensible data after a few test purchases

---

### Task 2.2: Fix Receipt Generation to Show Actual Data

**Files**: Receipt generation code (wherever `VerificationReceipt` is created)

**Problem**: `VerificationReceipt.isp_carrier` and `VerificationReceipt.area_code` show requested values, not actual.

**Changes**:

```python
receipt = VerificationReceipt(
    ...
    area_code=verification.assigned_area_code or verification.requested_area_code,
    isp_carrier=verification.assigned_carrier or verification.requested_carrier,
    ...
)
```

**Acceptance Criteria**:
- [ ] Receipt `area_code` shows the area code from the assigned phone number
- [ ] Receipt `isp_carrier` shows TextVerified's returned carrier type
- [ ] If no filter was requested, receipt fields are null (not fabricated)
- [ ] Existing receipts are not retroactively modified

---

### Task 2.3: Add Carrier Mismatch Analytics Table

**New File**: `app/models/carrier_analytics.py`

**Purpose**: Track every carrier-filtered request to understand TextVerified's actual behavior over time. This replaces the broken validation with observability.

```python
class CarrierAnalytics(BaseModel):
    __tablename__ = "carrier_analytics"

    verification_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    requested_carrier = Column(String, nullable=False)
    sent_to_textverified = Column(String, nullable=False)  # normalized value sent
    textverified_response = Column(String)                  # raw response carrier field
    assigned_phone = Column(String)
    assigned_area_code = Column(String)
    outcome = Column(String)  # accepted, cancelled, timeout, completed
    created_at = Column(DateTime, nullable=False)
```

**Acceptance Criteria**:
- [ ] Every carrier-filtered verification creates a `CarrierAnalytics` row
- [ ] Admin can query: "What % of verizon requests actually got Mobile back?"
- [ ] Data is queryable for monthly reports
- [ ] Migration runs cleanly on production database

---

## Milestone 3: Align Carrier List with Reality

**Timeline**: Days 8–12  
**Goal**: Stop showing carriers we can't verify and build toward real carrier data

---

### Task 3.1: Replace Hardcoded Carrier List with Honest Options

**Files**: `app/api/verification/carrier_endpoints.py`, `app/schemas/verification.py`

**Problem**: Frontend shows Verizon, AT&T, T-Mobile, Sprint, US Cellular. TextVerified accepts these as preferences but returns "Mobile" regardless. Sprint no longer exists (merged with T-Mobile). The fallback list is fictional.

**Changes**:

Option A (Recommended — Minimal): Keep the carrier list but add disclaimers and remove Sprint.

```python
CARRIER_OPTIONS = [
    {"id": "verizon", "name": "Verizon", "type": "preference", "guarantee": False},
    {"id": "att", "name": "AT&T", "type": "preference", "guarantee": False},
    {"id": "tmobile", "name": "T-Mobile", "type": "preference", "guarantee": False},
    {"id": "us_cellular", "name": "US Cellular", "type": "preference", "guarantee": False},
]
```

Option B (Aggressive): Remove carrier selection entirely until we can verify it works.

**Also update** `app/schemas/verification.py` — remove "sprint" from `allowed_carriers`:

```python
allowed_carriers = {"verizon", "att", "tmobile", "us_cellular"}  # Remove "sprint"
```

**Acceptance Criteria**:
- [ ] Sprint removed from all carrier lists (frontend, backend, schema validation)
- [ ] Every carrier option includes `guarantee: false` in API response
- [ ] Schema validator rejects "sprint" as a carrier
- [ ] Frontend carrier dropdown does not show Sprint
- [ ] Existing verifications with carrier="sprint" are not affected

---

### Task 3.2: Investigate TextVerified Carrier Lookup Capability

**Type**: Research spike (no code changes)

**Goal**: Determine if TextVerified provides any way to get the actual carrier of an assigned number, either via:
- A field in the verification response we're not reading
- A separate carrier lookup endpoint
- The SDK's `VerificationExpanded` object having carrier info

**Deliverable**: A short document (max 1 page) answering:
1. Does TextVerified return specific carrier info anywhere in their API?
2. If not, what third-party carrier lookup APIs exist? (Twilio Lookup, Numverify, etc.)
3. Cost per lookup and latency
4. Recommendation: integrate lookup API or accept "Mobile" as-is?

**Acceptance Criteria**:
- [ ] Document created at `docs/CARRIER_LOOKUP_RESEARCH.md`
- [ ] At least 2 third-party options evaluated with pricing
- [ ] Clear recommendation with rationale
- [ ] Team has reviewed and agreed on direction

---

### Task 3.3: Build Carrier Success Rate from Historical Data

**File**: `app/api/verification/carrier_endpoints.py`

**Problem**: The carrier endpoint queries `Verification.operator` for success rates, but `operator` is always "Mobile" or the requested carrier (not the actual carrier). Success rates are meaningless.

**Changes**:

1. Query `CarrierAnalytics` table (from Task 2.3) instead of `Verification.operator`
2. Calculate success rate as: verifications with `outcome=completed` / total for that `requested_carrier`
3. This gives "if you request Verizon, what % of the time does the verification succeed?" — which is actually useful

```python
@router.get("/carriers/{country}")
async def get_available_carriers(country: str, ...):
    # Query carrier analytics for real success rates
    stats = (
        db.query(
            CarrierAnalytics.requested_carrier,
            func.count(CarrierAnalytics.id).label("total"),
            func.sum(case((CarrierAnalytics.outcome == "completed", 1), else_=0)).label("completed"),
        )
        .filter(CarrierAnalytics.created_at >= thirty_days_ago)
        .group_by(CarrierAnalytics.requested_carrier)
        .all()
    )
    # Build response with real success rates
```

**Acceptance Criteria**:
- [ ] Carrier success rates are based on actual verification outcomes
- [ ] Success rate updates as new verifications complete
- [ ] Carriers with 0 verifications show "No data" instead of fabricated 95%
- [ ] Response includes `data_points` count so frontend can show confidence level

---

## Milestone 4: Pricing Alignment

**Timeline**: Days 13–16  
**Goal**: Ensure pricing reflects what TextVerified actually charges and what we can deliver

---

### Task 4.1: Audit Carrier Filter Pricing

**File**: `app/services/pricing_calculator.py`

**Problem**: PAYG users pay $0.20–$0.50 extra for carrier filtering. But since TextVerified treats carrier as a preference (not a guarantee), users are paying a premium for something that may not be honored.

**Decision Required**: Should we charge for carrier preference?

| Option | Description | Risk |
|--------|-------------|------|
| A: Keep charging | Users pay for preference, not guarantee | Users may feel cheated |
| B: Remove carrier surcharge | Free preference, no expectation | Revenue loss ~$0.20-0.50/SMS |
| C: Charge only if verified | Refund surcharge if carrier can't be confirmed | Complex logic |

**Recommended**: Option A with clear disclosure ("Carrier preference fee — best effort, not guaranteed")

**Changes** (if Option A):
- Update pricing breakdown response to label carrier charge as "Carrier preference (best effort)"
- Add `"note": "Carrier selection is a preference, not a guarantee"` to pricing API response

**Acceptance Criteria**:
- [ ] Decision documented and approved by product owner
- [ ] Pricing API response includes carrier charge label with "best effort" qualifier
- [ ] User sees "Carrier preference (best effort)" in cost breakdown before purchase
- [ ] No silent charges — user always sees filter costs before confirming

---

### Task 4.2: Sync Service Prices with TextVerified Real-Time Pricing

**File**: `app/services/textverified_service.py`

**Problem**: `_fetch_prices_inline()` has an 8-second per-service timeout and 12-second total timeout. If TextVerified is slow, services render without prices (`price: null`). Users can still purchase but don't know the cost upfront.

**Changes**:

1. Block the purchase button when `price` is null for the selected service
2. Show "Price loading..." instead of hiding the price
3. Add a "Refresh prices" button that re-fetches from API

**Acceptance Criteria**:
- [ ] Purchase button is disabled when selected service has `price: null`
- [ ] UI shows "Price loading..." for services without prices
- [ ] "Refresh prices" button triggers a new API call
- [ ] After price loads, purchase button enables automatically
- [ ] User cannot accidentally purchase a service with unknown cost

---

## Milestone 5: Observability & Monitoring

**Timeline**: Days 17–20  
**Goal**: Know when things break before users report them

---

### Task 5.1: Add TextVerified API Health Metrics

**Files**: `app/services/textverified_service.py`, `app/monitoring/`

**Metrics to track**:

| Metric | Type | Description |
|--------|------|-------------|
| `tv_api_requests_total` | Counter | Total API calls by endpoint |
| `tv_api_errors_total` | Counter | Failed API calls by endpoint and error type |
| `tv_api_latency_seconds` | Histogram | Response time by endpoint |
| `tv_carrier_preference_requests` | Counter | Carrier-filtered requests |
| `tv_area_code_fallback_total` | Counter | Area code fallbacks (same-state vs different-state) |
| `tv_verification_outcome` | Counter | By outcome (completed, timeout, cancelled, error) |
| `tv_services_cache_hit` | Counter | Cache hits vs misses for services list |

**Acceptance Criteria**:
- [ ] All metrics are emitted from `textverified_service.py`
- [ ] Grafana dashboard shows TextVerified API health at a glance
- [ ] Alert fires if `tv_api_errors_total` exceeds 10% of requests in 5 minutes
- [ ] Alert fires if `tv_api_latency_seconds` p95 exceeds 10 seconds
- [ ] Carrier preference analytics visible in admin dashboard

---

### Task 5.2: Add Structured Logging for Verification Flow

**Files**: `app/api/verification/purchase_endpoints.py`, `app/services/textverified_service.py`

**Problem**: Current logs are unstructured strings. Hard to query in production.

**Changes**: Add structured JSON log entries at key decision points:

```python
logger.info("verification.purchase", extra={
    "user_id": user_id,
    "service": request.service,
    "requested_carrier": carrier,
    "requested_area_code": area_code,
    "assigned_phone": textverified_result["phone_number"],
    "assigned_area_code": textverified_result.get("assigned_area_code"),
    "assigned_carrier_type": textverified_result.get("assigned_carrier"),
    "fallback_applied": textverified_result.get("fallback_applied"),
    "cost": actual_cost,
    "tv_cost": textverified_result["cost"],
    "tv_verification_id": textverified_result["id"],
})
```

**Acceptance Criteria**:
- [ ] All verification purchases emit a single structured log entry with all relevant fields
- [ ] Log entries are parseable by log aggregation tools (JSON format)
- [ ] Can query: "show me all verifications where fallback_applied=true in the last 24h"
- [ ] Can query: "show me all verifications where requested_carrier=verizon"
- [ ] No PII in log entries (phone numbers are acceptable as they're temporary)

---

### Task 5.3: Admin Dashboard — Carrier Analytics View

**Files**: `app/api/admin/verification_analytics.py`, `templates/admin/`

**Purpose**: Give admins visibility into carrier preference behavior.

**Dashboard should show**:
1. Carrier preference usage (pie chart: verizon 40%, att 30%, tmobile 20%, us_cellular 10%)
2. Success rate by carrier preference (bar chart)
3. Area code fallback rate (% of requests that got a different area code)
4. TextVerified API health (uptime, latency, error rate)
5. Recent carrier mismatch log (table)

**Acceptance Criteria**:
- [ ] Admin can view carrier analytics at `/admin/verification-analytics`
- [ ] Data refreshes on page load (no stale data)
- [ ] Charts render correctly with real data
- [ ] Empty state handled gracefully ("No carrier data yet")
- [ ] Only admin users can access this page

---

## Milestone Summary & Dependencies

```
Milestone 1 (Days 1-3): Stop the Bleeding
├── Task 1.1: Fix carrier validation ← CRITICAL, no dependencies
├── Task 1.2: Fix service loading error recovery ← CRITICAL, no dependencies
└── Task 1.3: Honest carrier UX ← depends on 1.1

Milestone 2 (Days 4-7): Data Integrity
├── Task 2.1: Clean up operator field ← depends on 1.1
├── Task 2.2: Fix receipt generation ← depends on 2.1
└── Task 2.3: Carrier analytics table ← no dependencies

Milestone 3 (Days 8-12): Align Carrier List
├── Task 3.1: Remove Sprint, add disclaimers ← depends on 1.3
├── Task 3.2: Research carrier lookup ← no dependencies (spike)
└── Task 3.3: Real success rates ← depends on 2.3

Milestone 4 (Days 13-16): Pricing Alignment
├── Task 4.1: Audit carrier filter pricing ← depends on 1.1, 3.2
└── Task 4.2: Block purchase without price ← no dependencies

Milestone 5 (Days 17-20): Observability
├── Task 5.1: API health metrics ← no dependencies
├── Task 5.2: Structured logging ← depends on 1.1
└── Task 5.3: Admin analytics dashboard ← depends on 2.3
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TextVerified changes API response format | Low | High | Pin SDK version, add response validation |
| Carrier lookup API adds latency to purchases | Medium | Medium | Make lookup async/post-purchase, not blocking |
| Users complain about losing "carrier guarantee" | Medium | Low | Clear communication, carrier preference is more honest |
| Sprint removal breaks existing user presets | Low | Low | Graceful handling — ignore invalid carrier in saved presets |
| Migration fails on production DB | Low | High | Test on staging first, have rollback script ready |

---

## Definition of Done (Global)

Every task in this roadmap is considered done when:

- [ ] Code changes are committed and pass CI
- [ ] Unit tests cover the changed logic (no decrease in coverage)
- [ ] Manual smoke test performed on staging
- [ ] No new linting errors introduced
- [ ] Related documentation updated (if applicable)
- [ ] PR reviewed and approved by at least one team member

---

## Files Affected (Complete List)

| File | Milestones | Type of Change |
|------|-----------|----------------|
| `app/api/verification/purchase_endpoints.py` | 1, 2 | Remove carrier validation, fix record creation |
| `app/services/textverified_service.py` | 1, 5 | Deprecate carrier extraction, add metrics |
| `app/api/verification/carrier_endpoints.py` | 1, 3 | Update labels, real success rates |
| `app/schemas/verification.py` | 3 | Remove sprint from allowed carriers |
| `app/models/verification.py` | 2 | Document operator field as legacy |
| `app/models/carrier_analytics.py` | 2 | New file — analytics model |
| `app/services/pricing_calculator.py` | 4 | Add best-effort label to carrier charge |
| `templates/verify_modern.html` | 1, 4 | Error recovery, UX labels, price blocking |
| `app/api/admin/verification_analytics.py` | 5 | New admin analytics endpoint |
| `app/monitoring/` | 5 | New Grafana dashboard config |
| `alembic/versions/` | 2 | Migration for carrier_analytics table |

---

**Last Updated**: March 14, 2026  
**Next Review**: After Milestone 1 completion
