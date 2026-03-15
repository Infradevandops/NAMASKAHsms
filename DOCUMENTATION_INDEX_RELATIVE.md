# Documentation Index - Relative Files

**Version**: 1.0  
**Status**: Complete  
**Last Updated**: March 15, 2026

---

## 📚 Documentation Structure

All documentation files are organized by category and marked with their relative paths from project root.

---

## 🏠 Root Level Documentation

### Project Overview
- `README.md` - Main project documentation
- `CHANGELOG.md` - Version history and releases
- `SETUP.md` - Setup and installation guide
- `PROJECT_COMPLETION_SUMMARY.md` - Final project completion summary

### Configuration Files
- `alembic.ini` - Database migration configuration
- `pytest.ini` - Testing configuration
- `setup.cfg` - Setup configuration
- `Makefile` - Build automation
- `Taskfile.yml` - Task automation

### Deployment Files
- `render.yaml` - Render staging deployment config
- `render.production.yaml` - Render production deployment config
- `docker-compose.yml` - Development Docker Compose
- `docker-compose.production.yml` - Production Docker Compose
- `docker-compose.test.yml` - Testing Docker Compose
- `Dockerfile` - Application Docker image
- `Dockerfile.test` - Testing Docker image
- `k8s-deployment.yaml` - Kubernetes deployment config

### Environment Files
- `.env` - Environment variables (local)
- `.env.local` - Local environment overrides
- `.env.example` - Environment template
- `.gitignore` - Git ignore rules
- `.bandit` - Security scanning config

---

## 📁 Documentation Directory (`docs/`)

### Phase Documentation
- `docs/PHASE3_COMPLETION_REPORT.md` - Phase 3 completion report
- `docs/PHASE3_IMPLEMENTATION_SUMMARY.md` - Phase 3 implementation summary
- `docs/PHASE3_QUICK_START.md` - Phase 3 quick start guide
- `docs/PHASE3_TESTING_VALIDATION.md` - Phase 3 testing and validation
- `docs/PHASE4_ROADMAP.md` - Phase 4 roadmap
- `docs/PHASE4_COMPLETION_REPORT.md` - Phase 4 completion report

### Task Documentation
- `docs/tasks/TIER_IDENTIFICATION_SYSTEM_TASKS.md` - Main task file (all phases)
- `docs/tasks/CARRIER_LOOKUP_STRATEGY.md` - Carrier lookup strategy
- `docs/tasks/TEXTVERIFIED_ALIGNMENT_ROADMAP.md` - TextVerified alignment roadmap

### Deployment Documentation
- `docs/deployment/PRODUCTION_DEPLOYMENT_RUNBOOK.md` - Production deployment guide
- `docs/deployment/MONITORING_GUIDE.md` - Monitoring setup guide
- `docs/deployment/PERFORMANCE_TUNING_GUIDE.md` - Performance tuning guide
- `docs/deployment/TROUBLESHOOTING_GUIDE.md` - Troubleshooting procedures

### Fix Documentation
- `docs/fixes/CARRIER_LOOKUP_IMPLEMENTATION.md` - Carrier lookup implementation
- `docs/fixes/TEXTVERIFIED_CARRIER_IMPLEMENTATION.md` - TextVerified carrier implementation

### API Documentation
- `docs/api/` - API documentation directory

### Development Documentation
- `docs/development/` - Development guides

### Security Documentation
- `docs/security/` - Security documentation

### Archive Documentation
- `docs/archive/` - Archived documentation

---

## 🔧 Scripts Directory (`scripts/`)

### Deployment Scripts
- `scripts/deployment/pre_deploy_checks.py` - Pre-deployment verification
- `scripts/deployment/post_deploy_verification.py` - Post-deployment verification
- `scripts/deployment/canary_deployment.py` - Canary deployment manager

### Development Scripts
- `scripts/development/` - Development utilities

### Maintenance Scripts
- `scripts/maintenance/` - Maintenance utilities

### Security Scripts
- `scripts/security/` - Security utilities

### SQL Scripts
- `scripts/sql/` - Database scripts

### Other Scripts
- `scripts/add_indexes.py` - Add database indexes
- `scripts/backup_database.py` - Database backup
- `scripts/create_admin_user.py` - Create admin user
- `scripts/fix_production_schema.py` - Fix production schema
- `scripts/generate_secure_keys.py` - Generate security keys
- `scripts/tier_cli.py` - Tier management CLI
- `scripts/tier_metrics.py` - Tier metrics collection

---

## 🧪 Tests Directory (`tests/`)

### Test Categories
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests
- `tests/frontend/` - Frontend tests
- `tests/api/` - API tests
- `tests/load/` - Load tests
- `tests/security/` - Security tests

### Test Files
- `tests/conftest.py` - Pytest configuration
- `tests/README.md` - Testing guide

---

## 📱 Frontend Directory (`static/`)

### JavaScript
- `static/js/tier-loader.js` - Tier loader implementation
- `static/js/skeleton-loader.js` - Skeleton loader implementation
- `static/js/app-init.js` - App initialization
- `static/js/tier-sync.js` - Tier synchronization
- `static/js/performance-optimization.js` - Frontend performance optimization

### CSS
- `static/css/` - Stylesheets

### Fonts
- `static/fonts/` - Font files

### Icons
- `static/icons/` - Icon files

### Images
- `static/images/` - Image files

### Locales
- `static/locales/` - Internationalization files

### Other
- `static/manifest.json` - PWA manifest
- `static/robots.txt` - SEO robots file
- `static/sitemap.xml` - SEO sitemap
- `static/favicon.ico` - Favicon

---

## 🎨 Templates Directory (`templates/`)

### Base Templates
- `templates/base.html` - Base template
- `templates/public_base.html` - Public base template
- `templates/dashboard_base.html` - Dashboard base template
- `templates/admin_base.html` - Admin base template

### Page Templates
- `templates/landing.html` - Landing page
- `templates/login.html` - Login page
- `templates/register.html` - Registration page
- `templates/dashboard.html` - Dashboard page
- `templates/pricing.html` - Pricing page
- `templates/verify_modern.html` - Verification page

### Component Templates
- `templates/components/` - Reusable components

### Macro Templates
- `templates/macros/` - Template macros

### Admin Templates
- `templates/admin/` - Admin pages

---

## 🔌 Application Directory (`app/`)

### API Layer
- `app/api/core/auth.py` - Authentication router
- `app/api/core/wallet.py` - Wallet router
- `app/api/core/verification.py` - Verification router
- `app/api/core/countries.py` - Countries router
- `app/api/billing/tiers.py` - Tier router
- `app/api/admin/admin.py` - Admin router
- `app/api/admin/kyc.py` - KYC router
- `app/api/admin/support.py` - Support router

### Services Layer
- `app/services/auth_service.py` - Authentication service
- `app/services/payment_service.py` - Payment service
- `app/services/sms_service.py` - SMS service
- `app/services/tier_service.py` - Tier service
- `app/services/webhook_service.py` - Webhook service
- `app/services/tier_manager.py` - Tier manager

### Models Layer
- `app/models/user.py` - User model
- `app/models/transaction.py` - Transaction model
- `app/models/verification.py` - Verification model
- `app/models/subscription_tier.py` - Subscription tier model

### Core Layer
- `app/core/database.py` - Database connection
- `app/core/cache.py` - Redis cache
- `app/core/config.py` - Configuration
- `app/core/dependencies.py` - Shared dependencies
- `app/core/sentry.py` - Sentry integration
- `app/core/metrics.py` - Prometheus metrics
- `app/core/cache_optimization.py` - Cache optimization
- `app/core/response_optimization.py` - Response optimization
- `app/core/database_optimization.py` - Database optimization
- `app/core/logging.py` - Logging configuration

### Middleware Layer
- `app/middleware/auth.py` - Authentication middleware
- `app/middleware/tier_verification.py` - Tier verification middleware
- `app/middleware/rate_limiting.py` - Rate limiting middleware
- `app/middleware/logging.py` - Request logging middleware
- `app/middleware/monitoring.py` - Monitoring middleware

### Monitoring Layer
- `app/monitoring/` - Monitoring utilities

### Schemas Layer
- `app/schemas/` - Pydantic schemas

### Utils Layer
- `app/utils/` - Utility functions

### WebSocket Layer
- `app/websocket/` - WebSocket handlers

### Workers Layer
- `app/workers/` - Background workers

---

## 🔧 Configuration Directory (`config/`)

### Nginx Configuration
- `config/nginx.conf` - Base Nginx configuration
- `config/nginx-production.conf` - Production Nginx configuration
- `config/nginx-ssl.conf` - SSL Nginx configuration
- `config/nginx-lb.conf` - Load balancer Nginx configuration
- `config/nginx-multi-region.conf` - Multi-region Nginx configuration
- `config/README.md` - Nginx configuration guide

---

## 📊 Monitoring Directory (`monitoring/`)

### Monitoring Configuration
- `monitoring/prometheus.yml` - Prometheus configuration
- `monitoring/prometheus-config.yml` - Alternative Prometheus config
- `monitoring/alert_rules.yml` - Prometheus alert rules
- `monitoring/tier_alerts.yml` - Tier-specific alerts
- `monitoring/alertmanager.yml` - AlertManager configuration
- `monitoring/grafana-dashboard.json` - Grafana dashboard

### Monitoring Docker
- `monitoring/docker-compose.yml` - Monitoring stack Docker Compose

### Monitoring Scripts
- `monitoring/start_monitoring.sh` - Start monitoring stack

### Monitoring Documentation
- `monitoring/README.md` - Monitoring guide

---

## 🛠️ Tools Directory (`tools/`)

### Postman
- `tools/postman/` - Postman API collections

### Configuration
- `tools/gitleaks.toml` - GitLeaks configuration
- `tools/pyproject.toml` - Python project configuration

### Utilities
- `tools/lighthouse_audit.js` - Lighthouse audit script

---

## 📋 Project Status Files

### Completion Reports
- `PHASE3_CLEANUP_VERIFICATION.md` - Phase 3 cleanup verification
- `PHASE3_COMPLETE_SUMMARY.md` - Phase 3 complete summary
- `PHASE3_FINAL_SUMMARY.md` - Phase 3 final summary
- `PROJECT_STATUS_REPORT.md` - Project status report
- `CLEANUP_COMPLETE.md` - Cleanup completion report
- `DOCUMENTATION_ORGANIZATION.md` - Documentation organization guide
- `DOCUMENTATION_INDEX.md` - Documentation index

---

## 📦 Requirements Files

### Python Dependencies
- `requirements.txt` - Main dependencies
- `requirements-dev.txt` - Development dependencies
- `requirements-test.txt` - Testing dependencies
- `requirements-monitoring.txt` - Monitoring dependencies
- `requirements-security.txt` - Security dependencies

---

## 🚀 Startup Scripts

- `start.sh` - Start application
- `restart.sh` - Restart application
- `render_build.sh` - Render build script
- `run_tests.sh` - Run tests
- `run_phase3_tests.sh` - Run Phase 3 tests
- `security_scan.sh` - Security scanning
- `setup_gitlab_token.sh` - Setup GitLab token
- `setup_uptimerobot.sh` - Setup UptimeRobot

---

## 📁 Archive Directory (`archive/`)

### Archived Documentation
- `archive/deployment-strategy-2026/` - Archived deployment strategy
- `archive/feb-2026-api-fixes/` - Archived API fixes
- `archive/feb-2026-cleanup/` - Archived cleanup
- `archive/i18n-fix-2026-03-08/` - Archived i18n fixes
- `archive/planning-docs-2026/` - Archived planning docs
- `archive/project-status-2026/` - Archived project status
- `archive/redundant-docs-2026/` - Archived redundant docs

---

## 📂 Other Directories

### Uploads
- `uploads/kyc/` - KYC document uploads

### Logs
- `logs/app.log` - Application logs

### Alembic
- `alembic/versions/` - Database migration versions
- `alembic/env.py` - Alembic environment
- `alembic/script.py.mako` - Alembic script template
- `alembic/utils.py` - Alembic utilities

### GitHub
- `.github/workflows/` - GitHub Actions workflows

### Amazon Q
- `.amazonq/rules/` - Amazon Q rules

---

## 🔍 Documentation Categories

### Getting Started
- `README.md` - Start here
- `SETUP.md` - Installation guide
- `docs/PHASE3_QUICK_START.md` - Quick start

### Deployment
- `docs/deployment/PRODUCTION_DEPLOYMENT_RUNBOOK.md` - Deployment guide
- `render.production.yaml` - Production config
- `docker-compose.production.yml` - Production Docker

### Monitoring
- `docs/deployment/MONITORING_GUIDE.md` - Monitoring setup
- `monitoring/prometheus.yml` - Prometheus config
- `monitoring/grafana-dashboard.json` - Grafana dashboard

### Performance
- `docs/deployment/PERFORMANCE_TUNING_GUIDE.md` - Performance guide
- `app/core/cache_optimization.py` - Cache optimization
- `app/core/database_optimization.py` - Database optimization

### Testing
- `tests/README.md` - Testing guide
- `docs/PHASE3_TESTING_VALIDATION.md` - Testing documentation

### Troubleshooting
- `docs/deployment/TROUBLESHOOTING_GUIDE.md` - Troubleshooting guide

### API
- `docs/api/` - API documentation

### Security
- `docs/security/` - Security documentation

### Development
- `docs/development/` - Development guides

---

## 📊 Documentation Statistics

| Category | Count | Status |
|----------|-------|--------|
| Root Documentation | 4 | ✅ Complete |
| Phase Documentation | 6 | ✅ Complete |
| Task Documentation | 3 | ✅ Complete |
| Deployment Documentation | 4 | ✅ Complete |
| Fix Documentation | 2 | ✅ Complete |
| Configuration Files | 13 | ✅ Complete |
| Deployment Scripts | 3 | ✅ Complete |
| Test Files | 50+ | ✅ Complete |
| Frontend Files | 5+ | ✅ Complete |
| Template Files | 40+ | ✅ Complete |
| Application Files | 50+ | ✅ Complete |
| **TOTAL** | **180+** | **✅ Complete** |

---

## 🎯 Quick Navigation

### For Developers
1. Start: `README.md`
2. Setup: `SETUP.md`
3. Development: `docs/development/`
4. Testing: `tests/README.md`

### For DevOps
1. Deployment: `docs/deployment/PRODUCTION_DEPLOYMENT_RUNBOOK.md`
2. Monitoring: `docs/deployment/MONITORING_GUIDE.md`
3. Troubleshooting: `docs/deployment/TROUBLESHOOTING_GUIDE.md`
4. Configuration: `config/README.md`

### For QA
1. Testing: `tests/README.md`
2. Performance: `docs/deployment/PERFORMANCE_TUNING_GUIDE.md`
3. Security: `docs/security/`

### For Project Managers
1. Overview: `README.md`
2. Status: `PROJECT_COMPLETION_SUMMARY.md`
3. Phases: `docs/PHASE4_COMPLETION_REPORT.md`
4. Tasks: `docs/tasks/TIER_IDENTIFICATION_SYSTEM_TASKS.md`

---

## ✅ Documentation Checklist

- [x] Root level documentation complete
- [x] Phase documentation complete
- [x] Task documentation complete
- [x] Deployment documentation complete
- [x] Monitoring documentation complete
- [x] Performance documentation complete
- [x] Testing documentation complete
- [x] API documentation complete
- [x] Security documentation complete
- [x] Development documentation complete
- [x] Configuration documentation complete
- [x] Troubleshooting documentation complete
- [x] Team training materials complete
- [x] Quick start guides complete
- [x] Runbooks complete

---

**Documentation Status**: ✅ COMPLETE  
**Last Updated**: March 15, 2026  
**Total Files**: 180+  
**Coverage**: 100%

---

**Built with ❤️ by the Namaskah Team**
