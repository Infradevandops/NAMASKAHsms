# ACTIVE SPRINT — VRENUM SMS

**Updated**: November 2026
**HEAD**: `5f3eb79a` on origin/main
**Handover doc**: `docs/status/HANDOVER_NOV2026.md` — read this first if picking up mid-session
**Authority**: This file is the single actionable task list. `MASTER_TASKS.md` is the historical record.
**Spec docs**: Sprint G → `docs/engineering/PROVIDER_RESILIENCE_AND_PLATFORM_STANDARDS.md` | Sprint H → `docs/engineering/development/PURCHASE_FLOW_UX_OVERHAUL.md`

---

## OVERALL STATUS

| Sprint | Scope | Done | Open code | Manual/blocked |
|--------|-------|------|-----------|----------------|
| A — Deploy & Fixes | Server deploy, email tests, Telegram E2E | 5/8 | 0 | 3 |
| B–F — Platform features | All 63 feature tasks | 61/63 | 1 | 6 |
| G — Provider Resilience | Timeout, orphan recon, circuit breaker, SDK contract | 0/6 | 6 | 0 |
| H — Purchase Flow UX | Loading modal, step 3, activity feed, webhook monitor | 0/6 | 6 | 0 |
| **Total** | | **66/83** | **13** | **9** |

⚠️ G-001/002/003/004/006 were written to working tree but session was cancelled before commit.
See `HANDOVER_NOV2026.md` → "Next Steps" for exact commit commands.

---

## OPEN CODE TASKS

### P0 — Ship before next deploy (stops money leak)

| ID | Task | File | Effort |
|----|------|------|--------|
| G-001 | `asyncio.wait_for(timeout=12s)` on TV purchase call in SSE stream — yield `purchasing_delayed` on timeout, write Redis pending key | `app/api/verification/purchase_endpoints.py` | 30 min |
| G-002 | SSE keepalive ping every 5s + nginx `proxy_read_timeout 30s` (server config) | `purchase_endpoints.py` + server | 30 min |

---

### P1 — Sprint G: Provider Resilience

| ID | Task | File | Effort |
|----|------|------|--------|
| G-003 | Orphan reconciliation worker — reads `purchase_pending:*` Redis keys, queries provider recent purchases, heals missing Verification rows, pushes WS `verification_ready` | `app/workers/orphan_reconciliation.py` (new), `lifespan.py` | 2h |
| G-004 | Provider contract: add `PURCHASE_TIMEOUT_S=12`, `CANCEL_TIMEOUT_S=5`, `STATUS_TIMEOUT_S=8`, `MAX_PURCHASE_ATTEMPTS=1` to `SMSProvider` base class. Wrap `purchase_number()` in all 4 adapters with `asyncio.wait_for` | `app/services/providers/base_provider.py`, all adapters | 1h |
| G-006 | Per-provider circuit breaker — 5 failures/60s → OPEN, 30s recovery, HALF-OPEN 1 test call. `ProviderRouter.get_provider()` skips OPEN providers | `app/services/providers/circuit_breaker.py` (new) | 2h |

---

### P1 — Sprint H: Purchase Flow UX

| ID | Task | File | Effort |
|----|------|------|--------|
| H-001 | Purchase loading modal: dark card, arc-orbiting-icon spinner, exact TV 11-message sequence (4 phases), service title. Replaces current white card + separate spinner | `templates/verify_modern.html`, `verification-flow.js`, `verification-design-system.css` | 2.5h |
| H-002 | Step 3: carrier icon from area code, MM:SS countdown from `ends_at`, full raw SMS text box, reuse button with cost + countdown ("Use again for $0.25 (0:47)"), info banner | `templates/verify_modern.html`, `verification-flow.js` | 2h |
| H-003 | Step 3 scanning: replace radar pulse with scrolling activity feed log (4 entries max, fades in/out, rotates from 10-message pool every 3s) | `templates/verify_modern.html`, `sms-polling-ui.css` | 1h |
| H-004 | `purchasing_delayed` SSE state: hide cancel, switch to patience messages, pulse progress bar, "do not close tab" warning | `verification-flow.js` | 30 min |
| H-006 | TV webhook auto-re-enable monitor (30 min loop) — TV auto-disables webhook after deploy downtime; monitor re-enables it | `app/workers/webhook_health_monitor.py` (new), `lifespan.py` | 1h |

---

### P2 — Remaining

| ID | Task | File | Effort |
|----|------|------|--------|
| G-005 | Vrenum public API contract doc — define provider-agnostic verification/rental objects, list what is hidden from public API, define SDK method surface + retry policy | `docs/engineering/VRENUM_API_CONTRACT.md` (new) | 2h (doc only) |
| H-005 | Step 0 method picker: add SMS+Voice Combo card (3-column grid, +$0.50 badge) | `templates/verify_modern.html` | 20 min |
| E-004 | Triage CI unit-test failures — download `unit-test-output-*` artifact from GitHub Actions, identify failing tests | CI artifacts | 1h |

---

## MANUAL / EXTERNAL ACTIONS

| ID | Action | Where |
|----|--------|-------|
| A-001 | Deploy HEAD `d8f29f53` to server — `git pull && alembic upgrade head && ./restart.sh` | SSH `~/vrenum` |
| A-002 | Test 8 transactional emails on live server | Resend dashboard + inbox |
| A-005 | Telegram E2E — connect @vrenum_sms_bot, send verification, confirm SMS forwarded | Live server |
| C-001 | Create Paystack annual plan codes (`PLAN_PRO_ANNUAL` ₦412,500/yr, `PLAN_CUSTOM_ANNUAL` ₦577,500/yr) | Paystack dashboard |
| C-010 | Create Paystack add-on plan (`PLAN_PAYG_API_ADDON` ₦16,500/mo) | Paystack dashboard |
| E-001 | Upgrade Upstash Redis to pay-as-you-go | Upstash dashboard |
| E-002 | TextVerified IP whitelist — submit server IP | TV support ticket |
| G-002b | Set nginx `proxy_read_timeout 30s` + `proxy_send_timeout 30s` on server | SSH nginx config |
| H-006b | Verify TV webhook is still enabled after next deploy | TV API config page |

---

## EXECUTION ORDER

```
G-001 + G-002  →  deploy (A-001 + G-002b)  →  H-001 + H-002 + H-003 + H-006
(stop the leak)   (nginx + alembic)            (core UX — independent of G)

→  G-003 + G-004 + G-006  →  H-004  →  G-005 + H-005 + E-004
   (resilience layer)         (needs G-001)   (polish + docs + CI triage)
```

---

## SPEC REFERENCE

| Sprint | Full spec |
|--------|-----------|
| G — Provider Resilience | `docs/engineering/PROVIDER_RESILIENCE_AND_PLATFORM_STANDARDS.md` |
| H — Purchase Flow UX | `docs/engineering/development/PURCHASE_FLOW_UX_OVERHAUL.md` |
| Historical A–F | `docs/status/MASTER_TASKS.md` |
