#!/bin/bash
# Critical Directory Cleanup - Executable Script
# Based on Taskfile.yml pattern and comprehensive analysis

set -e  # Exit on error

echo "🧹 CRITICAL DIRECTORY CLEANUP"
echo "============================="
echo ""
echo "📊 Current State Analysis:"
echo "  - Files tracked: $(git ls-files | wc -l)"
echo "  - Repository size: $(du -sh .git/ | cut -f1)"
echo "  - Python files: $(find . -name "*.py" | wc -l)"
echo "  - Markdown files: $(find . -name "*.md" | wc -l)"
echo ""

# Confirmation
read -p "🚨 This will make MAJOR changes. Type 'CLEANUP' to confirm: " confirm
if [ "$confirm" != "CLEANUP" ]; then
    echo "❌ Cancelled"
    exit 1
fi

echo "🔄 Creating backup branch..."
git checkout -b "backup-before-cleanup-$(date +%Y%m%d-%H%M%S)"
git checkout main

echo "📁 PHASE 1: Critical .gitignore fixes..."

# Remove .venv from tracking (CRITICAL - saves 128MB)
if git ls-files .venv/ | grep -q .; then
    echo "  🗑️  Removing .venv/ from tracking (128MB)..."
    git rm -r --cached .venv/
    echo "✅ .venv/ removed from tracking"
else
    echo "✅ .venv/ already untracked"
fi

# Remove __pycache__ directories
echo "  🗑️  Removing __pycache__ directories..."
find . -name "__pycache__" -type d | while read dir; do
    git rm -r --cached "$dir" 2>/dev/null || true
done
echo "✅ __pycache__ directories removed"

# Remove log and coverage files
git rm --cached coverage.xml 2>/dev/null || true
git rm --cached logs/app.log 2>/dev/null || true
git rm --cached server.log 2>/dev/null || true

# Update .gitignore
echo "" >> .gitignore
echo "# Critical cleanup additions" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "coverage.xml" >> .gitignore

echo "📁 PHASE 2: Remove duplicates and dead code..."

# Remove hidden CSS archive
if [ -d "static/css/_archive" ]; then
    echo "  🗑️  Removing static/css/_archive/..."
    rm -rf static/css/_archive/
    echo "✅ CSS archive removed"
fi

# Remove duplicate workflows
rm -f .github/workflows/ci-old.yml
rm -f .github/workflows/ci-improved.yml
echo "✅ Duplicate workflows removed"

# Remove redundant shell scripts
REDUNDANT_SCRIPTS=(
    "compare_repos.sh"
    "pull_gitlab_updates.sh"
    "check_gitlab_updates.sh"
    "verify_github_actions.sh"
    "restart-fixed.sh"
    "start-simple.sh"
    "start_local.sh"
)

for script in "${REDUNDANT_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        rm -f "$script"
        echo "  🗑️  Removed $script"
    fi
done

echo "📁 PHASE 3: Reorganize structure..."

# Create new directory structure
mkdir -p config/{docker,k8s,monitoring}
mkdir -p scripts/{sql,deployment,security,development}
mkdir -p docs/{api,architecture,user}
mkdir -p tools
mkdir -p archive/documentation-cleanup-2026

# Move SQL files
if [ -f "create_admin.sql" ]; then
    mv create_admin.sql scripts/sql/
fi
find scripts/ -name "*.sql" -exec mv {} scripts/sql/ \; 2>/dev/null || true

# Move configuration files
mv docker-compose*.yml config/docker/ 2>/dev/null || true
mv Dockerfile* config/docker/ 2>/dev/null || true
mv k8s-deployment.yaml config/k8s/ 2>/dev/null || true
mv render.yaml config/ 2>/dev/null || true
mv Taskfile.yml config/ 2>/dev/null || true

# Move monitoring
if [ -d "monitoring" ]; then
    mv monitoring/* config/monitoring/ 2>/dev/null || true
    rmdir monitoring 2>/dev/null || true
fi

# Move API documentation
mv docs/API_GUIDE.md docs/api/ 2>/dev/null || true
mv docs/api_v2_spec.yaml docs/api/ 2>/dev/null || true
mv docs/TIER_MANAGEMENT_API.md docs/api/ 2>/dev/null || true
mv docs/VOICE_VS_SMS_VERIFICATION.md docs/api/ 2>/dev/null || true

# Move architecture docs
mv docs/SECURITY_AND_COMPLIANCE.md docs/architecture/ 2>/dev/null || true
mv docs/MONITORING_SETUP.md docs/architecture/ 2>/dev/null || true

# Archive status/progress files
find docs/ -name "*_COMPLETE*.md" -exec mv {} archive/documentation-cleanup-2026/ \; 2>/dev/null || true
find docs/ -name "*_STATUS*.md" -exec mv {} archive/documentation-cleanup-2026/ \; 2>/dev/null || true
find docs/ -name "*_SUMMARY*.md" -exec mv {} archive/documentation-cleanup-2026/ \; 2>/dev/null || true

# Move development tools
if [ -d "postman" ]; then
    mv postman/ tools/
fi

echo "🧪 VERIFICATION PHASE..."

# Test application still works
echo "  🔍 Testing application startup..."
if python3 -c "from main import create_app; app = create_app(); print('✅ App creates successfully')" 2>/dev/null; then
    echo "✅ Application startup test passed"
else
    echo "❌ Application startup test failed"
    echo "🚨 ROLLBACK REQUIRED"
    exit 1
fi

# Check file count reduction
NEW_FILE_COUNT=$(git ls-files | wc -l)
echo "  📊 New tracked file count: $NEW_FILE_COUNT"

# Check directory structure
echo "  📁 Verifying new structure..."
[ -d "config/docker" ] && echo "✅ config/docker/ created"
[ -d "scripts/sql" ] && echo "✅ scripts/sql/ created"
[ -d "docs/api" ] && echo "✅ docs/api/ created"
[ -d "docs/architecture" ] && echo "✅ docs/architecture/ created"

echo ""
echo "🎉 CLEANUP COMPLETE!"
echo ""
echo "📊 Results:"
echo "  - Files tracked: $NEW_FILE_COUNT (was ~7,500)"
echo "  - Repository size: $(du -sh .git/ | cut -f1)"
echo "  - Structure: Organized into logical directories"
echo ""
echo "🎯 Next steps:"
echo "  1. Test full application: ./start.sh"
echo "  2. Run test suite: pytest tests/unit/"
echo "  3. Check for broken links in documentation"
echo "  4. Commit changes: git add . && git commit -m 'Critical directory cleanup and reorganization'"
echo ""
echo "⚠️  If issues occur, rollback with:"
echo "     git checkout backup-before-cleanup-*"