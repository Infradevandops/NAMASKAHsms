# Verification Flow Overhaul — Task File

**Created:** March 2026  
**Goal:** Reduce failed purchases from 8–12% → <2% by adding pre-purchase availability checking

---

## The Problem (One Picture)

```
CURRENT (broken)
────────────────
User selects service
        ↓
[PURCHASE — money deducted]
        ↓
TextVerified API called → may fail / return wrong area code / wrong carrier
        ↓
User charged but gets bad number → refund requested
        ↑
        8–12% failure rate, 5–7% refund rate

NEW (fixed)
───────────
User selects service
        ↓
User picks area code (optional) → availability checked live
        ↓
User picks carrier (optional) → availability checked live
        ↓
[CHECK AVAILABILITY] → "✅ Ready" or "❌ Out of stock + alternatives"
        ↓
[PURCHASE — money deducted] ← only if confirmed available
        ↓
Number guaranteed to match selections
```

**Root cause:** The purchase endpoint calls TextVerified blind — no pre-validation.  
**Fix:** Add a `/check-availability` endpoint + multi-step UI that gates purchase behind a confirmed availability check.

---

## What Already Exists (Don't Rebuild)

| Thing | Location | Status |
|-------|----------|--------|
| `TextVerifiedService` | `app/services/textverified_service.py` | ✅ Has `get_area_codes_list()`, `get_services_list()`, `_build_area_code_preference()`, `_build_carrier_preference()` |
| `availability_endpoints.py` | `app/api/verification/availability_endpoints.py` | ⚠️ Exists but queries DB history stats — NOT a pre-purchase live check |
| `Verification` model | `app/models/verification.py` | ✅ Already has `requested_area_code`, `requested_carrier` columns |
| `router.py` | `app/api/verification/router.py` | ⚠️ Minimal — only mounts `purchase_router` + `services_router` |
| Area code / carrier endpoints | `area_code_endpoints.py`, `carrier_endpoints.py` | ✅ Exist but not mounted in router |

---

## Tasks

### T1 — Add `check_availability()` to `TextVerifiedService`
**File:** `app/services/textverified_service.py`  
**What:** New async method that calls `self.client.verifications.pricing()` with the requested service/area_code/carrier and returns `{available: bool, cost: float, alternatives: []}`.  
**Why:** The pricing endpoint is the correct TextVerified call to check if a combo is purchasable before committing.  
**Acceptance:**
- [ ] Method exists and returns `available: True` when TextVerified responds
- [ ] Returns `available: False` + alternatives list when combo unavailable
- [ ] Falls back to `{available: True, cost: 2.50}` if TextVerified is disabled (don't block purchase)

---

### T2 — Add `POST /api/verify/check-availability` endpoint
**File:** `app/api/verification/availability_endpoints.py` (add new route to existing file)  
**What:** New `POST` route (separate from the existing `GET` stats routes) that accepts `{service, area_code?, carrier?, country}` and calls `TextVerifiedService.check_availability()`.  
**Why:** Frontend needs a single endpoint to gate the purchase button.  
**Acceptance:**
- [ ] Returns `{available, service, area_code, carrier, estimated_cost, alternatives}`
- [ ] Requires auth (`get_current_user_id`)
- [ ] 200 on both available and unavailable (availability is data, not an error)

---

### T3 — Mount missing routers in `router.py`
**File:** `app/api/verification/router.py`  
**What:** Include `area_code_endpoints`, `carrier_endpoints`, and the updated `availability_endpoints` routers.  
**Why:** They exist but are unreachable — frontend can't call them.  
**Acceptance:**
- [ ] `GET /api/verify/area-codes` reachable
- [ ] `GET /api/verify/carriers` reachable  
- [ ] `POST /api/verify/check-availability` reachable

---

### T4 — Add `GET /api/verify/options` parallel-load endpoint
**File:** `app/api/verification/availability_endpoints.py` (add alongside T2)  
**What:** Single endpoint that fires `asyncio.gather(get_services_list(), get_area_codes_list())` and returns both in one response.  
**Why:** Eliminates two sequential round-trips on page load; area codes are already cached 2h in `TextVerifiedService`.  
**Acceptance:**
- [ ] Returns `{services: [...], area_codes: [...]}`
- [ ] Completes in <2s (uses existing cache)

---

### T5 — Update `verify_modern.html` to multi-step flow
**File:** `templates/verify_modern.html`  
**What:** Replace single-form purchase with 3-step flow: (1) Service + area code + carrier selection, (2) Availability check with result display, (3) Purchase button enabled only after step 2 passes.  
**Why:** Users must see availability confirmation before money is deducted.  
**Acceptance:**
- [ ] Purchase button disabled until availability check returns `available: true`
- [ ] Shows alternatives if unavailable
- [ ] Falls back gracefully if `/check-availability` errors (enable purchase anyway — don't block on API failure)

---

### T6 — Update `static/js/verification.js` availability check logic
**File:** `static/js/verification.js`  
**What:** Add `checkAvailability()` function that calls `POST /api/verify/check-availability` and toggles the purchase button. Wire to service/area-code/carrier change events.  
**Why:** Keeps the multi-step state in JS without a full page reload.  
**Acceptance:**
- [ ] Calls check-availability when user clicks "Check Availability"
- [ ] Shows ✅/❌ status inline
- [ ] On ❌ renders alternatives as clickable options that pre-fill the selects

---

### T7 — Add `assigned_area_code` + `carrier_matched` tracking to `Verification` model
**File:** `app/models/verification.py`  
**What:** Add `assigned_area_code`, `area_code_matched` (bool), `assigned_carrier`, `carrier_matched` (bool) columns.  
**Why:** Enables post-purchase analytics to measure how often the overhaul actually prevents mismatches.  
**Note:** `requested_area_code` and `requested_carrier` already exist — only the "assigned" and "matched" columns are missing.  
**Acceptance:**
- [ ] Columns added to model
- [ ] Alembic migration created (`alembic/versions/005_add_verification_match_tracking.py`)
- [ ] `purchase_endpoints.py` populates these fields from `TextVerifiedService.create_verification()` return value (which already returns `assigned_area_code` and `fallback_applied`)

---

## Fix Order

```
T1 (service method) → T2 + T4 (endpoints) → T3 (mount routers) → T7 (model + migration) → T5 + T6 (frontend)
```

T1–T4 can be done in one pass (all backend). T7 is independent. T5–T6 depend on T3 being deployed.

---

## Success Metrics

| Metric | Now | Target |
|--------|-----|--------|
| Failed purchases | 8–12% | <2% |
| Refund rate | 5–7% | <1% |
| Purchase button shown without availability check | 100% | 0% |
