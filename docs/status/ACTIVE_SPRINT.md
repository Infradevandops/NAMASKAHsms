# ACTIVE SPRINT — VRENUM SMS

**Updated**: November 25, 2026
**HEAD**: `8a6b7234`
**Authority**: Single actionable task list. `MASTER_TASKS.md` is historical record.

---

## BLOCKER

### FK-001 — Purchase FK fix unverified
Fix deployed (`f791daf0`) — no successful purchase confirmed since.
```bash
docker compose logs app -f 2>&1 | grep -E "ForeignKey|Ledger Synced|balance_service"
```
Expected: `Ledger Synced for <user_id>: -$X.XX` with no `ForeignKeyViolation`.

---

## OPEN — CODE

| ID | Priority | Issue | File |
|----|----------|-------|------|
| L-014 | P2 | Unit-tests `continue-on-error: true` — pre-existing failures need triage, then harden gate | `.github/workflows/ci.yml` |
| PR-001 | P1 | TV availability gate runs before provider router — blocks non-TV providers for countries TV doesn't cover | `purchase_endpoints.py`, `provider_router.py` |
| PR-002 | P1 | US healthy-shortcut doesn't check adapter enabled or capability | `provider_router.py` |
| PR-003 | P2 | Voice page: legacy JSON purchase, fixed 300s timer, HTTP polling — not on SSE/WS lifecycle | `voice_verify_modern.html`, `purchase_endpoints.py` |
| PR-004 | P2 | `sms_and_voice` accepted and priced but combined lifecycle undefined | `purchase_endpoints.py`, `sms_polling_service.py` |
| PR-005 | P2 | WebSocket manager in-process memory — multi-worker deployments lose pushes | `app/websocket/manager.py` |
| PR-006 | P2 | `expired` vs `failed` terminal state inconsistency across poller, refund, notifications, UI | multiple |

---

## OPEN — SERVER / MANUAL

| ID | Priority | Action |
|----|----------|--------|
| FK-001 | P0 | Verify purchase fix — make real purchase, check logs |
| L-002 | P1 | Cloudflare WebSocket toggle — Dashboard → Network → WebSockets → Enable |
| L-003 | P1 | OTP login E2E — trigger on live server, confirm email + JWT |
| L-007 / A-005 | P1 | Telegram E2E — connect @vrenum_sms_bot, trigger verification, confirm forwarded |
| L-011 | P1 | Confirm VPS still running — doc says Dec 1 expiry, verify or plan migration |
| L-012 | P2 | Run `alembic upgrade head` on server — 5 pending migrations (fixes BW-001, BW-004) |
| L-013 | P2 | Create S3 bucket `vrenum-backups` or update `DEPLOYMENT_BEST_PRACTICES.md` |
| E-001 | P2 | Upgrade Upstash Redis to pay-as-you-go |
| E-002 | P2 | TextVerified IP whitelist — submit server IP (from `.env.production`) |
| C-001 | P2 | Create Paystack annual plan codes (`PLAN_PRO_ANNUAL`, `PLAN_CUSTOM_ANNUAL`) |
| C-010 | P2 | Create Paystack add-on plan (`PLAN_PAYG_API_ADDON`) |

---

## OPEN — BACKGROUND WORKER ERRORS

| ID | Error | Fix | Priority |
|----|-------|-----|----------|
| BW-001 | `column number_rentals.expiry_warned_at does not exist` | Run L-012 migrations | P2 |
| BW-002 | `cannot import name 'AsyncSessionLocal'` in back_order_monitor | Already fixed in code — needs deploy | P2 |
| BW-003 | `invalid username-password pair` — orphan reconciliation Redis | Check Upstash creds in `.env.production` | P2 |
| BW-004 | `User has no attribute 'annual_renewal_at'` | Run L-012 migrations | P3 |

---

## COMPLETED THIS SESSION ✅

| ID | What | Commit |
|----|------|--------|
| L-001 | Cloudflare cache purge — `chooseMethod` fixed | manual |
| L-004 | `margin_reconciliation` timedelta | stale — file doesn't exist |
| L-005 | Credentials scrubbed from 13 archive/deployment docs | `8a6b7234` |
| L-006 | Pre-commit gitleaks hook | stale — already in `.pre-commit-config.yaml` |
| L-008 | Voice `transcribing` SSE step | `1f210d86` |
| L-009 | Reuse banner | stale — already implemented |
| L-010 | `smsAndVoiceCombo` | stale — `sms_and_voice` already in schema |
| K-001–K-008 | Verification flow fixes | `dbce48c4` |
| I-001–I-010 | Notification/WS hardening | verified correct in code |
| J-001–J-010 | Verification flow UX | `64954e79` |
| IP scrub | Server IP removed from all docs | `1f210d86` |
| HANDOVER_NOV2026.md | Deleted — all items resolved | `1f210d86` |

---

## OVERALL PROGRESS

| Sprint | Scope | Done | Open |
|--------|-------|------|------|
| A–I | All previous sprints | 93/93 | 0 |
| J | Verification flow UX | 7/7 | ✅ |
| K | Verification fixes | 8/8 | ✅ |
| I | Notification/WS hardening | 10/10 | ✅ |
| L | Doc scan findings | 13/14 | 1 (L-014) |
| Provider gaps | Routing/lifecycle | 0/6 | 6 |
| Background workers | Non-critical errors | 2/4 | 2 (need server) |

---

## SPEC REFERENCE

| Doc | What it covers |
|-----|----------------|
| `docs/engineering/VRENUM_API_CONTRACT.md` | Public API contract |
| `docs/engineering/development/VERIFICATION_TASKS.md` | Verification system ground truth |
| `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md` | Telegram E2E checklist (A-005) |
| `docs/status/MASTER_TASKS.md` | Historical record of all completed work |
