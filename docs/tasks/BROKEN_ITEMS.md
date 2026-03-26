# Broken Items — Fix Tasklist

**Date**: March 2026
**Scope**: Verification flow + platform-wide

---

## Verification — Broken

### 1. Cancel route has double path
The cancel endpoint mounts as /api/verification/verification/cancel/{id} instead of /api/verification/cancel/{id}
The cancel_endpoint.py router has its own /verification prefix stacking on top of the parent router's /verification prefix

- [ ] Open app/api/verification/cancel_endpoint.py
- [ ] Remove or fix the duplicate /verification prefix on the router
- [ ] Confirm route resolves to /api/verification/cancel/{id}

Acceptance → GET /api/verification/cancel/{id} returns the correct response, not 404

---

### 2. Tests import a module that no longer exists
7 tests in test_verification_flow.py and test_verification_endpoints_comprehensive.py import app.api.verification.verification_routes which was renamed or deleted
These tests fail at collection — they never run

- [ ] Find what verification_routes was renamed to
- [ ] Update the import in both test files to the correct module path
- [ ] Confirm both files collect without ModuleNotFoundError

Acceptance → 0 ModuleNotFoundError on collection for verification test files

---

### 3. Integration tests pass auth_headers_factory as a dict instead of calling it
Tests in test_verification_api.py pass headers=auth_headers_factory instead of headers=auth_headers_factory(user_id)
This sends the fixture function object as headers, not an actual auth token

- [ ] Find all occurrences of headers=auth_headers_factory in test_verification_api.py
- [ ] Replace with headers=auth_headers_factory(user.id) using the correct user fixture

Acceptance → No 401 or 403 from missing/malformed auth headers in verification integration tests

---

### 4. TextVerified disabled in local environment
TEXTVERIFIED_API_KEY is not set in local .env so TextVerifiedService is disabled
Any test or local run that hits the purchase endpoint without mocking returns 503

- [ ] Add TEXTVERIFIED_API_KEY and TEXTVERIFIED_EMAIL to .env.local for local dev
- [ ] Ensure all unit tests that touch purchase_endpoints mock TextVerifiedService
- [ ] Confirm no test requires real credentials to pass

Acceptance → All verification unit tests pass with credentials unset

---

## Platform — Broken

### 5. SMTP not configured — email is silently broken
Email verification and password reset are disabled in production
Users who register cannot verify their email
Users who forget their password cannot reset it

- [ ] Set SMTP_USERNAME in Render environment variables
- [ ] Set SMTP_PASSWORD in Render environment variables
- [ ] Test by registering a new user and confirming the verification email arrives
- [ ] Test password reset flow end-to-end

Acceptance → Verification email arrives after registration, password reset email arrives and link works

---

### 6. Duplicate payment_logs table definition
app/models/payment.py and app/models/transaction.py both define __tablename__ = "payment_logs"
SQLAlchemy will crash if both are imported in the same process
Currently avoided by accident — any future import of payment.py will break the app

- [ ] Check if anything imports app/models/payment.py
- [ ] If nothing imports it → delete app/models/payment.py
- [ ] If something imports it → rename its table to something unique
- [ ] Run the full test suite to confirm no crash

Acceptance → Only one model defines payment_logs, app starts without SQLAlchemy mapper errors

---

### 7. SMSForwarding model references a table that does not exist
app/models/sms_forwarding.py has ForeignKey("rentals.id")
The rentals table was never created
Any migration or create_all that includes this model will fail

- [ ] Decide: is SMS forwarding a planned feature?
- [ ] If yes → create the rentals table and migration
- [ ] If no → remove the FK from sms_forwarding.py or delete the model entirely
- [ ] Confirm migrations run without NoReferencedTableError

Acceptance → No NoReferencedTableError on startup or migration

---

### 8. CI — 3 of 5 jobs still failing
Gitleaks → secrets scan failing, not yet investigated
Bandit / Safety / Semgrep → security scan not verified
Tests → 474 failures, coverage at 36% (target 60%)

- [ ] Run gitleaks locally to find the triggering line
- [ ] Add allowlist entry in tools/gitleaks.toml for false positives
- [ ] Confirm bandit==1.7.6 is pinned in ci.yml
- [ ] Run safety check and semgrep locally before pushing
- [ ] Continue fixing test failures per docs/tasks/CI_TEST_FAILURES.md
- [ ] Raise --cov-fail-under from 36% to 60% once failures are resolved

Acceptance → All 5 CI jobs green, deployment readiness job unblocks

---

### 9. No database backup running
scripts/backup_database.py is written and CI job exists
S3 credentials are not set so nothing is actually backing up
If the Render PostgreSQL database is dropped there is no recovery

- [ ] Create an S3 bucket for backups
- [ ] Set BACKUP_S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION in GitHub secrets
- [ ] Set PRODUCTION_DATABASE_URL in GitHub secrets
- [ ] Trigger a manual backup run to confirm it works
- [ ] Confirm backup file appears in S3

Acceptance → Backup file appears in S3 after every push to main

---

### 10. Render free tier cold starts
App spins down after 15 minutes of inactivity
First request after sleep takes 30–60 seconds
This is the first thing users experience if the app has been idle

- [ ] Upgrade to Render Starter plan ($7/month)
- [ ] Alternatively set up an uptime monitor to ping the app every 10 minutes to keep it warm

Acceptance → First request responds in under 3 seconds regardless of idle time

---

### 11. test_payment_race_condition.py causes a process segfault
This file kills the entire pytest process when it runs
Currently only --ignored in CI — not deleted
It is a live risk to the test suite

- [ ] Delete tests/unit/test_payment_race_condition.py
- [ ] Remove it from the --ignore list in ci.yml

Acceptance → File does not exist, --ignore flag removed from ci.yml

---

### 12. Admin tier falls back to freemium in some code paths
Two tier resolution functions existed with inconsistent admin handling
tier_helpers.get_user_tier() and tier_validation.require_tier() had no admin bypass
Fixed in this session but needs a production verification

- [ ] Deploy to Render
- [ ] Log in as admin
- [ ] Hit /api/tiers/current and confirm response shows custom tier
- [ ] Check admin dashboard shows Custom tier label

Acceptance → Admin always sees custom tier in UI and API after any cold start or redeploy

---

## Action Order

Fix cancel double path → 15 min
Fix verification_routes import → 15 min
Fix auth_headers_factory in integration tests → 15 min
Delete test_payment_race_condition.py → 1 min
Fix duplicate payment_logs table → 30 min
Fix SMSForwarding FK → 15 min
Configure SMTP in Render → 5 min
Verify admin tier in production → 5 min
Fix remaining CI jobs → 2–4 hrs
Upgrade Render plan or set up keep-warm → 5 min
Set up DB backup credentials → 1 hr
