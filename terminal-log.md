gitignore for project artifacts and temp files
b7ec960 Add DeepSource configuration for automated code quality analysis
2abac3e chore: cleanup and update gitignore
a097a87 Revert schema change - fix via DATABASE_URL instead
3ea37f2 Fix users table schema conflict with Supabase auth
bash-3.2$ cd "/Users/machine/Desktop/Namaskah. app" && git reset
Unstaged changes after reset:
M       .env.example
M       .eslintrc.js
M       .gitignore
M       .pre-commit-config.yaml
M       .prettierrc
D       DEPLOYMENT_CHECKLIST.md
D       FRONTEND_BACKEND_INTEGRATION.md
M       README.md
D       START_HERE.md
D       alembic/versions/001_initial_schema.py
D       alembic/versions/002_add_system_tables.py
D       alembic/versions/003_add_country_to_verification.py
D       alembic/versions/004_add_rentals_table.py
D       alembic/versions/005_add_5sim_fields.py
D       alembic/versions/006_add_google_oauth.py
D       alembic/versions/007_add_kyc_system.py
D       alembic/versions/008_add_enterprise_features.py
D       alembic/versions/009_add_waitlist_table.py
D       alembic/versions/010_add_whitelabel_table.py
D       alembic/versions/011_add_enterprise_tables.py
D       alembic/versions/012_add_affiliate_system.py
D       alembic/versions/013_add_5sim_fields.py
D       alembic/versions/0320b211ff27_add_rental_system.py
D       alembic/versions/83868cab20af_merge_google_oauth_with_existing_.py
D       app/api/admin.py
D       app/api/affiliate.py
D       app/api/ai_features.py
D       app/api/analytics.py
D       app/api/analytics_dashboard.py
D       app/api/analytics_fixed.py
D       app/api/analytics_rental.py
D       app/api/auth.py
D       app/api/blacklist.py
D       app/api/bulk_verification.py
D       app/api/business_features.py
D       app/api/business_intelligence.py
D       app/api/compliance.py
D       app/api/countries.py
D       app/api/dashboard.py
D       app/api/disaster_recovery.py
D       app/api/enterprise.py
D       app/api/forwarding.py
D       app/api/infrastructure.py
D       app/api/kyc.py
D       app/api/monitoring.py
D       app/api/personal_verify.py
D       app/api/preferences.py
D       app/api/rentals.py
D       app/api/reseller.py
D       app/api/revenue_sharing.py
D       app/api/services.py
D       app/api/setup.py
D       app/api/support.py
D       app/api/system.py
D       app/api/telegram.py
D       app/api/textverified.py
D       app/api/verification.py
D       app/api/verification_enhanced.py
D       app/api/waitlist.py
D       app/api/wallet.py
D       app/api/webhooks.py
D       app/api/websocket.py
D       app/api/whatsapp.py
D       app/api/whitelabel.py
D       app/api/whitelabel_enhanced.py
M       app/core/async_processing.py
M       app/core/auto_scaling.py
D       app/core/cache.py
D       app/core/caching.py
M       app/core/config.py
M       app/core/database_optimization.py
M       app/core/dependencies.py
M       app/core/exceptions.py
M       app/core/load_balancer.py
M       app/core/logging.py
M       app/core/metrics.py
M       app/core/migration.py
M       app/core/monitoring.py
M       app/core/region_manager.py
M       app/core/secrets.py
M       app/core/security_config.py
M       app/core/security_hardening.py
M       app/core/startup.py
M       app/middleware/__init__.py
M       app/middleware/csp.py
M       app/middleware/error_handler.py
M       app/middleware/error_handling.py
M       app/middleware/logging.py
M       app/middleware/monitoring.py
M       app/middleware/rate_limiting.py
M       app/middleware/security.py
M       app/middleware/whitelabel.py
M       app/models/__init__.py
M       app/models/affiliate.py
M       app/models/api_key.py
M       app/models/audit_log.py
M       app/models/base.py
M       app/models/blacklist.py
M       app/models/commission.py
M       app/models/enterprise.py
M       app/models/forwarding.py
M       app/models/kyc.py
M       app/models/payment.py
M       app/models/preferences.py
M       app/models/rental.py
M       app/models/reseller.py
M       app/models/system.py
M       app/models/transaction.py
M       app/models/user.py
M       app/models/verification.py
M       app/models/waitlist.py
M       app/models/whitelabel.py
M       app/models/whitelabel_enhanced.py
M       app/schemas/__init__.py
M       app/schemas/auth.py
M       app/schemas/kyc.py
M       app/schemas/payment.py
M       app/schemas/rental.py
M       app/schemas/rental_advanced.py
M       app/schemas/validators.py
M       app/schemas/verification.py
M       app/schemas/waitlist.py
M       app/services/__init__.py
M       app/services/affiliate_service.py
M       app/services/alerting_service.py
M       app/services/analytics_service.py
M       app/services/api_key_service.py
M       app/services/auth_service.py
M       app/services/auto_topup_service.py
M       app/services/business_intelligence.py
M       app/services/cdn_service.py
M       app/services/commission_engine.py
M       app/services/compliance_service.py
M       app/services/disaster_recovery.py
M       app/services/document_service.py
M       app/services/enterprise_service.py
M       app/services/fraud_detection.py
M       app/services/getsms_service.py
M       app/services/kyc_service.py
M       app/services/mfa_service.py
M       app/services/monitoring_service.py
M       app/services/notification_service.py
M       app/services/payment_service.py
M       app/services/provider_factory.py
M       app/services/rental_expiry_service.py
M       app/services/rental_service.py
M       app/services/reseller_service.py
M       app/services/smart_routing.py
M       app/services/sms_polling_service.py
M       app/services/sms_provider_interface.py
M       app/services/telegram_service.py
M       app/services/textverified_polling_service.py
M       app/services/textverified_service.py
M       app/services/webhook_notification_service.py
M       app/services/webhook_service.py
M       app/services/whatsapp_service.py
M       app/services/whitelabel_enhanced.py
M       app/services/whitelabel_service.py
M       app/tests/conftest.py
M       app/tests/test_admin_router.py
M       app/tests/test_analytics_router.py
M       app/tests/test_auth_service.py
M       app/tests/test_base_model.py
M       app/tests/test_base_service.py
M       app/tests/test_core_modules.py
M       app/tests/test_email_utils.py
M       app/tests/test_integration_comprehensive.py
M       app/tests/test_middleware.py
M       app/tests/test_middleware_complete.py
M       app/tests/test_rental_system.py
M       app/tests/test_schemas.py
M       app/tests/test_security_utils.py
M       app/tests/test_services.py
M       app/tests/test_utils.py
M       app/tests/test_validation_utils.py
M       app/utils/email.py
M       app/utils/performance.py
M       app/utils/validation.py
D       docker-compose.dev.yml
D       docker-compose.dr.yml
D       docker-compose.multi-region.yml
M       docker-compose.production.yml
M       main.py
M       monitoring/README.md
M       monitoring/alert_rules.yml
M       monitoring/alertmanager.yml
M       monitoring/grafana-dashboard.json
M       monitoring/grafana/provisioning/datasources/prometheus.yml
M       monitoring/prometheus.yml
M       monitoring/start_monitoring.sh
D       package-lock.json
D       package.json
M       requirements.txt
M       scripts/api_security_scan.py
M       scripts/backup_automation.sh
M       scripts/generate_analysis_report.py
M       scripts/setup_affiliate_programs.py
M       scripts/ssl_setup.sh
M       scripts/test_routes.py
D       static/css/auth.css
D       static/css/dark-theme.css
D       static/css/enhanced-ui.css
M       static/css/landing-improvements.css
D       static/css/legal-pages.css
D       static/css/mobile.css
M       static/css/style.css
D       static/js/analytics.js
D       static/js/auth-old.js
D       static/js/auth.js
D       static/js/cache-manager.js
D       static/js/config.js
D       static/js/csrf-token.js
D       static/js/dashboard-production.js
D       static/js/developer.js
D       static/js/enhanced-analytics.js
D       static/js/enhanced-dashboard.js
D       static/js/enhanced-verification-fixed.js
D       static/js/enhanced-verification-ui.js
D       static/js/enhanced-verification.js
D       static/js/error-handler.js
D       static/js/error-tracker.js
D       static/js/export_history.js
D       static/js/history.js
M       static/js/main.js
M       static/js/minimal-error-handling.js
D       static/js/mobile.js
D       static/js/notification-system.js
D       static/js/performance-monitor.js
D       static/js/performance-optimizer.js
D       static/js/realtime-ui.js
D       static/js/receipts.js
D       static/js/rentals.js
D       static/js/searchable-dropdown.js
D       static/js/secure-analytics.js
D       static/js/secure-verification.js
D       static/js/security-utils-fixed.js
D       static/js/security-utils-safe.js
D       static/js/security-utils.js
D       static/js/security.js
D       static/js/services.js
D       static/js/settings.js
D       static/js/test-error-handling.js
D       static/js/universal-nav.js
D       static/js/utils.js
D       static/js/verification-simple.js
D       static/js/verification.js
D       static/js/wallet.js
D       static/js/websocket.js
M       static/manifest.json
M       static/sw.js
M       templates/analytics_dashboard.html
D       templates/dashboard.html
D       templates/dashboard_enhanced.html
D       templates/dashboard_fixed.html
M       templates/dashboard_main.html
D       templates/enhanced_dashboard.html
M       templates/landing.html
M       templates/login.html
D       templates/verification_clean.html
D       templates/verification_dashboard.html
D       templates/verification_dashboard_v2_backup.html
M       templates/verification_enhanced.html
D       templates/verification_prod.html
bash-3.2$ cd "/Users/machine/Desktop/Namaskah. app" && git add .gitignore .env.example .pre-commit-config.yaml README.md requirements.txt monitoring/
bash-3.2$ cd "/Users/machine/Desktop/Namaskah. app" && git commit -m "chore: update configs and documentation
> 
> - Update gitignore for better artifact management
> - Update requirements and environment configs  
> - Consolidate monitoring setup configuration
> - Update README
> 
> Clean, safe cleanup without refactoring."
🔍 Checking for secrets in staged files...
✅ No real secrets detected in staged files.
[main bd3bdc4] chore: update configs and documentation
 13 files changed, 447 insertions(+), 614 deletions(-)
 create mode 100644 monitoring/grafana/provisioning/dashboards/dashboards.yml
bash-3.2$ cd "/Users/machine/Desktop/Namaskah. app" && git push origin main
Enumerating objects: 37, done.
Counting objects: 100% (37/37), done.
Delta compression using up to 4 threads
Compressing objects: 100% (18/18), done.
Writing objects: 100% (20/20), 15.68 KiB | 7.84 MiB/s, done.
Total 20 (delta 6), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (6/6), completed with 6 local objects.
To https://github.com/Infradevandops/NAMASKAHsms.git
   5f18e75..bd3bdc4  main -> main
bash-3.2$ cd "/Users/machine/Desktop/Namaskah. app" && git log --oneline -3
bd3bdc4 (HEAD -> main, origin/main) chore: update configs and documentation
5f18e75 Update gitignore for project artifacts and temp files
b7ec960 Add DeepSource configuration for automated code quality analysis
bash-3.2$ 
bash-3.2$ # View what's left
git status

# Option A: Keep refactoring for later (safe - nothing staged)^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^Hq translate 'View what'"'"'s left'
ash

# Option B: Review and stage refactoring in smaller chunks
git add app/api/admin/  # One directory at a time
git commit -m "refactor: reorganize bash-3.2$ git status

# Option A: Keep refactoring for later (safe - nothing staged)^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^Hq translate 'View what'"'"'s left'
ash

# Option B: Review and stage refactoring in smaller chunks
git add app/api/admin/  # One directory at a time
git commit -m "refactor: reorganize admin routes"On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add/rm <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   .eslintrc.js
        modified:   .prettierrc
        deleted:    DEPLOYMENT_CHECKLIST.md
        deleted:    FRONTEND_BACKEND_INTEGRATION.md
        deleted:    START_HERE.md
        deleted:    alembic/versions/001_initial_schema.py
        deleted:    alembic/versions/002_add_system_tables.py
        deleted:    alembic/versions/003_add_country_to_verification.py
        deleted:    alembic/versions/004_add_rentals_table.py
        deleted:    alembic/versions/005_add_5sim_fields.py
        deleted:    alembic/versions/006_add_google_oauth.py
        deleted:    alembic/versions/007_add_kyc_system.py
        deleted:    alembic/versions/008_add_enterprise_features.py
        deleted:    alembic/versions/009_add_waitlist_table.py
        deleted:    alembic/versions/010_add_whitelabel_table.py
        deleted:    alembic/versions/011_add_enterprise_tables.py
        deleted:    alembic/versions/012_add_affiliate_system.py
        deleted:    alembic/versions/013_add_5sim_fields.py
        deleted:    alembic/versions/0320b211ff27_add_rental_system.py
        deleted:    alembic/versions/83868cab20af_merge_google_oauth_with_existing_.py
        deleted:    app/api/admin.py
        deleted:    app/api/affiliate.py
        deleted:    app/api/ai_features.py
        deleted:    app/api/analytics.py
        deleted:    app/api/analytics_dashboard.py
        deleted:    app/api/analytics_fixed.py
        deleted:    app/api/analytics_rental.py
        deleted:    app/api/auth.py
        deleted:    app/api/blacklist.py
        deleted:    app/api/bulk_verification.py
        deleted:    app/api/business_features.py
        deleted:    app/api/business_intelligence.py
        deleted:    app/api/compliance.py
        deleted:    app/api/countries.py
        deleted:    app/api/dashboard.py
        deleted:    app/api/disaster_recovery.py
        deleted:    app/api/enterprise.py
        deleted:    app/api/forwarding.py
        deleted:    app/api/infrastructure.py
        deleted:    app/api/kyc.py
        deleted:    app/api/monitoring.py
        deleted:    app/api/personal_verify.py
        deleted:    app/api/preferences.py
        deleted:    app/api/rentals.py
        deleted:    app/api/reseller.py
        deleted:    app/api/revenue_sharing.py
        deleted:    app/api/services.py
        deleted:    app/api/setup.py
        deleted:    app/api/support.py
        deleted:    app/api/system.py
        deleted:    app/api/telegram.py
        deleted:    app/api/textverified.py
        deleted:    app/api/verification.py
        deleted:    app/api/verification_enhanced.py
        deleted:    app/api/waitlist.py
        deleted:    app/api/wallet.py
        deleted:    app/api/webhooks.py
        deleted:    app/api/websocket.py
        deleted:    app/api/whatsapp.py
        deleted:    app/api/whitelabel.py
        deleted:    app/api/whitelabel_enhanced.py
        modified:   app/core/async_processing.py
        modified:   app/core/auto_scaling.py
        deleted:    app/core/cache.py
        deleted:    app/core/caching.py
        modified:   app/core/config.py
        modified:   app/core/database_optimization.py
        modified:   app/core/dependencies.py
        modified:   app/core/exceptions.py
        modified:   app/core/load_balancer.py
        modified:   app/core/logging.py
        modified:   app/core/metrics.py
        modified:   app/core/migration.py
        modified:   app/core/monitoring.py
        modified:   app/core/region_manager.py
        modified:   app/core/secrets.py
        modified:   app/core/security_config.py
        modified:   app/core/security_hardening.py
        modified:   app/core/startup.py
        modified:   app/middleware/__init__.py
        modified:   app/middleware/csp.py
        modified:   app/middleware/error_handler.py
        modified:   app/middleware/error_handling.py
        modified:   app/middleware/logging.py
        modified:   app/middleware/monitoring.py
        modified:   app/middleware/rate_limiting.py
        modified:   app/middleware/security.py
        modified:   app/middleware/whitelabel.py
        modified:   app/models/__init__.py
        modified:   app/models/affiliate.py
        modified:   app/models/api_key.py
        modified:   app/models/audit_log.py
        modified:   app/models/base.py
        modified:   app/models/blacklist.py
        modified:   app/models/commission.py
        modified:   app/models/enterprise.py
        modified:   app/models/forwarding.py
        modified:   app/models/kyc.py
        modified:   app/models/payment.py
        modified:   app/models/preferences.py
        modified:   app/models/rental.py
        modified:   app/models/reseller.py
        modified:   app/models/system.py
        modified:   app/models/transaction.py
        modified:   app/models/user.py
        modified:   app/models/verification.py
        modified:   app/models/waitlist.py
        modified:   app/models/whitelabel.py
        modified:   app/models/whitelabel_enhanced.py
        modified:   app/schemas/__init__.py
        modified:   app/schemas/auth.py
        modified:   app/schemas/kyc.py
        modified:   app/schemas/payment.py
        modified:   app/schemas/rental.py
        modified:   app/schemas/rental_advanced.py
        modified:   app/schemas/validators.py
        modified:   app/schemas/verification.py
        modified:   app/schemas/waitlist.py
        modified:   app/services/__init__.py
        modified:   app/services/affiliate_service.py
        modified:   app/services/alerting_service.py
        modified:   app/services/analytics_service.py
        modified:   app/services/api_key_service.py
        modified:   app/services/auth_service.py
        modified:   app/services/auto_topup_service.py
        modified:   app/services/business_intelligence.py
        modified:   app/services/cdn_service.py
        modified:   app/services/commission_engine.py
        modified:   app/services/compliance_service.py
        modified:   app/services/disaster_recovery.py
        modified:   app/services/document_service.py
        modified:   app/services/enterprise_service.py
        modified:   app/services/fraud_detection.py
        modified:   app/services/getsms_service.py
        modified:   app/services/kyc_service.py
        modified:   app/services/mfa_service.py
        modified:   app/services/monitoring_service.py
        modified:   app/services/notification_service.py
        modified:   app/services/payment_service.py
        modified:   app/services/provider_factory.py
        modified:   app/services/rental_expiry_service.py
        modified:   app/services/rental_service.py
        modified:   app/services/reseller_service.py
        modified:   app/services/smart_routing.py
        modified:   app/services/sms_polling_service.py
        modified:   app/services/sms_provider_interface.py
        modified:   app/services/telegram_service.py
        modified:   app/services/textverified_polling_service.py
        modified:   app/services/textverified_service.py
        modified:   app/services/webhook_notification_service.py
        modified:   app/services/webhook_service.py
        modified:   app/services/whatsapp_service.py
        modified:   app/services/whitelabel_enhanced.py
        modified:   app/services/whitelabel_service.py
        modified:   app/tests/conftest.py
        modified:   app/tests/test_admin_router.py
        modified:   app/tests/test_analytics_router.py
        modified:   app/tests/test_auth_service.py
        modified:   app/tests/test_base_model.py
        modified:   app/tests/test_base_service.py
        modified:   app/tests/test_core_modules.py
        modified:   app/tests/test_email_utils.py
        modified:   app/tests/test_integration_comprehensive.py
        modified:   app/tests/test_middleware.py
        modified:   app/tests/test_middleware_complete.py
        modified:   app/tests/test_rental_system.py
        modified:   app/tests/test_schemas.py
        modified:   app/tests/test_security_utils.py
        modified:   app/tests/test_services.py
        modified:   app/tests/test_utils.py
        modified:   app/tests/test_validation_utils.py
        modified:   app/utils/email.py
        modified:   app/utils/performance.py
        modified:   app/utils/validation.py
        deleted:    docker-compose.dev.yml
        deleted:    docker-compose.dr.yml
        deleted:    docker-compose.multi-region.yml
        modified:   docker-compose.production.yml
        modified:   main.py
        deleted:    package-lock.json
        deleted:    package.json
        modified:   scripts/api_security_scan.py
        modified:   scripts/backup_automation.sh
        modified:   scripts/generate_analysis_report.py
        modified:   scripts/setup_affiliate_programs.py
        modified:   scripts/ssl_setup.sh
        modified:   scripts/test_routes.py
        deleted:    static/css/auth.css
        deleted:    static/css/dark-theme.css
        deleted:    static/css/enhanced-ui.css
        modified:   static/css/landing-improvements.css
        deleted:    static/css/legal-pages.css
        deleted:    static/css/mobile.css
        modified:   static/css/style.css
        deleted:    static/js/analytics.js
        deleted:    static/js/auth-old.js
        deleted:    static/js/auth.js
        deleted:    static/js/cache-manager.js
        deleted:    static/js/config.js
        deleted:    static/js/csrf-token.js
        deleted:    static/js/dashboard-production.js
        deleted:    static/js/developer.js
        deleted:    static/js/enhanced-analytics.js
        deleted:    static/js/enhanced-dashboard.js
        deleted:    static/js/enhanced-verification-fixed.js
        deleted:    static/js/enhanced-verification-ui.js
        deleted:    static/js/enhanced-verification.js
        deleted:    static/js/error-handler.js
        deleted:    static/js/error-tracker.js
        deleted:    static/js/export_history.js
        deleted:    static/js/history.js
        modified:   static/js/main.js
        modified:   static/js/minimal-error-handling.js
        deleted:    static/js/mobile.js
        deleted:    static/js/notification-system.js
        deleted:    static/js/performance-monitor.js
        deleted:    static/js/performance-optimizer.js
        deleted:    static/js/realtime-ui.js
        deleted:    static/js/receipts.js
        deleted:    static/js/rentals.js
        deleted:    static/js/searchable-dropdown.js
        deleted:    static/js/secure-analytics.js
        deleted:    static/js/secure-verification.js
        deleted:    static/js/security-utils-fixed.js
        deleted:    static/js/security-utils-safe.js
        deleted:    static/js/security-utils.js
        deleted:    static/js/security.js
        deleted:    static/js/services.js
        deleted:    static/js/settings.js
        deleted:    static/js/test-error-handling.js
        deleted:    static/js/universal-nav.js
        deleted:    static/js/utils.js
        deleted:    static/js/verification-simple.js
        deleted:    static/js/verification.js
        deleted:    static/js/wallet.js
        deleted:    static/js/websocket.js
        modified:   static/manifest.json
        modified:   static/sw.js
        modified:   templates/analytics_dashboard.html
        deleted:    templates/dashboard.html
        deleted:    templates/dashboard_enhanced.html
        deleted:    templates/dashboard_fixed.html
        modified:   templates/dashboard_main.html
        deleted:    templates/enhanced_dashboard.html
        modified:   templates/landing.html
        modified:   templates/login.html
        deleted:    templates/verification_clean.html
        deleted:    templates/verification_dashboard.html
        deleted:    templates/verification_dashboard_v2_backup.html
        modified:   templates/verification_enhanced.html
        deleted:    templates/verification_prod.html

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .env.docker
        .github/
        START_SERVER.sh
        add_dashboard_route.py
        alembic/versions/001_consolidated_initial_schema.py
        alembic/versions/002_auth_security_tables.py
        alembic/versions/003_session_management.py
        alembic/versions/004_add_moderator_role.py
        alembic/versions/005_add_performance_indexes.py
        alembic/versions/06e5fe3aacd9_add_bulk_id_to_verifications.py
        alembic/versions/a828e54f0016_merge_heads.py
        alembic/versions/add_sms_forwarding_model.py
        alembic/versions/add_sms_message_model.py
        alembic/versions/f6a9a9aafab3_add_soft_delete_columns.py
        app/api/admin/
        app/api/analytics/
        app/api/business/
        app/api/core/
        app/api/integrations/
        app/api/rentals/
        app/api/verification/
        app/core/api_versioning.py
        app/core/auth_security.py
        app/core/config_secrets.py
        app/core/csrf_protection.py
        app/core/custom_exceptions.py
        app/core/database_indexes.py
        app/core/database_indexes_fixed.py
        app/core/email_verification.py
        app/core/encryption.py
        app/core/openapi.py
        app/core/performance_monitor.py
        app/core/performance_monitor_fixed.py
        app/core/query_optimization.py
        app/core/query_optimization_fixed.py
        app/core/rbac.py
        app/core/secrets_audit.py
        app/core/secrets_manager.py
        app/core/session_manager.py
        app/core/token_manager.py
        app/core/unified_cache.py
        app/core/unified_error_handling.py
        app/core/unified_rate_limiting.py
        app/middleware/csrf_middleware.py
        app/middleware/prometheus.py
        app/middleware/rate_limit_middleware.py
        app/middleware/xss_protection.py
        app/models/sms_forwarding.py
        app/models/sms_message.py
        app/services/adaptive_polling.py
        app/services/audit_service.py
        app/services/error_handling.py
        app/services/event_service.py
        app/services/fivesim_provider.py
        app/services/fivesim_service.py
        app/services/fraud_detection_service.py
        app/services/oauth_service.py
        app/services/provider_base.py
        app/services/provider_init.py
        app/services/provider_manager.py
        app/services/provider_optimizer.py
        app/services/provider_orchestrator.py
        app/services/provider_registry.py
        app/services/provider_system.py
        app/services/sms_activate_service.py
        app/services/smsactivate_provider.py
        app/services/textverified_api.py
        app/services/textverified_auth.py
        app/services/textverified_integration.py
        app/services/textverified_provider.py
        app/services/textverified_service_updated.py
        app/services/unified_provider.py
        app/tests/fixtures.py
        app/tests/test_analytics_refactor.py
        app/tests/test_api_integration.py
        app/tests/test_cache_consolidation.py
        app/tests/test_core_services.py
        app/tests/test_data_masking.py
        app/tests/test_exception_handling.py
        app/tests/test_log_injection.py
        app/tests/test_path_traversal.py
        app/tests/test_provider_consolidation.py
        app/tests/test_provider_integration.py
        app/tests/test_security.py
        app/tests/test_security_comprehensive.py
        app/tests/test_sql_injection.py
        app/tests/test_textverified_integration.py
        app/tests/test_textverified_service.py
        app/tests/test_timezone_utils.py
        app/tests/test_unified_error_handling.py
        app/tests/test_unified_rate_limiting.py
        app/tests/test_verification_consolidation.py
        app/tests/test_webhook_service.py
        app/tests/test_xss_prevention.py
        app/utils/data_masking.py
        app/utils/exception_handling.py
        app/utils/function_refactor.py
        app/utils/log_sanitization.py
        app/utils/path_security.py
        app/utils/sanitization.py
        app/utils/timezone_utils.py
        check_status.sh
        create_admin.py
        create_test_user.py
        deploy_production.sh
        docker-compose.test.yml
        docs/FINAL_SECURITY_AUDIT.md
        fix_missing_tables.py
        init_database.py
        init_db.py
        main_patch.py
        monitoring_setup.py
        nginx-lb.conf
        nginx-ssl.conf
        postcss.config.js
        scripts/backup_database.py
        scripts/cleanup_migrations.sh
        scripts/fix_all_syntax_errors.py
        scripts/fix_code_quality.py
        scripts/fix_import_syntax.py
        scripts/fix_remaining_issues.py
        scripts/fix_syntax_errors.py
        scripts/fix_timezone_issues.py
        scripts/load_test.py
        scripts/load_test_fixed.py
        scripts/load_test_simple.py
        scripts/phase5_comprehensive_testing.py
        scripts/phase5_documentation_update.py
        scripts/phase5_final_validation.py
        scripts/remove_unused_imports.py
        scripts/restore_backup.sh
        scripts/run_security_tests.py
        scripts/safe_code_fixes.py
        scripts/security_scan.py
        scripts/simple_validation.py
        scripts/validate_exception_handling.py
        scripts/validate_migrations.py
        scripts/validate_sensitive_info.py
        setup_production.sh
        simple_login.py
        static/css/accessibility.css
        static/css/base.css
        static/css/responsive.css
        static/css/theme.css
        static/favicon.ico
        static/js/main.optimized.js
        static/js/modules/
        static/js/social-proof.js
        static/js/theme-toggle.js
        templates/account_settings.html
        templates/admin_dashboard.html
        templates/api_keys.html
        templates/billing_dashboard.html
        templates/dashboard_complete.html
        templates/gdpr_settings.html
        templates/register.html
        templates/rental_management.html
        templates/sms_inbox.html
        templates/verification_fixed.html
        terminal-log.md
        test-auth.py
        test_api.sh
        test_available_services.py
        test_login_direct.py
        test_server.py
        test_stock_availability.py
        test_textverified.py
        test_textverified_simple.py
        vite.config.js

no changes added to commit (use "git add" and/or "git commit -a")
bash-3.2$ 
bash-3.2$ q translate 'View what'"'"'s left'
error: You are not logged in. Run q login to login.
bash-3.2$ ash
bash: ash: command not found
bash-3.2$ 
bash-3.2$ # Option B: Review and stage refactoring in smaller chunks
bash-3.2$ git add app/api/admin/  # One directory at a time
bash-3.2$ git commit -m "refactor: reorganize admin routes"
bash-3.2$ # Option q translate 'Option A: Stash current changes (safest - preser'
remental commits^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^H^Hq translate 'Option q translate '"'"'Option A: Stash current changes (safest - preser'"'"''
 -m "refactor: reorganize admin routes into dedicated module"
git add app/api/core/
git commit -m "refactor: consolidate core API routes"
# ... continbash-3.2$ q translate 'Option q translate '"'"'Option A: Stash currenafest - preser'"'"''
 -m "refactor: reorganize admin routes into dedicated module"
git add app/api/core/
git commit -m "refactor: consolidate core API routes"
# ... continue for other moduleserror: You are not logged in. Run q login to login.
bash-3.2$  -m "refactor: reorganize admin routes into dedicated module"
bash: -m: command not found
bash-3.2$ git add app/api/core/
bash-3.2$ git commit -m "refactor: consolidate core API routes"
🔍 Checking for secrets in staged files...
✅ No real secrets detected in staged files.
[main 96e7fe0] refactor: consolidate core API routes
 27 files changed, 5050 insertions(+)
 create mode 100644 app/api/admin/__init__.py
 create mode 100644 app/api/admin/admin.py
 create mode 100644 app/api/admin/admin_router.py
 create mode 100644 app/api/admin/alerts.py
 create mode 100644 app/api/admin/analytics_monitoring.py
 create mode 100644 app/api/admin/compliance.py
 create mode 100644 app/api/admin/dashboard.py
 create mode 100644 app/api/admin/disaster_recovery.py
 create mode 100644 app/api/admin/infrastructure.py
 create mode 100644 app/api/admin/kyc.py
 create mode 100644 app/api/admin/monitoring.py
 create mode 100644 app/api/admin/support.py
 create mode 100644 app/api/core/__init__.py
 create mode 100644 app/api/core/auth.py
 create mode 100644 app/api/core/auth_enhanced.py
 create mode 100644 app/api/core/blacklist.py
 create mode 100644 app/api/core/countries.py
 create mode 100644 app/api/core/forwarding.py
 create mode 100644 app/api/core/gdpr.py
 create mode 100644 app/api/core/preferences.py
 create mode 100644 app/api/core/provider_health.py
 create mode 100644 app/api/core/services.py
 create mode 100644 app/api/core/setup.py
 create mode 100644 app/api/core/system.py
 create mode 100644 app/api/core/waitlist.py
 create mode 100644 app/api/core/wallet.py
 create mode 100644 app/api/core/wallet_updated.py
bash-3.2$ # ... continue for other modules