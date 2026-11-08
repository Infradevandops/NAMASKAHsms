# Email System Hardening — Target Architecture and Implementation Plan

## 1. Design principles

1. **One transport boundary:** all application-originated email is sent through one canonical facade and provider adapter interface.
2. **Separate policy from transport:** consent/category eligibility is evaluated before optional messages are created and again at dispatch time where a preference may have changed.
3. **Persist important intent:** business state and the email/outbox intent are committed together wherever they share the same database transaction.
4. **At-least-once processing, idempotent outcomes:** workers may retry; stable event keys and database uniqueness prevent duplicate logical messages. External delivery cannot be claimed to be exactly once unless the provider supplies a matching idempotency contract.
5. **Security by default:** autoescaped template values, validated links, restricted template editing, secret-safe logs and signed webhook verification.
6. **Compatibility before cleanup:** preserve old import/method signatures through adapters during migration; remove only after call-site and test evidence.
7. **No hidden success:** distinguish accepted/persisted, provider-accepted, delivered, bounced, complained, suppressed and permanently failed states.

## 2. Proposed logical architecture

```text
Business event / API / scheduler
          |
          v
Message classification + preference policy
          |
          v
Email facade (typed message intent)
          |
          +---- immediate path only for explicitly best-effort/admin diagnostics
          |
          v
Database transaction: email_outbox row + business change
          |
          v
Outbox worker (claim/lease, concurrency limit)
          |
          v
Provider adapter interface
      /             \
   Resend           SMTP
      \             /
       Provider result
          |
          v
Delivery event / status update / retry or dead-letter
```

The first implementation may use the existing relational database and a supervised worker process rather than adding Redis/Celery/RabbitMQ by default. Choose infrastructure only after inspecting current deployment, database, worker lifecycle and operational limits. Do not make a second queue dependency a prerequisite if a database-backed outbox can meet measured throughput.

## 3. Core contracts

### 3.1 Message classification

Use an explicit enum or equivalent stable values:

| Class | Examples | Preference behavior |
|---|---|---|
| `account_security` | password reset, login/security alert, email verification | Not governed by promotional opt-in. Apply security controls, token validity, abuse limits and legal requirements. |
| `transactional_essential` | payment receipt, refund confirmation, material payment failure/charge status | Not governed by marketing opt-in. Send only for a real business event; deduplicate by event identity. |
| `optional_product` | low-balance reminder, daily/weekly digest, routine verification progress, product tips | Require category enabled, email delivery method enabled, frequency eligibility and no applicable suppression. |
| `user_configured_forwarding` | SMS-to-email forwarding | Require explicit forwarding feature enablement and configured destination; separate from marketing preferences. |
| `operational_admin` | revenue-zero, provider outage or service alert | Use configured operational recipients and severity policy; not end-user preferences. |
| `user_initiated_test` | “send test email” action | Explicitly requested diagnostic; rate-limit and audit it. |

Do not label routine verification progress “essential” merely because it mentions verification. A verification token that is required to activate or secure an account is account/security; a progress update or reminder is optional product notification.

### 3.2 Preference policy

Create one policy service, e.g. `EmailPreferencePolicy`, that accepts user, category, delivery mode and message class.

For `optional_product`, the default allow rule must be explicit and testable:

- category preference row/default exists;
- `enabled is True`;
- `email` is present in normalized `delivery_methods`;
- `frequency` permits this delivery (instant/daily/weekly/never);
- no global unsubscribe, hard-bounce suppression, complaint suppression or account-level suppression applies;
- quiet hours are honored where the product promises them.

Resolve legacy `NotificationSettings.email_on_sms` and `email_on_low_balance` fields. Recommended migration: define a single precedence rule, migrate existing values into category preferences, then stop reading legacy flags after compatibility period. Do not silently let one model override the other.

Preference changes must be effective at dispatch time for optional mail. A queued optional message that becomes disallowed before dispatch should transition to `suppressed`, not be sent.

### 3.3 Outbox record

Use a dedicated model/table (name to align with current naming conventions, e.g. `EmailOutbox`) with at least:

- stable primary ID;
- unique `idempotency_key` / logical event key;
- message class, category and template key/version;
- recipient (protected as personal data; minimize access and retention);
- structured template payload or secure reference to payload;
- provider preference/selection metadata (never credentials);
- status: `pending`, `processing`, `provider_accepted`, `delivered`, `retry_wait`, `suppressed`, `bounced`, `complained`, `failed_permanent`;
- attempt count, next-attempt timestamp, lease owner/expiry;
- provider name and provider message ID;
- normalized last error code/class (avoid sensitive raw body);
- created, updated, accepted, delivered and terminal timestamps;
- correlation ID / source event ID.

Use a database unique constraint on the logical idempotency key. Keep payload retention and recipient data retention policy explicit. Consider encrypting sensitive payload fields at rest if the platform's existing database protection does not adequately cover them.

### 3.4 Worker behavior

- Claim a bounded batch atomically; use row locking/leases appropriate to the configured database.
- Recover expired leases after worker crash.
- Apply current optional-email policy before provider send.
- Render and validate immediately before send, using the stored template version or a deliberate version-pinning rule.
- Use stable provider idempotency keys if supported; never mint a new key per retry.
- Set finite connection/read timeouts.
- Retry network errors, rate limits and transient provider/server failures with exponential backoff plus jitter and a maximum attempt count.
- Do not retry deterministic validation, malformed address, template/schema, authentication/authorization or unverified-sender errors without a configuration change.
- Move exhausted messages to a visible terminal failure/dead-letter state and expose an operator replay path with audit.
- Acknowledge the fundamental uncertainty when a provider accepts a message but the worker times out before recording acceptance. Provider idempotency and reconciliation are needed to reduce duplicates.

### 3.5 Provider interface

Define a small provider-neutral contract such as:

- `send(message) -> ProviderSendResult`
- `ProviderSendResult(provider, accepted, provider_message_id, error_code, retryable, response_metadata)`

Implement Resend and SMTP adapters. Do not claim automatic Resend-to-SMTP failover unless the code explicitly attempts it and tests demonstrate the behavior. If failover is introduced, define which failures trigger it, how duplicate risk is controlled, and whether sender identity is valid on both providers.

### 3.6 Delivery events

Add authenticated provider webhook endpoints for supported events (delivery, bounce, complaint, rejection) only after checking current Resend event support and the existing routing/security conventions.

- Verify webhook signatures using the provider's documented signing mechanism.
- Persist provider event IDs with a unique constraint to make webhook replay safe.
- Correlate provider message IDs to outbox records.
- Hard bounce and complaint events create suppression state; do not keep retrying invalid recipients.
- Separate provider acceptance from actual delivery.
- Keep webhook payloads and logs free of API keys and unnecessary personal data.

## 4. Template system and content rules

### 4.1 Keep two responsibilities, not two senders

- `email_service.py` (or a small `email/` package after migration) owns facade, message contracts and provider adapters.
- `email_template_service.py` owns whitelabel template management, versions, preview/render and analytics.
- The template service must not open SMTP/Resend connections directly.
- Legacy `utils/email.py` and notification wrappers delegate temporarily, then become deprecated once imports are migrated.

### 4.2 Rendering

- Use a configured Jinja `Environment(autoescape=select_autoescape(["html", "xml"]))` for HTML and a deliberate text environment for plain text.
- Validate variables in subject, HTML and text against a typed per-template schema.
- Use explicit safe URL builders for reset, verification, dashboard, support and top-up links. Permit only approved schemes (normally HTTPS) and trusted hosts for application-generated links.
- Never mark user-provided strings as safe HTML.
- If whitelabel customers can author HTML, sanitize allowed tags/attributes and prohibit scripts, event handlers, unsafe URL schemes, remote form actions and other active content according to the product's threat model.
- Generate plain text using a real HTML parser/converter, not a regex that strips tags.
- Validate subject length, control characters and header injection.
- Preview and test-send should use the same renderer as production, with safe test-recipient restrictions and audit records.

### 4.3 Layout and content consistency

Retain the existing Vrenum pink branded layout unless design review finds a concrete accessibility or deliverability issue. Standardize:

- responsive, table-based email layout;
- text alternative for every HTML message;
- meaningful subject and preheader;
- accessible CTA contrast and descriptive links;
- support and privacy links;
- locale/currency/date formatting;
- template version and content owner;
- correct legal/footer text by message class.

Do not put a generic “unsubscribe from all email” statement on password-reset, account-verification or transaction-essential templates. Optional notification mail should expose a working preference/unsubscribe route. Provide public, signed, expiring unsubscribe tokens for one-click optional-category opt-out where required; do not require an authenticated session for a recipient to exercise a valid unsubscribe link.

## 5. Sender identity and configuration

Inspect `app/core/config.py` and standardize canonical configuration fields. Recommended logical values:

- `TRANSACTIONAL_FROM_EMAIL`
- `NOTIFICATION_FROM_EMAIL`
- `SUPPORT_EMAIL`
- `ADMIN_NOTIFY_EMAIL`
- `RESEND_API_KEY`
- SMTP host, port, username and password

A backward-compatible migration may map the existing `FROM_EMAIL_ADDRESS` to `TRANSACTIONAL_FROM_EMAIL` and use it as the initial default for notification mail. Keep a display name separately. Validate email addresses at startup and fail health/readiness checks for invalid production configuration without logging secrets. Keep reply-to distinct from From identity.

Do not update the runbook's “Resend is already live” or sending-address assertions without production verification.

## 6. Contact form design

1. Validate and rate-limit request.
2. Create a durable `ContactSubmission` record with submitted fields, status and timestamps.
3. In the same transaction, create a support-forwarding outbox item keyed by submission ID.
4. Return success only after the transaction commits.
5. Worker sends to configured support destination using escaped/rendered content.
6. Record delivery state and expose an authorized support/admin review and replay path.
7. Apply spam/abuse controls, retention limits and access restrictions to personal data.

If adding a full ticketing workflow is out of scope, a durable submission table plus operator-visible admin query is the minimum acceptable persistence behavior.

## 7. Payment and refund ownership

Trace the complete successful payment path before changing it. The final design must have one business event owner enqueue one receipt for one settled payment reference. Use a unique key such as `payment-receipt:{provider}:{payment_reference}`. The payment webhook must remain idempotent independently of email.

Refund confirmation should similarly key from refund ID/reference. Failed payment notifications should be sent only for a final meaningful failure, not every transient retry or intermediate provider callback.

## 8. Migration sequence and compatibility

1. Inventory all imports, direct SMTP calls, `asyncio.create_task`, `BackgroundTasks`, scheduler loops, test patches and templates.
2. Add message classification, preference policy and typed facade contracts with tests; do not yet remove wrappers.
3. Add outbox/contact persistence models and migrations. Confirm database migration tooling, naming and rollback conventions.
4. Implement provider adapters and worker with bounded concurrency, leases, retries and observability.
5. Migrate contact, payment, auth, refund, notification, digest, forwarding and admin alert call sites in isolated groups.
6. Harden whitelabel rendering and template schemas while preserving template version history.
7. Add provider webhooks/suppression only after signature verification and event mapping are tested.
8. Run migration on staging, backfill/normalize preferences, verify sender identity and execute end-to-end tests.
9. Deploy worker and API in a compatible order; observe queue lag and failure rates before enabling all mail classes.
10. Remove deprecated helper imports only after repository search is clean and compatibility tests are removed intentionally.

## 9. Operational metrics and alerts

Track at minimum:

- pending outbox count and oldest pending age;
- processing lease expirations;
- attempts and retry distribution;
- provider acceptance rate by provider and message class;
- delivered, bounced, complained, suppressed and permanent-failure counts;
- provider latency and timeout/error classes;
- digest enqueue/send counts;
- contact submission forwarding lag;
- duplicate idempotency-key conflicts;
- template render/validation failures.

Alert on sustained queue age, provider outage, bounce/complaint threshold, dead-letter growth and configuration failure. Do not expose recipient email addresses in metric labels.

## 10. Rollback and safety

- Feature-flag outbox dispatch per message class.
- Keep old facade methods delegating to the new implementation during rollout.
- Do not drop legacy preference columns/tables in the first migration.
- Keep migrations additive until backfill and rollback strategy are verified.
- Pause the worker rather than deleting pending rows during an incident.
- Replays require an operator action, a reason and a stable original idempotency key unless a deliberate new logical send is intended.
- Never log tokens, full reset URLs, API keys or full rendered email bodies.
