# Namaskah — Project Assessment

**Date**: March 2026  
**Version**: v4.4.1  
**Assessed by**: Amazon Q

---

## Overview

Namaskah is an SMS verification platform. Users buy credits, get temporary phone numbers via TextVerified, and receive OTP codes. Payments via Paystack. Hosted on Render.com (free tier).

**Stack**: FastAPI/Python 3.9, PostgreSQL, Redis, TextVerified API, Paystack, Jinja2 templates, vanilla JS frontend.

---

## Scale

| Component | Count |
|-----------|-------|
| Python source lines | 39,448 |
| Services | 52 |
| Models | 36 |
| API route files | 95 |
| HTML templates | 50 |
| JS files | 52 |
| Test files | 184 |
| DB migrations | 12 |
| Git commits | 399 |

---

## What's Working ✅

- **Core verification flow** — TextVerified called first, credits deducted after success, Decimal/float arithmetic correct, `verification.cost` synced after refund
- **Auth** — JWT login/register, Google OAuth, token revocation, password reset
- **Wallet** — Paystack payment init, webhook processing, credit deduction, transaction history
- **Tier system** — Freemium/PAYG/Pro/Custom, quota tracking, overage billing, tier gating
- **Admin** — User management, verification history, audit logs, KYC
- **Notifications** — WebSocket real-time, email, mobile push, notification preferences
- **Refund system** — Auto-refund on area code/carrier mismatch (v4.4.1)
- **CI pipeline** — 5 jobs: secrets scan, code quality, security, tests, deployment readiness
- **Test suite** — 1,306/1,780 passing (73.4%), 0 collection errors

---

## Critical Issues 🔴

### 1. Duplicate `payment_logs` table
**Files**: `app/models/payment.py` and `app/models/transaction.py` both define `__tablename__ = "payment_logs"`  
**Risk**: SQLAlchemy mapper conflict if both are imported in the same process. Currently avoided by only importing `Transaction` from `transaction.py`, but any future import of `payment.py` will crash the app.  
**Fix**: Delete `app/models/payment.py` or rename its table. Audit all imports.

### 2. SMTP not configured
**Impact**: Email verification and password reset are silently disabled in production. Users who register cannot verify their email. Users who forget their password cannot reset it.  
**Fix**: Set `SMTP_USERNAME` and `SMTP_PASSWORD` in Render environment variables.

### 3. `SMSForwarding` model references non-existent `rentals` table
**File**: `app/models/sms_forwarding.py` — `ForeignKey("rentals.id")`  
**Risk**: Any migration or `create_all` that includes this model will fail with `NoReferencedTableError`. Currently avoided by not importing it in conftest, but it's a landmine.  
**Fix**: Remove the FK or create the `rentals` table if SMS forwarding is a planned feature.

---

## High Priority Issues 🟠

### 4. 22 dead services with zero imports
These services exist in `app/services/` but nothing in the app imports them:

| Service | Notes |
|---------|-------|
| `activity_service` | Activity logging — not wired up |
| `adaptive_polling` | Alternative polling strategy — unused |
| `alerting_service` | Alerts — not connected |
| `analytics_service` | Analytics — not wired to any router |
| `audit_service` | Audit logging — not used |
| `business_intelligence` | BI reporting — not used |
| `commission_engine` | Affiliate commissions — not wired |
| `currency_service` | Currency conversion — not used |
| `error_handling` | Error handling — not used |
| `event_broadcaster` | WebSocket events — not wired |
| `event_service` | Events — not used |
| `fraud_detection_service` | Fraud detection — not used |
| `mfa_service` | MFA — not used |
| `pricing_template_service` | Pricing templates — not wired |
| `reseller_service` | Reseller — service created, no API endpoints |
| `sms_gateway` | SMS gateway — not used |
| `transaction_service` | Transactions — not used |
| `verification_pricing_service` | Pricing — not used |
| `webhook_notification_service` | Webhook notifications — not used |
| `whitelabel_enhanced` | Whitelabel — not wired |

**Risk**: Maintenance burden, confusion about what's active, dead code inflating codebase size.  
**Fix**: Either wire them up or delete them. Don't leave half-built features silently sitting.

### 5. Reseller system half-built
`app/services/reseller_service.py` and `app/models/reseller.py` exist with full data models (`ResellerAccount`, `SubAccount`, `SubAccountTransaction`, `BulkOperation`) but there are **zero API endpoints**. Users cannot access reseller functionality.  
**Fix**: Either build the endpoints or remove the models/service until ready.

### 6. WhiteLabel half-built
`app/services/whitelabel_enhanced.py`, `app/models/whitelabel.py`, `app/models/whitelabel_enhanced.py` exist but no active API routes serve them.  
**Fix**: Same as reseller — build or remove.

### 7. CI Tests job still failing
474 test failures remaining. Coverage at 36% (target 60%). Three CI jobs failing:
- Secrets Detection (Gitleaks) — not investigated
- Security Scan (Bandit/Safety/Semgrep) — not verified
- Tests — 474 failures, coverage below threshold

See `docs/tasks/CI_TEST_FAILURES.md` for full breakdown.

---

## Medium Priority Issues 🟡

### 8. `namaskah_fallback.db` in repo root
A 932KB SQLite fallback database sits in the project root. It's in `.gitignore` so not tracked by git, but it exists locally and gets created whenever PostgreSQL is unavailable (e.g. local dev without Postgres running). This file may contain real user data from local testing.  
**Fix**: Add to `.gitignore` explicitly (already there), delete the file, and ensure it's never committed.

### 9. Render free tier limitations
Currently on Render free plan:
- **Spins down after 15 minutes of inactivity** — first request after sleep takes 30–60 seconds
- **512MB RAM** — may be tight with 2 Uvicorn workers + PostgreSQL connections
- **750 hours/month** — enough for one service running continuously

**Fix**: Upgrade to Render Starter ($7/month) to eliminate cold starts. Critical for user experience.

### 10. No database backup active
`scripts/backup_database.py` is written and the CI job exists, but it requires AWS S3 credentials (`BACKUP_S3_BUCKET`, `AWS_ACCESS_KEY_ID`, etc.) which aren't set. If the Render PostgreSQL database is corrupted or accidentally dropped, there is no recovery path.  
**Fix**: Set up S3 bucket and credentials, or use an alternative free backup (pg_dump to GitHub artifact, Supabase, etc.).

### 11. Multiple CI workflow files
`.github/workflows/` contains: `ci.yml` (active), `ci-simple.yml` (disabled), `ci-strict.yml` (disabled), `deploy.yml`, `security-testing.yml`, `sync-to-gitlab.yml`.  
The disabled files are marked `[DISABLED - use ci.yml]` but still exist.  
**Fix**: Delete `ci-simple.yml` and `ci-strict.yml` to reduce confusion.

### 12. Python version inconsistency
CI uses Python 3.11 (`env.PYTHON_VERSION: '3.11'`). Local `.venv` uses Python 3.9.6. No `.python-version` file to enforce consistency.  
**Fix**: Add `.python-version` file with `3.11`, recreate venv with Python 3.11 to match CI.

### 13. `test_payment_race_condition.py` — segfault risk
This file causes a process-level segfault that kills the entire pytest run. Currently only `--ignore`d in CI. It's not skipped, it's not deleted — it's a live grenade.  
**Fix**: Delete it.

### 14. Alembic migrations not chained properly
Migration files use non-standard revision IDs (`quota_pricing_v3_1`, `safe_add_tiers`) instead of Alembic-generated hashes. The chain is incomplete — `safe_add_tiers` has `down_revision = None` suggesting it's a root, but there are 12 migration files with unclear ordering.  
**Fix**: Run `alembic history` on production to confirm current state. Ensure all migrations are applied and the chain is linear.

---

## Low Priority / Future 🟢

### 15. `BASE_URL` not in `.env`
Config references `BASE_URL` but it's not set in `.env`. May affect email links, OAuth callbacks, or webhook URLs.  
**Fix**: Add `BASE_URL=https://namaskah.onrender.com` to Render env vars.

### 16. Hypothesis test data in repo
`.hypothesis/constants/` contains 200+ binary files from property-based testing. These are test artifacts, not source code.  
**Fix**: Add `.hypothesis/` to `.gitignore` and remove from repo.

### 17. Monitoring stack not connected
`monitoring/` directory has full Prometheus + Grafana config, but it's not running. `app/core/metrics.py` and `app/middleware/prometheus.py` exist but Prometheus isn't scraping anything in production.  
**Fix**: Either set up monitoring or remove the dead config to reduce confusion.

### 18. i18n partially implemented
9 locale files exist (`en`, `es`, `fr`, `de`, `ar`, `hi`, `ja`, `pt`, `zh`). `app/utils/i18n.py` exists. But `test_i18n.py` and `test_i18n_frontend.py` are ignored in CI — suggesting i18n is incomplete or broken.  
**Fix**: Either complete i18n or remove it from the codebase until ready.

### 19. Forwarding feature disabled
`app/api/core/forwarding.py` is imported in `main.py` but the router is commented out (`# from app.api.core.forwarding import router as forwarding_router`). `SMSForwarding` model references a non-existent `rentals` table.  
**Fix**: Either complete the feature or remove the model and router file.

### 20. `scripts/` directory cluttered
60+ scripts in `scripts/` root, many one-off migration/diagnostic scripts (`purchase_new_215.py`, `distribute_users.py`, `clean_test_balances.py`). These are operational scripts that ran once and should be archived.  
**Fix**: Move one-off scripts to `scripts/archive/` or delete them.

---

## Action Priority

| Priority | Item | Effort |
|----------|------|--------|
| 🔴 Now | Fix duplicate `payment_logs` table | 30 min |
| 🔴 Now | Configure SMTP in Render | 5 min |
| 🔴 Now | Fix `SMSForwarding` FK to non-existent table | 15 min |
| 🟠 Soon | Delete 22 dead services or wire them up | 2–4 hrs |
| 🟠 Soon | Delete `test_payment_race_condition.py` | 1 min |
| 🟠 Soon | Fix remaining CI jobs (Gitleaks, Bandit, coverage) | 2–4 hrs |
| 🟡 Next | Upgrade Render to Starter plan | 5 min |
| 🟡 Next | Set up DB backup (S3 or alternative) | 1 hr |
| 🟡 Next | Add `.python-version` file, align to 3.11 | 30 min |
| 🟡 Next | Delete `ci-simple.yml`, `ci-strict.yml` | 5 min |
| 🟢 Later | Complete or remove reseller system | 1–2 days |
| 🟢 Later | Complete or remove whitelabel system | 1–2 days |
| 🟢 Later | Add `.hypothesis/` to `.gitignore` | 5 min |
| 🟢 Later | Archive one-off scripts | 30 min |
| 🟢 Later | Complete or remove i18n | 1 day |
| 🟢 Later | Complete or remove forwarding feature | 1 day |
