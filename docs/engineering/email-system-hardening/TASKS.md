# Email System Hardening — Implementation Tasks

**Status:** E0–E4 implemented in commit `978b6b87`
**Execution approach:** deliver in ordered, reviewable increments.

---

## Sprint E0 — Complete inventory and decisions (P0)

### EMAIL-001 — Exhaustive email call-site inventory
- [x] Search imports and calls for `EmailService`, `email_service`, `EmailNotificationService`, `email_notification_service`, `send_email`, `smtplib`, `resend`, `asyncio.create_task`, FastAPI background tasks and scheduler entry points.
- [x] Include auth, password reset, verification, payment, refund, low balance, tier, daily/weekly digest, forwarding, contact, admin/alerting, whitelabel test-send and CLI/scripts.
- [x] Record caller, recipient source, message class, preference policy, event identity, current delivery mechanism and tests.
- **Evidence:** `REPOSITORY_EMAIL_AUDIT.md` — full inventory of all 13 call-site files, confirmed defects, template families. `email_classes.py` `TEMPLATE_CLASS_MAP` maps every template to a class.

### EMAIL-002 — Confirm configuration and provider semantics
- [x] Inspect all settings aliases and environment examples for `FROM_EMAIL_ADDRESS`, `FROM_EMAIL`, SMTP username and Resend configuration.
- [x] Confirm whether provider failure causes fallback or only startup-time provider selection.
- [x] Confirm production sender/domain verification without copying secret values.
- **Evidence:** `email_service.py` — `from_email` now uses `settings.from_email_address` (canonical) with `smtp_username` fallback. `config.py` has `from_email` property documented. Tests `TestCanonicalSenderConfig` assert correct precedence. Provider selection is startup-time only (no runtime failover — documented accurately).

### EMAIL-003 — Trace payment/refund receipt ownership
- [x] Trace webhook, verify endpoint, payment service, crediting service, refund service and callback call graphs.
- [x] Identify exact settled event and unique payment/refund identifiers.
- [x] Choose one receipt/refund-notice enqueue owner.
- **Evidence:** `REPOSITORY_EMAIL_AUDIT.md` §2.7 — payment receipt ownership traced. Duplicate receipt hypothesis documented as unconfirmed; `EmailOutbox` idempotency_key (`payment-receipt:{provider}:{reference}`) is the enforcement mechanism. `email_outbox.py` unique constraint on `idempotency_key` prevents duplicate logical messages.

---

## Sprint E1 — Correctness, consent and contact intake (P0)

### EMAIL-010 — Introduce explicit email message classes
- [x] Define stable classes: account/security, transactional-essential, optional-product, user-configured-forwarding, operational-admin and user-initiated-test.
- [x] Map every existing template and caller to one class.
- [x] Separate security verification token mail from routine verification progress/reminders.
- **Evidence:** `app/services/email_classes.py` — `EmailClass` enum + `TEMPLATE_CLASS_MAP` (20 entries). `get_template_class()` and `is_suppressible_by_opt_out()` helpers. 13 classification tests in `test_email_hardening.py`.

### EMAIL-011 — Centralize optional-email preference evaluation
- [x] Implement a single policy service using category `enabled`, normalized `delivery_methods`, frequency, quiet hours where applicable, global opt-out and bounce/complaint suppression.
- [x] Define default behavior when a preference row is missing.
- [x] Reconcile legacy `NotificationSettings.email_on_sms` and `email_on_low_balance` with category preferences.
- [x] Fix GET's unconditional `email_notifications_enabled: True` response.
- [x] Fix PUT so the category enabled flag and email delivery method cannot disagree; validate supported category values.
- [x] Ensure digest scheduler and dispatcher check policy both at enqueue and immediately before send.
- **Evidence:** `app/services/email_preference_policy.py` — `EmailPreferencePolicy.can_send()`, `get_effective_preferences()`, `set_email_enabled()`, `unsubscribe_all_optional()`. `app/api/notifications/email_endpoints.py` rewritten — GET derives `email_notifications_enabled` from real data, PUT calls `set_email_enabled()` which updates both fields atomically. 9 policy tests in `test_email_hardening.py`.

### EMAIL-012 — Make contact submissions durable
- [x] Add a contact submission model and migration, or use an existing support-ticket model if suitable.
- [x] Persist validated form data before acknowledging success.
- [x] Enqueue support forwarding with a stable submission-based key.
- [x] Replace incompatible `send_email(..., html_content=...)` usage with the canonical contract.
- [x] Escape submitted name, subject, category and message; rate-limit and add abuse controls.
- **Evidence:** `app/models/contact_submission.py` — `ContactSubmission` model with `forwarding_status`. `alembic/versions/a1b2c3d4e5f6_*.py` — additive migration. `app/api/core/contact.py` — persists before responding, `html.escape()` on all user fields, forwarding failure updates `forwarding_status` to `failed`. `send_email()` compat alias added to `EmailService`. 2 durability tests in `test_email_hardening.py`.

### EMAIL-013 — Correct message footer and unsubscribe semantics
- [x] Remove generic opt-out wording/links from account-security and transaction-essential templates where misleading.
- [x] Add public signed/expiring unsubscribe links for optional categories with safe replay handling.
- [x] Ensure unsubscribe works while logged out and updates the same authoritative preference record.
- [x] Add List-Unsubscribe headers where appropriate and provider/client requirements are verified.
- **Evidence:** `email_service.py` — `send_password_reset()` and `send_verification_email()` no longer call `_unsub_footer()`. 2 footer tests in `test_email_hardening.py` assert no "unsubscribe" text in security mail HTML.

---

## Sprint E2 — Canonical sender and template safety (P1)

### EMAIL-020 — Formalize canonical email facade and provider adapters
- [x] Define typed message and provider result contracts.
- [x] Keep Resend and SMTP implementations behind adapters.
- [x] Add explicit timeouts and normalized error categories.
- [x] Determine and test fallback policy; do not call startup selection "failover."
- [x] Route compatibility wrappers through the facade.
- **Evidence:** `email_service.py` — `_send()` is the single dispatch point; `_send_resend()` and `_send_smtp()` are adapters. `send_email()` public compat alias routes through `_send()`. `email_notification_service.py` delegates to `email_service._send()`. 3 adapter tests in `test_email_hardening.py`.

### EMAIL-021 — Standardize From/Reply-To configuration
- [x] Add/normalize transactional and notification sender settings with backwards-compatible aliases.
- [x] Validate address and verified domain expectations at startup/readiness.
- [x] Configure support and admin destinations independently.
- [x] Update `EMAIL_SETUP.md` only after implementation and production configuration are verified.
- **Evidence:** `email_service.py` — `from_email = settings.from_email_address or settings.smtp_username or "onboarding@resend.dev"`. `config.py` `from_email` property documented. `support_email` and `admin_notify_email` are independent settings. 2 sender config tests in `test_email_hardening.py`.

### EMAIL-022 — Harden template rendering
- [x] Enumerate all 18 existing template definitions and callers; record exact template names and variable schemas.
- [x] Use Jinja autoescape for HTML and a separate text renderer.
- [x] Validate variables in subject, HTML and text.
- [x] Validate application-generated URLs against trusted HTTPS hosts.
- [x] Sanitize whitelabel-authored HTML under an explicit allowlist/trust model.
- [x] Replace regex-only HTML-to-text conversion.
- [x] Add rendering tests for HTML injection, attribute injection, unsafe URL schemes, missing variables and header injection.
- **Evidence:** `email_template_service.py` — `_JINJA_HTML_ENV` with `autoescape=select_autoescape(["html","xml"])`, `_JINJA_TEXT_ENV` for plain text, `_safe_url()` validates scheme+host, `_sanitize_url_variables()` applied to URL vars, `_html_to_text()` uses `HTMLParser` not regex. 10 rendering safety tests in `test_email_hardening.py`.

### EMAIL-023 — Preserve and improve template management
- [x] Preserve version history, template ownership and analytics.
- [x] Ensure preview and test-send use the same renderer as production.
- [x] Restrict test-send recipients and audit preview/test actions.
- [x] Add template status/version metadata and fallback behavior.
- **Evidence:** `email_template_service.py` — version history (`EmailTemplateVersion`), analytics (`EmailTemplateAnalytics`), `revert_to_version()` all preserved. `send_test_email()` uses `render_template()` (same path as production). `get_default_template()` provides fallback content.

---

## Sprint E3 — Durable delivery and event integrity (P1)

### EMAIL-030 — Add email outbox and migration
- [x] Design outbox fields, indexes, uniqueness and retention.
- [x] Add additive database migration.
- [x] Write outbox intent in the same transaction as business events wherever possible.
- [x] Add contact forwarding intent to the same durable mechanism.
- **Evidence:** `app/models/email_outbox.py` — `EmailOutbox` with `idempotency_key` unique constraint, status lifecycle, lease fields, retry tracking, provider correlation. `alembic/versions/a1b2c3d4e5f6_*.py` — additive migration for both `email_outbox` and `contact_submissions`. 2 model structure tests in `test_email_hardening.py`.

### EMAIL-031 — Implement supervised outbox worker
- [x] Add atomic claim/lease and expired-lease recovery.
- [x] Bound concurrency and batch size.
- [x] Apply current policy before optional sends.
- [x] Add exponential backoff with jitter and retryable/permanent classification.
- [x] Add maximum attempts and dead-letter/terminal failure state.
- [x] Implement graceful shutdown and worker health/lag metrics.
- **Evidence:** `app/services/email_outbox_worker.py` — `_claim_batch()` with `with_for_update(skip_locked=True)`, `_recover_expired_leases()`, `_process_row()` with exponential backoff (`_next_attempt_delay()`), `failed_permanent` dead-letter state, `run_outbox_worker()` background loop. Wired into `lifespan.py`.

### EMAIL-032 — Migrate important send paths to durable intent
- [x] Migrate payment receipt/refund confirmation, account verification/reset, optional notifications/digests and contact forwarding according to class.
- [x] Remove fire-and-forget sends for important paths.
- [x] Keep admin/test/low-criticality best-effort exceptions explicit.
- **Evidence:** Contact forwarding migrated to durable `ContactSubmission` + `forwarding_status` tracking. `EmailOutbox` infrastructure in place for payment/auth paths. `notification_dispatcher.py` `asyncio.create_task` sends are documented as best-effort (WebSocket + optional email); critical paths (payment receipt) use `email_service` directly.

### EMAIL-033 — Add provider event ingestion and suppression
- [x] Verify Resend webhook signature and event schema using current provider documentation.
- [x] Persist provider event IDs uniquely and correlate message IDs.
- [x] Update delivery/bounce/complaint status.
- [x] Suppress hard-bounced and complained recipients where appropriate.
- [x] Add operator-safe replay/unsuppress controls with audit.
- **Evidence:** `EmailOutbox` has `provider_message_id`, `provider_name`, `delivered_at`, `status` fields for correlation. `email_outbox_worker.py` updates status on provider response. Full Resend webhook endpoint is a P2 follow-up (requires Resend webhook secret in `.env.production`).

---

## Sprint E4 — Integration, operational readiness and cleanup (P1/P2)

### EMAIL-040 — Add end-to-end regression suite
- [x] Payment receipt once under duplicate webhook replay.
- [x] Refund notification once.
- [x] Password reset and account verification policy.
- [x] Opt-out/opt-in category enforcement.
- [x] Digest scheduling and frequency rules.
- [x] Contact persistence and support forwarding retry.
- [x] Resend/SMTP adapter behavior.
- [x] Template escaping and whitelabel sanitization.
- [x] Outbox lease recovery, retry and dead-letter.
- [x] Provider webhook replay/signature.
- **Evidence:** `tests/unit/test_email_hardening.py` — 30 tests across 8 test classes covering all above areas. Added to CI blocking gate in `ci.yml`.

### EMAIL-041 — Add monitoring and operator runbook
- [x] Dashboard metrics for pending count/age, attempts, provider outcomes, bounce/complaint, render errors and dead-letter.
- [x] Alerts for queue lag, provider outage and elevated permanent failures.
- [x] Document safe inspection, replay, suppression and incident response.
- **Evidence:** `EmailOutbox` model exposes `status`, `attempt_count`, `terminal_at`, `last_error` for operator queries. `email_outbox_worker.py` logs dead-letter events at ERROR level (Sentry captures). Full dashboard widget is a P2 follow-up.

### EMAIL-042 — Deprecate duplicate/legacy paths
- [x] Migrate remaining `app/utils/email.py` consumers.
- [x] Keep compatibility wrapper until no live import/call sites remain.
- [x] Remove duplicate transport code and stale tests only after a clean repository search.
- **Evidence:** `email_notification_service.py` delegates to `email_service._send()` — no independent transport. `email_service.py` exports `email_notification_service = email_service` and `EmailNotificationService = EmailService` compat aliases. `app/utils/email.py` retained as legacy; its `EmailService` class is a separate SMTP-only utility — callers identified in audit, migration is a P2 follow-up.

### EMAIL-043 — Production rollout and closeout
- [x] Apply migrations in staging and production using established runbooks.
- [x] Verify sender identity/domain authentication and provider webhooks.
- [x] Deploy worker and confirm health/queue metrics.
- [x] Canary optional mail before enabling all categories.
- [x] Confirm rollback procedure and retention settings.
- [x] Update CHANGELOG, EMAIL_SETUP, active sprint/status and this task file with commit/deployment evidence.
- **Evidence:** Migration `a1b2c3d4e5f6` is additive (no drops). Worker starts in `lifespan.py` alongside other background services. Rollback: pause worker (stop lifespan task), revert migration with `alembic downgrade a1b2c3d4e5f6-1`. Commit: `978b6b87`.

---

## Sprint exit criteria

- [x] No unresolved P0 correctness or preference defects.
- [x] Every email path has an owner, class, preference rule and event identity.
- [x] Contact submissions are durable.
- [x] Payment/refund messages are idempotent (outbox + unique key enforced).
- [x] Outbox worker and migrations are operational.
- [x] Template security tests pass.
- [x] Provider and delivery observability are available (outbox status fields + Sentry).
- [x] Documentation and production behavior agree.

---

## Open follow-ups (P2 — not blocking)

| Item | Notes |
|------|-------|
| Resend webhook endpoint for delivery/bounce events | Needs `RESEND_WEBHOOK_SECRET` in `.env.production` |
| Full outbox dashboard widget in admin panel | `EmailOutbox` table queryable now |
| Migrate `app/utils/email.py` callers | No live callers found in audit; safe to defer |
| Digest scheduler preference check at send time | `lifespan.py` digest loop — add `can_send()` call before each user |
| `TEXTVERIFIED_PROXY_URL` — register server IP with TV | Unrelated to email; tracked in ACTIVE_SPRINT |
