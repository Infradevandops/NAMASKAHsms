# OPS SUMMARY

**Last Updated**: November 10, 2026
**Remote HEAD**: `8b96b5ab` — 66/83 tasks done
**Local HEAD**: `8c188763` — behind remote, pull needed
**CI**: ⚠️ Unit tests failing (E-004 — triage needed, non-blocking)
**Deploy**: ⚠️ Server behind — migration + restart needed after next code push

---

## SERVER STATE

| Check | Result |
|-------|--------|
| TV enabled | ✅ True |
| TV balance | $42.15 (last checked Nov 10) |
| Pricing URL `/pricing/verifications` | ✅ 200 confirmed |
| Server commit | `e06e91ce` (behind — everything to `8b96b5ab` pending) |
| Migration pending | `expiry_warned_at`, `billing_period`, `annual_renewal_at`, `stock_watches`, `rental_back_orders`, `subscription_addons` |

---

## CI PIPELINE

```
secrets-scan (continue-on-error) → frontend-unit-tests (BLOCKING)
                                 → smoke-test (BLOCKING)
                                 → unit-tests (continue-on-error — currently failing)
                                 → integration-tests (non-blocking)
                                 → e2e-tests (non-blocking)
```

**Blocking gate**: `frontend-unit-tests` (92/92 JS) + `smoke-test` (27/27 Python)
**Non-blocking**: `unit-tests` — failing, needs E-004 triage
**Action**: Download `unit-test-output-*` artifact from GitHub Actions run on `8c188763`

---

## OPEN TASKS SUMMARY

| Priority | ID | Task | Status |
|----------|----|------|--------|
| P0 | G-001 | 12s purchase timeout + `purchasing_delayed` SSE | 📋 |
| P0 | G-002 | SSE keepalive ping | 📋 |
| P1 | G-003 | Orphan reconciliation worker | 📋 |
| P1 | G-004 | Provider timeout contract (base_provider + 4 adapters) | 📋 |
| P1 | G-006 | Circuit breaker | 📋 |
| P1 | H-001 | Loading modal: arc spinner + TV 11-message sequence | 📋 |
| P1 | H-002 | Step 3: carrier icon + MM:SS + full SMS + reuse btn | 📋 |
| P1 | H-003 | Step 3 activity feed | 📋 |
| P1 | H-004 | `purchasing_delayed` frontend state | 📋 (blocked G-001) |
| P1 | H-006 | TV webhook auto-re-enable monitor | 📋 |
| P2 | G-005 | Vrenum API contract doc | 📋 |
| P2 | H-005 | Combo method picker card | 📋 |
| P2 | E-004 | CI unit-test triage | 📋 |
| Manual | A-001 | Deploy + alembic upgrade head | ⚠️ |
| Manual | A-002 | Test 8 transactional emails | ⚠️ |
| Manual | A-005 | Telegram E2E | ⚠️ |
| Manual | C-001 | Paystack annual plan codes | ⚠️ |
| Manual | C-010 | Paystack add-on plan | ⚠️ |
| Manual | E-001 | Upstash Redis upgrade | ⚠️ |
| Manual | E-002 | TV IP whitelist | ⚠️ |
| Manual | G-002b | nginx proxy_read_timeout 30s | ⚠️ |

---

## INFRASTRUCTURE

| Component | Status |
|-----------|--------|
| FastAPI app (gunicorn, 2 workers) | ✅ Running |
| PostgreSQL | ✅ Running |
| Redis | ✅ Running |
| TV webhook endpoint | ✅ Live (monitor pending H-006) |
| Background services | ✅ 11 active |
| Sentry | ✅ Active |
| BetterStack uptime | ✅ Active |
| CI gate | ⚠️ Unit tests failing (non-blocking) |
| Deploy workflow | ✅ CI-gated |
