# PLATFORM STATUS — AUTHORITATIVE SOURCE

**Last Updated**: November 7, 2026
**Overall Status**: ✅ Production Ready — Running on secondary IP (TV rate limited)
**CI Status**: ✅ Deployed @ `f1975971`

---

## EXECUTIVE SUMMARY

Vrenum SMS is production-ready. A dense 24-hour sprint shipped 15 commits covering
verification flow hardening, TV SDK correctness fixes, area code improvements, and
infrastructure upgrades. 13 of 15 commits are live. 2 commits (`3f805f8a`, `ee895ce8`)
are pending deploy — CI is running on `ee895ce8` which fixes 2 broken reservation tests
introduced by the SDK correctness fixes. Deploy fires automatically on CI green.

No version bump until CI is confirmed green and the pending deploy fires.

---

## WHAT IS LIVE

### Verification Flow
- ✅ SSE streaming purchase — real-time step feedback, cancel before charge commits
- ✅ Dynamic `ends_at` from TV — no hardcoded 2-min timeout
- ✅ TV webhook instant SMS delivery — eliminates polling wait
- ✅ Orphan verification recovery on page reload
- ✅ "Still working..." message after 10s on purchasing step
- ✅ P0 availability gate on legacy purchase path (fail fast <1s vs 5-30s)
- ✅ Null-price services filtered from picker at API layer
- ✅ Out-of-stock services greyed out and unclickable in JS picker
- ✅ Stock monitor 90s loop — cache always warm before TTL expires

### Infrastructure
- ✅ Real `/health` endpoint with DB + Redis checks
- ✅ Deploy hard-gated on CI pass — no more broken deploys
- ✅ demandBadge JS broken ternary fixed

### Notifications
- ✅ 405 fix on /api/notifications/categories (double-prefix router bug)
- ✅ Duplicate "Still Waiting" notifications eliminated (Redis distributed lock)
- ✅ Dark theme notification dropdown CSS hex fallbacks

### CI Pipeline
- ✅ 24-file unit test gate
- ✅ Coverage floor 25%
- ✅ Frontend JS tests blocking (92/92 passing)
- ✅ Secrets scan + code quality (black + isort + flake8) blocking
- ✅ Integration + E2E non-blocking (continue-on-error)

---

## KNOWN ISSUES

- **`GET /health` returns degraded** — false alarm. `main_routes.py` checks
  `TEXTVERIFIED_USERNAME` but server has `TEXTVERIFIED_EMAIL`. Fix committed, pending deploy.
- **`quantity: null` on all services** — TV rate limiting on secondary IP blocks
  `fetch_raw_services_with_quantity()`. Availability still works (price-based fallback).
  Not blocking purchases.
- **Disk 80%** — 61/76GB. Monitor; clean docker layers if hits 85%.
- **Deploy workflow health gate failing** — caused by the `tv_configured` bug above.
  Every deploy since health check was added exits with error even though app is healthy.

---

## FULL FEATURE INVENTORY

### Core Platform
- ✅ All 23 admin dashboard tabs (100% complete)
- ✅ Phase 1 Analytics (all 6 event types: signup, login, verification, payment, tier change)
- ✅ Telegram SMS forwarding (@vrenum_sms_bot — code complete, pending E2E)
- ✅ TV webhook — instant SMS delivery, registered in TV dashboard
- ✅ SSE streaming purchase — real-time progress, pre-charge cancel button
- ✅ Dynamic verification window from TV ends_at
- ✅ Orphaned verification recovery
- ✅ Number rentals (5 endpoints, expiry monitor)
- ✅ Voice verification (stable, audio player)
- ✅ Area code intelligence + carrier verification
- ✅ Fraud detection + MFA (TOTP)

### Notifications & Comms
- ✅ Notification center 405 fix
- ✅ Duplicate notification prevention (Redis lock)
- ✅ Dark theme notification dropdown
- ✅ All transactional emails CAN-SPAM compliant
- ✅ Revenue-zero alert (18:00 UTC daily)
- ✅ Daily + weekly digest email scheduler

### Business
- ✅ Affiliate program + commission engine
- ✅ Disputes management with evidence upload
- ✅ GDPR compliance tools
- ✅ Promo pricing templates
- ✅ Crypto approval → revenue recognition

### Infrastructure
- ✅ Real-time WebSocket events
- ✅ PWA + onboarding tour
- ✅ SEO (40 URLs, GA4, blog)
- ✅ JS test suite (92/92 passing, 13 suites)
- ✅ Mobile responsiveness (320px–768px)
- ✅ CI pipeline: 4-stage blocking gate

---

## BACKGROUND SERVICES (10 active after pending deploy)

| Service | Interval | Status |
|---------|----------|--------|
| SMS polling | Adaptive 5–10s | ✅ Active |
| TV webhook receiver | On-demand | ✅ Active |
| Refund policy enforcer | 5 min | ✅ Active |
| Health audit loop | 4 hours | ✅ Active |
| Daily growth snapshot | 24 hours | ✅ Active |
| Rental expiry monitor | 15 min | ✅ Active |
| Abandoned payment cleanup | 1 hour | ✅ Active |
| Revenue-zero monitor | Daily 18:00 UTC | ✅ Active |
| Digest scheduler | Daily 08:00 UTC | ✅ Active |
| Stock monitor | 90s | ✅ Active |
| Area code cache refresh | 23h | ⏳ Pending deploy |

---

## OPEN TASKS

| Task | Priority | Status |
|------|----------|--------|
| Confirm CI green on ee895ce8 | P0 | ⏳ Running |
| Verify TV pricing URL from VPS | P1 | ⏳ Needs VPS test |
| Telegram E2E live test | P1 | ⏳ Pending manual test |
| Add test_textverified_service.py to CI gate | P1 | 📋 Ready |
| CI coverage push 25% → 60% | P2 | 📋 Planned |
| Phase 2 Analytics (cohort, churn, revenue charts) | P2 | 📋 Planned |
| smsAndVoiceCombo capability | P3 | 📋 Planned |
| Reuse/Reactivate UI surface | P3 | 📋 Planned |
| Multi-region deployment | Low | 📋 Q3 2026 |

---

## ENGINEERING DOCS UPDATED THIS SPRINT

| Doc | What it covers |
|-----|---------------|
| `docs/engineering/TV_API_REAL_FLOW.md` | Full SDK source truth, all 12 files read, rental breakage, corrections |
| `docs/engineering/TV_API_FLOW_GAP_ASSESSMENT.md` | Gap analysis vs TV API, implementation status |
| `docs/engineering/PLATFORM_VERIFICATION_RENTAL_FLOW_STANDARD.md` | Provider-agnostic canonical flow |
| `docs/engineering/AREA_CODE_SELECTOR_FLOW.md` | Area code data flow from TV to UI, gaps, fixes |
| `docs/engineering/TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md` | Stock accuracy gaps, P0 fixes |

---

## MONITORING

- ✅ Sentry: https://dev-vp.sentry.io/issues/
- ✅ BetterStack: https://uptime.betterstack.com/team/t545038/monitors/4422808
- ✅ Revenue-zero: Email alert at 18:00 UTC → ADMIN_NOTIFY_EMAIL
- ✅ Prometheus: Metrics collection active

---

## DEPLOYMENT

- **Production**: vrenum.app (DigitalOcean, Docker Compose)
- **Deploy trigger**: CI pass on main → deploy.yml fires automatically
- **Rollback**: `git revert` to previous commit, CI passes, auto-deploys
- **Downtime**: 0 minutes (hot reload via docker compose up --build)
- **Last confirmed live commit**: `f1975971`
- **Pending deploy**: health check fix (tv_configured env var bug — `main_routes.py`)
