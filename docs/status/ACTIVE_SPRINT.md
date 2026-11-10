# ACTIVE SPRINT — Stability Locked + Area Code Price Display Fix

**Updated**: November 10, 2026
**Server**: https://vrenum.app — ✅ Healthy ($42.15 TV balance)
**CI**: ✅ Green — 25-file gate
**Deploy**: ✅ All commits live

---

## Stability Acceptance Criteria — STATUS

- [x] CI green confirmed
- [x] All commits live on server
- [x] TV pricing URL verified from VPS — `/pricing/verifications` = 200, old path = 404
- [x] `test_textverified_service.py` added to CI gate (25 files, 31 tests)
- [x] `TEXTVERIFIED_EMAIL` health check fix deployed
- [x] Stock monitor fixed — price-based availability, no more `available: 0`
- [ ] Telegram E2E live test — code complete, pending manual test
- [ ] No Sentry errors from SDK fixes in first 24h post-deploy (monitor ongoing)

---

## Open Tasks — Priority Order

### P1 — Area code price display mismatch
**What**: `check_service_available()` always sends `area_code=False` → returns base price.
When user selects an area code, UI shows base price but they get charged base + $0.25 surcharge.
**Fix**: Pass `area_code=True` to `check_service_available()` when area code is selected,
so the displayed price includes the surcharge before the user commits.
**File**: `textverified_service.py` → `check_service_available()` + call site in `purchase_endpoints.py`

### P1 — Telegram E2E live test
Code complete since v4.9.0. Steps in `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md`.
Manual test with a real Telegram account — connect bot, trigger verification, confirm forward.

### P2 — Delete dead code in `textverified_service.py`
Two methods have no live callers since v4.9.9:
- `_fetch_prices_inline()` — replaced by `_fetch_and_cache_pricing()` (SDK path)
- `fetch_raw_services_with_quantity()` — removed from stock monitor (qty=0 was root cause)

### P2 — CI coverage push 25% → 60%
Next batch to audit and wire (run locally first, fix failures, then add to `ci.yml`):
```
tests/unit/test_verification_endpoints.py
tests/unit/test_payment_service.py
tests/unit/test_auth_endpoints.py
tests/unit/test_wallet_service.py
tests/unit/test_transaction_service.py
tests/unit/test_tier_manager.py
tests/unit/test_quota_service.py
tests/unit/test_stock_monitor.py
tests/unit/test_area_code_check.py
```
Raise `--cov-fail-under` by 5% per batch.

### P3 — Trivial fixes
- Stock monitor docstring says "15-minute refresh" — should be "90 seconds" (Gap 8)
- `validating` SSE step does no real work — remove or wire to `get_verification_details()` (Gap 2)
- No `transcribing` SSE status for voice verifications (Gap 7)

---

## What Is Confirmed Live

### TV Integration
- ✅ `check_service_available()` uses SDK `verifications.pricing()` — correct URL confirmed from VPS
- ✅ `verifications.create()` — SDK, correct enums, `max_price` wired
- ✅ Voice pricing uses `NumberType.VOIP`
- ✅ `reactivate` before `report` on timeout (saves refund cost)
- ✅ `can_report` checked before calling `report_verification()`
- ✅ `ends_at` from TV persisted to DB (accurate polling timeout)
- ✅ Voice: `sms_content` used as transcription
- ✅ 5 broken rental SDK calls fixed
- ✅ TV webhook instant SMS delivery registered

### Verification Flow
- ✅ SSE streaming purchase — real-time steps, cancel before charge commits
- ✅ Dynamic `ends_at` window from TV
- ✅ Orphan verification recovery on page reload
- ✅ P0 availability gate on both SSE and legacy paths
- ✅ Null-price services filtered from picker
- ✅ Out-of-stock services greyed out and unclickable
- ✅ Stock monitor 90s loop — price-based availability

### Infrastructure
- ✅ Real `/health` endpoint — DB + Redis + TV credentials check
- ✅ `TEXTVERIFIED_EMAIL` accepted as fallback for `TEXTVERIFIED_USERNAME`
- ✅ Deploy hard-gated on CI pass
- ✅ Area code modal shows city names ("212 — New York, NY")
- ✅ 23h area code cache background refresh

---

## Next Phases (post-stability)

### Phase 2 Analytics
Cohort retention, revenue breakdown by tier/service/day, churn signal (14+ days inactive).
Pre-work: assess `user_events` + `purchase_outcomes` tables for existing data.
Task doc: `docs/features/PHASE2_ANALYTICS.md` (to be created).

### Reuse + Reactivate UI
Backend implemented. Not surfaced to users.
- **Reactivate**: show "Extending your window..." when timeout triggers reactivation
- **Reuse**: post-code receipt offers "Verify another service with this number" at lower price

### smsAndVoiceCombo capability
`ReservationCapability.SMS_AND_VOICE_COMBO` exists in SDK, never used.
One number receives both SMS and voice — useful for services that try SMS then fall back to call.
