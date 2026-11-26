# ACTIVE SPRINT — VRENUM SMS

**Updated**: November 25, 2026
**HEAD**: `8cd7f78d` (local + remote in sync)
**Server HEAD**: `f791daf0` (1 commit behind — docs-only commit, no deploy needed)
**Authority**: Single actionable task list. `MASTER_TASKS.md` is historical record.

---

## CURRENT BLOCKERS — Fix These First

### FK-001 — Purchase FK violation (UNVERIFIED FIX)
**Status**: Fix deployed (`f791daf0`) but no successful purchase confirmed since fix.
**Fix**: `balance_service.py` — `db.flush([balance_tx, transaction])` then `sa_text()` raw UPDATE for FK.
**Verify**: Make a real purchase → check logs for `Ledger Synced` with no `ForeignKeyViolation`.
```bash
cd /root/vrenum && docker compose logs app -f 2>&1 | grep -E "ForeignKey|Ledger Synced|balance_service"
```

---

## SPRINT K — UNMERGED FIXES (from Copilot static review, Nov 25)

**Source**: `docs/engineering/VERIFICATION_FLOW_HANDOVER_NOV2026.md`
**State**: Fixes were validated locally (27 tests passing) but **never committed**. Must be re-applied.

| ID | Priority | Issue | File(s) |
|----|----------|-------|---------|
| K-001 | P0 | Orphan timeout writes Unix int — reconciliation worker only accepts ISO, deletes key on parse failure → orphan purchases lost | `purchase_endpoints.py` (SSE stream timeout handler) |
| K-002 | P0 | TV webhook completion skips shared completion routine — misses receipt flags, `sms_received` notification, downstream completion behavior | `app/api/verification/tv_webhook.py` |
| K-003 | P0 | Orphan worker emits `purchase_healed` WS event but UI has no resume callback — user stays stuck on purchase-loading screen | `static/js/verification-flow.js` |
| K-004 | P1 | UI local expiry says "not charged" and navigates away before server confirms terminal state | `static/js/verification-flow.js` |
| K-005 | P1 | `auto_refund_service` doesn't handle `expired` status — only `failed` | `app/services/auto_refund_service.py` |
| K-006 | P1 | Completion latency arithmetic breaks on naive/aware datetime mismatch | `app/services/sms_polling_service.py` |
| K-007 | P1 | SMS OTP codes written into telemetry/log data (security) | `app/services/sms_polling_service.py` or `purchase_intelligence.py` |
| K-008 | P2 | `PurchaseIntelligenceService` telemetry is fire-and-forget unawaited coroutine — silently dropped | `app/services/purchase_intelligence.py` |

---

## SPRINT J — VERIFICATION FLOW UI (partially done)

| ID | Priority | Issue | Status |
|----|----------|-------|--------|
| J-001 | P0 | Step 0+1 stacking bug — both shown simultaneously | ✅ Fixed `92812341` |
| J-009 | P1 | Orphan recovery hijacked Step 0 | ✅ Fixed `3ddcf4d1` |
| J-010 | P0 | Duplicate service selector — inline form + modal do same job | 🔴 Open — spec in `docs/status/VERIFY_FLOW_REDESIGN.md` |
| J-004 | P1 | Step 1 Back → should go to Step 0, not `/dashboard` | ✅ Fixed (resetFlow) |
| J-005 | P1 | Step 2 Back → verify goes to Step 1 correctly | ✅ Fixed |
| J-006 | P1 | Voice page — assess for same stacking bug | 📋 Not assessed |
| J-007 | P2 | Cloudflare cache bypass rule | ✅ Done |

---

## SPRINT I — NOTIFICATION & WEBSOCKET HARDENING (partially done)

| ID | Priority | Issue | Status |
|----|----------|-------|--------|
| I-001 | P0 | `on_sms_received` not awaited in `_complete_verification()` — WS broadcast silently no-ops | 🔴 Open |
| I-002 | P0 | TV webhook pushes `sms_received` before verifying debit committed | 🔴 Open (overlaps K-002) |
| I-003 | P0 | `mark-all-read` URL mismatch — JS calls wrong endpoint | 🔴 Open |
| I-004 | P1 | `asyncio.create_task()` in sync `_broadcast_notification()` — silent drop from workers | 🔴 Open |
| I-005 | P1 | `purchasing_delayed` has no WS event — orphan heal gives no real-time signal | 🔴 Open (overlaps K-003) |
| I-006 | P1 | Refund notification exposes internal reason codes to users | 🔴 Open |
| I-007 | P2 | `get_unread_count` defined twice in `notification_service.py` | 🔴 Open |
| I-008 | P2 | `_channels` dict lazy-init — potential AttributeError | 🔴 Open |
| I-009 | P2 | `cleanup_old_notifications()` exists but never called | 🔴 Open |
| I-010 | P3 | `datetime.utcnow()` (naive) in `telegram_service.py` | 🔴 Open |

---

## BACKGROUND WORKER ERRORS (non-critical, every restart)

| Error | Fix | Priority |
|---|---|---|
| `column number_rentals.expiry_warned_at does not exist` | Alembic migration | P2 |
| `cannot import name 'AsyncSessionLocal'` in back_order_monitor | Fix import | P2 |
| `invalid username-password pair` — orphan reconciliation Redis | Check Upstash creds in env | P2 |
| `User has no attribute 'annual_renewal_at'` | Add column or remove loop | P3 |

---

## PROVIDER / ROUTING GAPS (from Copilot review)

| ID | Priority | Issue |
|----|----------|-------|
| PR-001 | P1 | TV availability/price gate runs BEFORE provider router — blocks non-TV providers for countries TV doesn't cover |
| PR-002 | P1 | US healthy-shortcut in router doesn't check adapter is enabled or supports capability |
| PR-003 | P2 | Voice page uses legacy JSON purchase, fixed 300s timer, HTTP polling — not on SSE/WS lifecycle |
| PR-004 | P2 | `sms_and_voice` accepted and priced but combined lifecycle not defined or tested |
| PR-005 | P2 | WebSocket manager is in-process memory — multi-worker deployments lose pushes |
| PR-006 | P2 | `expired` vs `failed` terminal state inconsistency across poller, refund service, notifications, UI |

---

## MANUAL / EXTERNAL ACTIONS

| ID | Priority | Action |
|----|----------|--------|
| A-005 | P1 | Telegram E2E — connect @vrenum_sms_bot, trigger verification, confirm SMS forwarded |
| E-001 | P2 | Upgrade Upstash Redis to pay-as-you-go |
| E-002 | P2 | TextVerified IP whitelist — submit server IP `169.255.57.146` |
| C-001 | P2 | Create Paystack annual plan codes (`PLAN_PRO_ANNUAL`, `PLAN_CUSTOM_ANNUAL`) |
| C-010 | P2 | Create Paystack add-on plan (`PLAN_PAYG_API_ADDON`) |

---

## EXECUTION ORDER (recommended)

```
1. Verify FK-001 fix with real purchase
2. Sprint K — re-apply 8 unmerged fixes (K-001 through K-008)
3. Sprint I P0s — I-001, I-002 (overlaps K-002), I-003
4. J-010 — verify flow UI redesign
5. Sprint I P1s — I-004 through I-006
6. Provider gaps — PR-001, PR-002
7. Background worker errors
8. Sprint I P2/P3s + PR-003 through PR-006
```

---

## OVERALL PROGRESS

| Sprint | Scope | Done | Open |
|--------|-------|------|------|
| A–I | All previous sprints | 90/93 | 3 manual/external |
| J | Verification flow UX | 5/7 | 2 open (J-010, J-006) |
| K | Unmerged Copilot fixes | 0/8 | 8 open |
| I | Notification/WS hardening | 0/10 | 10 open |
| Provider gaps | Routing/lifecycle | 0/6 | 6 open |

---

## SPEC REFERENCE

| Doc | What it covers |
|-----|----------------|
| `docs/status/VERIFY_FLOW_REDESIGN.md` | J-010 full redesign spec |
| `docs/engineering/VERIFICATION_FLOW_HANDOVER_NOV2026.md` | Copilot static review — source of Sprint K |
| `docs/engineering/TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md` | Stock accuracy + flow gaps |
| `docs/engineering/VRENUM_API_CONTRACT.md` | Public API contract |
| `docs/status/HANDOVER_NOV2026.md` | Nov 24 session handover |
| `docs/status/MASTER_TASKS.md` | Historical record of all completed work |
