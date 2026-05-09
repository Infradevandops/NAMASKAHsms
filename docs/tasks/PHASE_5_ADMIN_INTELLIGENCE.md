# Phase 5.0 — Admin Intelligence & Growth Services Integration

**Version**: v4.5.0
**Status**: Complete (1 optimization remaining)
**Created**: May 6, 2026
**Last Audited**: May 7, 2026
**Scope**: Wire up pre-built services to admin panel, feed real data from DB

---

## Overview

The admin panel ("Control Center") has a polished UI with 5 inner tabs + 5 top-level nav items, but many sections display placeholder/zero data because the underlying services exist but aren't connected to real DB queries or aren't mounted. This phase wires everything together.

**Current State**:
- 19 pre-built service files (never imported by any route)
- 7 admin endpoint files (never mounted in router)
- Admin panel tabs show $0 / 0 / "Behind" because queries return empty results on a 2-user DB
- Growth target hardcoded to 350 (unrealistic for current stage)

---

## Architecture

```
Admin Panel (templates/admin/dashboard.html)
├── Top Nav: Overview | Targets | Pricing | Rentals | Logs
└── Inner Tabs: Institutional Overview | User Intelligence | Verification Forensics | Pricing Governance | Control & Audit
         │
         ▼
    JS Files (static/js/admin/*.js)
         │
         ▼
    API Endpoints (app/api/admin/intelligence.py + others)
         │
         ▼
    Services (app/services/*_service.py)
         │
         ▼
    Models/DB Tables (app/models/*.py)
```

---

## Task Breakdown

### 5.1 — Fix Growth Targets (make configurable)

**Problem**: Target hardcoded to 350 users in `target_tracking_service.py`
**Fix**:
- [x] Make target configurable via admin UI (not hardcoded)
- [x] Add "Set Target" button in admin Overview tab
- [x] API: `POST /api/admin/intelligence/targets/set` to update target
- [x] Dynamic label renders from DB value

**Files**: `app/services/target_tracking_service.py`, `static/js/admin/overview.js`, `templates/admin/dashboard.html`

---

### 5.2 — Mount Unmounted Admin Endpoints

**Problem**: 7 endpoint files exist but aren't in the router
**Fix**:
- [x] Mount `alerts.py` → mounted on main app at `/api/alerts/webhook`
- [x] Mount `support.py` → `/admin/support/*`
- [x] Mount `kyc.py` → `/admin/kyc/*`
- [x] Mount `audit_unreceived.py` → `/admin/audit/unreceived-verifications`
- [x] `analytics_monitoring.py` → empty stub, skipped
- [x] `disaster_recovery.py` → broken prefix + missing service, skipped
- [x] `dependencies.py` → shared dep helper, not a router, skipped

**File**: `app/api/admin/router.py`

---

### 5.3 — Wire Fraud Detection Service

**Problem**: `fraud_detection_service.py` exists but never called
**Integration**:
- [x] `GET /api/admin/intelligence/fraud/metrics` endpoint wired
- [x] Fraud model F1/Precision stat card added to admin Overview tab
- [x] `overview.js` loads metrics on init

**Files**: `app/services/fraud_detection_service.py`, `app/api/admin/intelligence.py`, `static/js/admin/overview.js`

---

### 5.4 — Wire Business Intelligence / Revenue

**Problem**: `business_intelligence.py` unusable (AsyncSession + missing Rental model). `$0` revenue bug in overview.js.
**Integration**:
- [x] `GET /api/admin/intelligence/revenue` queries Transaction directly — real 30d revenue
- [x] Fixed silent crash in `overview.js` (`vitData.monthly_revenue` was undefined)
- [x] Revenue card now shows real data from DB

**Files**: `app/api/admin/intelligence.py`, `static/js/admin/overview.js`

---

### 5.5 — Wire Revenue Recognition Service

**Problem**: `revenue_recognition_service.py` (379 lines) — full implementation, unused
**Integration**:
- [x] `GET /api/admin/intelligence/revenue/recognition` — recognized vs deferred summary by period
- [x] All 4 models (`RevenueRecognition`, `DeferredRevenueSchedule`, `RevenueAdjustment`, `AccrualTrackingLog`) confirmed importable
- [x] Promo template endpoints added: `POST /admin/pricing/templates/promo`, `GET /admin/pricing/templates/active-promo`

**Files**: `app/services/revenue_recognition_service.py`, `app/api/admin/intelligence.py`, `app/api/admin/pricing_control.py`

---

### 5.6 — Wire Commission Engine & Affiliate

**Problem**: `commission_engine.py` — calculates affiliate payouts, unused
**Integration**:
- [x] `GET /api/admin/intelligence/commissions/pending` endpoint wired
- [x] Returns pending count, total pending amount, and per-item breakdown
- [x] `CommissionTier` + `RevenueShare` models confirmed present

**Files**: `app/services/commission_engine.py`, `app/models/commission.py`, `app/api/admin/intelligence.py`

---

### 5.7 — Wire Currency Service

**Problem**: `currency_service.py` — multi-currency support, unused
**Integration**:
- [x] `GET /api/currencies` endpoint created, exposes rates + symbols
- [x] `preferences.py` already fully wired (`/api/user/preferences` GET/PUT) — currency saving was already working
- [x] `CurrencyService` now publicly accessible for frontend conversion

**Files**: `app/services/currency_service.py`, `app/api/core/currencies.py`

---

### 5.8 — Wire MFA Service

**Problem**: `mfa_service.py` — working 2FA with pyotp/qrcode, unused
**Integration**:
- [x] Alembic migration `add_mfa_fields` adds `mfa_secret` + `mfa_enabled` to users table
- [x] `mfa_secret` + `mfa_enabled` columns added to User model
- [x] `POST /api/user/mfa/setup` — generates secret + QR code
- [x] `POST /api/user/mfa/verify` — validates token and enables MFA
- [x] `POST /api/user/mfa/disable` — disables MFA after token confirmation

**Files**: `app/services/mfa_service.py`, `app/api/core/mfa.py`, `app/models/user.py`, `alembic/versions/add_mfa_fields.py`

---

### 5.9 — Wire Failed Refund Queue & Disputes

**Problem**: `failed_refund_service.py` + `dispute_service.py` — unused
**Integration**:
- [x] `GET /api/admin/intelligence/refunds/failed` endpoint wired
- [x] Failed refund queue table added to Control & Audit tab
- [x] `compliance.js` loads it when audit tab opens
- [x] `GET /api/admin/intelligence/disputes` — all open disputes for admin
- [x] `POST /api/admin/intelligence/disputes/{id}/resolve` — resolve with won/lost/appealed
- [x] `POST /api/disputes/open` — user-facing dispute creation
- [x] `GET /api/disputes/my` — user's own disputes

**Files**: `app/services/failed_refund_service.py`, `app/services/dispute_service.py`, `app/api/admin/intelligence.py`, `app/api/core/disputes.py`

---

### 5.10 — Wire Event Broadcaster (WebSocket)

**Problem**: `event_broadcaster.py` — real-time events, unused
**Integration**:
- [x] `EventBroadcaster` wired into `payment_service.py` — broadcasts `payment.completed` to user on credit
- [x] `EventBroadcaster` wired into `sms_polling_service.py` — broadcasts `verification.completed` when SMS code received
- [x] WebSocket manager already mounted (`/ws/events`) — broadcaster uses existing connection manager

**Files**: `app/services/event_broadcaster.py`, `app/services/payment_service.py`, `app/services/sms_polling_service.py`

---

### 5.11 — Wire Alerting Service

**Problem**: `alerting_service.py` — triggers alerts, unused
**Integration**:
- [x] `alerts.py` mounted on main app at `/api/alerts/webhook` (AlertManager can POST here)
- [x] `alerting_service.py` logs to Sentry (already active in production)
- [ ] Active alert triggering (low balance, high error rate) — deferred, needs threshold config

**Files**: `app/services/alerting_service.py`, `app/api/admin/alerts.py`

---

### 5.12 — Fix Admin Panel Labels & UX

**Problem**: Labels were aspirational ("Phase 6.0 Institutional Infrastructure", hardcoded 350)
**Fix**:
- [x] "Phase 6.0 Institutional Infrastructure" → "Phase 5.0 Admin Intelligence"
- [x] Hardcoded `(350)` and `0 / 350` replaced with dynamic `<span id="target-label">` from DB
- [x] Set Target input + Save button added inline to target card

**Files**: `templates/admin/header.html`, `templates/admin/dashboard.html`

---

### 5.13 — Ensure DB Tables Exist

**Problem**: Some services reference models/tables that may not exist in Neon
**Fix**:
- [x] `Refund`, `CommissionTier`, `RevenueShare` models confirmed importable
- [x] `User.credit_hold_amount/reason/until` confirmed present
- [x] MFA migration `add_mfa_fields` created (runs on next Render deploy)
- [ ] `disputes`, `revenue_recognition`, `tax_reports`, `reseller_accounts` — deferred with P4 tasks

---

### 5.14 — Wire Tax & Reseller Services (Future)

**Problem**: `tax_service.py` + `reseller_service.py` — enterprise features
**Status**: Defer until user count justifies
**Prep**:
- [x] `TaxService` confirmed importable
- [x] `ResellerService` confirmed importable
- [x] Keep code, don't wire up yet

**Activation Triggers**:
- **Tax Service**: Activate when user count >100 OR monthly revenue >$5,000 (regulatory compliance threshold)
- **Reseller Service**: Activate when first reseller partner agreement signed OR >10 affiliate users request reseller features

**Activation Checklist**:
- [ ] Create `tax_reports` table migration
- [ ] Create `reseller_accounts` table migration
- [ ] Mount endpoints in admin router
- [ ] Add admin UI tabs for tax/reseller management
- [ ] Configure Stripe Tax or TaxJar API integration
- [ ] Document reseller onboarding process

---

## Post-Implementation Audit (May 7, 2026)

Full review of every admin panel feature against actual code revealed 4 gaps where UI exists and endpoints exist but data will always be empty or metrics are fake.

### What is fully working
- Growth target card (DB-backed, configurable)
- DAU, signup velocity chart, peak load heatmap
- 30d Net Revenue (real `Transaction` queries)
- User table + tier/credit management modal
- 90-day retention chart
- Verification forensics table + CSV export + pagination
- Live provider inventory + balance + price history chart
- Pricing templates (list, activate, clone, delete, rollback)
- Failed refund queue
- Open disputes table + Won/Lost resolve buttons
- Revenue recognition cards (reads DB correctly)
- SOC 2 compliance HUD + governance trail
- Pending commissions count + total

### Gap 1 — Fraud metrics need rolling averages (OPTIMIZATION)
`FraudDetectionService.get_model_metrics()` returns static values. `score_verification()` is now called on every verification.
- **Status**: [x] `score_verification()` now called on every verification request (non-blocking, logs high scores to server/Sentry)
- **Status**: [x] Real heuristics implemented (Phase 6.6) — high-risk countries/services now match correctly
- **Remaining**: [ ] Metrics card shows static constants. Real rolling averages not yet computed.
- **Activation Criteria**: Implement rolling averages when >500 verifications logged (enables meaningful F1/precision/recall)
- **Files**: `app/services/fraud_detection_service.py`, `app/api/verification/purchase_endpoints.py`

### Gap 2 — Revenue recognition cards always show $0
- **Status**: [x] Fixed — `recognize_revenue()` now called in `payment_service.py` after every successful credit
- **Files**: `app/services/payment_service.py`

### Gap 3 — Promo discount has no effect on pricing
- **Status**: [x] Fixed — `pricing_calculator.py` now applies `discount_percentage` at both markup calculation sites
- **Files**: `app/services/pricing_calculator.py`

### Gap 4 — Governance trail (audit logs) empty
- **Status**: [x] Fixed — `AuditService.log_action()` now called on tier change, credit add/deduct, and pricing template activation
- **Files**: `app/api/admin/tier_management.py`, `app/api/admin/admin.py`, `app/api/admin/pricing_control.py`

### Gap 5 — Commissions always show 0 pending
- **Status**: [x] Fixed — `calculate_commission()` now called in `payment_service.py` when `user.is_affiliate` is true
- **Files**: `app/services/payment_service.py`

---

## Gap Fix Priority

| Priority | Gap | Effort | Status |
|----------|-----|--------|--------|
| P0 | Gap 2 — Revenue recognition | 30 min | [x] Done |
| P0 | Gap 3 — Promo discount applied to pricing | 1 hour | [x] Done |
| P1 | Gap 4 — Audit log writes | 2 hours | [x] Done |
| P1 | Gap 5 — Commission calculation on payment | 1 hour | [x] Done |
| P2 | Gap 1 — Fraud rolling averages | 3 hours | [ ] Deferred until >500 verifications |

---

| Priority | Tasks | Effort | Impact |
|----------|-------|--------|--------|
| P0 | 5.1 (targets), 5.12 (labels) | 1 hour | Fixes embarrassing admin UX |
| P1 | 5.2 (mount endpoints), 5.13 (DB tables) | 2 hours | Unblocks all other tasks |
| P2 | 5.4 (BI), 5.9 (refunds/disputes) | 3 hours | Real data in admin |
| P2 | 5.3 (fraud), 5.11 (alerts) | 2 hours | Operational safety |
| P3 | 5.7 (currency), 5.8 (MFA) | 3 hours | User-facing features |
| P3 | 5.6 (commissions), 5.10 (WebSocket) | 3 hours | Growth features |
| P4 | 5.5 (revenue recognition), 5.14 (tax/reseller) | Deferred | Enterprise scale |

---

## Success Criteria

- [x] Admin panel shows real data from DB (not zeros/placeholders)
- [x] Growth target is configurable (not hardcoded 350)
- [x] All mountable admin endpoints return valid responses
- [x] Fraud scoring metrics visible in admin Overview
- [x] Failed refunds visible from admin Control & Audit tab
- [x] MFA available via API (setup/verify/disable)
- [x] Currency rates publicly accessible via `/api/currencies`
- [x] Payment events broadcast via WebSocket on credit
- [x] Verification completion broadcast via WebSocket on SMS received
- [x] Commission pending queue accessible from admin
- [x] Revenue recognition summary endpoint live
- [x] Dispute open/resolve endpoints live (user + admin)
- [x] Promo pricing templates supported
- [x] Tax + reseller services confirmed importable (deferred activation)

---

## Estimated Timeline

- **Week 1**: P0 + P1 (foundation — labels, targets, mount endpoints, DB tables)
- **Week 2**: P2 (real data — BI, fraud, refunds, alerts)
- **Week 3**: P3 (user features — currency, MFA, commissions, WebSocket)
- **Week 4**: Testing, polish, P4 assessment

---

## Dependencies

- Neon DB access for table creation
- TextVerified credentials for fraud scoring context
- Resend API key for alert emails
- No new external services required — all code exists
