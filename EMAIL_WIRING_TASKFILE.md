# EMAIL WIRING TASKFILE
**Version**: 1.0.0
**Created**: May 19, 2026
**Status**: Ready for Implementation
**Priority**: High — email is a core retention and trust signal

---

## Overview

18 email templates exist across 3 layers. 5 are live and branded. 13 need work.
This taskfile covers every fix needed to make all 18 production-ready.

---

## Current State Summary

| Layer | File | Templates | Branded | Sending | Broken |
|-------|------|-----------|---------|---------|--------|
| Transactional | `email_service.py` | 5 | ✅ | ✅ | Minor gaps |
| Notification | `email_notification_service.py` | 6 | ❌ | ✅ | Variables don't render |
| Whitelabel | `email_template_service.py` | 7 | ❌ | ❌ | send_test_email is a TODO |

---

## PHASE 1 — Fix Broken Variable Rendering (P0 — Critical)
**Files**: `app/services/email_notification_service.py`
**Problem**: Templates 6–11 use triple-quoted strings with `{variable}` syntax
but are NOT f-strings. Variables print literally e.g. `{notification.title}`.
**Estimated effort**: 2 hours

### Task 1.1 — Fix `_create_notification_html`
- [ ] Convert to f-string or `.format()` call
- [ ] Variables to wire: `notification.title`, `notification.message`,
  `notification.type`, `notification.link`, `unsubscribe_link`
- [ ] Test: rendered HTML contains actual values not `{notification.title}`

### Task 1.2 — Fix `_create_verification_initiated_html`
- [ ] Convert to f-string
- [ ] Variables to wire: `service_name`, `verification_id`, `unsubscribe_link`
- [ ] Test: service name appears in rendered output

### Task 1.3 — Fix `_create_verification_completed_html`
- [ ] Convert to f-string
- [ ] Variables to wire: `service_name`, `verification_id`, `cost`, `unsubscribe_link`
- [ ] Test: cost renders as `$2.50` not `{cost:.2f}`

### Task 1.4 — Fix `_create_daily_digest_html`
- [ ] Convert to f-string
- [ ] Variables to wire: `notifications_html`, `unsubscribe_link`
- [ ] Test: notification items render in output

### Task 1.5 — Fix `_create_weekly_digest_html`
- [ ] Convert to f-string
- [ ] Variables to wire: `notifications_html`, `stats_html`, `unsubscribe_link`
- [ ] Test: stats table renders correctly

---

## PHASE 2 — Rebrand Notification Templates (P0 — Critical)
**Files**: `app/services/email_notification_service.py`
**Problem**: All 6 notification templates use old purple `#667eea` branding.
Must match the 5 transactional templates (pink gradient header, white card, footer).
**Estimated effort**: 3 hours

### Task 2.1 — Apply branded wrapper to all 6 notification templates
Each template needs:
- Pink gradient header: `linear-gradient(135deg, #FE3C72, #E0245E)`
- White card body: `border-radius:16px; box-shadow`
- Consistent footer: `© 2026 Vrenum · vrenum.app · Privacy Policy`
- Replace all `#667eea` with `#FE3C72`
- Replace all `background: #667eea` buttons with pink gradient CTA

Templates to rebrand:
- [ ] `_create_notification_html` — generic notification
- [ ] `_create_verification_initiated_html` — verification started
- [ ] `_create_verification_completed_html` — verification completed
- [ ] `_create_low_balance_alert_html` — low balance
- [ ] `_create_daily_digest_html` — daily digest
- [ ] `_create_weekly_digest_html` — weekly digest

---

## PHASE 3 — Add Personalisation to All Templates (P1 — High)
**Files**: `email_service.py`, `email_notification_service.py`
**Problem**: No template addresses the user by name. Personalisation
increases open rates and trust.
**Estimated effort**: 1.5 hours

### Task 3.1 — Add `user_name` to transactional templates
All 5 templates in `email_service.py` need a greeting line.

- [ ] `send_verification_email` — add `user_name` param, add "Hi {user_name},"
- [ ] `send_password_reset` — add `user_name` param, add "Hi {user_name},"
- [ ] `send_payment_receipt` — pull `user_name` from `payment_details` dict
- [ ] `send_payment_failed_alert` — pull `user_name` from `payment_details` dict
- [ ] `send_refund_notification` — pull `user_name` from `refund_details` dict

### Task 3.2 — Add `user_name` to notification templates
- [ ] Pass `user_name` into all 6 `_create_*_html` methods
- [ ] Add greeting to each template body

### Task 3.3 — Update all callers to pass user_name
- [ ] `app/api/auth_routes.py` — pass display name to `send_verification_email`
- [ ] `app/api/core/user_settings.py` — pass display name to `send_password_reset`
- [ ] `app/api/billing/payment_endpoints.py` — pass user name to `send_payment_receipt`

---

## PHASE 4 — Add Unsubscribe Links to Transactional Templates (P1 — High)
**Files**: `email_service.py`
**Problem**: Templates 1–5 have no unsubscribe link. Required for CAN-SPAM/GDPR
compliance and to avoid spam classification.
**Estimated effort**: 1 hour

### Task 4.1 — Add unsubscribe footer to all 5 transactional templates
- [ ] Add `unsubscribe_token` optional param to each send method
- [ ] Add to footer: `Unsubscribe · Manage preferences`
- [ ] Link to: `https://vrenum.app/settings?tab=notifications`
- [ ] Templates: verification, password reset, receipt, failed, refund

---

## PHASE 5 — Wire Notification Templates to App Events (P1 — High)
**Files**: Various service files
**Problem**: The 6 notification templates exist and now send correctly,
but are never called anywhere in the app.
**Estimated effort**: 3 hours

### Task 5.1 — Wire `send_low_balance_alert_email`
- [ ] File: `app/services/balance_service.py` or payment deduction logic
- [ ] Trigger: after any debit, if `user.credits < user.low_balance_threshold`
- [ ] Context: `current_balance`, `threshold`

### Task 5.2 — Wire `send_verification_initiated_email`
- [ ] File: `app/api/verification/purchase_endpoints.py`
- [ ] Trigger: after successful number purchase (step 3 of flow)
- [ ] Context: `service_name`, `verification_id`
- [ ] Gate: only if user has email notifications enabled

### Task 5.3 — Wire `send_verification_completed_email`
- [ ] File: `app/services/sms_polling_service.py` or webhook handler
- [ ] Trigger: when SMS code received and verification status → completed
- [ ] Context: `service_name`, `verification_id`, `cost`
- [ ] Gate: only if user has email notifications enabled

### Task 5.4 — Wire `send_notification_email`
- [ ] File: `app/services/notification_dispatcher.py`
- [ ] Trigger: when a notification is created for a user
- [ ] Context: full `Notification` object
- [ ] Gate: check `user.notification_preferences.email_enabled`

### Task 5.5 — Wire `send_daily_digest_email` (scheduled)
- [ ] Create a scheduled task / cron job
- [ ] Trigger: daily at 8am UTC
- [ ] Context: all unread notifications from past 24h per user
- [ ] Gate: only users with `digest_frequency = daily`

### Task 5.6 — Wire `send_weekly_digest_email` (scheduled)
- [ ] Create a scheduled task / cron job
- [ ] Trigger: Monday 8am UTC
- [ ] Context: all notifications from past 7 days + weekly stats
- [ ] Gate: only users with `digest_frequency = weekly`

---

## PHASE 6 — Fix Whitelabel `send_test_email` (P2 — Medium)
**File**: `app/services/email_template_service.py`
**Problem**: `send_test_email` has `# TODO: Integrate with actual email service`
and only logs. Pro/Custom users cannot test their custom templates.
**Estimated effort**: 30 minutes

### Task 6.1 — Wire `send_test_email` to `email_service._send()`
- [ ] Import `email_service` singleton
- [ ] Replace `logger.info(...)` with `await email_service._send(recipient_email, subject, html_content)`
- [ ] Return actual send result

---

## PHASE 7 — Upgrade Whitelabel Default Templates (P2 — Medium)
**File**: `app/services/email_template_service.py`
**Problem**: 7 default templates are bare `<h1>/<p>` with no styling.
When Pro users first open the template editor they see unstyled HTML.
**Estimated effort**: 2 hours

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
**Problem**: There is no welcome email sent on registration.
`email_template_service.py` has a `welcome` whitelabel template but
`email_service.py` has no `send_welcome_email` method and it's never called.
**Estimated effort**: 1 hour

### Task 8.1 — Add `send_welcome_email` to `email_service.py`
- [ ] Subject: `Welcome to Vrenum — you're all set`
- [ ] Content: greeting, what Vrenum does, 3 quick-start steps, CTA to verify
- [ ] Trigger: call from `auth_routes.py` register endpoint after user created
- [ ] Gate: non-blocking (same pattern as verification email)

---

## PHASE 9 — Add Missing Template: Tier Upgrade Email (P2 — Medium)
**Problem**: When a user upgrades their tier, no email is sent.
**Estimated effort**: 45 minutes

### Task 9.1 — Add `send_tier_upgrade_email` to `email_service.py`
- [ ] Subject: `You've upgraded to {tier_name} — here's what's new`
- [ ] Content: old tier → new tier, list of new features unlocked, CTA to dashboard
- [ ] Trigger: call from tier upgrade endpoint in `app/api/billing/`

---

## Progress Tracking

### Overall: 0% Complete

| Phase | Tasks | Est. Hours | Priority |
|-------|-------|-----------|----------|
| 1 — Fix variable rendering | 5 | 2h | P0 |
| 2 — Rebrand notification templates | 6 | 3h | P0 |
| 3 — Add personalisation | 3 | 1.5h | P1 |
| 4 — Add unsubscribe links | 1 | 1h | P1 |
| 5 — Wire to app events | 6 | 3h | P1 |
| 6 — Fix send_test_email | 1 | 0.5h | P2 |
| 7 — Upgrade whitelabel defaults | 1 | 2h | P2 |
| 8 — Welcome email | 1 | 1h | P2 |
| 9 — Tier upgrade email | 1 | 0.75h | P2 |
| **Total** | **25** | **14.75h** | |

---

## Template Inventory (Final State After All Phases)

| # | Name | Trigger | Personalised | Branded | Unsubscribe |
|---|------|---------|-------------|---------|-------------|
| 1 | Email Verification | Register | ✅ | ✅ | ✅ |
| 2 | Password Reset | Forgot password | ✅ | ✅ | ✅ |
| 3 | Payment Receipt | Successful payment | ✅ | ✅ | ✅ |
| 4 | Payment Failed | Failed charge | ✅ | ✅ | ✅ |
| 5 | Refund Processed | Auto-refund | ✅ | ✅ | ✅ |
| 6 | Generic Notification | Any notification | ✅ | ✅ | ✅ |
| 7 | Verification Started | SMS flow begins | ✅ | ✅ | ✅ |
| 8 | Verification Completed | SMS code received | ✅ | ✅ | ✅ |
| 9 | Low Balance Alert | Balance < threshold | ✅ | ✅ | ✅ |
| 10 | Daily Digest | Scheduled daily | ✅ | ✅ | ✅ |
| 11 | Weekly Digest | Scheduled weekly | ✅ | ✅ | ✅ |
| 12 | Welcome | Register | ✅ | ✅ | ✅ |
| 13 | Tier Upgrade | Tier change | ✅ | ✅ | ✅ |
| 14–20 | Whitelabel (7) | Pro/Custom users | Jinja2 vars | ✅ | ✅ |

---

**Next Action**: Start Phase 1 (variable rendering fix) — 2 hour estimate
**Owner**: Development Team
**Related Files**:
- `app/services/email_service.py`
- `app/services/email_notification_service.py`
- `app/services/email_template_service.py`
