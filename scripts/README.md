# Scripts

Utility scripts organised by purpose. All scripts require the project virtualenv and `.env` loaded.

```
scripts/
├── deployment/    # Production ops — deploy, backup, start, diagnose
├── development/   # Local dev — seed data, check APIs, run tests
├── maintenance/   # Live DB ops — refunds, reconciliation, resets
├── security/      # Security scans, secrets rotation, audits
└── sql/           # Raw SQL — schema patches, audit queries
```

## Usage

```bash
# Activate virtualenv first
source .venv/bin/activate

# Load env
export $(cat .env | xargs)

# Example
python scripts/maintenance/reconcile_wallets.py
python scripts/deployment/production_diagnostic.py
```

## deployment/
| Script | Purpose |
|--------|---------|
| `deploy_production.sh` | Full production deploy |
| `pre_deploy_checks.py` | Pre-deploy validation |
| `post_deploy_verification.py` | Post-deploy smoke test |
| `backup_database.py` | PostgreSQL → S3 backup |
| `backup_rclone.py` | Rclone-based backup |
| `backup_automation.sh` | Automated backup runner |
| `generate_secure_keys.py` | Generate SECRET_KEY / JWT_SECRET_KEY |
| `production_diagnostic.py` | Live system health check |
| `validate_version_sync.py` | Verify version consistency across files |
| `restart.sh` | Restart application |
| `start_monitoring.sh` | Start Prometheus + Grafana |
| `migrate.sh` | Run Alembic migrations |
| `run_production_migration.sh` | Production migration runner |
| `ssl_setup.sh` | SSL certificate setup |
| `setup-cicd.sh` | CI/CD pipeline setup |
| `canary_deployment.py` | Canary deploy logic |
| `deploy_to_vps.sh` | VPS deployment |
| `migrate_remote_db.py` | Remote DB migration helper |
| `backup_rclone.sh` | Rclone shell backup |

## development/
| Script | Purpose |
|--------|---------|
| `add_credits.py` | Add credits to test user |
| `update_balance.py` | Update user balance |
| `add_indexes.py` | Add DB performance indexes |
| `create_admin_user.py` | Create admin account |
| `init_freemium_tiers.py` | Seed freemium tier config |
| `init_pricing_templates.py` | Seed pricing templates |
| `init_subscription_tiers_production.py` | Seed production tiers |
| `setup_affiliate_programs.py` | Seed affiliate programs |
| `setup_enterprise_tiers.py` | Seed enterprise tiers |
| `setup_test_tiers.py` | Seed test tier data |
| `setup_test_users.py` | Create test users |
| `check_api_balance.py` | Check TextVerified balance |
| `check_textverified_pricing.py` | Check live TV pricing |
| `compare_all_providers.py` | Compare SMS provider pricing |
| `tier_cli.py` | Tier management CLI |
| `tier_metrics.py` | Tier usage metrics |
| `run_tests.sh` | Run full test suite |
| `audit_api_models.py` | Audit API response models |

## maintenance/
| Script | Purpose |
|--------|---------|
| `reconcile_wallets.py` | Reconcile user wallet balances |
| `reconcile_refunds.py` | Reconcile pending refunds |
| `process_unreceived_refunds.py` | Process stuck refunds |
| `issue_refund.py` | Manual refund issuance |
| `critical_refund_analysis.py` | Analyse refund failures |
| `audit_financial_integrity.py` | Full financial audit |
| `backfill_verification_metrics.py` | Backfill historical metrics |
| `cancel_pending_verifications.py` | Cancel stuck verifications |
| `cleanup_old_verifications.py` | Purge old verification records |
| `clean_test_balances.py` | Reset test user balances |
| `reset_admin_account.py` | Reset admin account |
| `reset_admin_password.py` | Reset admin password |
| `reset_database.py` | Full DB reset (dev only) |
| `set_user_passwords.py` | Bulk password reset |
| `restore_backup.sh` | Restore from backup |

## security/
| Script | Purpose |
|--------|---------|
| `security_audit.py` | Full security audit |
| `api_security_scan.py` | API endpoint security scan |
| `security_scan.py` | Codebase security scan |
| `security_check.py` | Quick security check |
| `security_update.py` | Apply security updates |
| `manage_secrets.py` | Secrets management |
| `rotate_api_keys.sh` | Rotate API keys |
| `final_secrets_audit.sh` | Pre-deploy secrets audit |
| `run_security_tests.py` | Run security test suite |

## sql/
| File | Purpose |
|------|---------|
| `create_admin.sql` | Create admin user SQL |
| `create_payment_tables.sql` | Payment tables schema |
| `apply_payment_schema.sql` | Apply payment schema patch |
| `audit_unreceived_verifications.sql` | Audit query for unreceived SMS |
