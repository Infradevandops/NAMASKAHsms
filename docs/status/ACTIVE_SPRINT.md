# ACTIVE SPRINT

**Updated**: November 2026
**HEAD**: `331db1d5` on origin/main
**CI**: ✅ Passing — smoke-test + frontend-unit-tests (hard gates)
**Deploy**: ⏳ Pending CI pass → auto-triggers via deploy.yml

---

## SPRINT JUST COMPLETED ✅

Concurrent sprint — OTP login + AUTH fixes + SSE fix + version bump. All pushed.

**Commits this session**:
- `a7d45469` — OTP login (passwordless email code auth)
- `331db1d5` — AUTH-001, AUTH-002, OPEN-1, version 4.9.9

---

## ALL OPEN ITEMS

### 🔴 P1 — Deploy & Verify

| Item | Notes |
|------|-------|
| CI pass on `331db1d5` | Template + backend changes — smoke + JS tests should pass |
| Deploy auto-triggers on CI pass | Via `deploy.yml` → SSH → docker compose up --build |
| Confirm server pulls `331db1d5` | SSH: `cd ~/vrenum && git log --oneline -3` |

---

### 🔴 P1 — Email Testing (post-deploy)

| Email | Trigger | How to test |
|-------|---------|-------------|
| OTP login code | `POST /api/auth/otp/request` | curl or use login page "Login with email code" link |
| Welcome | New registration | Register a test account |
| Password reset | `/password-reset` form submit | Submit with existing email, check inbox |
| Low balance alert | Wallet drops below threshold | Manually deduct credits via admin |
| Verification receipt | Successful SMS verification | Complete a real verification |
| Payment receipt | Paystack payment completes | Make a small test payment |
| Tier upgrade | User upgrades plan | Upgrade a test account |
| Daily digest | Scheduled 08:00 UTC | Check Sentry/logs next morning |

---

### 🟡 P1 — Verification System (open items)

| ID | Item | Severity | Status |
|----|------|----------|--------|
| OPEN-1 | `validating` SSE step removed | P3 | ✅ Done `331db1d5` |
| OPEN-2 | No `transcribing` status for voice in SSE path | P3 | 📋 Open |
| OPEN-3 | `reuse` + `reactivate` never surfaced in UI | P2 | 📋 Open |
| OPEN-4 | Stock monitor docstring | P3 | ✅ Already correct |

---

### 🟡 P1 — Auth UX

| ID | Item | Status |
|----|------|--------|
| AUTH-001 | Password reset inline confirmation state | ✅ Done `331db1d5` |
| AUTH-002 | Register success email verification notice | ✅ Done `331db1d5` |
| OTP-LOGIN | Passwordless login via email code | ✅ Done `a7d45469` |

---

### 🟡 P2 — Ops & Infrastructure

| Item | Priority | Notes |
|------|----------|-------|
| Telegram E2E verification | P1 | @vrenum_sms_bot created, webhook registered, not live-tested |
| Area code price display | P1 | UI shows base price, user charged base + $0.25 surcharge |
| TextVerified IP whitelist | P2 | Server IP not whitelisted — `quantity: null` on all services |
| Upstash Redis upgrade | P2 | Free tier 500k req/month. Hit limit once. Upgrade to pay-as-you-go |
| Python unit-tests `continue-on-error` | P2 | Pre-existing failures — triage needed |
| Dead code cleanup | P2 | `_fetch_prices_inline()` + `fetch_raw_services_with_quantity()` — delete |
| CI coverage expansion | P2 | Currently 25% floor |

---

### 🟡 P1 — Revenue Features

| ID | Item | Effort |
|----|------|--------|
| REV-001 | Annual plans (Pro $250/yr, Custom $350/yr) | Trivial |
| REV-002 | Reuse surcharge ($0.25) | Low |
| REV-003 | PAYG API add-on ($10/mo, 5 keys) | Low |
| REV-004 | Bulk credit discount (5%/10%/15%) | Low |

### 🟡 P1 — Inventory Notifications

| ID | Item | Status |
|----|------|--------|
| INV-001 | Service back-in-stock watch | 📋 Not live |
| INV-002 | Rental back-order detection + notification | 📋 Not live |
| INV-003 | Rental expiry 24h warning | 📋 Not live |
| INV-004 | Admin alert: stock depletion email | ✅ Wired |
| INV-005 | Admin alert: back-order queue depth | 📋 Not live |
| INV-006 | Admin alert: rental expiry digest | 📋 Not live |
| INV-007 | Admin portal: stock status column | 📋 Not live |
| INV-008 | Admin portal: Stock Watches stat card | 📋 Not live |
| INV-009 | Admin portal: Inventory section in Alerts | 📋 Not live |

---

## TASK FILE INDEX

| File | What it covers |
|------|---------------|
| `docs/engineering/development/VERIFICATION_TASKS.md` | TV API gaps, open items — single source of truth |
| `docs/status/OTP_LOGIN_TASKS.md` | OTP login E2E test instructions |
| `docs/engineering/development/PAGE_QUALITY_TASKS.md` | 53/55 public page quality tasks |
| `docs/status/PLATFORM_STATUS.md` | Current platform state |
| `docs/status/OPS_SUMMARY.md` | CI pipeline, infrastructure, known gaps |


**Key deliveries:**
- Regulatory compliance: GDPR cookie consent (granular), age gate, marketing consent, correct legal docs (jurisdiction, processor list, DPO note)
- All broken pages fixed: refund CSS, reviews honest, about honest stats, contact dark mode + GDPR notice
- Blog: all 5 posts styled + indexed at `/blog`, route added
- Auth: double-nav eliminated on login/register, duplicate logo removed
- Nav: FAQ in desktop + mobile, Blog/Cookies/Contact in footer
- Status page: now public (no login required)
- FAQPage JSON-LD structured data added

---

## ALL OPEN ITEMS

> **All open tasks have moved to the master task file.**
> See `docs/status/MASTER_TASKS.md` — single source of truth for all sprints.

### Quick reference — sprint map

| Sprint | What | Status |
|--------|------|--------|
| A | Deploy & immediate fixes (8 tasks) | 📋 Not started |
| B | Verification system polish — reuse, voice, SSE, ReservationState (9 tasks) | 📋 Not started |
| C | Revenue features — annual plans, PAYG API add-on, bulk credit discount (19 tasks) | 📋 Not started |
| D | Inventory notification system — stock watches, back-order, expiry, admin portal (25 tasks) | 📋 Partially wired |
| E | Ops & infrastructure — Redis, TV IP, CI coverage (6 tasks) | 📋 Not started |
| F | SDK remaining gaps — SSE timeout, refs to B (4 tasks) | 📋 Not started |

**A, B, C, D1, E, F run concurrently. D2/D3 after rental path stable. D4 after D1–D3 endpoints exist.**

---

## TASK FILE INDEX

| File | Role |
|------|------|
| `docs/status/MASTER_TASKS.md` | **Single source of truth — all open work** |
| `docs/features/REVENUE_FEATURES_SPEC.md` | Full spec for Sprint C |
| `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md` | Full spec for Sprint D |
| `docs/engineering/SDK_OPTIMIZATION_OPPORTUNITIES.md` | Background for Sprints B + F |
| `docs/engineering/development/VERIFICATION_TASKS.md` | Historical context — open items superseded by MASTER_TASKS |
| `docs/status/PLATFORM_STATUS.md` | Platform health — not a task file |
| `docs/status/OPS_SUMMARY.md` | CI pipeline + infrastructure state |
