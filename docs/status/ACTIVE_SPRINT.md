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
| G — Provider Resilience | Timeout, orphan recon, circuit breaker | 0/6 | 6 | 0 |
| H — Purchase Flow UX | Loading modal, step 3, activity feed, webhook monitor | 0/6 | 6 | 0 |
| **Total** | | **66/83** | **13** | **9** |

---

## OPEN CODE TASKS

### P0 — Ship before next deploy (stops money leak)

| ID | Task | File | Effort |
|----|------|------|--------|
| G-001 | `asyncio.wait_for(timeout=12s)` on TV purchase call in SSE stream — yield `purchasing_delayed` on timeout, write Redis `purchase_pending:*` key | `app/api/verification/purchase_endpoints.py` | 30 min |
| G-002 | SSE keepalive ping every 5s (prevents nginx dropping connection) | `purchase_endpoints.py` | 15 min |

### P1 — Sprint G: Provider Resilience

| ID | Task | File | Effort |
|----|------|------|--------|
| G-003 | Orphan reconciliation worker — reads `purchase_pending:*` Redis keys, queries provider recent purchases, heals missing Verification rows, pushes WS `verification_ready` | `app/workers/orphan_reconciliation.py` (new) + `lifespan.py` | 2h |
| G-004 | Provider contract: `PURCHASE_TIMEOUT_S=12`, `CANCEL_TIMEOUT_S=5`, `STATUS_TIMEOUT_S=8`, `MAX_PURCHASE_ATTEMPTS=1` on `SMSProvider` base class. Wrap `purchase_number()` in all 4 adapters | `app/services/providers/base_provider.py` + all adapters | 1h |
| G-006 | Per-provider circuit breaker — 5 failures/60s → OPEN, 30s recovery. `ProviderRouter.get_provider()` skips OPEN providers | `app/services/providers/circuit_breaker.py` (new) + `provider_router.py` | 2h |

### P1 — Sprint H: Purchase Flow UX

| ID | Task | File | Effort |
|----|------|------|--------|
| H-001 | Purchase loading modal: dark card, arc-orbiting-icon spinner, exact TV 11-message sequence (4 phases) | `templates/verify_modern.html`, `verification-flow.js`, `verification-design-system.css` | 2.5h |
| H-002 | Step 3: carrier icon from area code, MM:SS countdown from `ends_at`, full raw SMS text box, reuse button with cost + countdown | `templates/verify_modern.html`, `verification-flow.js` | 2h |
| H-003 | Step 3 scanning: replace radar pulse with scrolling activity feed log (10-message pool, rotates every 3s, max 4 visible) | `templates/verify_modern.html`, `sms-polling-ui.css` | 1h |
| H-004 | `purchasing_delayed` SSE state: hide cancel, switch to patience messages, pulse progress bar, "do not close tab" warning | `verification-flow.js` | 30 min |
| H-006 | TV webhook auto-re-enable monitor (30 min loop) — TV auto-disables webhook after deploy downtime | `app/workers/webhook_health_monitor.py` (new) + `lifespan.py` | 1h |

### P2 — Polish

| ID | Task | File | Effort |
|----|------|------|--------|
| G-005 | Vrenum public API contract doc — provider-agnostic verification/rental objects, SDK surface | `docs/engineering/VRENUM_API_CONTRACT.md` (new) | 2h doc |
| H-005 | Step 0 method picker: add SMS+Voice Combo card (3-column grid, +$0.50 badge) | `templates/verify_modern.html` | 20 min |
| E-004 | Triage CI unit-test failures — download `unit-test-output-*` artifact from GitHub Actions | CI artifacts | 1h |

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
| G-002b | Set nginx `proxy_read_timeout 30s` + `proxy_send_timeout 30s` | SSH nginx config |
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
