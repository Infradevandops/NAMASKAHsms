# Project Tasks & Status

**Last Updated**: April 13, 2026  
**Version**: 4.4.1  
**CI Status**: ✅ All checks passing

---

## ✅ COMPLETED (12/13 original + multi-provider routing)

- [x] **Cancel route double path** - Fixed routing
- [x] **Test module imports** - Updated to correct modules
- [x] **auth_headers_factory** - Fixed integration tests
- [x] **SMS polling settings** - Added to config
- [x] **Tier upgrade test** - Fixed MagicMock comparison
- [x] **Verification endpoint routes** - Updated /api/verify → /api/verification
- [x] **Email/SMTP configuration** - Resend API working
- [x] **Duplicate payment_logs** - Not duplicated (verified)
- [x] **SMSForwarding FK constraint** - Removed invalid FK
- [x] **test_payment_race_condition** - Already deleted
- [x] **Admin balance sync** - Syncs from TextVerified API
- [x] **CI pipeline** - All 4 checks passing + provider gate added
- [x] **Admin tier verification** - Code verified correct
- [x] **Multi-provider routing** - TextVerified, Telnyx, 5sim (commit 0bcace42)
- [x] **HTTP client resource leaks** - Fixed via lazy singleton (commit ee8f376e)
- [x] **Telnyx adapter tests** - 23 tests written (commit ee8f376e)
- [x] **5sim adapter tests** - 25 tests written (commit ee8f376e)
- [x] **SMS polling dispatch tests** - 15 tests written (commit ee8f376e)
- [x] **Provider router edge case tests** - 8 new tests (commit ee8f376e)
- [x] **SMS gateway tests** - 4 tests written (commit ee8f376e)
- [x] **Adaptive polling tests** - 9 tests written (commit ee8f376e)
- [x] **Availability service tests** - 7 tests written (commit ee8f376e)
- [x] **Event broadcaster tests** - 10 tests written (commit ee8f376e)

---

## 🔴 OUTSTANDING — MUST FIX BEFORE PRODUCTION (3 items)

- [ ] **Startup health checks** — `app/services/providers/health_check.py` does not exist. Bad API keys only discovered when a user tries to purchase. Need `check_textverified_health()`, `check_telnyx_health()`, `check_fivesim_health()`, wired into `main.py` startup event. ~2 hours

- [ ] **Error handling (17 broad `except Exception`)** — All 17 are still in provider files (`telnyx_adapter.py` ×4, `fivesim_adapter.py` ×6, `provider_router.py` ×5, `textverified_adapter.py` ×2). Need specific handlers: `httpx.TimeoutException` → retry 3×, `httpx.HTTPStatusError` → raise RuntimeError, `httpx.ConnectError` → raise immediately, `KeyError` → raise ValueError. ~3 hours

- [ ] **Provider balance monitoring** — `app/services/providers/balance_monitor.py` does not exist. No alerts when credits run low. Need scheduled job every 5 min, alert at $50/$25, auto-disable at $10, `GET /api/admin/provider-balances` endpoint. ~2 hours

---

## 🟡 OUTSTANDING — SHOULD DO (3 items)

- [ ] **Purchase endpoint integration tests** — 5 tests needed: `test_purchase_us_routes_textverified`, `test_purchase_gb_routes_fivesim`, `test_verification_record_provider_field`, `test_purchase_failover_success`, `test_purchase_business_error_no_failover`. ~2 hours

- [ ] **TextVerified regression tests** — 18 bug fixes in `textverified_service.py` have no regression coverage. 10 tests needed covering: `poll_sms_standard` uses TV object, `parsed_code` used first, `ends_at` returned, stale SMS filtered, report called on timeout, area code fallback, VOIP rejection, retry logic. ~3 hours

- [ ] **Load tests** — 1000 sequential requests, 50 concurrent, memory stable. Not run yet. ~2 hours

---

## 📋 OPTIONAL IMPROVEMENTS

- [ ] **TextVerified local setup** - Add credentials to .env.local (15 min)
- [ ] **Database backups** - Set up S3 backups (1 hr)
- [ ] **Render cold starts** - Upgrade to Starter plan $7/mo (5 min)
- [ ] **Incident runbook** - Document on-call procedures (1 hr)
- [ ] **Troubleshooting guide** - Common issues and fixes (1 hr)

---

## 🚀 ROADMAP

### Q2 2026
- [ ] Enable Telnyx/5sim in production (needs API keys)
- [ ] Enhanced analytics dashboard
- [ ] SDK libraries (Python, JavaScript, Go)
- [ ] API rate limiting improvements
- [ ] Update NGN_USD_RATE if exchange rate drifts

### Q3 2026
- [ ] Premium tier with Carrier Guarantee
- [ ] Multi-region deployment
- [ ] Advanced carrier analytics

### Q4 2026
- [ ] Commercial APIs (if volume justifies)
- [ ] Enterprise tier features
- [ ] Advanced reporting

---

## 📊 SUMMARY

**Progress**: All original items done + multi-provider routing implemented  
**Critical Issues**: 3 (health checks, error handling, balance monitoring)  
**CI Health**: 4/4 checks passing + provider 90% coverage gate  
**Next Action**: Fix 3 outstanding critical items (~7 hours total)

---

## 📝 DETAILED STATUS

<details>
<summary>Click to expand detailed status of all items</summary>

### ✅ 1. Cancel Route Double Path
**Status**: Fixed  
**Details**: Removed router prefix from cancel_endpoint.py, added /verification prefix in router.py  
**Route**: `/api/verification/cancel/{id}`

### ✅ 2. Test Module Imports
**Status**: Fixed  
**Details**: Rewritten test_verification_and_tier.py to use correct modules  
**Changes**:
- create_verification → purchase_endpoints.request_verification
- get_verification_status → status_polling.get_verification_status
- get_verification_sms → sms_polling_service._poll_verification

### ✅ 3. auth_headers_factory Issue
**Status**: Fixed  
**Details**: test_verification_api.py uses correct local fixture returning plain dict

### ✅ 4. SMS Polling Settings
**Status**: Fixed  
**Details**: Added settings to config.py:
- sms_polling_initial_interval_seconds
- sms_polling_later_interval_seconds
- sms_polling_max_minutes
- sms_polling_error_backoff_seconds

### ✅ 5. Tier Upgrade Test
**Status**: Fixed  
**Details**: Mocked TierConfig and PaymentService to avoid MagicMock comparison errors

### ✅ 6. Verification Endpoint Routes
**Status**: Fixed (March 30, 2026 - Commit 998506dc)  
**Details**: Updated all routes from /api/verify to /api/verification in test_verification_endpoints_comprehensive.py

### ✅ 7. Email/SMTP Configuration
**Status**: Working (Not broken)  
**Details**:
- Resend API key configured: `RESEND_API_KEY=re_CRsTXCGH_AtjVPHdBeVEKmRzqtA1ncdys`
- Set in Render environment variables
- Email verification and password reset functional

### ✅ 8. Duplicate payment_logs
**Status**: Not a problem (Verified)  
**Details**: Only 1 definition exists in app/models/transaction.py. No duplicate found.

### ✅ 9. SMSForwarding FK Constraint
**Status**: Fixed (March 30, 2026 - Commit 998506dc)  
**Details**: Removed ForeignKey("rentals.id") from app/models/sms_message.py

### ✅ 10. test_payment_race_condition
**Status**: Already deleted  
**Details**: File does not exist in codebase

### ✅ 11. Admin Balance Sync
**Status**: Implemented (March 30, 2026 - Commits 211845bf, 459b4e7e)  
**Details**:
- Admin balance syncs from TextVerified API
- Transaction history preserved
- Files: app/services/balance_service.py, app/services/transaction_service.py

### ✅ 12. CI Pipeline
**Status**: Fixed (March 30, 2026 - Commit 85cc2c8f)  
**Details**: Removed codecov, all 4 checks passing

### ✅ 13. Admin Tier Verification
**Status**: Verified  
**Details**: Code audit confirmed admin tier logic is correct. `TierManager.get_user_tier()` bypasses expiry for admins and defaults to "custom" if no tier set. No code changes needed.


---

**See also**: `docs/tasks/SMART_MULTI_PROVIDER_ROUTING.md` for routing implementation details
