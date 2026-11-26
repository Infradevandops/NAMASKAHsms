# ACTIVE SPRINT — VRENUM SMS

**Updated**: November 25, 2026
**HEAD**: `64954e79` (local + remote in sync)
**Authority**: Single actionable task list. `MASTER_TASKS.md` is historical record.

---

## BLOCKER — Verify Before Anything Else

### FK-001 — Purchase FK fix unverified
Fix deployed (`f791daf0`) but no successful purchase confirmed since.
```bash
docker compose logs app -f 2>&1 | grep -E "ForeignKey|Ledger Synced|balance_service"
```
Expected: `Ledger Synced for <user_id>: -$X.XX` with no `ForeignKeyViolation`.

---

## SPRINT L — DOC SCAN FINDINGS

| ID | Priority | Issue | Status |
|----|----------|-------|--------|
| L-001 | P0 | Cloudflare cache purge — `chooseMethod` undefined | ✅ Done (manual) |
| L-002 | P1 | Cloudflare WebSocket toggle | ⏳ Manual — Cloudflare Dashboard → Network → WebSockets |
| L-003 | P1 | OTP login E2E test on live server | ⏳ Manual |
| L-004 | P2 | `margin_reconciliation` missing `timedelta` | ✅ Stale — file does not exist |
| L-005 | P2 | Credentials in archive/deployment docs (gitleaks) | 🔴 Open — scrub 12 files |
| L-006 | P2 | Pre-commit hook not installed | ✅ Stale — `.pre-commit-config.yaml` already has gitleaks |
| L-007 | P1 | Telegram E2E — 12 ACs unchecked | ⏳ Manual (A-005) |
| L-008 | P3 | No `transcribing` SSE step for voice | ✅ Fixed (`purchase_endpoints.py`) |
| L-009 | P2 | Reuse banner not in UI | ✅ Stale — WS push + UI handler already implemented |
| L-010 | P3 | `smsAndVoiceCombo` capability unused | ✅ Stale — `sms_and_voice` already in schema |
| L-011 | P1 | VPS expiry / Render migration | ⏳ Manual — confirm server status |
| L-012 | P2 | 5 pending Alembic migrations not run on server | ⏳ Manual — SSH → `alembic upgrade head` |
| L-013 | P2 | S3 bucket `vrenum-backups` not created | ⏳ Create bucket or update doc |
| L-014 | P2 | Unit-tests `continue-on-error` — failures need triage | 🔴 Open |

---

## SPRINT K — VERIFICATION FIXES ✅ Complete

| ID | Issue | Status |
|----|-------|--------|
| K-001 | Orphan timeout ISO timestamp | ✅ Fixed |
| K-002 | TV webhook shared completion | ✅ Fixed |
| K-003 | `purchase_healed` UI resume callback | ✅ Fixed |
| K-004 | UI local expiry nav-away | ✅ Fixed |
| K-005 | `auto_refund_service` `expired` status | ✅ Fixed |
| K-006 | Naive/aware datetime latency | ✅ Fixed |
| K-007 | OTP in success log | ✅ Fixed |
| K-008 | Unawaited telemetry in refund service | ✅ Fixed |

---

## SPRINT J — VERIFICATION FLOW UI ✅ Complete

| ID | Issue | Status |
|----|-------|--------|
| J-001 | Step 0+1 stacking | ✅ Fixed |
| J-004 | Step 1 Back → Step 0 | ✅ Fixed |
| J-005 | Step 2 Back → Step 1 | ✅ Fixed |
| J-006 | Voice page stacking assessment | ✅ Assessed (no stacking — different flow) |
| J-007 | Cloudflare cache bypass rule | ✅ Done |
| J-009 | Orphan recovery hijacked Step 0 | ✅ Fixed |
| J-010 | Duplicate service selector | ✅ Fixed |

---

## SPRINT I — NOTIFICATION & WEBSOCKET HARDENING

| ID | Priority | Issue | Status |
|----|----------|-------|--------|
| I-001 | P0 | `on_sms_received` not awaited in `_complete_verification()` | ✅ Already awaited |
| I-002 | P0 | TV webhook pushes `sms_received` before debit confirmed | ✅ Already guarded (`refund_eligible` check) |
| I-003 | P0 | `mark-all-read` URL mismatch | ✅ `/api/notifications/bulk-read` matches JS call |
| I-004 | P1 | `asyncio.create_task()` in sync `_broadcast_notification()` | ✅ Uses `loop.create_task` with `RuntimeError` guard |
| I-005 | P1 | `purchasing_delayed` no WS event | ✅ Fixed (K-003) |
| I-006 | P1 | Refund notification exposes internal reason codes | ✅ Fixed |
| I-007 | P2 | `get_unread_count` defined twice | ✅ Only one definition |
| I-008 | P2 | `_channels` dict lazy-init — potential AttributeError | ✅ Initialized in `__init__` |
| I-009 | P2 | `cleanup_old_notifications()` never called | ✅ Called in lifespan |
| I-010 | P3 | `datetime.utcnow()` naive in `telegram_service.py` | ✅ Fixed |

---

## PROVIDER / ROUTING GAPS

| ID | Priority | Issue |
|----|----------|-------|
| PR-001 | P1 | TV availability gate runs before provider router — blocks non-TV providers |
| PR-002 | P1 | US healthy-shortcut doesn't check adapter enabled or capability |
| PR-003 | P2 | Voice page: legacy JSON purchase, fixed 300s timer, HTTP polling — not SSE/WS |
| PR-004 | P2 | `sms_and_voice` accepted and priced but lifecycle undefined |
| PR-005 | P2 | WebSocket manager in-process — multi-worker loses pushes |
| PR-006 | P2 | `expired` vs `failed` inconsistency across poller, refund, notifications, UI |

---

## BACKGROUND WORKER ERRORS

| ID | Error | Fix | Priority |
|----|-------|-----|----------|
| BW-001 | `column number_rentals.expiry_warned_at does not exist` | Alembic migration (L-012) | P2 |
| BW-002 | `cannot import name 'AsyncSessionLocal'` in back_order_monitor | Fix import | P2 |
| BW-003 | `invalid username-password pair` — orphan reconciliation Redis | Check Upstash creds in `.env` | P2 |
| BW-004 | `User has no attribute 'annual_renewal_at'` | Add column via migration (L-012) | P3 |

---

## MANUAL / EXTERNAL ACTIONS

| ID | Priority | Action |
|----|----------|--------|
| A-005 | P1 | Telegram E2E — connect @vrenum_sms_bot, trigger verification, confirm SMS forwarded (see L-007) |
| E-001 | P2 | Upgrade Upstash Redis to pay-as-you-go |
| E-002 | P2 | TextVerified IP whitelist — submit server IP (see `.env.production`) |
| C-001 | P2 | Create Paystack annual plan codes (`PLAN_PRO_ANNUAL`, `PLAN_CUSTOM_ANNUAL`) |
| C-010 | P2 | Create Paystack add-on plan (`PLAN_PAYG_API_ADDON`) |

---

## EXECUTION ORDER

```
1. FK-001 — verify purchase fix with real purchase (blocker for everything)
2. L-001 — Cloudflare cache purge (P0, 2 min)
3. L-002 — Cloudflare WebSocket toggle (P1, 2 min)
4. L-011 — confirm VPS migration status (P1, time-sensitive)
5. L-012 — run pending Alembic migrations on server (fixes BW-001, BW-004)
6. BW-002, BW-003 — fix AsyncSessionLocal import + Redis creds
7. L-003 — OTP E2E test + A-005 Telegram E2E
8. I-001, I-002, I-003 — notification P0s
9. L-009 — reuse banner (revenue)
10. L-005 — scrub archive docs credentials (gitleaks)
11. L-006 — pre-commit hook install
12. PR-001, PR-002 — provider routing fixes
13. I-004, I-007, I-008, I-009 — notification P2s
14. L-004, L-008, L-010, L-013, L-014 — remaining P2/P3s
```

---

## OVERALL PROGRESS

| Sprint | Scope | Done | Open |
|--------|-------|------|------|
| A–I | All previous sprints | 93/93 | 0 |
| J | Verification flow UX | 7/7 | ✅ Complete |
| K | Verification fixes | 8/8 | ✅ Complete |
| I | Notification/WS hardening | 10/10 | ✅ Complete |
| L | Doc scan findings | 12/14 | 2 open (L-005, L-014) |
| Provider gaps | Routing/lifecycle | 0/6 | 6 open |
| Background workers | Non-critical errors | 0/4 | 4 open (need server SSH) |

---

## SPEC REFERENCE

| Doc | What it covers |
|-----|----------------|
| `docs/status/VERIFY_FLOW_REDESIGN.md` | J-010 spec (implemented) |
| `docs/engineering/VERIFICATION_FLOW_HANDOVER_NOV2026.md` | Sprint K source (all resolved) |
| `docs/engineering/development/VERIFICATION_TASKS.md` | Source of L-008, L-009, L-010 |
| `docs/status/TASKS_NOV2026.md` | Source of L-001, L-002, L-004, L-011 |
| `docs/status/OTP_LOGIN_TASKS.md` | Source of L-003 |
| `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md` | Source of L-007 / A-005 |
| `docs/engineering/VRENUM_API_CONTRACT.md` | Public API contract |
| `docs/status/MASTER_TASKS.md` | Historical record |
