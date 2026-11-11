# ACTIVE SPRINT

**Updated**: November 2026
**HEAD**: `f4b030d5` on origin/main
**CI**: Pending pass on `f4b030d5` → auto-deploys via deploy.yml
**Full task list**: `docs/status/MASTER_TASKS.md`

---

## SPRINT STATUS

| Sprint | Done | Open code | Manual/blocked |
|--------|------|-----------|----------------|
| A — Deploy & Fixes | 5/8 | 0 | 3 |
| B — Verification Polish | 8/9 | 1 (B-008 smsAndVoiceCombo) | 0 |
| C — Revenue Features | 14/19 | 5 | 2 (Paystack plans) |
| D — Inventory Notifications | 15/25 | 10 | 0 |
| E — Ops & Infrastructure | 0/6 | 4 | 2 |
| F — SDK Gaps | 3/4 | 1 (see B-008) | 0 |
| **Total** | **45/71** | **21** | **7** |

---

## NEXT CODE TASKS (priority order)

### High value / short
| ID | Task | File | Time |
|----|------|------|------|
| E-006 | `wake_number=True` for rental polling | `textverified_service.py` | 15 min |
| C-019 | `bonus_credits` in-app notification | `notification_service.py` | 15 min |
| C-015 | Paystack webhook activates `SubscriptionAddon` on add-on payment | `payment_service.py` | 30 min |
| C-006 | Settings page — show billing period | `templates/settings.html` | 30 min |
| C-007 | Annual renewal reminder email (30 days before `annual_renewal_at`) | `email_service.py`, `lifespan.py` | 30 min |
| D-017/018 | Expiry monitor 24h warning + digest call | `app/workers/expiry_monitor.py` | 45 min |

### Medium
| ID | Task | File | Time |
|----|------|------|------|
| B-008 | `smsAndVoiceCombo` capability | `schemas/`, `pricing_calculator.py`, `verification-flow.js` | 2h |
| C-018 | Wallet bonus tier table + dynamic display | `templates/wallet.html` | 1h |
| D-010 | `create_reservation()` back-order detection | `textverified_service.py` | 1h |
| D-013 | Rentals page back-order UI | `templates/rentals_modern.html` | 1h |
| D-006/014/019 | Notification center — 3 new types | `templates/notification_center.html` | 1h |
| D-007/015/020 | 3 user emails (stock, rental_ready, rental_expiring) | `email_service.py` | 1h |

### Ops
| ID | Task | File | Time |
|----|------|------|------|
| E-003/004 | CI coverage triage + raise floor to 30% | `.github/workflows/ci.yml` | 2-3h |

---

## MANUAL ACTIONS PENDING

| Action | Where |
|--------|-------|
| Confirm latest commit live on server | SSH: `cd ~/vrenum && git log --oneline -3` |
| Test 8 transactional emails | Resend dashboard |
| Create Paystack annual plan codes (C-001) | Paystack dashboard |
| Create Paystack PAYG API addon plan (C-010) | Paystack dashboard |
| Upgrade Upstash Redis to pay-as-you-go (E-001) | Upstash dashboard |
| TextVerified IP whitelist (E-002) | TV support ticket |
