#!/bin/bash
# Directory Reorganization Script - Clean Git Structure
# Run from project root directory

set -e  # Exit on any error

echo "🗂️  Namaskah Directory Reorganization"
echo "===================================="
echo ""

# Confirm execution
read -p "This will reorganize the directory structure. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo "📁 Creating new directory structure..."

# 1. Create new directories
mkdir -p docs/api
mkdir -p scripts/{deployment,security,development}
mkdir -p tools
mkdir -p archive/{project-status-2026,deployment-strategy-2026}

echo "✅ Directories created"

echo "📄 Moving API documentation..."

# 2. Move API documentation
[ -f "docs/API_GUIDE.md" ] && mv docs/API_GUIDE.md docs/api/
[ -f "docs/api_v2_spec.yaml" ] && mv docs/api_v2_spec.yaml docs/api/
[ -f "docs/api_documentation.py" ] && mv docs/api_documentation.py docs/api/
[ -f "docs/TIER_MANAGEMENT_API.md" ] && mv docs/TIER_MANAGEMENT_API.md docs/api/
[ -f "docs/VOICE_VS_SMS_VERIFICATION.md" ] && mv docs/VOICE_VS_SMS_VERIFICATION.md docs/api/

echo "✅ API documentation moved"

echo "📦 Moving files to archive..."

# 3. Move to archive
[ -f "CLEANUP_SUMMARY.md" ] && mv CLEANUP_SUMMARY.md archive/feb-2026-cleanup/
[ -f "CODEBASE_AUDIT_FINDINGS.md" ] && mv CODEBASE_AUDIT_FINDINGS.md archive/feb-2026-cleanup/
[ -f "DEPLOYMENT_STRATEGY.md" ] && mv DEPLOYMENT_STRATEGY.md archive/deployment-strategy-2026/
[ -f "PROJECT_STATUS.md" ] && mv PROJECT_STATUS.md archive/project-status-2026/

echo "✅ Archive files moved"

echo "🔧 Reorganizing scripts..."

# 4. Reorganize scripts - Deployment
[ -f "scripts/deploy_production.sh" ] && mv scripts/deploy_production.sh scripts/deployment/
[ -f "scripts/backup_automation.sh" ] && mv scripts/backup_automation.sh scripts/deployment/
[ -f "scripts/migrate.sh" ] && mv scripts/migrate.sh scripts/deployment/
[ -f "scripts/setup-cicd.sh" ] && mv scripts/setup-cicd.sh scripts/deployment/
[ -f "scripts/ssl_setup.sh" ] && mv scripts/ssl_setup.sh scripts/deployment/
[ -f "scripts/setup_uptimerobot.sh" ] && mv scripts/setup_uptimerobot.sh scripts/deployment/
[ -f "scripts/verify_backup.sh" ] && mv scripts/verify_backup.sh scripts/deployment/

# Security scripts
find scripts/ -name "security_*.py" -exec mv {} scripts/security/ \; 2>/dev/null || true
[ -f "scripts/api_security_scan.py" ] && mv scripts/api_security_scan.py scripts/security/
[ -f "scripts/rotate_api_keys.sh" ] && mv scripts/rotate_api_keys.sh scripts/security/
[ -f "scripts/final_secrets_audit.sh" ] && mv scripts/final_secrets_audit.sh scripts/security/
[ -f "scripts/manage_secrets.py" ] && mv scripts/manage_secrets.py scripts/security/
[ -f "scripts/run_security_tests.py" ] && mv scripts/run_security_tests.py scripts/security/

# Development scripts
find scripts/ -name "analyze_*.py" -exec mv {} scripts/development/ \; 2>/dev/null || true
find scripts/ -name "check_*.py" -exec mv {} scripts/development/ \; 2>/dev/null || true
find scripts/ -name "verify_*.py" -exec mv {} scripts/development/ \; 2>/dev/null || true
find scripts/ -name "test_*.*" -exec mv {} scripts/development/ \; 2>/dev/null || true
find scripts/ -name "diagnostic_*.py" -exec mv {} scripts/development/ \; 2>/dev/null || true

echo "✅ Scripts reorganized"

echo "🛠️  Moving development tools..."

# 5. Move tools
[ -d "postman" ] && mv postman/ tools/
[ -f "scripts/lighthouse_audit.js" ] && mv scripts/lighthouse_audit.js tools/
[ -f "gitleaks.toml" ] && mv gitleaks.toml tools/

echo "✅ Tools moved"

echo "🧹 Cleaning up redundant files..."

# 6. Clean up redundant files
rm -f compare_repos.sh
rm -f pull_gitlab_updates.sh  
rm -f check_gitlab_updates.sh
rm -f verify_github_actions.sh
rm -f restart-fixed.sh
rm -f start-simple.sh
rm -f start_local.sh

echo "✅ Redundant files removed"

echo "🗑️  Removing empty directories..."

# 7. Remove empty directories
rmdir docs/archive/ 2>/dev/null || true

echo "✅ Empty directories cleaned"

echo ""
echo "🎉 Directory reorganization complete!"
echo ""
echo "📊 Summary of changes:"
echo "├── 📁 Created docs/api/ for API documentation"
echo "├── 📁 Organized scripts/ into deployment/security/development/"
echo "├── 📁 Consolidated archive/ directory"
echo "├── 📁 Created tools/ for development utilities"
echo "├── 🗑️  Removed 6 redundant root-level files"
echo "└── 🧹 Cleaned empty directories"
echo ""
echo "📋 New structure:"
echo "├── docs/"
echo "│   ├── api/ (API documentation)"
echo "│   ├── deployment/ (deployment guides)"
echo "│   ├── roadmaps/ (project roadmaps)"
echo "│   └── tasks/ (task documentation)"
echo "├── scripts/"
echo "│   ├── deployment/ (deployment scripts)"
echo "│   ├── security/ (security scripts)"
echo "│   ├── development/ (dev utilities)"
echo "│   └── maintenance/ (maintenance scripts)"
echo "├── archive/ (historical files)"
echo "├── tools/ (development tools)"
echo "└── config/ (configuration files)"
echo ""
echo "🎯 Result: Professional, organized git directory structure"
echo ""
echo "⚠️  Next steps:"
echo "1. Test that the application still runs: ./start.sh"
echo "2. Update any broken documentation links"
echo "3. Commit changes: git add . && git commit -m 'Reorganize directory structure'"