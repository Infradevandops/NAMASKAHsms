#!/bin/bash
# Deep Project Cleanup Script
# Removes redundant files, cache, and organizes project structure
# Date: January 30, 2026

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Dry run flag
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}🔍 DRY RUN MODE - No files will be deleted${NC}"
    echo ""
fi

echo -e "${BLUE}🧹 Deep Project Cleanup${NC}"
echo "======================================"
echo ""

# Function to remove files/directories
remove_item() {
    local item=$1
    local description=$2
    
    if [ -e "$item" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}[DRY RUN]${NC} Would remove: $item ($description)"
        else
            rm -rf "$item"
            echo -e "${GREEN}✓${NC} Removed: $item ($description)"
        fi
    fi
}

# Function to move files
move_item() {
    local source=$1
    local dest=$2
    local description=$3
    
    if [ -e "$source" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}[DRY RUN]${NC} Would move: $source -> $dest ($description)"
        else
            mv "$source" "$dest"
            echo -e "${GREEN}✓${NC} Moved: $source -> $dest ($description)"
        fi
    fi
}

# Category 1: Python Cache Files
echo -e "${BLUE}📦 Category 1: Python Cache Files${NC}"
echo "-----------------------------------"

# Remove __pycache__ directories
if [ "$DRY_RUN" = true ]; then
    pycache_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${YELLOW}[DRY RUN]${NC} Would remove $pycache_count __pycache__ directories"
else
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Removed all __pycache__ directories"
fi

# Remove .pyc files
if [ "$DRY_RUN" = true ]; then
    pyc_count=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${YELLOW}[DRY RUN]${NC} Would remove $pyc_count .pyc files"
else
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Removed all .pyc files"
fi

# Remove pytest cache
remove_item ".pytest_cache" "pytest cache"
remove_item ".mypy_cache" "mypy cache"
remove_item ".hypothesis" "hypothesis cache"

echo ""

# Category 2: Test Databases
echo -e "${BLUE}💾 Category 2: Test Databases${NC}"
echo "-----------------------------------"

remove_item "namaskah.db" "development database"
remove_item "test.db" "test database"
remove_item "backups/" "old backups"

echo ""

# Category 3: Coverage Reports
echo -e "${BLUE}📊 Category 3: Coverage Reports${NC}"
echo "-----------------------------------"

remove_item "htmlcov/" "HTML coverage report"
remove_item ".coverage" "coverage data"
remove_item "coverage.xml" "coverage XML"
remove_item "coverage.json" "coverage JSON"

echo ""

# Category 4: Log Files
echo -e "${BLUE}📝 Category 4: Log Files${NC}"
echo "-----------------------------------"

remove_item "logs/" "log directory"
remove_item ".cache_ggshield" "ggshield cache"

echo ""

# Category 5: Test Scripts in Root
echo -e "${BLUE}🔧 Category 5: Test Scripts (Moving to scripts/)${NC}"
echo "-----------------------------------"

# Create scripts directory if it doesn't exist
if [ "$DRY_RUN" = false ]; then
    mkdir -p scripts/
fi

# Move test scripts
move_item "test_215_philadelphia.py" "scripts/" "test script"
move_item "test_704_charlotte.py" "scripts/" "test script"
move_item "test_admin_login.sh" "scripts/" "test script"
move_item "test_admin_sqlite.py" "scripts/" "test script"
move_item "test_cancel_refund.py" "scripts/" "test script"
move_item "test_prod_admin.sh" "scripts/" "test script"
move_item "test_verification_safety.py" "scripts/" "test script"

# Move utility scripts
move_item "check_verification_status.py" "scripts/" "utility script"
move_item "create_admin_user.py" "scripts/" "utility script"
move_item "critical_refund_analysis.py" "scripts/" "analysis script"
move_item "diagnostic_frontend_issues.py" "scripts/" "diagnostic script"
move_item "production_diagnostic.py" "scripts/" "diagnostic script"
move_item "purchase_new_215.py" "scripts/" "purchase script"
move_item "reconcile_refunds.py" "scripts/" "reconcile script"

echo ""

# Category 6: Redundant Deployment Scripts
echo -e "${BLUE}🚀 Category 6: Redundant Deployment Scripts${NC}"
echo "-----------------------------------"

remove_item "deploy_refund_fix.sh" "one-time deployment script"
remove_item "deploy_to_production.sh" "duplicate deployment script"
remove_item "git_push_production.sh" "redundant git script"
remove_item "verify-ci-cd.sh" "one-time verification script"

# Keep deploy_production.sh in root or move to scripts
if [ -f "deploy_production.sh" ] && [ -f "scripts/deploy_production.sh" ]; then
    remove_item "deploy_production.sh" "duplicate (exists in scripts/)"
fi

echo ""

# Category 7: Redundant Cleanup Scripts
echo -e "${BLUE}🗑️  Category 7: Redundant Cleanup Scripts${NC}"
echo "-----------------------------------"

remove_item "cleanup-completed-tasks.sh" "superseded by cleanup-project-docs.sh"
remove_item "COMMIT_NOW.sh" "one-time commit script"

echo ""

# Category 8: OS and IDE Files
echo -e "${BLUE}💻 Category 8: OS and IDE Files${NC}"
echo "-----------------------------------"

# Remove .DS_Store files
if [ "$DRY_RUN" = true ]; then
    ds_count=$(find . -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${YELLOW}[DRY RUN]${NC} Would remove $ds_count .DS_Store files"
else
    find . -name ".DS_Store" -delete 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Removed all .DS_Store files"
fi

# Remove IDE directories (optional - uncomment if needed)
# remove_item ".vscode/" "VS Code settings"

echo ""

# Category 9: Empty Directories
echo -e "${BLUE}📁 Category 9: Empty Directories${NC}"
echo "-----------------------------------"

# Check if uploads is empty
if [ -d "uploads" ] && [ -z "$(ls -A uploads)" ]; then
    remove_item "uploads/" "empty uploads directory"
fi

echo ""

# Summary
echo -e "${BLUE}📊 Cleanup Summary${NC}"
echo "======================================"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}This was a DRY RUN - no files were actually deleted${NC}"
    echo ""
    echo "To perform the actual cleanup, run:"
    echo "  ./deep-cleanup.sh"
    echo ""
else
    echo -e "${GREEN}✅ Cleanup complete!${NC}"
    echo ""
    echo "Removed:"
    echo "  ✓ Python cache files (__pycache__, .pyc)"
    echo "  ✓ Test databases (*.db)"
    echo "  ✓ Coverage reports (htmlcov/)"
    echo "  ✓ Log files (logs/)"
    echo "  ✓ OS files (.DS_Store)"
    echo "  ✓ Redundant scripts"
    echo ""
    echo "Organized:"
    echo "  ✓ Moved test scripts to scripts/"
    echo "  ✓ Removed duplicate deployment scripts"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git status"
    echo "  2. Run tests: python3 -m pytest tests/unit/ -v"
    echo "  3. Commit changes: git add -A && git commit -m 'chore: deep cleanup'"
    echo ""
fi

# Show disk space saved
if [ "$DRY_RUN" = false ]; then
    echo -e "${BLUE}💾 Disk Space${NC}"
    echo "-----------------------------------"
    echo "Current project size (excluding .venv, node_modules):"
    du -sh . --exclude=.venv --exclude=node_modules --exclude=.git 2>/dev/null || echo "Unable to calculate"
    echo ""
fi

echo -e "${GREEN}Done!${NC}"
