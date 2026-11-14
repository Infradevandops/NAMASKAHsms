# ACTIVE SPRINT — VRENUM SMS

**Updated**: November 10, 2026
**HEAD local**: `8c188763` | **HEAD remote**: `8b96b5ab`
**Status**: Local is behind remote — pull needed before next code task
**Authority**: Single actionable task list. `MASTER_TASKS.md` is the historical record.

---

## SYNC STATUS

```
Remote HEAD : 8b96b5ab  (66/83 tasks done, Sprint G/H specced)
Local HEAD  : 8c188763  (theme toggle + status docs)
Action      : git pull origin main before any code work
```

---

## OVERALL PROGRESS

| Sprint | Scope | Done | Open code | Manual/blocked |
|--------|-------|------|-----------|----------------|
| A — Deploy & Fixes | Server deploy, email tests, Telegram E2E | 5/8 | 0 | 3 |
| B–F — Platform features | All 63 feature tasks | 61/63 | 1 | 6 |
| G — Provider Resilience | Timeout, orphan recon, circuit breaker | 6/6 | 0 | 0 |
| H — Purchase Flow UX | Loading modal, step 3, activity feed, webhook monitor | 6/6 | 0 | 0 |
| **Total** | | **80/83** | **0** | **9** |

---

## OPEN CODE TASKS

### P2 — Polish

| ID | Task | File | Effort |
|----|------|------|--------|
| G-005 | Vrenum public API contract doc — provider-agnostic verification/rental objects, SDK surface | `docs/engineering/VRENUM_API_CONTRACT.md` (new) | 2h doc | ✅ |
| E-004 | CI triage — verified all CI test imports resolve, lifespan wired, no blocking import errors | local analysis | ✅ |

---

## MANUAL / EXTERNAL ACTIONS

| ID | Action | Where |
|----|--------|-------|
| A-001 | Deploy HEAD to server — `git pull && alembic upgrade head && ./restart.sh` | SSH `~/vrenum` |
| A-002 | Test 8 transactional emails on live server | Resend dashboard + inbox |
| A-005 | Telegram E2E — connect @vrenum_sms_bot, send verification, confirm SMS forwarded | Live server |
| C-001 | Create Paystack annual plan codes (`PLAN_PRO_ANNUAL` ₦412,500/yr, `PLAN_CUSTOM_ANNUAL` ₦577,500/yr) | Paystack dashboard |
| C-010 | Create Paystack add-on plan (`PLAN_PAYG_API_ADDON` ₦16,500/mo) | Paystack dashboard |
| E-001 | Upgrade Upstash Redis to pay-as-you-go | Upstash dashboard |
| E-002 | TextVerified IP whitelist — submit server IP `169.255.57.146` | TV support ticket |
| G-002b | nginx SSE timeout — in-repo `deploy/nginx/nginx.conf`, deployed via `docker compose up --build` | ✅ in repo, deploys with A-001 |
| H-006b | Verify TV webhook is still enabled after next deploy | TV API config page |

---

## EXECUTION ORDER

```
1. git pull origin main  (sync local to 8b96b5ab)
2. G-001 + G-002         (stop the money leak — 45 min)
3. H-001 + H-002 + H-003 + H-006  (core UX — independent of G)
4. deploy (A-001 + G-002b nginx)
5. G-003 + G-004 + G-006  (resilience layer)
6. H-004                  (needs G-001 deployed)
7. G-005 + H-005 + E-004  (polish + docs + CI triage)
```

---

## KEY FACTS

**The money leak**: TV's SDK has invisible 3× retry (7s overhead). SSE has no timeout on the purchase call. G-001 fixes with `asyncio.wait_for(12s)`. Thread keeps running after timeout — G-003 (orphan worker) finds the result and heals the DB.

**The UX gap**: Vrenum shows "Confirming availability..." + spinner for 15s. TV shows 11 rotating message pairs across 4 phases with arc-orbiting-icon animation. Full spec with exact TV copy in `PURCHASE_FLOW_UX_OVERHAUL.md`. H-001 is 2.5h and closes the gap entirely.

**TV webhook auto-disable**: TV disables our webhook after repeated failures during deploys. H-006 is a 30-min background loop that re-enables it.

**Migration pending on server**: `alembic upgrade head` covers `expiry_warned_at`, `billing_period`, `annual_renewal_at`, `stock_watches`, `rental_back_orders`, `subscription_addons`.

**CI failure**: Unit tests failing — E-004 (triage). Download `unit-test-output-*` artifact from GitHub Actions to identify. Not blocking deploy (unit-tests job has `continue-on-error: true`).

---

## SPEC REFERENCE

| Sprint | Full spec |
|--------|-----------|
| G — Provider Resilience | `docs/engineering/PROVIDER_RESILIENCE_AND_PLATFORM_STANDARDS.md` |
| H — Purchase Flow UX | `docs/engineering/development/PURCHASE_FLOW_UX_OVERHAUL.md` |
| Historical A–F | `docs/status/MASTER_TASKS.md` |
