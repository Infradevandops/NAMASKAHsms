#!/bin/bash
# Critical Directory Cleanup - Minimal Implementation
# Addresses only the most critical issues from CRITICAL_DIRECTORY_CLEANUP.md

set -e

echo "🚨 CRITICAL CLEANUP - Minimal Implementation"
echo "This will:"
echo "  - Remove duplicate workflow files"
echo "  - Clean up CSS archives"
echo "  - Consolidate SQL files"
echo "  - Remove coverage.xml if tracked"
echo ""

read -p "Continue? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ Cancelled"
    exit 1
fi

echo "🧹 Starting cleanup..."

# 1. Remove duplicate workflows (if they exist)
echo "📁 Removing duplicate workflows..."
rm -f .github/workflows/ci-old.yml
rm -f .github/workflows/ci-improved.yml

# 2. Remove CSS archives
echo "🎨 Cleaning CSS archives..."
rm -rf static/css/_archive/

# 3. Consolidate SQL files
echo "📊 Consolidating SQL files..."
mkdir -p scripts/sql/
if [ -f "create_admin.sql" ]; then
    mv create_admin.sql scripts/sql/
fi

# Move any loose SQL files in scripts/ to scripts/sql/
find scripts/ -maxdepth 1 -name "*.sql" -exec mv {} scripts/sql/ \; 2>/dev/null || true

# 4. Remove coverage.xml if tracked
echo "📋 Removing coverage files..."
git rm --cached coverage.xml 2>/dev/null || true

# 5. Clean up any __pycache__ that might be tracked
echo "🐍 Cleaning Python cache..."
find . -name "__pycache__" -type d -exec git rm -r --cached {} + 2>/dev/null || true

echo "✅ Critical cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Removed duplicate workflow files"
echo "  - Cleaned CSS archives"
echo "  - Consolidated SQL files to scripts/sql/"
echo "  - Removed tracked cache files"
echo ""
echo "🎯 Next steps:"
echo "  - Commit these changes"
echo "  - Run 'git status' to verify"