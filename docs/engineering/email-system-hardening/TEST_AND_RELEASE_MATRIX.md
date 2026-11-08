# Email System Hardening — Test and Release Matrix

## 1. Unit tests

| Area | Required assertions |
|---|---|
| Message classification | Every known template/caller maps to an allowed class; missing/unknown class rejected. |
| Preference policy | Category disabled, email method absent, frequency never, global optional unsubscribe, bounce and complaint suppress optional email. |
| Transactional policy | Password reset, account verification and essential receipts are not suppressed by optional marketing opt-out; abuse/security controls still apply. |
| Provider adapters | Resend and SMTP success; timeout; network error; rate limit; permanent validation/auth error; provider message ID capture. |
| Sender configuration | Canonical From and Reply-To used; invalid production sender rejected; SMTP login is not implicitly treated as From unless configured. |
| Rendering | HTML escaping; safe URL validation; subject/header injection rejection; missing/extra variables; text alternative generation. |
| Whitelabel security | Sanitizer strips/rejects scripts, event handlers, unsafe schemes and disallowed markup; template version history remains intact. |
| Retry classification | Retryable vs permanent failures; bounded attempts; exponential backoff with jitter; no retry storm. |
| Idempotency | Same logical key creates one outbox item; duplicate event is harmless; concurrent insert race protected by unique constraint. |
| Worker | Atomic claim, lease expiry recovery, graceful shutdown, concurrent worker safety, terminal dead-letter state. |

## 2. Integration scenarios

| Scenario | Setup | Expected result |
|---|---|---|
| Contact submission | Valid contact form; provider unavailable | Submission persists; API response says received/stored, not delivered; forwarding remains pending/retryable. |
| Contact retry | Worker fails once then provider recovers | One logical support email is accepted; submission status reflects progress. |
| Payment webhook replay | Same successful provider event delivered repeatedly | Credit operation remains idempotent; one receipt outbox record; no duplicate logical receipt. |
| Payment verify + webhook race | Same payment reaches both entry paths concurrently | Unique payment-event key prevents two receipt intents. |
| Refund replay | Same refund event replayed | One refund notification intent. |
| Optional notification opt-out | User has category disabled or email absent | No provider send; record suppressed reason. |
| Preference changes after enqueue | User opts out before worker dispatch | Worker suppresses queued optional email. |
| Digest frequency | Daily/weekly/never preferences | Only eligible cadence is enqueued; no duplicate digest for same period. |
| SMS forwarding disabled | Forwarding rule disabled | No email; user preference for marketing is irrelevant. |
| SMS forwarding enabled | Valid configured address and rule | Forwarded email uses canonical sender and safe body rendering. |
| Security mail | User opted out of optional notifications | Password reset/security mail follows account-security policy. |
| Provider event replay | Same signed delivery/bounce webhook replayed | Event is stored once; state transition remains idempotent. |
| Hard bounce/complaint | Provider reports recipient suppression event | Future optional messages are suppressed; event is auditable. |

## 3. Contract and API tests

- GET preferences returns computed values from the authoritative policy source; it must not report a hard-coded enabled value.
- PUT preferences updates a coherent category state and validates supported category values.
- Missing preference rows follow documented defaults or are created deterministically; no accidental 404 behavior.
- Public unsubscribe token route works while logged out, is signed/expiring, scoped to optional categories and replay-safe.
- Authenticated preference UI and public unsubscribe route modify the same source of truth.
- Test-send endpoint is rate-limited, authenticated and auditable.
- Contact endpoint validates, rate-limits and persists before success response.

## 4. Test quality rules

- Assert exact provider call counts and exact logical message counts.
- Do not accept either `True` or `False` for a test whose expected behavior is known.
- Do not treat 404/405 as acceptable for a required endpoint.
- Mock network/provider boundaries, not the policy or business logic under test.
- Use a real test database for uniqueness, transactions and migration behavior.
- Include concurrency tests for idempotency and outbox claiming.
- Verify all existing email tests still cover compatibility wrappers during migration.

## 5. Staging release gates

- [ ] Additive migrations applied successfully to a staging copy.
- [ ] Preference backfill dry-run reviewed; legacy settings precedence documented.
- [ ] Canonical sender and reply-to validated against verified domain.
- [ ] Resend/SMTP credentials are supplied through secret management; no secrets in repository.
- [ ] Worker runs under process supervision with health and graceful shutdown.
- [ ] Outbox lag, retry and dead-letter metrics visible.
- [ ] Contact submission persistence and forwarding retry verified.
- [ ] Payment webhook replay and receipt idempotency verified.
- [ ] Template rendering/injection tests pass.
- [ ] Provider webhook signature and replay tests pass if event ingestion is enabled.
- [ ] Rollback procedure rehearsed.

## 6. Production canary

1. Deploy additive schema and backward-compatible application code.
2. Start worker in observation/limited mode; verify it claims only intended test/canary records.
3. Send a controlled test message to an authorized mailbox for each provider.
4. Verify From, Reply-To, HTML, text, links, provider message ID and provider event correlation.
5. Enable account/security and transactional message classes after end-to-end checks.
6. Enable optional notifications by category in a measured rollout; confirm opt-out suppression.
7. Watch queue age, acceptance, delivery, bounce, complaint and permanent-failure rates.
8. Expand rollout only after agreed thresholds remain healthy.

## 7. Rollback

- Pause worker; do not delete pending rows.
- Revert feature flags to prior sending path only if the old path remains safe and compatible.
- Keep additive schema and data until a separately reviewed cleanup migration.
- Preserve event/idempotency records to avoid replay duplicates.
- If sender configuration is invalid, stop outbound sends and surface the readiness failure; do not silently use an unverified fallback identity.
- Document any messages manually replayed or suppressed during incident recovery.

## 8. Closeout evidence

For each task, record commit SHA, migration revision, test command/result, deployment ID/time, canary result and any known limitation. “Pushed” is not equivalent to “tested” or “delivered.”
