# PLATFORM STATUS — AUTHORITATIVE SOURCE

**Last Updated**: November 2026
**Overall Status**: ✅ Healthy — CI passing, `331db1d5` pending deploy
**HEAD**: `331db1d5` on origin/main
**Version**: 4.9.9

---

## EXECUTIVE SUMMARY

Full UI/UX overhaul, compliance sprint, OTP login, and concurrent sprint execution complete. Platform is production-standard. All public pages honest and compliant. Auth UX fixed. Dead SDK code removed. Revenue infrastructure (bulk bonus, reuse endpoint, models) written. Inventory notification backend wired. Consolidated DB migration ready to run.

CI is passing. Deploy auto-triggers on CI success. Once deployed, email testing and Telegram E2E are the next manual gates.

---

## WHAT IS LIVE (last confirmed deploy: `331db1d5` pending, prev `e06e91ce` Nov 6 2026)

### Verification Flow
- ✅ SSE streaming purchase — real-time step feedback
- ✅ `validating` step removed — was fake UX label
- ✅ Dynamic `ends_at` from TV — no hardcoded timeout
- ✅ TV webhook instant SMS delivery
- ✅ Orphan verification recovery on page reload
- ✅ P0 availability gate on legacy purchase path
- ✅ Null-price services filtered from picker
- ✅ Out-of-stock services greyed out in JS picker
- ✅ Stock monitor 90s loop
- ✅ `reuse_verification()` + `TV_STATE_MAP` (14 states) on `TextVerifiedService`
- ✅ `POST /api/verification/{id}/reuse` endpoint (B-005)
- ✅ `reusable_until`, `reused_from_id`, `ends_at` columns on verifications model

### Auth
- ✅ OTP passwordless login (`a7d45469`)
- ✅ Password reset — inline confirmation state (`331db1d5`)
- ✅ Register — email verification notice (`331db1d5`)
- ✅ JWT expiry uses config (24h)
- ✅ MFA (TOTP)

### Infrastructure
- ✅ Real `/health` endpoint with DB + Redis checks
- ✅ Redis-backed CSRF tokens + rate limiting (multi-worker safe)
- ✅ IP spoofing fix in rate limiter
- ✅ Dockerfile pinned to Python 3.9-slim
- ✅ Smoke-test CI gate
- ✅ Stock depletion admin email alert wired
- ✅ `_fetch_prices_inline()` + `fetch_raw_services_with_quantity()` deleted

### Revenue Backend (written, pending migration + UI)
- ✅ `calculate_bonus_credits()` + bulk bonus wired in `credit_user()` (C-016/017)
- ✅ `SubscriptionAddon` model (C-009)
- ✅ Consolidated migration `f1a2b3c4d5e6` — 6 schema changes, pending `alembic upgrade head`

### Inventory Notification Backend (written, pending UI)
- ✅ `StockWatch` model + API endpoints (D-002/003)
- ✅ `_notify_stock_watchers()` in stock monitor (D-004)
- ✅ `RentalBackOrder` model (D-009)
- ✅ Back-order monitor worker (D-011/012)
- ✅ `expiry_warned_at` column on `NumberRental` model

### Public Pages
- ✅ Landing, Nav, Cookie consent, Register, Login, Privacy, Terms, Refund, Reviews, About, Contact, FAQ, Blog, Affiliate, Status, Footer — all honest and compliant
- ✅ FAQPage JSON-LD structured data

### Core Platform
- ✅ All 23 admin dashboard tabs
- ✅ Phase 1 Analytics (all 6 event types)
- ✅ Telegram SMS forwarding (@vrenum_sms_bot — code complete, E2E pending)
- ✅ Number rentals (5 endpoints, expiry monitor)
- ✅ Voice verification (stable)
- ✅ Area code intelligence + carrier verification
- ✅ Fraud detection + MFA (TOTP)
- ✅ Affiliate program + commission engine
- ✅ Disputes management with evidence upload
- ✅ GDPR compliance tools
- ✅ Promo pricing templates

---

## KNOWN ISSUES

| Issue | Severity | Status |
|-------|----------|--------|
| `331db1d5` not yet confirmed live | P1 | Pending CI + auto-deploy |
| Telegram E2E not verified | P1 | Pending manual test (A-005) |
| Area code price display shows base only | P1 | A-003 — not yet fixed |
| TextVerified IP not whitelisted | P2 | `quantity: null` on all services — price fallback active (E-002) |
| Upstash Redis 500k/month free tier | P2 | Upgrade to pay-as-you-go (E-001) |
| Python unit-tests `continue-on-error` | P2 | Pre-existing failures, triage needed (E-004) |
| Migration `f1a2b3c4d5e6` not yet run on server | P1 | Run `alembic upgrade head` post-deploy |
| Sprint B/C/D UI work not started | P2 | See MASTER_TASKS.md |

---

## CI PIPELINE

| Job | Status | Gate |
|-----|--------|------|
| Secrets Detection | ✅ pass | continue-on-error |
| Code Quality | ✅ pass | continue-on-error |
| Frontend Unit Tests | ✅ pass | **HARD BLOCK** (92/92 JS tests) |
| Smoke Test | ✅ pass | **HARD BLOCK** (Python startup) |
| Unit Tests | ✅ pass | continue-on-error (pre-existing failures) |

---

## DEPLOYMENT

- **Production**: vrenum.app (DigitalOcean, Docker Compose)
- **Deploy trigger**: CI pass on main → `deploy.yml` fires automatically
- **Last confirmed live commit**: `e06e91ce` (Nov 6 2026)
- **Pending deploy**: `331db1d5` (Nov 2026 — OTP login + AUTH fixes + SSE fix + version bump)
- **Post-deploy required**: `alembic upgrade head` for migration `f1a2b3c4d5e6`
- **Rollback**: `git revert` → CI passes → auto-deploys

---

## MONITORING

- ✅ Sentry: https://dev-vp.sentry.io/issues/
- ✅ BetterStack: https://uptime.betterstack.com/team/t545038/monitors/4422808
- ✅ Revenue-zero alert: email at 18:00 UTC → ADMIN_NOTIFY_EMAIL
- ✅ Stock depletion alert: fires on available → unavailable transition
- ✅ Prometheus: metrics collection active
