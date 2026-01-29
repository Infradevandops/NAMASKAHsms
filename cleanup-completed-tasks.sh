#!/bin/bash
# Cleanup Script for Namaskah Project
# Organizes completed task files and active documentation
# Date: January 29, 2026

set -e

echo "🧹 Namaskah Project Cleanup Script"
echo "=================================="
echo ""

# Create archive directories
echo "📁 Creating archive directories..."
mkdir -p docs/archive/completed-tasks/{ci-cd,deployment,bug-fixes,phases}
mkdir -p docs/tasks/coverage-initiative

# Archive CI/CD files (8 files)
echo "📦 Archiving CI/CD files..."
mv CI_CD_COMPLETE_RESOLUTION.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true
mv CI_CD_FINAL_FIXES.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true
mv CI_CD_FINAL_STATUS.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true
mv CI_CD_FIXES_COMPREHENSIVE.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true
mv CI_CD_FIX_SUMMARY.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true
mv CI_CD_RESOLUTION_SUMMARY.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true
mv CI_CD_TEST_FIXTURES_SUMMARY.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true
mv CI_COMPREHENSIVE_FIX.md docs/archive/completed-tasks/ci-cd/ 2>/dev/null || true

# Archive deployment files (3 files)
echo "📦 Archiving deployment files..."
mv DEPLOYMENT_STATUS.md docs/archive/completed-tasks/deployment/ 2>/dev/null || true
mv DEPLOYMENT_SUCCESS.md docs/archive/completed-tasks/deployment/ 2>/dev/null || true
mv PRODUCTION_FIX.md docs/archive/completed-tasks/deployment/ 2>/dev/null || true

# Archive bug fix files (4 files)
echo "📦 Archiving bug fix files..."
mv HISTORY_PAGE_DIAGNOSIS.md docs/archive/completed-tasks/bug-fixes/ 2>/dev/null || true
mv HISTORY_PAGE_FIX_SUMMARY.md docs/archive/completed-tasks/bug-fixes/ 2>/dev/null || true
mv NOTIFICATION_BELL_FIX.md docs/archive/completed-tasks/bug-fixes/ 2>/dev/null || true
mv NOTIFICATION_BADGE_FIX.md docs/archive/completed-tasks/bug-fixes/ 2>/dev/null || true

# Archive phase completion files (3 files)
echo "📦 Archiving phase completion files..."
mv PHASE_1_COMPLETION_BRIEF.md docs/archive/completed-tasks/phases/ 2>/dev/null || true
mv PHASE_2_COMPLETION_SUMMARY.md docs/archive/completed-tasks/phases/ 2>/dev/null || true
mv PHASE_2_PROGRESS_BRIEF.md docs/archive/completed-tasks/phases/ 2>/dev/null || true

# Archive quick guides (2 files)
echo "📦 Archiving quick guides..."
mv QUICK_CI_FIX_GUIDE.md docs/archive/completed-tasks/ 2>/dev/null || true
mv QUICK_START_100_COVERAGE.md docs/archive/completed-tasks/ 2>/dev/null || true

# Organize active coverage tasks (8 files)
echo "📋 Organizing active coverage tasks..."
mv 100_COVERAGE_ACTION_PLAN.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv COVERAGE_100_TASK_BREAKDOWN.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv COVERAGE_GAPS_ANALYSIS.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv COVERAGE_STATUS_REPORT.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv TASK_TRACKER.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv PHASE_1_FIX_FAILING_TESTS.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv PHASE_2_API_ENDPOINT_TESTS.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv PHASE_3_INFRASTRUCTURE_TESTS.md docs/tasks/coverage-initiative/ 2>/dev/null || true
mv PHASE_4_COMPLETENESS_TESTS.md docs/tasks/coverage-initiative/ 2>/dev/null || true

# Create archive index
echo "📝 Creating archive index..."
cat > docs/archive/INDEX.md << 'EOF'
# Archived Documentation Index

This directory contains completed task documentation that has been archived for historical reference.

## Directory Structure

### completed-tasks/ci-cd/
CI/CD pipeline fixes and improvements (8 files)
- All CI/CD checks now passing
- Pipeline hardened and production-ready
- Archived: January 29, 2026

### completed-tasks/deployment/
Production deployment fixes and status (3 files)
- All deployment issues resolved
- Production environment stable
- Archived: January 29, 2026

### completed-tasks/bug-fixes/
Bug fixes for history page and notifications (4 files)
- History page rendering fixed
- Notification bell/badge issues resolved
- Archived: January 29, 2026

### completed-tasks/phases/
Phase completion summaries (3 files)
- Phase 1: Foundation complete
- Phase 2: Core features complete
- Phase 2.5: Notification system complete
- Archived: January 29, 2026

### completed-tasks/
Quick start guides (2 files)
- CI/CD quick fixes
- Coverage quick start
- Archived: January 29, 2026

## Active Documentation

Active task documentation has been moved to:
- `docs/tasks/coverage-initiative/` - 100% coverage initiative files

## Core Documentation

Core documentation remains in project root:
- `README.md` - Main project documentation
- `CHANGELOG.md` - Version history
- `COMMIT_GUIDE.md` - Git commit guidelines
- `BYPASS_HOOK_COMMIT.md` - Pre-commit hook bypass

## Restoration

To restore any archived file:
```bash
cp docs/archive/completed-tasks/[category]/[filename] ./
```

---

**Archive Date**: January 29, 2026
**Total Files Archived**: 20 files
**Reason**: Completed tasks, no longer actively referenced
EOF

# Create tasks index
echo "📝 Creating tasks index..."
cat > docs/tasks/coverage-initiative/README.md << 'EOF'
# 100% Test Coverage Initiative

This directory contains all active documentation for the 100% test coverage initiative.

## Current Status
- **Coverage**: 40.27% → Target: 100%
- **Tests**: 877 active (540 passing, 45 failing)
- **Timeline**: 4 weeks (60-80 hours)

## Files

### Master Planning
- `TASK_TRACKER.md` - Master task tracker (START HERE)
- `100_COVERAGE_ACTION_PLAN.md` - Detailed execution plan
- `COVERAGE_STATUS_REPORT.md` - Current state & roadmap
- `COVERAGE_100_TASK_BREAKDOWN.md` - Phase-by-phase breakdown
- `COVERAGE_GAPS_ANALYSIS.md` - Gap analysis

### Phase Task Files
- `PHASE_1_FIX_FAILING_TESTS.md` - Fix 45 failing tests (3/45 done)
- `PHASE_2_API_ENDPOINT_TESTS.md` - Create 140+ endpoint tests (✅ 98% complete)
- `PHASE_3_INFRASTRUCTURE_TESTS.md` - Create 170+ infrastructure tests (NEXT)
- `PHASE_4_COMPLETENESS_TESTS.md` - Create 150+ completeness tests

## Quick Start

1. Read `TASK_TRACKER.md` for overview
2. Check current phase status
3. Follow phase-specific task file
4. Run tests and check coverage
5. Commit progress

## Commands

```bash
# Check coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run specific phase tests
pytest tests/unit/test_*_comprehensive.py -v

# Generate HTML report
pytest tests/ --cov=app --cov-report=html
```

---

**Last Updated**: January 29, 2026
**Next Milestone**: Phase 3 - Infrastructure Tests
EOF

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Archived: 20 completed task files"
echo "  - Organized: 9 active task files"
echo "  - Root directory now has: $(ls -1 *.md 2>/dev/null | wc -l | tr -d ' ') markdown files"
echo ""
echo "📁 New structure:"
echo "  - docs/archive/completed-tasks/ (20 files)"
echo "  - docs/tasks/coverage-initiative/ (9 files + README)"
echo "  - Root directory (4-5 core docs)"
echo ""
echo "📖 View details:"
echo "  - Archive index: docs/archive/INDEX.md"
echo "  - Tasks index: docs/tasks/coverage-initiative/README.md"
echo "  - Assessment: PROJECT_CLEANUP_ASSESSMENT.md"
echo ""
echo "🎯 Next steps:"
echo "  1. Review PROJECT_CLEANUP_ASSESSMENT.md"
echo "  2. Continue with Phase 3: Infrastructure Tests"
echo "  3. See docs/tasks/coverage-initiative/TASK_TRACKER.md"
echo ""
