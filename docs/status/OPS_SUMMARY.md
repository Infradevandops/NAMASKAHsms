# OPS SUMMARY

**Last Updated**: November 10, 2026
**HEAD**: `a7188224`
**CI**: ⏳ Running — `frontend-unit-tests` on `a7188224`
**Deploy**: Auto-fires when CI concludes `success`
**TV**: ✅ Operational — $42.15 balance, pricing URL confirmed

---

## CI PIPELINE

```
frontend-unit-tests (BLOCKING — no needs, runs independently)
secrets-scan        (continue-on-error)
code-quality        (continue-on-error)
smoke-test          (continue-on-error, needs: secrets-scan)
unit-tests          (continue-on-error, needs: frontend-unit-tests + smoke-test)
integration-tests   (continue-on-error, needs: unit-tests)
e2e-tests           (continue-on-error, needs: unit-tests)
```

Workflow concludes `success` if `frontend-unit-tests` passes (92/92 JS tests).
Deploy fires automatically on `success`.

**Recent CI fixes**:
- `a7188224`: `frontend-unit-tests` runs independently (no `needs`) — fixes workflow conclusion
- `fe6be54d`: `integration-tests` continue-on-error
- `22d15292`: Python 3.11 + ubuntu-22.04
- `d632e429`: actions/checkout@v4, setup-python@v5

---

## OPEN MANUAL ACTIONS

| ID | Priority | Action | Where |
|----|----------|--------|-------|
| A-001 | P0 | Confirm deploy — `git log --oneline -3`, run `alembic upgrade head` | SSH `~/vrenum` |
| H-006b | P0 | Verify TV webhook enabled after deploy | TV API config page |
| A-002 | P1 | Test 8 transactional emails | Resend dashboard + inbox |
| A-005 | P1 | Telegram E2E — @vrenum_sms_bot | Live server |
| E-001 | P2 | Upstash Redis → pay-as-you-go | Upstash dashboard |
| E-002 | P2 | TV IP whitelist — submit server IP | TV support ticket |
| C-001 | P2 | Paystack annual plan codes | Paystack dashboard |
| C-010 | P2 | Paystack add-on plan | Paystack dashboard |

---

## INFRASTRUCTURE

| Component | Status |
|-----------|--------|
| FastAPI app (gunicorn, 2 workers) | ✅ Running |
| PostgreSQL | ✅ Running |
| Redis | ✅ Running |
| TV webhook endpoint | ✅ Live (H-006 monitor active) |
| Orphan reconciliation worker | ✅ Active (60s loop) |
| Circuit breaker | ✅ Active (per-provider) |
| Back-order monitor | ✅ Active (5-min loop) |
| Stock monitor | ✅ Active (90s loop) |
| TV webhook health monitor | ✅ Active (30-min loop) |
| Sentry | ✅ Active |
| BetterStack uptime | ✅ Active |
| CI gate | ⏳ Running on a7188224 |
| Deploy workflow | ✅ CI-gated, auto-fires |

---

## MIGRATION PENDING ON SERVER

Run after deploy (`alembic upgrade head`):
- `expiry_warned_at` on NumberRental
- `billing_period` + `annual_renewal_at` on User
- `stock_watches` table
- `rental_back_orders` table
- `subscription_addons` table
