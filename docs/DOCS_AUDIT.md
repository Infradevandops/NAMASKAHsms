# DOCS AUDIT — Absolute vs Redundant

**Date**: October 26, 2026
**Purpose**: Identify which docs are live references vs safe to delete

---

## ABSOLUTE — Keep, these are actively used

| File | Why it's essential |
|------|--------------------|
| `README.md` | Project overview, architecture diagrams, quick start |
| `CHANGELOG.md` | Version history — source of truth for what shipped when |
| `docs/status/PLATFORM_STATUS.md` | Current version, background services, open tasks |
| `docs/status/OPS_SUMMARY.md` | Ops runbook — deploy commands, infra, emails, revenue, SEO |
| `docs/INDEX.md` | Navigation hub for all docs |
| `docs/deployment/DEPLOYMENT_BEST_PRACTICES.md` | Full Linux deploy guide |
| `docs/deployment/DEPLOYMENT_CHECKLIST.md` | Pre-deploy verification steps |
| `docs/deployment/DEPLOYMENT_QUICK_REFERENCE.md` | Quick SSH/Docker commands |
| `docs/deployment/SECURITY_AUDIT.md` | OWASP compliance record |
| `docs/operations/MONITORING.md` | Sentry + BetterStack setup |
| `docs/operations/PRODUCTION_MIGRATION_GUIDE.md` | DB migration procedures |
| `docs/operations/LOGS_GUIDE.md` | Log locations + troubleshooting |
| `docs/operations/EMAIL_SETUP.md` | Email provider DNS + config |
| `docs/business/PRICING_REFERENCE.md` | Definitive pricing — single source of truth |
| `docs/business/PROJECT_VISION.md` | Roadmap + strategic direction |
| `docs/business/ESSENTIAL_STARTUP_BRIEF.md` | Investor/partner brief |
| `docs/knowledge/BUSINESS_LOGIC.md` | Tier rules, credit logic |
| `docs/knowledge/SMS_LOGIC.md` | TextVerified flow, polling, refund triggers |
| `docs/knowledge/REFUND_LOGIC_VERIFIED.md` | Refund policy rules (verified against code) |
| `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md` | E2E test criteria for Telegram forwarding |
| `docs/features/ADVANCED_ANALYTICS_CUSTOM_REPORTS.md` | Phase 2 analytics spec |
| `docs/features/BILLING_HISTORY.md` | Billing UI spec |
| `docs/features/COMPLIANCE_GDPR_CHECKER.md` | GDPR feature spec |
| `docs/features/DISPUTES_COMMENTS_ATTACHMENTS.md` | Disputes feature spec |
| `docs/features/KYC_DOCUMENT_VIEWER.md` | KYC feature spec |
| `docs/features/USAGE_QUOTAS.md` | Quota system spec |
| `docs/features/USER_MANAGEMENT_ACTIVITY_TIMELINE.md` | User management spec |
| `docs/engineering/TESTING_STRATEGY.md` | Test coverage targets + approach |
| `.github/workflows/ci.yml` | CI pipeline — actively runs on every push |
| `.github/workflows/deploy.yml` | CD pipeline — deploys to production |

---

## REDUNDANT — Safe to delete or already superseded

### Deployment folder clutter

| File | Reason redundant |
|------|-----------------|
| `docs/deployment/DEPLOYMENT.md` | Superseded by `DEPLOYMENT_BEST_PRACTICES.md` |
| `docs/deployment/DEPLOY_NOW.md` | One-off action doc, deploy is now automated via CI/CD |
| `docs/deployment/DEPLOYMENT_LOG.md` | Historical log, no ongoing value |
| `docs/deployment/LOGIN_FIX_ROOT_CAUSE.md` | One-off bug post-mortem, resolved |
| `docs/deployment/PHASE1_IMPLEMENTATION_GUIDE.md` | Phase 1 is 100% complete |
| `docs/deployment/ADMIN_CREDENTIALS_TESTING.md` | One-off testing doc |
| `docs/deployment/ADMIN_OVERHAUL_PLAN.md` | Plan doc, work is complete |

### Status folder — stale snapshots

| File | Reason redundant |
|------|-----------------|
| `docs/status/CODEBASE_ASSESSMENT.md` | Point-in-time snapshot, superseded by PLATFORM_STATUS |
| `docs/status/STABLE_VERSION_BRIEF.md` | Old version brief, superseded |
| `docs/status/TEST_SUITE_REALITY_CHECK.md` | Old test audit, superseded by CI results |
| `docs/status/PRODUCTION_SETUP_CHECKLIST.md` | Superseded by DEPLOYMENT_CHECKLIST |

### Tasks folder — all completed

| File | Reason redundant |
|------|-----------------|
| `docs/tasks/TEST_REMEDIATION_TASKFILE.md` | Work complete |
| `docs/tasks/TEST_REMEDIATION_PHASE_4_PLAN.md` | Work complete |
| `docs/tasks/TEST_REMEDIATION_PHASE_4A_LOG.md` | Work complete |
| `docs/tasks/TEST_REMEDIATION_PHASE_4B_ASSESSMENT.md` | Work complete |
| `docs/tasks/TEST_REMEDIATION_PHASE_4B_LOG.md` | Work complete |
| `docs/tasks/TEST_REMEDIATION_CORRECTED_SUMMARY.md` | Work complete |
| `docs/tasks/DRIVER_JS_IMPLEMENTATION_COMPLETE.md` | Work complete |
| `docs/tasks/DRIVER_JS_ONBOARDING_TOUR_TASKFILE.md` | Work complete |
| `docs/tasks/EMAIL_WIRING_TASKFILE.md` | Work complete |
| `docs/tasks/ONBOARDING_WIZARD_TASKFILE.md` | Work complete |
| `docs/tasks/MOBILE_RESPONSIVENESS_TASKFILE.md` | Work complete |
| `docs/tasks/POST_DEPLOYMENT_STABILIZATION.md` | Work complete |
| `docs/tasks/CODEBASE_CLEANUP_ASSESSMENT.md` | Point-in-time, stale |
| `docs/tasks/FRONTEND_UPGRADE_PLAN.md` | Superseded by shipped features |
| `docs/tasks/Namaskah. app.code-workspace` | Wrong folder, not a doc |

### Root-level docs folder

| File | Reason redundant |
|------|-----------------|
| `docs/DEPLOYMENT_INDEX.md` | Superseded by `docs/INDEX.md` |
| `docs/DEPLOYMENT_SUMMARY_v4.8.2.md` | Old version summary, in CHANGELOG |
| `docs/ORGANIZATION_SUMMARY.md` | Meta-doc about doc structure, superseded by INDEX |

### Operations folder

| File | Reason redundant |
|------|-----------------|
| `docs/operations/DIGITALOCEAN_DEPLOYMENT.md` | Superseded by `DEPLOYMENT_BEST_PRACTICES.md` |
| `docs/operations/monitoring-links.html` | HTML file in docs folder, links are in OPS_SUMMARY |

### Entire archive folder

| Path | Reason redundant |
|------|-----------------|
| `docs/archive/` (entire folder) | Historical only — all work superseded. Safe to delete if disk space needed. Keep if you want audit trail. |

---

## BROKEN LINKS (were in INDEX.md — now removed)

These files are referenced in old docs but **do not exist on disk**:

- `docs/status/PHASE1_STATUS.md` — never created
- `docs/status/ASSESSMENT_SUMMARY.md` — never created
- `docs/deployment/PHASE1_ACTION_PLAN.md` — never created
- `docs/deployment/VERIFICATION_CHECKLIST.md` — never created
- `docs/QUICK_START.md` — referenced in INDEX but doesn't exist (there's `QUICK_START.md` at repo root)

---

## SUMMARY

| Category | Count |
|----------|-------|
| Absolute (keep) | 30 |
| Redundant (safe to delete) | 28 |
| Broken links fixed | 5 |
