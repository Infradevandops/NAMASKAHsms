# Phase 6.0 — Platform Hardening & Feature Completion

**Version**: v4.6.0
**Status**: Planning
**Created**: May 7, 2026
**Scope**: Close security gaps, fix broken infrastructure, complete half-built features

---

## Context

Full codebase assessment conducted May 7, 2026.
- 336 Python files, 66 templates, 76 JS files, 48 models, 71 services
- 2,319 tests collected (1,541 unit, 24 integration) — 2 broken test files
- Core SMS verification + Paystack payments: fully working end-to-end
- Phase 5.0 admin intelligence: complete
- Remaining issues: security gaps, broken infrastructure, half-built features, scaffolding

---

## P0 — Security & Liability (do immediately)

### 6.1 — Remove crypto placeholder addresses
**Problem**: `config.py` has hardcoded placeholder BTC/ETH addresses (`bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`, `0x742d35Cc...`). These are displayed to users via `GET /api/wallet/crypto/addresses`. If a user sends real crypto to these addresses, funds are lost — the addresses belong to unknown parties.
**Fix**:
- [ ] Remove crypto payment UI from frontend entirely (no real on-chain verification exists)
- [ ] Return `{"available": false, "message": "Crypto payments coming soon"}` from the endpoint
- [ ] Or replace with real addresses if crypto payments are intended
**Files**: `app/core/config.py`, `app/api/billing/wallet_endpoints.py`, any template showing crypto addresses
**Effort**: 30 min

---

### 6.2 — Fix broken test collection (translation_service missing)
**Problem**: `tests/test_i18n.py` and `tests/test_i18n_frontend.py` import `app.services.translation_service` which doesn't exist. This causes 2 collection errors on every CI run and makes 778 tests in those files unreachable.
**Fix**:
- [ ] Create a minimal `app/services/translation_service.py` stub with the methods the tests expect
- [ ] Or delete both test files if i18n is not a planned feature
**Files**: `tests/test_i18n.py`, `tests/test_i18n_frontend.py`, `app/services/translation_service.py`
**Effort**: 15 min

---

## P1 — Security Gaps (before scaling)

### 6.3 — Session invalidation is a stub
**Problem**: `app/api/core/auth_enhanced.py` has `get_session()`, `invalidate_session()`, and `invalidate_all_sessions()` all returning `None`/`pass`. The logout and logout-all endpoints call these stubs. A stolen JWT remains valid until expiry regardless of logout — there is no server-side session revocation.
**Fix**:
- [ ] Implement session tracking using Redis (store JTI on login, delete on logout)
- [ ] `invalidate_session(db, refresh_token)` — delete from Redis by JTI
- [ ] `invalidate_all_sessions(db, user_id)` — delete all keys matching `session:{user_id}:*`
- [ ] Add JTI check in `get_current_user_id` dependency
**Files**: `app/api/core/auth_enhanced.py`, `app/core/dependencies.py`
**Effort**: 2 hours

---

### 6.4 — Affiliate approval flow missing
**Problem**: `CommissionEngine.calculate_commission()` now fires on payments when `user.is_affiliate` is true. But there is no way to set `user.is_affiliate = True` through normal flow — no admin endpoint to approve affiliate applications. `apply_for_affiliate` endpoint exists but approval is missing.
**Fix**:
- [ ] Add `POST /api/admin/users/{user_id}/approve-affiliate` endpoint
- [ ] Sets `user.is_affiliate = True`, `user.partner_type`, `user.commission_tier`
- [ ] Add to admin user management UI (Manage modal)
- [ ] Write audit log entry on approval
**Files**: `app/api/admin/user_management.py` or `app/api/admin/admin.py`, `static/js/admin/users.js`
**Effort**: 1 hour

---

## P2 — Broken Infrastructure

### 6.5 — v1 API router has most core routes disabled
**Problem**: `app/api/v1/router.py` comment says "Many core routers temporarily disabled for CI fix". The v1 router only includes admin + billing + verification routes. All core user-facing routes (auth, settings, notifications, preferences, etc.) are missing from `/api/v1/`. Any external API client using the v1 prefix gets incomplete coverage.
**Fix**:
- [ ] Audit which core routers were disabled and why
- [ ] Re-enable them in `v1_router` one by one, verifying no syntax errors
- [ ] Remove the "temporarily disabled" comment once complete
**Files**: `app/api/v1/router.py`
**Effort**: 1 hour

---

### 6.6 — Fraud scoring heuristic always returns 0.0
**Problem**: `score_verification()` is now called on every request (Phase 5 gap fix), but the heuristic checks for `"high_risk_country"` and `"high_risk_service"` as literal strings — these never match real country codes or service names. Every request scores 0.0. The admin fraud metrics card still shows hardcoded static constants.
**Fix**:
- [ ] Replace placeholder strings with real high-risk country codes (e.g. `["NG", "RU", "CN", "PK"]`)
- [ ] Replace placeholder service strings with known high-fraud services
- [ ] Update `get_model_metrics()` to compute rolling averages from recent `score_verification()` calls (store scores in Redis or a lightweight table)
**Files**: `app/services/fraud_detection_service.py`
**Effort**: 2 hours

---

### 6.7 — `notification_endpoints.py` silently swallows import errors
**Problem**: `app/api/core/notification_endpoints.py` wraps all sub-router imports in `try/except SyntaxError: pass`. If any notification sub-router has a syntax error, it's silently dropped with no log. This makes debugging notification issues very hard.
**Fix**:
- [ ] Replace bare `except SyntaxError: pass` with `except Exception as e: logger.error(f"Failed to load notification router: {e}")`
- [ ] Or verify all sub-routers import cleanly and remove the try/except entirely
**Files**: `app/api/core/notification_endpoints.py`
**Effort**: 15 min

---

## P3 — Incomplete Features (wire up when needed)

### 6.8 — Telegram SMS forwarding
**Problem**: Telegram forwarding is listed as "coming soon" in `forwarding.py`. The model (`sms_forwarding.py`) reserves the field. Users who want Telegram forwarding get a stub response.
**Fix**:
- [ ] Integrate Telegram Bot API (requires `TELEGRAM_BOT_TOKEN` env var)
- [ ] Implement `_send_forwarding_telegram()` in `forwarding.py`
- [ ] Add Telegram token input to forwarding settings UI
**Files**: `app/api/core/forwarding.py`, `templates/settings.html`
**Effort**: 3 hours
**Dependency**: Telegram bot token

---

### 6.9 — Whitelabel feature
**Problem**: `templates/whitelabel_setup.html` has a form with inputs but no JS wired to them (all placeholder text). `whitelabel_service.py` and `whitelabel_enhanced.py` exist in services (combined ~200 lines) but no endpoints mount them.
**Fix**:
- [ ] Create `app/api/core/whitelabel.py` with CRUD endpoints
- [ ] Wire form JS in `whitelabel_setup.html`
- [ ] Mount router in `main.py`
**Files**: `app/services/whitelabel_service.py`, `templates/whitelabel_setup.html`
**Effort**: 4 hours

---

### 6.10 — Push notifications
**Problem**: `device_token` model exists, `push_endpoints.py` exists, `enable_push_notifications: bool = True` in config. No FCM/APNs integration implemented.
**Fix**:
- [ ] Integrate Firebase Cloud Messaging (requires `FCM_SERVER_KEY` env var)
- [ ] Implement `push_endpoints.py` device registration + send
- [ ] Wire into `NotificationDispatcher`
**Files**: `app/api/notifications/push_endpoints.py`, `app/services/mobile_notification_service.py`
**Effort**: 4 hours
**Dependency**: Firebase project + FCM server key

---

### 6.11 — Real fraud scoring heuristics
**Covered by 6.6 above** — listed separately here as a P3 product decision.
When user count grows, replace heuristic with a lightweight ML model (scikit-learn logistic regression on verification history). Requires labeled training data (fraud vs. legitimate verifications).
**Effort**: 1 day when data exists

---

## P4 — Deferred (enterprise / future)

### 6.12 — Tax service activation
`tax_service.py` (386 lines) confirmed importable. Needs jurisdiction config and product decision on tax collection. Activate at >100 users or first enterprise client.

### 6.13 — Reseller service activation
`reseller_service.py` (206 lines) confirmed importable. Needs partner agreements and reseller onboarding flow. Activate when first reseller partner is signed.

### 6.14 — KYC document storage backend
`document_service` imports cleanly and KYC endpoints are mounted. But file upload depends on a storage backend (S3/GCS) that isn't configured. Activate when KYC is required (regulatory or enterprise).
**Dependency**: S3 bucket + `AWS_S3_BUCKET` env var

### 6.15 — Crypto payment verification
`wallet_endpoints.py` has crypto intent recording but no on-chain confirmation. Needs blockchain explorer webhook (Blockcypher, Alchemy, or Moralis) to confirm transactions. Activate if crypto payment volume justifies it.

---

## Platform Feature Status Summary (as of May 7, 2026)

### Fully working end-to-end
| Feature | Status |
|---------|--------|
| SMS verification purchase | ✅ |
| Carrier/area code enforcement | ✅ |
| VOIP rejection | ✅ |
| Paystack payments + webhook | ✅ |
| Revenue recognition on payment | ✅ |
| WebSocket real-time events | ✅ |
| MFA (setup/verify/disable/login) | ✅ |
| Currency selector + conversion | ✅ |
| SMS forwarding (email + webhook) | ✅ |
| API key management | ✅ |
| Referral tracking | ✅ |
| Blacklist management | ✅ |
| GDPR export + account deletion | ✅ |
| Admin panel (all 5 tabs) | ✅ |
| Pricing templates + promo | ✅ |
| Audit logging (tier/credit/pricing) | ✅ |
| Disputes (open/resolve) | ✅ |
| Failed refund queue | ✅ |
| Commission calculation | ✅ |
| Fraud scoring (call wired) | ✅ |

### Partially working
| Feature | Gap |
|---------|-----|
| Fraud scoring | Heuristic always returns 0.0 — fix in 6.6 |
| Session invalidation | Logout is a stub — fix in 6.3 |
| Affiliate program | No approval flow — fix in 6.4 |
| Crypto payments | Placeholder addresses, no on-chain verification |
| v1 API | Most core routes disabled |

### Not yet implemented
| Feature | Task |
|---------|------|
| Telegram forwarding | 6.8 |
| Push notifications | 6.10 |
| Whitelabel | 6.9 |
| KYC document storage | 6.14 |
| Tax collection | 6.12 |
| Reseller program | 6.13 |

---

## Priority Order

| Priority | Task | Effort | Risk if ignored |
|----------|------|--------|----------------|
| P0 | 6.1 — Remove crypto placeholder addresses | 30 min | Users lose real money |
| P0 | 6.2 — Fix broken test files | 15 min | CI noise, 778 tests unreachable |
| P1 | 6.3 — Session invalidation | 2 hrs | Stolen tokens stay valid forever |
| P1 | 6.4 — Affiliate approval flow | 1 hr | Commission engine fires but no affiliates exist |
| P2 | 6.5 — Re-enable v1 core routes | 1 hr | External API clients get incomplete coverage |
| P2 | 6.6 — Fraud scoring heuristics | 2 hrs | Metric always 0, useless |
| P2 | 6.7 — Notification import error swallowing | 15 min | Silent failures hard to debug |
| P3 | 6.8 — Telegram forwarding | 3 hrs | Feature gap |
| P3 | 6.9 — Whitelabel | 4 hrs | Template exists, no backend |
| P3 | 6.10 — Push notifications | 4 hrs | Nice to have |
| P4 | 6.12–6.15 — Tax/Reseller/KYC/Crypto | Deferred | Enterprise scale |

---

## Success Criteria

- [ ] No placeholder crypto addresses exposed to users
- [ ] CI collects all tests cleanly (0 errors)
- [ ] Logout actually invalidates tokens server-side
- [ ] Admin can approve affiliate applications
- [ ] v1 API router includes all core routes
- [ ] Fraud scoring returns non-zero scores for real requests
- [ ] Notification import failures are logged not silently swallowed
