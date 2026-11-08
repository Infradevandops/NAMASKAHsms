# Repository Email Audit

**Reviewed:** 9 November 2026  
**Baseline:** `main`, observed commit `e5c20f1ad8722fbfa986df0f2ef154d285cd9bc1`  
**Method:** GitHub code search plus direct reads of the service, endpoint, model, configuration, operations and documentation files listed below. This is a repository snapshot review, not a claim that every dynamic import or indirect call site has been exhausted.

## Executive finding

The repository has already moved further toward consolidation than an older description suggests: the current `email_service.py` contains notification methods and exports compatibility aliases:

- `email_service = EmailService()`
- `email_notification_service = email_service`
- `EmailNotificationService = EmailService`

The changelog also records that `email_notification_service.py` was merged into `email_service.py` and retained as a compatibility wrapper. Therefore, the immediate problem is not simply “four equal senders.” It is **one emerging transport service with multiple legacy entry points, plus a separate whitelabel template subsystem and a lightweight utility whose consumers must be migrated deliberately**.

The highest-risk confirmed defects are contact-form delivery acknowledgement without durable persistence or verified delivery, preference API inconsistency, incorrect/ambiguous sender configuration, and unsafe template rendering boundaries. Background scheduling is currently in-process and non-durable.

## 1. Current components and responsibilities

| Path | Current responsibility | Audit interpretation |
|---|---|---|
| `app/services/email_service.py` | Resend-first/SMTP-mode transport, transactional templates and notification email methods | Canonical sender candidate. It catches provider exceptions and returns `False`; no durable delivery ledger is visible in the inspected implementation. |
| `app/services/email_notification_service.py` | Compatibility/delegation layer for notification-oriented calls | Consolidation is recorded in the changelog; retain compatibility while callers and tests are migrated. Do not instantiate as if it owns an independent provider. |
| `app/services/email_template_service.py` | Whitelabel template CRUD, version history, default templates, rendering and analytics counters | Separate product feature, not a transport. Keep its domain responsibility but route final sends through the canonical sender. |
| `app/utils/email.py` | Lightweight SMTP/template helper | Legacy/secondary transport path. Inventory imports and migrate callers before deprecation/removal. |
| `app/services/notification_service.py` | In-app notification creation and an email method | Another potential outbound boundary. Decide whether it becomes notification orchestration only or delegates through the canonical email facade. |
| `app/services/notification_dispatcher.py` | WebSocket broadcast plus optional email fan-out | Current best-effort email dispatch uses `asyncio.create_task`; policy enforcement must be centralized before enqueue/send. |
| `app/api/notifications/email_endpoints.py` | Test email, preferences, authenticated unsubscribe | API currently exposes preference state that is not fully authoritative. |
| `app/api/core/contact.py` | Contact form submission and attempted support forwarding | Confirmed false-success risk; it logs and acknowledges even when forwarding raises. No persistence is performed in the inspected endpoint. |
| `app/api/core/forwarding.py` | SMS-to-email forwarding | Separate user-configured feature. Must retain its own enablement/address semantics and use the canonical transport. |
| `app/core/config.py` | Resend, SMTP and sender/support/admin configuration | Configuration source of truth; runtime sender selection must match documented variables. |
| `app/models/notification_preference.py` | Per-category enabled flag, delivery methods and frequency | Existing preference model supports a policy; no new parallel global toggle should be added without a schema review. |
| `app/models/user.py` | User relationship and legacy `NotificationSettings` model | Contains separate legacy `email_on_sms` and `email_on_low_balance` settings. Reconcile with category preferences rather than silently ignoring either. |
| `docs/operations/EMAIL_SETUP.md` | Resend/SMTP setup and operational guidance | Useful setup guide, but its sender claims need reconciliation with actual code. |

## 2. Confirmed code-level observations

### 2.1 Canonical sender and provider behavior

In `app/services/email_service.py`:

- Resend is selected when `RESEND_API_KEY` is configured; otherwise SMTP is selected when host, username and password exist.
- The SMTP path sends through `smtplib.SMTP` with STARTTLS and login.
- Resend is invoked through an executor.
- `_send()` catches broad exceptions, logs an error and returns `False`.
- The inspected implementation does not expose a provider-neutral result object with provider message ID, categorized failure, retryability or delivery state.
- The sender is initialized as `settings.smtp_username or "onboarding@resend.dev"`. The operations guide says `FROM_EMAIL_ADDRESS` controls the visible From address. These two sources are inconsistent and must be reconciled against the actual settings model and production environment.
- The current class docstring says Resend preferred and SMTP fallback, but the initialization logic chooses one mode; the inspected path does not demonstrate a Resend attempt followed by SMTP fallback after a Resend send failure. Document the behavior accurately and add an explicit failover policy only if operationally desired and safe.

**Required verification:** inspect all fields/aliases in `app/core/config.py`, environment variable aliases and deployed configuration names. Never print secret values in logs or docs.

### 2.2 Contact form: false acknowledgement

`app/api/core/contact.py` calls:

- `email_service.send_email(..., html_content=...)`

The inspected central service exposes `_send()`, `_send_email()` and named methods; the displayed public interface does not show a compatible `send_email(to_email, subject, html_content=...)` method. The endpoint catches any forwarding error, logs a warning and still returns:

- `status: success`
- “Message received. We'll respond within 24 hours.”

The submission is not persisted in the inspected endpoint. This means a user can receive success even though support never receives the message and the content cannot be recovered from an application record.

**Required correction:** persist a contact submission first (or atomically with an outbox record), return an acknowledgement only after durable persistence, and make support forwarding a retryable downstream action. Escape all user-provided fields in HTML or use a safe template renderer. Add rate limiting, abuse controls and retention policy.

### 2.3 Preferences: API state and delivery policy are not aligned

`app/api/notifications/email_endpoints.py`:

- GET builds category values from `NotificationPreference.enabled`, `delivery_methods` and `frequency`, but returns `email_notifications_enabled: True` unconditionally.
- PUT changes the comma-separated `delivery_methods` value but does not change the category's `enabled` flag.
- The endpoint returns 404 when a category preference row does not exist rather than applying a documented default or creating the preference.
- The authenticated unsubscribe endpoint modifies preferences, but the visible template links and authentication requirements need an end-to-end review.
- The test-email route uses the notification service and is an explicit user-initiated diagnostic; it should not be treated as an ordinary digest or marketing notification.

The model's intended policy fields are clear: `enabled`, `delivery_methods`, and `frequency`. The separate legacy `NotificationSettings` fields (`email_on_sms`, `email_on_low_balance`) create a second policy source that needs a migration/precedence decision.

**Required correction:** one policy evaluator must decide whether an optional category can be sent. At minimum, category enabled must be true, email must be in delivery methods, frequency must permit the requested delivery mode, and global/account suppression must not apply. Resolve defaults explicitly. Do not apply optional-notification opt-outs to password resets or mandatory security/account notices.

### 2.4 Notification and digest delivery are process-local

`app/services/notification_dispatcher.py` sends email using `asyncio.create_task` after snapshotting values from the SQLAlchemy objects. The snapshot addresses a detached-instance problem, but it does not make the task durable. A process restart, shutdown or unhandled task failure can lose the send.

The digest scheduler is started from `app/core/lifespan.py` with in-process loops and `asyncio.create_task`. It selects users and unread notifications, then calls daily/weekly digest methods. In the inspected scheduler excerpt, the user selection and send loop do not apply the category email preference before sending.

**Required correction:** persist notification intent and use a supervised worker/outbox. Ensure digest selection and send-time authorization both evaluate current preferences to avoid stale consent snapshots.

### 2.5 Whitelabel template renderer: escaping and validation gaps

`app/services/email_template_service.py`:

- Uses Jinja-like `{{ variable }}` syntax but imports `jinja2.Template`, which does not enable autoescaping by default.
- Validates only variable names found in the HTML content using a regular expression. Subject and text content are not equivalently validated in the inspected method.
- Variable declarations are broad strings; URL variables such as `top_up_url` and `reset_link` need scheme/host allowlisting and context-aware rendering.
- Template HTML is stored as user-editable content. Variable escaping alone does not make arbitrary merchant-supplied HTML safe; restrict editing capability and sanitize/validate HTML according to the product's trust model.
- Text conversion strips tags with a regex, which is not a robust HTML-to-text conversion.
- The service tracks template versions and analytics, which are valuable and should be preserved.

**Required correction:** use an autoescaping Jinja environment for HTML templates, explicit plain-text rendering, schema validation for subject/HTML/text variables, safe URL helpers, HTML sanitization/allowlisting for user-authored template markup, and tests for hostile input.

### 2.6 Transactional template content and classification

The central service contains custom HTML for verification, password reset, payment receipt, failed payment and refund messages, plus notification/digest templates. The code includes a shared notification wrapper and an unsubscribe/footer helper.

The audit found a policy mismatch: the shared unsubscribe footer helper is inserted into account/security and payment-oriented templates as well as optional notification content. This risks implying that security and transaction-essential mail can be unsubscribed from in the same way as optional notifications. The footer and public unsubscribe route must distinguish message classes.

Several HTML templates interpolate dynamic values directly into strings. Receipt fields such as reference and timestamps, user names, failure reasons, notification title/message/link and forwarding content must be treated as untrusted. Escape text values and validate links before interpolation.

### 2.7 Payment receipt ownership and idempotency

Payment-related sends appear in both webhook/endpoint code and payment-service code in search results. The repository also contains payment idempotency logic, but that does not prove receipt delivery itself is deduplicated.

The previous review's “duplicate receipt” hypothesis must be verified against the complete current webhook and crediting call graph before changing ownership. It is not recorded here as a proven duplicate. Trace every successful-payment path, including webhook replay, verification endpoint, credit service and any callback, then nominate exactly one owner to enqueue the receipt with a stable key derived from the payment reference.

**Required correction:** one receipt event per settled payment reference, enforced with a unique database constraint and replay tests. Do not rely on a process-local boolean or random idempotency key.

### 2.8 Forwarding and other integrations

SMS-to-email forwarding is a distinct user-configured delivery feature, not a marketing subscription. It must check that forwarding is enabled and that the configured destination is valid, then delegate transport to the canonical sender. Review `app/api/core/forwarding.py` and all settings/recipient storage before implementation.

Alerting/admin emails also have distinct recipient and severity semantics. They should share transport and observability, but not inherit end-user notification preferences.

## 3. Template catalogue observed

The changelog records 18 templates across three layers: 7 transactional templates in `email_service.py`, 6 notification templates consolidated into `email_service.py`, and 7 whitelabel template types in `email_template_service.py`.

The whitelabel types explicitly declared in code are:

1. `welcome`
2. `verification_code`
3. `payment_success`
4. `payment_failed`
5. `low_balance`
6. `tier_upgrade`
7. `password_reset`

The exact current names and methods for all 7 transactional and 6 notification templates must be extracted from the complete service and captured in [TEMPLATE_CATALOG.md](./TEMPLATE_CATALOG.md) during implementation. Do not infer template names from a changelog count.

## 4. Tests and coverage concerns

Relevant existing test files found by code search include:

- `tests/unit/test_email_service.py`
- `tests/unit/test_email_notification_service.py`
- `tests/unit/test_email_notifications.py`
- `tests/unit/test_email_templates.py`

The current test surface should be reviewed before rewriting. The implementation must add strict assertions for provider calls, policy decisions, exact send counts, persisted contact submissions, duplicate payment event replay, safe rendering, and retry state. Tests that accept either `True` or `False`, or tolerate missing endpoint routes without asserting expected behavior, are not sufficient release evidence.

## 5. Files inspected / search targets to complete

Directly inspected during this documentation pass:

- `app/services/email_service.py`
- `app/services/email_template_service.py`
- `app/api/notifications/email_endpoints.py`
- `app/api/core/contact.py`
- `app/services/notification_dispatcher.py`
- `app/models/notification_preference.py`
- `app/models/user.py`
- `app/core/lifespan.py`
- `docs/operations/EMAIL_SETUP.md`
- `docs/INDEX.md`

Search results also identified:

- `app/services/email_notification_service.py`
- `app/utils/email.py`
- `app/services/notification_service.py`
- `app/api/core/forwarding.py`
- `app/api/billing/payment_endpoints.py`
- `app/services/payment_service.py`
- `app/services/refund_service.py`
- `app/api/auth_routes.py`
- `app/api/verification/purchase_endpoints.py`
- `app/core/config.py`
- `app/models/whitelabel_models.py`
- `templates/email_templates.html`

Complete a repository-wide import/call-site inventory before deleting or deprecating any path.
