# Phase 6.0 — Platform Hardening, Rentals & Voice Verification

**Version**: v4.6.0
**Status**: P0–P2 Complete, Whitelabel Done, TASKS.md Complete
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
- [ ] Option B (OpenAI Whisper) — deferred
  - **Activation Trigger**: When >50 voice verifications/month OR user requests transcription feature
  - **Prerequisites**: `OPENAI_API_KEY` env var, Whisper API integration
  - **Estimated Cost**: $0.006/minute (~$0.01 per voice verification)

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
- [ ] Rolling averages for `get_model_metrics()` — deferred
  - **Activation Trigger**: When >500 verifications logged (enables meaningful statistical analysis)
  - **Implementation**: Calculate 30-day rolling F1/precision/recall from verification outcomes
  - **Estimated Effort**: 3 hours

### 6.7 — Notification import error swallowing
- [x] All 5 `except SyntaxError: pass` replaced with `except Exception as e: logger.error(...)`
- [x] All 5 notification sub-routers confirmed to import cleanly

---

## P3 — Growth Features (external dependency)

### 6.8 — Telegram SMS forwarding
- [ ] Requires `TELEGRAM_BOT_TOKEN` env var
- [ ] Implement `_send_forwarding_telegram()` in `app/api/core/forwarding.py`
- [ ] Add Telegram config to settings UI

**Activation Checklist**:
1. Create Telegram bot via @BotFather
2. Store bot token in Render secrets
3. Configure webhook URL: `https://vrenum.onrender.com/api/telegram/webhook`
4. Test message delivery
5. Deploy to production

**Estimated Effort**: 4-6 hours (see TASKS_Q2_2026.md for detailed breakdown)

### 6.9 — Whitelabel feature
- [x] `app/api/core/whitelabel.py` created — `GET/POST/DELETE /api/whitelabel`, Pro+ tier gated
- [x] `/whitelabel` page route added to `main_routes.py`
- [x] `whitelabel_setup.html` form wired — loads existing config on page load, saves on button click
- [x] Upserts `WhiteLabelConfig` by `partner_id`

**Status**: ✅ Complete

### 6.10 — Push notifications
- [ ] Requires `FCM_SERVER_KEY` env var (Firebase)
- [ ] Implement `push_endpoints.py` device registration + send
- [ ] Wire into `NotificationDispatcher`

**Activation Checklist**:
1. Create Firebase project at console.firebase.google.com
2. Generate FCM server key
3. Store key in Render secrets
4. Configure web push certificates
5. Test notification delivery
6. Deploy to production

**Estimated Effort**: 6-8 hours (see TASKS_Q2_2026.md for detailed breakdown)
**Estimated Cost**: $20-50/month for 1,000 users

### 6.11 — Real fraud ML model
- [ ] Replace heuristic with scikit-learn logistic regression on verification history
- [ ] Requires labeled training data (fraud vs. legitimate)

**Activation Trigger**: When >1,000 verifications logged with labeled outcomes
**Prerequisites**:
- Manual fraud labeling of 200+ historical verifications
- Feature engineering (user behavior, service patterns, timing)
- Model training pipeline

**Estimated Effort**: 2-3 weeks

---

## P4 — Enterprise Features

### 6.12 — Tax service
`tax_service.py` importable.

**Activation Triggers**:
- User count >100 OR
- Monthly revenue >$5,000 OR
- First enterprise client requiring tax compliance

**Prerequisites**:
- Stripe Tax or TaxJar API integration
- `tax_reports` table migration
- Admin tax management UI

### 6.13 — Reseller service
`reseller_service.py` importable.

**Activation Triggers**:
- First reseller partner agreement signed OR
- >10 affiliate users request reseller features

**Prerequisites**:
- `reseller_accounts` table migration
- Reseller onboarding documentation
- Commission calculation rules

### 6.14 — KYC document storage
Endpoints mounted, `document_service` importable.

**Activation Trigger**: First Pro/Custom user requests KYC verification

**Prerequisites**:
- AWS S3 bucket configuration (`AWS_S3_BUCKET`)
- Document encryption at rest
- Retention policy (7 years for compliance)

### 6.15 — Crypto on-chain verification
**Activation Trigger**: Crypto payment volume >$1,000/month

**Prerequisites**:
- Blockchain explorer webhook (Etherscan, Blockchair)
- On-chain transaction monitoring
- Automated credit application on confirmation

---

## Platform Feature Status (as of May 7, 2026 — post Phase 6)

### Fully working end-to-end
| Feature | Status | Notes |
|---------|--------|-------|
| SMS verification purchase | ✅ | |
| Voice verification | ✅ | Audio player functional |
| Number rentals | ✅ | All 5 endpoints + expiry monitor |
| Carrier/area code enforcement | ✅ | |
| VOIP rejection | ✅ | |
| Paystack payments + webhook | ✅ | |
| Revenue recognition on payment | ✅ | |
| WebSocket real-time events | ✅ | Payment + SMS completion |
| MFA | ✅ | Setup/verify/disable/login enforcement |
| Session invalidation | ✅ | Logout revokes JWT via Redis |
| Currency selector + conversion | ✅ | |
| SMS forwarding | ✅ | Email + webhook (Telegram pending) |
| API key management | ✅ | |
| Referral tracking | ✅ | |
| Blacklist management | ✅ | |
| GDPR export + deletion | ✅ | |
| Admin panel | ✅ | All 5 tabs, real data |
| Pricing templates + promo | ✅ | Discount applied to calculations |
| Audit logging | ✅ | Tier/credit/pricing/affiliate |
| Disputes | ✅ | Open/resolve |
| Failed refund queue | ✅ | |
| Commission calculation | ✅ | On payment |
| Fraud scoring | ✅ | Real heuristics (rolling avg pending) |
| Affiliate approval/revoke | ✅ | |
| Admin rentals page | ✅ | |
| Rental expiry monitor | ✅ | |
| Whitelabel | ✅ | |
| v1 API | ✅ | 231 routes |
| CI test collection | ✅ | 2,338 tests, 0 errors |

### Optimizations pending
| Feature | Gap | Activation Trigger |
|---------|-----|--------------------|
| Fraud metrics | Static constants | >500 verifications |
| Voice transcription | No Whisper | >50 voice verifications/month |

### Not yet implemented (P3/P4)
| Feature | Task | Dependency | Effort |
|---------|------|------------|--------|
| Telegram forwarding | 6.8 | Bot token | 4-6 hours |
| Push notifications | 6.10 | Firebase key | 6-8 hours |
| KYC document storage | 6.14 | S3 bucket | 8-12 hours |
| Tax collection | 6.12 | >100 users OR >$5k/mo | 2-3 weeks |
| Reseller program | 6.13 | Partner agreement | 2-3 weeks |
| Crypto on-chain | 6.15 | >$1k crypto/mo | 1-2 weeks |
| Fraud ML model | 6.11 | >1,000 verifications | 2-3 weeks |

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
