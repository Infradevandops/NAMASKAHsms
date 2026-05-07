# Phase 6.0 — Platform Hardening, Rentals & Voice Verification

**Version**: v4.6.0
**Status**: P0–P2 Complete — P3 Deferred
**Created**: May 7, 2026
**Last Updated**: May 7, 2026
**Scope**: Close security gaps, fix broken infrastructure, complete half-built features, implement number rentals, verify voice stability

---

## Context

Full codebase assessment conducted May 7, 2026.
- 336 Python files, 66 templates, 76 JS files, 48 models, 71 services
- 2,338 tests collected (0 collection errors after fix)
- Core SMS verification + Paystack payments: fully working end-to-end
- Phase 5.0 admin intelligence: complete

---

## Number Rentals

### 6.16 — Rental API endpoints
- [x] `app/api/verification/rental_endpoints.py` created with all 5 endpoints
- [x] `POST /api/rentals/request` — Pro+ tier gate, balance check, `create_reservation()`, `NumberRental` saved, credits deducted, transaction record written
- [x] `GET /api/rentals/active` — lists user's active rentals with minutes remaining
- [x] `GET /api/rentals/{id}/messages` — proxies to `get_reservation_messages()`
- [x] `POST /api/rentals/{id}/extend` — charges for extension, updates `expires_at`
- [x] `POST /api/rentals/{id}/cancel` — cancels with provider, partial refund for unused hours
- [x] Mounted in `app/api/verification/router.py`

### 6.17 — Rental expiry background task
- [x] 15-minute loop added to `app/core/lifespan.py`
- [x] Marks `NumberRental` records as `expired` when `expires_at < now`
- [x] Sends `rental_expiring_soon` notification when within 1 hour and `warning_sent=False`
- [x] Sets `warning_sent=True` after sending

### 6.18 — Admin rentals page
- [x] `templates/admin/rentals.html` created — stat cards + full rentals table
- [x] `/admin/rentals` route added to `app/api/main_routes.py`
- [x] Calls `GET /api/admin/dashboard/v2/rentals`, renders active/expiring rentals with time remaining

---

## Voice Verification

### 6.19 — Voice transcription
- [x] Option C implemented: `audio_url` received → mark complete with `sms_code="VOICE_RECV"` immediately, no re-poll
- [ ] Option B (OpenAI Whisper) — deferred, requires `OPENAI_API_KEY`

### 6.20 — Voice audio player UI
- [x] `<audio controls>` added to `voice_status.html`
- [x] Shows "🔊 Audio Ready" when `sms_code === "VOICE_RECV"`
- [x] Audio player shown when `audio_url` present

### 6.21 — Voice pricing vs SMS
- [x] Investigated: TextVerified returns `result.total_cost` from SDK regardless of capability
- [x] Voice pricing is identical to SMS at provider level — no differentiation needed
- [x] Closed — no code change required

### 6.22 — Voice polling timeout fix
- [x] `sms_polling_service.py` updated: when `audio_url` received, marks complete immediately with `VOICE_RECV` — no re-poll that could timeout

---

## P0 — Security & Liability

### 6.1 — Crypto placeholder addresses
- [x] `GET /api/wallet/crypto/addresses` returns `{"available": false, "message": "Crypto payments coming soon"}`
- [x] Crypto tab in `wallet.html` disabled with "Coming Soon" label and `cursor:not-allowed`

### 6.2 — Broken test collection
- [x] `app/services/translation_service.py` stub created with `get_available_languages()` and `translate()`
- [x] 2,338 tests now collect cleanly (0 errors, up from 2 errors)

---

## P1 — Security Gaps

### 6.3 — Session invalidation
- [x] `auth_enhanced.py` logout calls `AuthService.revoke_token()` — adds JTI to Redis blacklist
- [x] `auth_enhanced.py` logout-all sets `logout_all:{user_id}` Redis key (30-day TTL)
- [x] `auth_service.py` `verify_token()` checks both JTI blacklist and `logout_all` key
- [x] Main login (`auth_routes.py`) now includes `jti` + `iat` in JWT payload — tokens are revocable

### 6.4 — Affiliate approval flow
- [x] `POST /api/admin/users/{id}/approve-affiliate` — sets `is_affiliate=True`, `partner_type`, `commission_tier`, writes audit log
- [x] `POST /api/admin/users/{id}/revoke-affiliate` — reverses it
- [x] Admin Manage modal has Approve/Revoke Affiliate button wired to endpoints

---

## P2 — Broken Infrastructure

### 6.5 — v1 API router
- [x] `app/api/v1/router.py` restored from ~16 routes to 231
- [x] Added `core_router` (105 routes), `auth_router`, `notification_router`
- [x] "Temporarily disabled" comment removed

### 6.6 — Fraud scoring heuristics
- [x] Replaced placeholder strings with real risk lists
- [x] High-risk countries: `NG, RU, CN, PK, BD, VN, IN, UA, KE, GH`
- [x] High-risk services: `telegram, whatsapp, tiktok, instagram, facebook, uber`
- [ ] Rolling averages for `get_model_metrics()` — deferred (needs data accumulation)

### 6.7 — Notification import error swallowing
- [x] All 5 `except SyntaxError: pass` replaced with `except Exception as e: logger.error(...)`
- [x] All 5 notification sub-routers confirmed to import cleanly

---

## P3 — Deferred (external dependency or growth feature)

### 6.8 — Telegram SMS forwarding
- [ ] Requires `TELEGRAM_BOT_TOKEN` env var
- [ ] Implement `_send_forwarding_telegram()` in `app/api/core/forwarding.py`
- [ ] Add Telegram config to settings UI
**Activate when**: Telegram bot token is available

### 6.9 — Whitelabel feature
- [ ] Create `app/api/core/whitelabel.py` with CRUD endpoints
- [ ] Wire form JS in `templates/whitelabel_setup.html`
- [ ] Mount router in `main.py`
**Activate when**: First whitelabel customer

### 6.10 — Push notifications
- [ ] Requires `FCM_SERVER_KEY` env var (Firebase)
- [ ] Implement `push_endpoints.py` device registration + send
- [ ] Wire into `NotificationDispatcher`
**Activate when**: Firebase project configured

### 6.11 — Real fraud ML model
- [ ] Replace heuristic with scikit-learn logistic regression on verification history
- [ ] Requires labeled training data (fraud vs. legitimate)
**Activate when**: >1,000 verifications logged

---

## P4 — Enterprise / Future

### 6.12 — Tax service
`tax_service.py` importable. Activate at >100 users or first enterprise client.

### 6.13 — Reseller service
`reseller_service.py` importable. Activate when first reseller partner signed.

### 6.14 — KYC document storage
Endpoints mounted, `document_service` importable. Needs S3 bucket (`AWS_S3_BUCKET`).

### 6.15 — Crypto on-chain verification
Needs blockchain explorer webhook. Activate if crypto volume justifies it.

---

## Platform Feature Status (as of May 7, 2026 — post Phase 6)

### Fully working end-to-end
| Feature | Status |
|---------|--------|
| SMS verification purchase | ✅ |
| Voice verification | ✅ |
| Number rentals | ✅ |
| Carrier/area code enforcement | ✅ |
| VOIP rejection | ✅ |
| Paystack payments + webhook | ✅ |
| Revenue recognition on payment | ✅ |
| WebSocket real-time events (payment + SMS) | ✅ |
| MFA (setup/verify/disable/login enforcement) | ✅ |
| Session invalidation (logout revokes JWT) | ✅ |
| Currency selector + conversion | ✅ |
| SMS forwarding (email + webhook) | ✅ |
| API key management | ✅ |
| Referral tracking | ✅ |
| Blacklist management | ✅ |
| GDPR export + account deletion | ✅ |
| Admin panel (all 5 tabs, real data) | ✅ |
| Pricing templates + promo (discount applied) | ✅ |
| Audit logging (tier/credit/pricing/affiliate) | ✅ |
| Disputes (open/resolve) | ✅ |
| Failed refund queue | ✅ |
| Commission calculation on payment | ✅ |
| Fraud scoring (real heuristics) | ✅ |
| Affiliate approval/revoke | ✅ |
| Admin rentals page | ✅ |
| Rental expiry monitor | ✅ |
| v1 API (231 routes) | ✅ |
| CI test collection (2,338 tests, 0 errors) | ✅ |

### Partially working
| Feature | Gap |
|---------|-----|
| Fraud scoring | Heuristics work; rolling averages for metrics card deferred |
| Crypto payments | UI disabled; endpoint returns unavailable; no on-chain verification |
| Voice transcription | Audio player works; Whisper transcription deferred |

### Not yet implemented (P3/P4)
| Feature | Task | Dependency |
|---------|------|-----------|
| Telegram forwarding | 6.8 | Bot token |
| Push notifications | 6.10 | Firebase key |
| Whitelabel | 6.9 | None |
| KYC document storage | 6.14 | S3 bucket |
| Tax collection | 6.12 | Product decision |
| Reseller program | 6.13 | Partner agreements |
| Crypto on-chain | 6.15 | Blockchain webhook |

---

## Success Criteria

- [x] No placeholder crypto addresses exposed to users
- [x] CI collects all tests cleanly (0 errors)
- [x] Logout actually invalidates tokens server-side
- [x] Admin can approve/revoke affiliate applications
- [x] v1 API router includes all core routes (231 routes)
- [x] Fraud scoring returns non-zero scores for real high-risk requests
- [x] Notification import failures are logged not silently swallowed
- [x] Rentals page fully functional (request, view, extend, cancel)
- [x] Rental expiry warnings sent, expired rentals marked in DB
- [x] Voice verification completes without hanging in "transcribing" status
- [x] Voice audio player shown when audio_url is present
- [x] Voice pricing verified — identical to SMS at provider level
