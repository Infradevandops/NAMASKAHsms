# Email System Hardening

**Status:** Planned — implementation not started by this documentation change  
**Owner:** Backend / Platform Engineering  
**Scope:** Transactional email, optional notifications, branded and whitelabel templates, contact-form delivery, provider operations  
**Repository baseline reviewed:** `main`, observed commit `e5c20f1ad8722fbfa986df0f2ef154d285cd9bc1` (9 November 2026 review)

## Purpose

This initiative hardens the existing Vrenum email system without replacing working product behavior or prematurely introducing a second notification platform. The first deliverable is a reliable, auditable email architecture with explicit message classification, one sending boundary, safe template rendering, preference enforcement, durable delivery for important messages, and tests that prove the intended behavior.

This folder is the implementation source of truth for the email-hardening work. Keep the existing operational provider instructions in [EMAIL_SETUP.md](../../operations/EMAIL_SETUP.md); update that document only when implementation changes the real setup or runtime behavior.

## Read in this order

1. [Repository email audit](./REPOSITORY_EMAIL_AUDIT.md) — observed code, template inventory, verified defects and items requiring confirmation.
2. [Target architecture and implementation plan](./IMPLEMENTATION_PLAN.md) — design decisions, migration sequence, compatibility and operational requirements.
3. [Implementation tasks](./TASKS.md) — ordered sprint-ready tasks and acceptance criteria.
4. [Template and message catalogue](./TEMPLATE_CATALOG.md) — current template families, data contracts, message classification and required content rules.
5. [Verification matrix](./TEST_AND_RELEASE_MATRIX.md) — test coverage, release gates and production verification.

## Non-goals

- Do not redesign every email's visual identity as a prerequisite to reliability work.
- Do not replace Resend or SMTP before measuring the existing adapter and configuration behavior.
- Do not classify security, account-access or transaction records as marketing.
- Do not promise exactly-once delivery across an external provider boundary. The target is durable intent, at-least-once processing, provider idempotency where available, and deduplication/reconciliation.
- Do not build a marketing campaign platform as part of this initiative.

## Definition of done

- All email call sites are inventoried and routed through an explicit sending boundary or documented exception.
- Optional notifications honor one authoritative category preference policy on every path.
- Account/security and transaction-essential messages have documented policy and are not accidentally suppressed by marketing opt-outs.
- Contact submissions are durably recorded before the API acknowledges receipt; forwarding failure is visible and retryable.
- Payment receipt ownership is singular and replay-safe.
- Sender identity is driven by validated canonical configuration.
- User-controlled content is safely rendered; URLs are validated for their intended context.
- Important email intent is persisted and processed by a supervised worker with bounded retries and terminal failure visibility.
- Provider responses, delivery events and suppression events are correlated without logging credentials or sensitive message bodies.
- Tests enforce outcomes, not merely tolerate either success or failure.
- Deployment, migration, rollback and operator runbooks are updated and verified.

## Implementation rule

The documents describe the intended end state, not evidence that it already exists. Keep task status unchecked until code, migrations, tests and deployment evidence demonstrate completion.
