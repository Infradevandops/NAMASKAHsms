# Namaskah Project Assessment
March 2026 — v4.4.1

---

## What the app does

SMS verification platform. Users buy credits → get a temporary phone number via TextVerified → receive an OTP code on it. Payments via Paystack. Hosted on Render.com.

Stack → FastAPI / Python 3.9 / PostgreSQL / Redis / Jinja2 templates / vanilla JS

---

## Size

39,000 lines of Python
52 services → 36 models → 95 API route files
50 HTML templates → 52 JS files → 184 test files
12 DB migrations → 399 git commits

---

## What's confirmed working

Auth → JWT login, register, Google OAuth, token revocation
Wallet → Paystack payment init, webhook, credit deduction, transaction history
Tier system → Freemium / PAYG / Pro / Custom, quota, overage billing, tier gating
Admin tier → Fixed. Admin always gets custom tier, never falls to freemium
Admin panel → User management, verification history, audit logs, KYC
Notifications → WebSocket real-time, mobile push, notification preferences
Test suite → 1,306 / 1,780 passing (73.4%), 0 collection errors (was 56)
CI pipeline → 5 jobs configured: secrets, quality, security, tests, deployment

---

## What's code-correct but NOT confirmed live in production

Verification flow → TextVerified called first, credits deducted after, cost synced after refund — unit tested only, never confirmed with a real API call on Render
SMS polling → Logic correct, unit tests pass with mocks — never confirmed a real OTP was received end-to-end
Refund system → Auto-refund on area code / carrier mismatch — unit tested only, never confirmed credits land back in production
Email → SMTP not configured so email verification and password reset are silently broken

---

## Things that need a live test on production

Create a verification → confirm a real phone number comes back
Use that number on Telegram or WhatsApp → confirm OTP arrives
Complete a Paystack test payment → confirm credits land
Request a specific area code, get a different one → confirm refund hits balance
Register a new user → confirm verification email arrives (needs SMTP first)
Trigger password reset → confirm email arrives with working link
Log in as admin after cold start → confirm tier shows custom at /api/tiers/current
Hit the app after 15+ min idle → measure how long cold start takes

---

## Critical — fix now

1. Duplicate payment_logs table
   app/models/payment.py and app/models/transaction.py both define the same table name
   → SQLAlchemy will crash if both are ever imported together
   → Delete app/models/payment.py or rename its table

2. SMTP not configured
   Email verification and password reset are silently disabled
   → Set SMTP_USERNAME and SMTP_PASSWORD in Render environment variables

3. SMSForwarding model points to a table that doesn't exist
   app/models/sms_forwarding.py has a ForeignKey to rentals.id — that table was never created
   → Remove the FK or create the rentals table if forwarding is a planned feature

---

## High priority — fix soon

4. 22 dead services with zero imports
   These files exist in app/services/ but nothing in the app calls them:
   activity_service, adaptive_polling, alerting_service, analytics_service,
   audit_service, business_intelligence, commission_engine, currency_service,
   error_handling, event_broadcaster, event_service, fraud_detection_service,
   mfa_service, pricing_template_service, reseller_service, sms_gateway,
   transaction_service, verification_pricing_service, webhook_notification_service,
   whitelabel_enhanced
   → Wire them up or delete them

5. Reseller system half-built
   Models and service exist → no API endpoints → users can't access it
   → Build the endpoints or remove everything until ready

6. WhiteLabel half-built
   Models and service exist → no active API routes serve them
   → Same as reseller — build or remove

7. CI still failing
   474 test failures remaining → coverage at 36% (target 60%)
   Gitleaks job → not investigated
   Bandit / Safety / Semgrep → not verified
   → See docs/tasks/CI_TEST_FAILURES.md for full breakdown

8. test_payment_race_condition.py causes a process-level segfault
   Currently only ignored in CI — not deleted
   → Delete it

---

## Medium priority — fix next

9. Render free tier cold starts
   App spins down after 15 min of inactivity → first request takes 30–60 seconds
   512MB RAM → tight with 2 workers and DB connections
   → Upgrade to Render Starter ($7/month) to eliminate cold starts

10. No database backup running
    Backup script is written → CI job exists → but S3 credentials are not set
    If the Render DB is dropped there is no recovery path
    → Set up S3 credentials or use an alternative free backup method

11. Python version mismatch
    CI uses Python 3.11 → local venv uses Python 3.9.6 → no .python-version file
    → Add .python-version with 3.11, recreate venv to match CI

12. Alembic migration chain unclear
    12 migration files with non-standard revision IDs and unclear ordering
    safe_add_tiers has down_revision = None suggesting it's a root but the chain is incomplete
    → Run alembic history on production to confirm current state

13. Two disabled CI workflow files still in repo
    ci-simple.yml and ci-strict.yml are marked disabled but still exist
    → Delete them

---

## Low priority — fix later

14. BASE_URL not set in environment
    Config references BASE_URL but it's missing → may break email links and OAuth callbacks
    → Add BASE_URL=https://namaskah.onrender.com to Render env vars

15. .hypothesis/ folder in repo
    200+ binary test artifact files committed to git
    → Add .hypothesis/ to .gitignore and remove from repo

16. Monitoring stack not connected
    Full Prometheus + Grafana config exists in monitoring/ but nothing is running
    → Set it up or remove the dead config

17. i18n partially implemented
    9 locale files exist → i18n tests are ignored in CI → feature is incomplete
    → Complete it or remove it

18. Forwarding feature disabled
    Router is commented out in main.py → model references non-existent rentals table
    → Complete the feature or remove the model and router file

19. scripts/ directory cluttered
    60+ scripts in root including one-off migration and diagnostic scripts
    → Move one-off scripts to scripts/archive/ or delete them

---

## Action order

Fix duplicate payment_logs table → 30 min
Configure SMTP in Render → 5 min
Fix SMSForwarding FK → 15 min
Delete test_payment_race_condition.py → 1 min
Delete 22 dead services or wire them up → 2–4 hrs
Fix remaining CI jobs → 2–4 hrs
Upgrade Render to Starter plan → 5 min
Set up DB backup → 1 hr
Add .python-version file → 30 min
Delete ci-simple.yml and ci-strict.yml → 5 min
Complete or remove reseller system → 1–2 days
Complete or remove whitelabel system → 1–2 days
Add .hypothesis/ to .gitignore → 5 min
Archive one-off scripts → 30 min
Complete or remove i18n → 1 day
Complete or remove forwarding feature → 1 day
