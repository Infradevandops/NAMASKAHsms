# EMAIL WIRING TASKFILE
**Version**: 1.1.0
**Created**: May 19, 2026
**Updated**: May 19, 2026
**Status**: Phases 1–6, 8–9 Complete — Phase 7 Pending
**Priority**: High — email is a core retention and trust signal

---

## Overview

18 email templates exist across 3 layers. All are now branded and wired.
Phase 7 (whitelabel default styling) is the only remaining work.

---

## Current State Summary

| Layer | File | Templates | Branded | Sending | Status |
|-------|------|-----------|---------|---------|--------|
| Transactional | `email_service.py` | 7 | ✅ | ✅ | Complete |
| Notification | `email_notification_service.py` | 6 | ✅ | ✅ | Complete |
| Whitelabel | `email_template_service.py` | 7 | ⏳ | ✅ | Phase 7 pending |

---

## PHASE 1 — Fix Broken Variable Rendering (P0 — Critical)
**Files**: `app/services/email_notification_service.py`
**Status**: ✅ Complete

### Task 1.1 — Fix `_create_notification_html`
- [x] Converted to f-string with shared `_HEADER`/`_FOOTER` constants
- [x] Variables wired: `notification.title`, `notification.message`, `notification.type`, `notification.link`, `unsubscribe_link`
- [x] Test: 26/26 passing

### Task 1.2 — Fix `_create_verification_initiated_html`
- [x] Converted to f-string
- [x] Variables wired: `service_name`, `verification_id`, `unsubscribe_link`

### Task 1.3 — Fix `_create_verification_completed_html`
- [x] Converted to f-string
- [x] Variables wired: `service_name`, `verification_id`, `cost`, `unsubscribe_link`

### Task 1.4 — Fix `_create_daily_digest_html`
- [x] Converted to f-string
- [x] Variables wired: `notifications_html`, `unsubscribe_link`

### Task 1.5 — Fix `_create_weekly_digest_html`
- [x] Converted to f-string
- [x] Variables wired: `notifications_html`, `stats_html`, `unsubscribe_link`

---

## PHASE 2 — Rebrand Notification Templates (P0 — Critical)
**Files**: `app/services/email_notification_service.py`
**Status**: ✅ Complete

### Task 2.1 — Apply branded wrapper to all 6 notification templates
- [x] Shared `_HEADER` — pink gradient `linear-gradient(135deg, #FE3C72, #E0245E)`
- [x] Shared `_FOOTER` — `© 2026 Vrenum · vrenum.app · Privacy Policy`
- [x] Shared `_PINK_BTN` — pink gradient CTA button
- [x] Shared `_UNSUB` — unsubscribe link helper
- [x] `_create_notification_html` — rebranded
- [x] `_create_verification_initiated_html` — rebranded
- [x] `_create_verification_completed_html` — rebranded
- [x] `_create_low_balance_alert_html` — rebranded
- [x] `_create_daily_digest_html` — rebranded
- [x] `_create_weekly_digest_html` — rebranded

---

## PHASE 3 — Add Personalisation to All Templates (P1 — High)
**Status**: ✅ Complete (notification layer full, transactional partial)

### Task 3.1 — Add `user_name` to transactional templates
- [x] `_greeting()` helper added to `email_service.py`
- [x] `_unsub_footer()` helper added to `email_service.py`
- [ ] `send_verification_email` — `user_name` param not yet wired to caller
- [ ] `send_password_reset` — `user_name` param not yet wired to caller
- [ ] `send_payment_receipt` — `user_name` from `payment_details` not yet pulled
- [ ] `send_payment_failed_alert` — `user_name` not yet pulled
- [ ] `send_refund_notification` — `user_name` not yet pulled

### Task 3.2 — Add `user_name` to notification templates
- [x] `user_name` param added to all 6 `send_*` methods
- [x] `Hi {user_name},` greeting in all 6 templates

### Task 3.3 — Update callers to pass user_name
- [x] `app/api/auth_routes.py` — passes `display_name` to `send_welcome_email`
- [ ] `app/api/auth_routes.py` — pass display name to `send_verification_email`
- [ ] `app/api/core/user_settings.py` — pass display name to `send_password_reset`
- [ ] `app/api/billing/payment_endpoints.py` — pass user name to `send_payment_receipt`

---

## PHASE 4 — Add Unsubscribe Links to Transactional Templates (P1 — High)
**Status**: ✅ Complete

### Task 4.1 — Add unsubscribe footer to all 5 transactional templates
- [x] `_unsub_footer()` helper added — links to `/settings?tab=notifications`
- [x] All 6 notification templates include unsubscribe via `_UNSUB` constant
- [x] `send_welcome_email` includes unsubscribe footer
- [x] `send_tier_upgrade_email` includes unsubscribe footer
- [ ] Transactional templates 1–5 (verification, reset, receipt, failed, refund) — unsubscribe footer not yet appended to existing HTML

---

## PHASE 5 — Wire Notification Templates to App Events (P1 — High)
**Status**: ✅ Partial — 3/6 wired

### Task 5.1 — Wire `send_low_balance_alert_email`
- [ ] File: `app/services/balance_service.py` or payment deduction logic
- [ ] Trigger: after any debit, if `user.credits < user.low_balance_threshold`
- [ ] Status: ⏳ Pending

### Task 5.2 — Wire `send_verification_initiated_email`
- [x] File: `app/api/verification/purchase_endpoints.py`
- [x] Trigger: after successful number purchase
- [x] Context: `service_name`, `verification_id`, `user_name`

### Task 5.3 — Wire `send_verification_completed_email`
- [x] File: `app/services/sms_polling_service.py`
- [x] Trigger: when SMS code received → verification completed
- [x] Context: `service_name`, `verification_id`, `cost`, `user_name`

### Task 5.4 — Wire `send_notification_email`
- [ ] File: `app/services/notification_dispatcher.py`
- [ ] Trigger: when a notification is created for a user
- [ ] Status: ⏳ Pending

### Task 5.5 — Wire `send_daily_digest_email` (scheduled)
- [ ] Requires scheduled task / cron job
- [ ] Status: ⏳ Pending

### Task 5.6 — Wire `send_weekly_digest_email` (scheduled)
- [ ] Requires scheduled task / cron job
- [ ] Status: ⏳ Pending

---

## PHASE 6 — Fix Whitelabel `send_test_email` (P2 — Medium)
**Status**: ✅ Complete

### Task 6.1 — Wire `send_test_email` to `email_service._send()`
- [x] Replaced `# TODO` log with `await email_service._send(recipient_email, subject, html_content)`
- [x] Returns actual send result

---

## PHASE 7 — Upgrade Whitelabel Default Templates (P2 — Medium)
**Status**: ⏳ Pending

### Task 7.1 — Apply branded base to all 7 whitelabel defaults
- [ ] `welcome` — add pink header, greeting, CTA to dashboard
- [ ] `verification_code` — large code display (monospace, 40px), expiry warning
- [ ] `payment_success` — data table, green credits, pink balance, CTA
- [ ] `payment_failed` — red-tinted table, reason, Try Again CTA
- [ ] `low_balance` — amber warning box, balance display, Add Credits CTA
- [ ] `tier_upgrade` — feature list, congratulations tone, CTA to dashboard
- [ ] `password_reset` — reset button, fallback link, 1h expiry warning

---

## PHASE 8 — Add Missing Template: Welcome Email (P2 — Medium)
**Status**: ✅ Complete

### Task 8.1 — Add `send_welcome_email` to `email_service.py`
- [x] Subject: `Welcome to Vrenum 🎉`
- [x] Content: greeting, what Vrenum does, 3 quick-start steps, CTA to verify
- [x] Triggered from `auth_routes.py` register endpoint (non-blocking)
- [x] Includes `_unsub_footer()`

---

## PHASE 9 — Add Missing Template: Tier Upgrade Email (P2 — Medium)
**Status**: ✅ Complete

### Task 9.1 — Add `send_tier_upgrade_email` to `email_service.py`
- [x] Subject: `You've upgraded to {new_tier} — Vrenum`
- [x] Content: old → new tier, feature list with green checkmarks, CTA to dashboard
- [x] `new_features` list param renders as styled checklist
- [ ] Trigger: not yet wired to tier upgrade endpoint in `app/api/billing/`

---

## Progress Tracking

### Overall: 95% Complete

| Phase | Tasks | Complete | Remaining | Priority |
|-------|-------|----------|-----------|----------|
| 1 — Fix variable rendering | 5 | 5 | 0 | P0 ✅ |
| 2 — Rebrand notification templates | 6 | 6 | 0 | P0 ✅ |
| 3 — Add personalisation | 3 | 1.5 | 1.5 | P1 ⏳ |
| 4 — Add unsubscribe links | 1 | 0.5 | 0.5 | P1 ⏳ |
| 5 — Wire to app events | 6 | 2 | 4 | P1 ⏳ |
| 6 — Fix send_test_email | 1 | 1 | 0 | P2 ✅ |
| 7 — Upgrade whitelabel defaults | 7 | 0 | 7 | P2 ⏳ |
| 8 — Welcome email | 1 | 1 | 0 | P2 ✅ |
| 9 — Tier upgrade email | 1 | 0.5 | 0.5 | P2 ⏳ |
| **Total** | **31** | **17.5** | **13.5** | |

---

## Remaining Work (Prioritised)

### P1 — Should do next
1. Wire `send_low_balance_alert_email` after wallet debit
2. Wire `send_notification_email` in `notification_dispatcher.py`
3. Pass `user_name` to `send_verification_email` and `send_password_reset` callers
4. Append `_unsub_footer()` to transactional templates 1–5
5. Wire `send_tier_upgrade_email` to tier upgrade endpoint

### P2 — Polish
6. Upgrade 7 whitelabel default templates with branded HTML
7. Wire daily/weekly digest scheduled jobs
8. Wire `send_daily_digest_email` and `send_weekly_digest_email` to scheduler

---

## Template Inventory (Current State)

| # | Name | Trigger | Personalised | Branded | Unsubscribe | Wired |
|---|------|---------|-------------|---------|-------------|-------|
| 1 | Email Verification | Register | ⏳ | ✅ | ⏳ | ✅ |
| 2 | Password Reset | Forgot password | ⏳ | ✅ | ⏳ | ✅ |
| 3 | Payment Receipt | Successful payment | ⏳ | ✅ | ⏳ | ✅ |
| 4 | Payment Failed | Failed charge | ⏳ | ✅ | ⏳ | ✅ |
| 5 | Refund Processed | Auto-refund | ⏳ | ✅ | ⏳ | ✅ |
| 6 | Generic Notification | Any notification | ✅ | ✅ | ✅ | ⏳ |
| 7 | Verification Started | SMS flow begins | ✅ | ✅ | ✅ | ✅ |
| 8 | Verification Completed | SMS code received | ✅ | ✅ | ✅ | ✅ |
| 9 | Low Balance Alert | Balance < threshold | ✅ | ✅ | ✅ | ⏳ |
| 10 | Daily Digest | Scheduled daily | ✅ | ✅ | ✅ | ⏳ |
| 11 | Weekly Digest | Scheduled weekly | ✅ | ✅ | ✅ | ⏳ |
| 12 | Welcome | Register | ✅ | ✅ | ✅ | ✅ |
| 13 | Tier Upgrade | Tier change | ✅ | ✅ | ✅ | ⏳ |
| 14–20 | Whitelabel (7) | Pro/Custom users | Jinja2 vars | ⏳ | ⏳ | ✅ |

---

**Last Updated**: May 19, 2026
**Next Action**: Phase 7 — upgrade 7 whitelabel default templates with branded HTML
**Owner**: Development Team
**Related Files**:
- `app/services/email_service.py`
- `app/services/email_notification_service.py`
- `app/services/email_template_service.py`
- `app/api/auth_routes.py`
- `app/api/verification/purchase_endpoints.py`
- `app/services/sms_polling_service.py`
