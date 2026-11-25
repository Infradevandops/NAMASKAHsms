# Verification Flow Handover

**Reviewed:** November 25, 2026
**Scope:** Customer SMS, voice, and combined verification; provider routing; billing/refunds; WebSocket and notification delivery.
**State:** Static review and focused local tests completed. No live provider path was available or exercised.

## Executive summary

The app has the core pieces for verification, but the end-to-end contract is not yet consistent across SMS, voice, combined capability, and providers. The main customer SMS page uses SSE for purchase, HTTP status polling, provider polling in a background task, and an authenticated WebSocket for immediate delivery. The voice page uses a separate legacy JSON purchase flow, fixed five-minute UI timeout, and HTTP polling. Provider selection exists, but purchase-time pricing/availability is checked against TextVerified before routing, which can prevent non-TV providers from serving countries or services they support.

Several confirmed defects were fixed in the current local working tree: orphan purchase timestamps, missing orphan UI recovery, webhook completion bookkeeping/notification parity, local-expiry UI behavior, expired-state refunds, naive/aware timestamp arithmetic, sensitive SMS-code logging, and fire-and-forget telemetry writes that could be dropped. These code changes have not been committed or deployed as part of this handover. Existing unrelated working-tree changes were present; stage only the intended files when preparing any code release.

## What was checked

### SMS customer flow

1. `static/js/verification-flow.js` submits `POST /api/verification/request/stream`.
2. The SSE handler checks availability/pricing, balance, and asks `ProviderRouter` to purchase with a 12-second ceiling.
3. On success it creates a `Verification`, debits wallet credits and writes ledger transactions, commits, then starts `SMSPollingService`.
4. The UI displays the assigned number and polls `/api/verification/status/{id}`. The backend polls TextVerified through `sms.incoming()` for TV activations; other providers use their adapter message-check path.
5. Delivery can also arrive from the TV webhook. The authenticated notification socket sends an `sms_received` payload; polling can still surface the stored code if the socket is unavailable.
6. Timeout handling attempts a customer wallet refund and then provider recovery (reactivation where available, otherwise report when allowed). Refunds are tracked in the verification and transaction records.

### Voice and combined capability

- The voice UI is in `templates/voice_verify_modern.html`. It purchases through the JSON request endpoint, uses `capability: "voice"`, and polls status every five seconds.
- The voice UI hardcodes a 300-second timeout rather than following provider `ends_at`. Its timeout posts an outcome asynchronously and immediately displays an error; it does not wait for the backend's terminal state/refund result.
- The voice UI does not use the same SSE purchase/resume or explicit WebSocket delivery handler as the main SMS flow.
- The request schema accepts `sms`, `voice`, and `sms_and_voice`; the public API draft says `combo`. Pricing also has a `sms_and_voice` surcharge. A complete combined-channel lifecycle was not demonstrated.

### Providers, money, and notifications

- `ProviderRouter` has TextVerified, 5sim, Telnyx, and PVAPins adapters and scores/filters providers based on country, tier, health, and coverage.
- The request endpoints run a TextVerified availability/price gate before the router, so the router cannot reliably choose an alternate provider when TV lacks the requested country/service. Country and capability coverage need to be evaluated before provider-specific pricing.
- Purchase debit paths write wallet balance and ledger rows; admin and regular-user paths differ and both need transaction-level tests.
- SMS polling's shared completion routine updates completion flags, forwards messages, and dispatches notifications. TV webhook completion previously skipped this common path; the current local change routes webhook completion through it.
- The WebSocket manager keeps connections in process memory. Multi-worker deployment can lose pushes when the worker handling an event differs from the worker holding the user's connection.
- Notification/email/push behavior is best-effort in parts of the code. A persisted notification, WebSocket receipt, email, OneSignal push, and Telegram forwarding are separate outcomes and should be observed independently.

## Confirmed local fixes and validation

Changes made in the working tree for this investigation:

- Purchase timeout now records an ISO timestamp; orphan reconciliation still accepts legacy epoch timestamps.
- The delayed-purchase WebSocket event now has a UI recovery callback that loads the healed verification and resumes the waiting screen.
- TV webhook completion now uses the shared polling completion routine, updates receipt/refund flags, and triggers the same downstream completion behavior.
- SMS content is no longer written into the stale-message warning log.
- Local UI expiry no longer tells the user “not charged” and navigates away before server confirmation. Progress follows the computed duration; `expired` is handled.
- The automatic refund service accepts `expired`, matching the status poller's possible terminal status.
- Completion latency normalizes database-naive timestamps before subtraction.
- SMS codes were removed from success event telemetry data.
- Purchase-intelligence database updates now await completion rather than spawning a coroutine that may be discarded.

Focused validation on the working tree:

| Tests/checks | Result |
|---|---:|
| `test_orphan_reconciliation.py` + `test_tv_webhook.py` | 21 passed |
| `test_sms_polling.py` | 5 passed, 1 skipped |
| `test_auto_refund_service.py` | 1 passed |
| Python compilation, JavaScript syntax, `git diff --check` | Passed |

The timeout test had previously emitted a `PurchaseIntelligenceService.update_sms_received` un-awaited coroutine warning. The awaited telemetry write removed that warning in the isolated timeout/refund test. The complete repository suite has not been rerun to completion.

## Highest-priority work to straighten the flow

### P0 — Make provider choice and price one coherent operation

1. Move availability/pricing behind provider selection. Query candidates for `(country, service, capability)`, remove providers without coverage/inventory, then compare normalized prices and health.
2. Fix the healthy-US shortcut so it cannot return a disabled or incapable TextVerified adapter.
3. Return a normalized quote carrying provider, price, currency, expiry, capability, and quote timestamp. Revalidate/hold inventory where provider APIs permit, then debit only after purchase outcome is known.
4. Do not retry a purchase after ambiguous timeout. Reconcile idempotently; if the provider purchase cannot be identified, escalate instead of silently deleting the pending record.
5. Add route tests for US/TextVerified, Ghana/alternate provider, unsupported country, provider disabled, insufficient provider balance, capability mismatch, and failover on infrastructure errors only.

### P0 — Define one transaction and terminal-state model

1. Define allowed transitions, e.g. `created -> pending -> completed | failed | cancelled | expired`; include `transcribing` only as a documented nonterminal state.
2. Treat provider terminal status, customer credit refund, provider recoup, and notifications as separate but correlated outcomes.
3. Make debit/refund idempotent under duplicate HTTP requests, repeated webhooks, concurrent polling, cancellation, and worker restart. Use a single database transaction/conditional transition and unique ledger references.
4. Normalize `expired`, `timeout`, and `failed` semantics and reason mapping so status, refund policy, support history, analytics, and UI agree.
5. Verify wallet balance, `BalanceTransaction`, legacy `Transaction`, verification cost/refund flags, and `PurchaseOutcome` for both standard users and admin accounts.

### P0 — Use one SMS/voice/combined lifecycle

1. Share purchase UI/API state handling, server-provided `ends_at`, cancellation, reconnect/resume, status polling, and terminal/refund display across SMS and voice.
2. Specify voice payload representation: parsed code versus transcription, `sms_text`, audio/transcription metadata, and UI rendering. Do not classify valid transcription-only voice completion as timeout.
3. Specify `sms_and_voice` semantics: whether either channel completes the session, how duplicate messages are deduplicated, and how the channel affects price and refunds.
4. Render provider message/code as text, not executable HTML; bind copy controls through event listeners.
5. Add UI tests for purchase success/failure/delay, SMS webhook delivery, voice transcription, combined duplicate delivery, timeout/refund, cancellation, and reload/resume.

### P1 — Reliable push and notification fanout

1. Replace or augment the in-memory WebSocket manager with Redis/pub-sub or another shared broker for multi-worker/multi-instance deployments.
2. Define stable event envelopes with `event_id`, `verification_id`, event type, status, timestamp, and safe message metadata. Document delivery as at-least-once and make clients idempotent.
3. Have all completion/refund paths emit the same notification policy. Verify persisted notification, WebSocket, email, push, and Telegram preferences separately; do not imply that a best-effort send succeeded.
4. Add reconnect handling that fetches current verification state; WebSocket delivery must not be required for correctness.
5. Test mismatched IDs, duplicate events, late SMS after refund/expiry, missing auth token, expired JWT, reconnect, and socket hosted by another worker.

### P1 — Make expiry and recovery server-authoritative

1. Persist the provider's actual `ends_at` on `Verification` and return that value. Current status polling derives expiry using a configured duration.
2. Ensure the UI never locally cancels/refunds or claims “not charged” based only on its timer. Continue status reconciliation through the server terminal transition.
3. Reconcile orphan purchases safely and visibly. Keep unresolved keys long enough for recovery; alert on expiry or unmatched provider purchases instead of silently losing financial evidence.
4. Ensure the delayed-purchase page can resume after refresh, not just while the original tab/socket remains connected.

### P2 — Contract, operations, and customer care

- Bring the public API contract in line with mounted routes. The documented short `/api/v1/verify` paths are not the routes found in the current router; current paths include `/api/v1/verification/request` and `/api/v1/verification/request/stream`.
- Define provider-neutral country/service/capability availability and expose customer-safe routing outcomes without leaking provider credentials or internal IDs.
- Add dashboards/alerts for purchase latency, unmatched orphan purchases, provider inventory/health, SMS/voice delivery latency, provider recoup failure, wallet refunds, notification delivery, and WebSocket disconnects.
- Keep support history privacy-safe: redact full phone numbers and never retain or log OTPs unless there is a narrowly justified, access-controlled retention requirement.
- Add a runbook for provider credential rotation, webhook signature configuration, provider health/balance, Redis availability, and refund reconciliation.

## Acceptance criteria before declaring this complete

- A simulated end-to-end test covers SMS, voice, and combined capability through purchase, debit, provider selection, delivery, timeout, refund, and notification.
- Duplicate webhook/poll/timeout/cancel races create at most one terminal transition, one debit, one wallet refund, and one customer-facing terminal notification.
- Provider routing correctly serves a non-US country through an eligible configured adapter when TextVerified lacks coverage, without first failing a TextVerified-only gate.
- The UI displays the server's real expiry and final wallet outcome; refresh and socket loss do not strand the customer.
- WebSocket and fallback HTTP polling converge to identical state across multiple app workers.
- Ledger and provider reconciliation match for success, timeout, report/refund, cancellation, and ambiguous purchase timeout.
- Focused tests and the full relevant suite pass; deploy verification is recorded separately from local CI/test results.

## Live-test status and next action

No live purchase, provider report/cancel, OTP, or customer notification has been performed. The repository-root `.env.prod` is absent, and the local router reported **no enabled providers**. No secret values were read.

The user authorized one timeout-only trial with a total cap of $4 and permitted real notification channels, but the provider environment is not configured. A successful OTP test was deferred; it requires an account/recipient controlled by the user. Do not run any live test until a provider is configured, a precise maximum per-purchase amount is confirmed, and the user is ready to enter a test number into their own account. Never request or print provider credentials or account passwords in chat.

## Files to start with

- [TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md](./TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md) — evidence and current findings.
- [VRENUM_API_CONTRACT.md](./VRENUM_API_CONTRACT.md) — intended public API contract and implementation caveats.
- `app/api/verification/purchase_endpoints.py` — purchase prechecks, routing, debit, SSE.
- `app/services/providers/provider_router.py` — provider coverage and selection.
- `app/services/sms_polling_service.py` — polling, completion, timeout, provider recoup.
- `app/api/verification/tv_webhook.py` — inbound SMS webhook.
- `app/api/verification/status_polling.py` — browser status and terminal state.
- `app/services/verification_status_service.py` and `app/services/auto_refund_service.py` — completion flags and customer credit refunds.
- `static/js/verification-flow.js` and `templates/voice_verify_modern.html` — SMS and voice customer UI.
- `app/websocket/manager.py`, `app/api/websocket_endpoints.py`, and `app/services/notification_dispatcher.py` — push and notification delivery.
