# Email System Hardening — Implementation Tasks

**Status:** All tasks are planned; none are marked complete by this documentation commit.  
**Execution approach:** deliver in ordered, reviewable increments. Update this file as implementation proceeds and link commits/tests/deployment evidence.

## Sprint E0 — Complete inventory and decisions (P0)

### EMAIL-001 — Exhaustive email call-site inventory
- [ ] Search imports and calls for `EmailService`, `email_service`, `EmailNotificationService`, `email_notification_service`, `send_email`, `smtplib`, `resend`, `asyncio.create_task`, FastAPI background tasks and scheduler entry points.
- [ ] Include auth, password reset, verification, payment, refund, low balance, tier, daily/weekly digest, forwarding, contact, admin/alerting, whitelabel test-send and CLI/scripts.
- [ ] Record caller, recipient source, message class, preference policy, event identity, current delivery mechanism and tests.
- **Acceptance:** inventory covers all repository matches; every unresolved path is explicitly marked for follow-up.

### EMAIL-002 — Confirm configuration and provider semantics
- [ ] Inspect all settings aliases and environment examples for `FROM_EMAIL_ADDRESS`, `FROM_EMAIL`, SMTP username and Resend configuration.
- [ ] Confirm whether provider failure causes fallback or only startup-time provider selection.
- [ ] Confirm production sender/domain verification without copying secret values.
- **Acceptance:** one documented canonical sender rule; tests assert selected sender and provider behavior.

### EMAIL-003 — Trace payment/refund receipt ownership
- [ ] Trace webhook, verify endpoint, payment service, crediting service, refund service and callback call graphs.
- [ ] Identify exact settled event and unique payment/refund identifiers.
- [ ] Choose one receipt/refund-notice enqueue owner.
- **Acceptance:** a replayed webhook/verification request results in one logical receipt intent; no unsupported claim of existing duplication remains.

## Sprint E1 — Correctness, consent and contact intake (P0)

### EMAIL-010 — Introduce explicit email message classes
- [ ] Define stable classes: account/security, transactional-essential, optional-product, user-configured-forwarding, operational-admin and user-initiated-test.
- [ ] Map every existing template and caller to one class.
- [ ] Separate security verification token mail from routine verification progress/reminders.
- **Acceptance:** every send request has a class; class policy is covered by tests and documentation.

### EMAIL-011 — Centralize optional-email preference evaluation
- [ ] Implement a single policy service using category `enabled`, normalized `delivery_methods`, frequency, quiet hours where applicable, global opt-out and bounce/complaint suppression.
- [ ] Define default behavior when a preference row is missing.
- [ ] Reconcile legacy `NotificationSettings.email_on_sms` and `email_on_low_balance` with category preferences.
- [ ] Fix GET's unconditional `email_notifications_enabled: True` response.
- [ ] Fix PUT so the category enabled flag and email delivery method cannot disagree; validate supported category values.
- [ ] Ensure digest scheduler and dispatcher check policy both at enqueue and immediately before send.
- **Acceptance:** opted-out optional mail causes zero provider calls; opted-in permitted mail produces one logical send; a queued message suppressed after opt-out is not sent; transactional/security mail follows its distinct policy.

### EMAIL-012 — Make contact submissions durable
- [ ] Add a contact submission model and migration, or use an existing support-ticket model if suitable.
- [ ] Persist validated form data before acknowledging success.
- [ ] Enqueue support forwarding with a stable submission-based key.
- [ ] Replace incompatible `send_email(..., html_content=...)` usage with the canonical contract.
- [ ] Escape submitted name, subject, category and message; rate-limit and add abuse controls.
- **Acceptance:** database persistence succeeds even if provider is down; API does not claim that support email was delivered; forwarding failure remains visible and retryable; tests verify stored content and exact provider payload.

### EMAIL-013 — Correct message footer and unsubscribe semantics
- [ ] Remove generic opt-out wording/links from account-security and transaction-essential templates where misleading.
- [ ] Add public signed/expiring unsubscribe links for optional categories with safe replay handling.
- [ ] Ensure unsubscribe works while logged out and updates the same authoritative preference record.
- [ ] Add List-Unsubscribe headers where appropriate and provider/client requirements are verified.
- **Acceptance:** optional mail can be unsubscribed without login; security/reset mail is not represented as marketing; tests prove correct category-only and global optional suppression.

## Sprint E2 — Canonical sender and template safety (P1)

### EMAIL-020 — Formalize canonical email facade and provider adapters
- [ ] Define typed message and provider result contracts.
- [ ] Keep Resend and SMTP implementations behind adapters.
- [ ] Add explicit timeouts and normalized error categories.
- [ ] Determine and test fallback policy; do not call startup selection “failover.”
- [ ] Route compatibility wrappers through the facade.
- **Acceptance:** all production sends use the canonical interface; adapter tests cover success, timeout, authentication, rate limit and provider server error.

### EMAIL-021 — Standardize From/Reply-To configuration
- [ ] Add/normalize transactional and notification sender settings with backwards-compatible aliases.
- [ ] Validate address and verified domain expectations at startup/readiness.
- [ ] Configure support and admin destinations independently.
- [ ] Update `EMAIL_SETUP.md` only after implementation and production configuration are verified.
- **Acceptance:** no sender path derives From from SMTP login unless explicitly configured; tests cover Resend and SMTP sender headers.

### EMAIL-022 — Harden template rendering
- [ ] Enumerate all 18 existing template definitions and callers; record exact template names and variable schemas.
- [ ] Use Jinja autoescape for HTML and a separate text renderer.
- [ ] Validate variables in subject, HTML and text.
- [ ] Validate application-generated URLs against trusted HTTPS hosts.
- [ ] Sanitize whitelabel-authored HTML under an explicit allowlist/trust model.
- [ ] Replace regex-only HTML-to-text conversion.
- [ ] Add rendering tests for HTML injection, attribute injection, unsafe URL schemes, missing variables and header injection.
- **Acceptance:** untrusted text is rendered as text; unsafe links/markup are rejected or neutralized; HTML and text alternatives are generated consistently.

### EMAIL-023 — Preserve and improve template management
- [ ] Preserve version history, template ownership and analytics.
- [ ] Ensure preview and test-send use the same renderer as production.
- [ ] Restrict test-send recipients and audit preview/test actions.
- [ ] Add template status/version metadata and fallback behavior.
- **Acceptance:** template edits remain versioned; rollback to prior version works; invalid template cannot be activated.

## Sprint E3 — Durable delivery and event integrity (P1)

### EMAIL-030 — Add email outbox and migration
- [ ] Design outbox fields, indexes, uniqueness and retention.
- [ ] Add additive database migration.
- [ ] Write outbox intent in the same transaction as business events wherever possible.
- [ ] Add contact forwarding intent to the same durable mechanism.
- **Acceptance:** business event and outbound intent commit/rollback together; duplicate event key cannot create a second logical message.

### EMAIL-031 — Implement supervised outbox worker
- [ ] Add atomic claim/lease and expired-lease recovery.
- [ ] Bound concurrency and batch size.
- [ ] Apply current policy before optional sends.
- [ ] Add exponential backoff with jitter and retryable/permanent classification.
- [ ] Add maximum attempts and dead-letter/terminal failure state.
- [ ] Implement graceful shutdown and worker health/lag metrics.
- **Acceptance:** worker survives restart, retries transient failures, stops retrying permanent failures and exposes exhausted work for operator action.

### EMAIL-032 — Migrate important send paths to durable intent
- [ ] Migrate payment receipt/refund confirmation, account verification/reset, optional notifications/digests and contact forwarding according to class.
- [ ] Remove fire-and-forget sends for important paths.
- [ ] Keep admin/test/low-criticality best-effort exceptions explicit.
- **Acceptance:** process restart after enqueue does not lose pending intent; tests verify all migrated paths and exact logical send counts.

### EMAIL-033 — Add provider event ingestion and suppression
- [ ] Verify Resend webhook signature and event schema using current provider documentation.
- [ ] Persist provider event IDs uniquely and correlate message IDs.
- [ ] Update delivery/bounce/complaint status.
- [ ] Suppress hard-bounced and complained recipients where appropriate.
- [ ] Add operator-safe replay/unsuppress controls with audit.
- **Acceptance:** duplicate webhook is harmless; invalid signature is rejected; bounce/complaint changes future optional send eligibility.

## Sprint E4 — Integration, operational readiness and cleanup (P1/P2)

### EMAIL-040 — Add end-to-end regression suite
- [ ] Payment receipt once under duplicate webhook replay.
- [ ] Refund notification once.
- [ ] Password reset and account verification policy.
- [ ] Opt-out/opt-in category enforcement.
- [ ] Digest scheduling and frequency rules.
- [ ] Contact persistence and support forwarding retry.
- [ ] Resend/SMTP adapter behavior.
- [ ] Template escaping and whitelabel sanitization.
- [ ] Outbox lease recovery, retry and dead-letter.
- [ ] Provider webhook replay/signature.
- **Acceptance:** deterministic tests fail on regression and assert exact expected provider call counts/status transitions.

### EMAIL-041 — Add monitoring and operator runbook
- [ ] Dashboard metrics for pending count/age, attempts, provider outcomes, bounce/complaint, render errors and dead-letter.
- [ ] Alerts for queue lag, provider outage and elevated permanent failures.
- [ ] Document safe inspection, replay, suppression and incident response.
- **Acceptance:** an operator can identify and recover failed mail without database ad hoc edits or secret exposure.

### EMAIL-042 — Deprecate duplicate/legacy paths
- [ ] Migrate remaining `app/utils/email.py` consumers.
- [ ] Keep compatibility wrapper until no live import/call sites remain.
- [ ] Remove duplicate transport code and stale tests only after a clean repository search.
- **Acceptance:** one canonical sender path; no unowned direct SMTP/Resend calls remain.

### EMAIL-043 — Production rollout and closeout
- [ ] Apply migrations in staging and production using established runbooks.
- [ ] Verify sender identity/domain authentication and provider webhooks.
- [ ] Deploy worker and confirm health/queue metrics.
- [ ] Canary optional mail before enabling all categories.
- [ ] Confirm rollback procedure and retention settings.
- [ ] Update CHANGELOG, EMAIL_SETUP, active sprint/status and this task file with commit/deployment evidence.
- **Acceptance:** production verification evidence is recorded; no task is closed solely because code was pushed.

## Sprint exit criteria

- No unresolved P0 correctness or preference defects.
- Every email path has an owner, class, preference rule and event identity.
- Contact submissions are durable.
- Payment/refund messages are idempotent.
- Outbox worker and migrations are operational.
- Template security tests pass.
- Provider and delivery observability are available.
- Documentation and production behavior agree.
