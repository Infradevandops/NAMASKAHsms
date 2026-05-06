# Phase 5.0 — Admin Intelligence & Growth Services Integration

**Version**: v4.5.0
**Status**: Planning
**Created**: May 6, 2026
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
- [ ] Make target configurable via admin UI (not hardcoded)
- [ ] Add "Set Target" button in admin Overview tab
- [ ] API: `POST /api/admin/intelligence/targets` to update target
- [ ] Reasonable default: 10 users for month 1, scale from there

**Files**: `app/services/target_tracking_service.py`, `static/js/admin/overview.js`, `templates/admin/dashboard.html`

---

### 5.2 — Mount Unmounted Admin Endpoints

**Problem**: 7 endpoint files exist but aren't in the router
**Fix**:
- [ ] Mount `alerts.py` → webhook alerting
- [ ] Mount `support.py` → support ticket system
- [ ] Mount `kyc.py` → KYC verification
- [ ] Mount `audit_unreceived.py` → unreceived verification audit
- [ ] Mount `analytics_monitoring.py` → real-time analytics
- [ ] Mount `disaster_recovery.py` → DR status/backup triggers
- [ ] Mount `dependencies.py` (if it has routes)

**File**: `app/api/admin/router.py`

---

### 5.3 — Wire Fraud Detection Service

**Problem**: `fraud_detection_service.py` (54 lines) exists but never called
**Integration**:
- [ ] Call `score_verification()` during verification creation flow
- [ ] Add fraud score column to forensics table in admin
- [ ] Block/flag verifications with score > threshold
- [ ] Show fraud alerts in admin "Control & Audit" tab

**Files**: `app/services/fraud_detection_service.py`, `app/services/textverified_service.py`

---

### 5.4 — Wire Business Intelligence Service

**Problem**: `business_intelligence.py` (94 lines) has revenue metrics but isn't called
**Integration**:
- [ ] Feed "30d Net Revenue" card from `get_revenue_metrics()`
- [ ] Add revenue breakdown chart to admin Overview
- [ ] Connect to existing `operational_intelligence_service.py` vitality endpoint

**Files**: `app/services/business_intelligence.py`, `app/api/admin/intelligence.py`

---

### 5.5 — Wire Revenue Recognition Service

**Problem**: `revenue_recognition_service.py` (379 lines) — full implementation, unused
**Integration**:
- [ ] Add "Revenue" sub-tab or card in Pricing Governance tab
- [ ] Show recognized vs deferred revenue
- [ ] Monthly revenue recognition report endpoint
- [ ] Ensure `revenue_recognition` DB table exists (migration if needed)

**Files**: `app/services/revenue_recognition_service.py`, `app/models/revenue_recognition.py`

---

### 5.6 — Wire Commission Engine & Affiliate

**Problem**: `commission_engine.py` (178 lines) — calculates affiliate payouts, unused
**Integration**:
- [ ] Connect to affiliate program page (`templates/affiliate_program.html`)
- [ ] Add commission tracking to admin panel
- [ ] Endpoint: `GET /api/admin/commissions/pending`
- [ ] Ensure `commission_tiers` and `revenue_shares` tables exist

**Files**: `app/services/commission_engine.py`, `app/models/commission.py`

---

### 5.7 — Wire Currency Service

**Problem**: `currency_service.py` (58 lines) — multi-currency support, unused
**Integration**:
- [ ] Connect to the currency selector in dashboard header
- [ ] Fetch live exchange rates (or use static rates)
- [ ] Store user currency preference (already in `UserPreference` model)
- [ ] Convert displayed amounts based on selected currency

**Files**: `app/services/currency_service.py`, `static/js/currency.js`

---

### 5.8 — Wire MFA Service

**Problem**: `mfa_service.py` (37 lines) — working 2FA with pyotp/qrcode, unused
**Integration**:
- [ ] Add "Two-Factor Authentication" section to user settings page
- [ ] Endpoints: `POST /api/user/mfa/enable`, `POST /api/user/mfa/verify`, `POST /api/user/mfa/disable`
- [ ] Show QR code for authenticator app setup
- [ ] Enforce MFA check on login if enabled

**Files**: `app/services/mfa_service.py`, `templates/settings.html`

---

### 5.9 — Wire Failed Refund & Dispute Services

**Problem**: `failed_refund_service.py` (223 lines) + `dispute_service.py` (226 lines) — unused
**Integration**:
- [ ] Add "Refund Queue" section to admin Control & Audit tab
- [ ] Show failed refunds with retry button
- [ ] Add dispute creation endpoint for users
- [ ] Admin dispute resolution UI

**Files**: `app/services/failed_refund_service.py`, `app/services/dispute_service.py`, `app/models/dispute.py`

---

### 5.10 — Wire Event Broadcaster (WebSocket)

**Problem**: `event_broadcaster.py` (282 lines) — real-time events, unused
**Integration**:
- [ ] Connect to admin dashboard for live updates (new signups, verifications)
- [ ] Push notifications to user dashboard (verification complete, payment received)
- [ ] WebSocket endpoint: `ws://host/ws/events`

**Files**: `app/services/event_broadcaster.py`, `static/js/admin/overview.js`

---

### 5.11 — Wire Alerting Service

**Problem**: `alerting_service.py` (85 lines) — triggers alerts, unused
**Integration**:
- [ ] Trigger alerts on: low provider balance, high error rate, fraud detection
- [ ] Show active alerts in admin header
- [ ] Connect to `admin/alerts.py` webhook endpoint
- [ ] Email/Slack notification on critical alerts

**Files**: `app/services/alerting_service.py`, `app/api/admin/alerts.py`

---

### 5.12 — Fix Admin Panel Labels & UX

**Problem**: Labels are aspirational ("Institutional", "Phase 6.0", "DAU (Institutional)")
**Fix**:
- [ ] Rename "Phase 6.0 Institutional Infrastructure" → "Admin Control Center"
- [ ] Rename "DAU (Institutional)" → "Daily Active Users"
- [ ] Rename "Institutional Overview" → "Overview"
- [ ] Make growth target card show realistic numbers
- [ ] Fix "Status: Behind" to show meaningful context

**Files**: `templates/admin/header.html`, `templates/admin/dashboard.html`

---

### 5.13 — Ensure DB Tables Exist

**Problem**: Some services reference models/tables that may not exist in Neon
**Fix**:
- [ ] Verify these tables exist in production DB:
  - `monthly_targets`
  - `daily_user_snapshots`
  - `audit_logs`
  - `disputes`
  - `revenue_recognition` (+ related)
  - `tax_reports` (+ related)
  - `commission_tiers`, `revenue_shares`, `payout_requests`
  - `reseller_accounts`
  - `refunds`
- [ ] Create Alembic migration for any missing tables
- [ ] Apply to Neon production

---

### 5.14 — Wire Tax & Reseller Services (Future)

**Problem**: `tax_service.py` (386 lines) + `reseller_service.py` (206 lines) — enterprise features
**Status**: Defer until user count justifies (>100 users)
**Prep**:
- [ ] Ensure models are importable
- [ ] Document activation criteria
- [ ] Keep code, don't wire up yet

---

## Priority Order

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

- [ ] Admin panel shows real data from DB (not zeros/placeholders)
- [ ] Growth target is configurable (not hardcoded 350)
- [ ] All mounted admin endpoints return valid responses
- [ ] Fraud scoring runs on every verification attempt
- [ ] Failed refunds visible and retryable from admin
- [ ] MFA available in user settings
- [ ] Currency conversion works with selector

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
