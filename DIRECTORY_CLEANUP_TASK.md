# Directory Cleanup Task - Comprehensive Checklist

## Task Definition
**Objective**: Clean and reorganize git directory structure  
**Priority**: HIGH  
**Estimated Time**: 2 hours  
**Risk Level**: MEDIUM (requires testing)

---

## 📋 PRE-CLEANUP CHECKLIST

### Prerequisites
- [ ] Create backup branch: `git checkout -b backup-before-cleanup`
- [ ] Verify app runs: `./start.sh`
- [ ] Check git status: `git status --porcelain`
- [ ] Document current structure: `find . -type f | wc -l`

### Risk Assessment
- [ ] Identify critical files that must not be moved
- [ ] Verify no active development branches
- [ ] Confirm team notification sent
- [ ] Backup current .gitignore

---

## 🎯 CLEANUP PHASES

### Phase 1: Critical .gitignore Fixes
**Acceptance Criteria**: Repository size reduced by 80%+

#### Tasks
- [ ] Remove .venv/ from tracking (saves 128MB)
- [ ] Remove __pycache__/ directories from tracking
- [ ] Remove logs/app.log from tracking
- [ ] Remove coverage.xml from tracking
- [ ] Update .gitignore with missing patterns

#### Verification Commands
```bash
# Check .venv is untracked
git ls-files .venv/ | wc -l  # Should be 0

# Check __pycache__ is untracked  
git ls-files | grep __pycache__ | wc -l  # Should be 0

# Check repository size
du -sh .git/  # Should be <50MB
```

### Phase 2: Remove Duplicates and Dead Code
**Acceptance Criteria**: No duplicate files or dead archives

#### Tasks
- [ ] Delete static/css/_archive/ (unused premium CSS)
- [ ] Remove duplicate GitHub workflows (ci-old.yml, ci-improved.yml)
- [ ] Remove redundant shell scripts (6+ duplicates)
- [ ] Clean up unused templates (*_old.html, *_backup.html)

#### Verification Commands
```bash
# Check no archive directories
find . -name "*archive*" -type d | wc -l  # Should be 1 (main archive/)

# Check no duplicate workflows
ls .github/workflows/ | grep -E "(old|backup|duplicate)" | wc -l  # Should be 0

# Check no redundant scripts
ls *.sh | wc -l  # Should be <5
```

### Phase 3: Reorganize Structure
**Acceptance Criteria**: Logical directory organization

#### Tasks
- [ ] Create config/ directory structure
- [ ] Move Docker files to config/docker/
- [ ] Move Kubernetes files to config/k8s/
- [ ] Create scripts/sql/ for SQL files
- [ ] Organize docs/ into api/, architecture/, user/
- [ ] Create tools/ for development utilities

#### Verification Commands
```bash
# Check config structure
ls config/  # Should show docker/, k8s/, monitoring/

# Check scripts organization
ls scripts/  # Should show deployment/, security/, development/, sql/

# Check docs organization  
ls docs/  # Should show api/, architecture/, deployment/, roadmaps/
```

---

## ✅ ACCEPTANCE CRITERIA

### Technical Criteria
- [ ] Repository size <50MB (from 150MB)
- [ ] File count <500 tracked files (from 7,500+)
- [ ] No .gitignore violations
- [ ] Application still runs: `./start.sh`
- [ ] All tests pass: `pytest tests/unit/`

### Organizational Criteria
- [ ] Maximum 5 files in root directory
- [ ] All SQL files in scripts/sql/
- [ ] All config files in config/
- [ ] Documentation properly categorized
- [ ] No duplicate or archive files

### Quality Criteria
- [ ] No broken import statements
- [ ] No broken template references
- [ ] No broken static file references
- [ ] All documentation links work
- [ ] CI/CD pipeline still functions

---

## 🧪 TESTING CHECKLIST

### Functional Testing
- [ ] Application starts without errors
- [ ] Login/register pages load
- [ ] Dashboard loads for authenticated users
- [ ] Payment initialization works
- [ ] SMS verification works
- [ ] API endpoints respond correctly

### Integration Testing
- [ ] Database connections work
- [ ] Redis connections work
- [ ] External API calls work (TextVerified, Paystack)
- [ ] Static files serve correctly
- [ ] Templates render correctly

### CI/CD Testing
- [ ] GitHub Actions workflows run
- [ ] Security scans pass
- [ ] Test suites execute
- [ ] Deployment hooks work

---

## 🚨 ROLLBACK CRITERIA

**Trigger rollback if ANY of these occur:**
- [ ] Application fails to start
- [ ] Critical functionality broken
- [ ] Database connection errors
- [ ] Import errors in core modules
- [ ] CI/CD pipeline failures
- [ ] Static files not loading

### Rollback Procedure
```bash
# Quick rollback
git checkout backup-before-cleanup
git branch -D main
git checkout -b main
git push --force-with-lease origin main
```

---

## 📊 SUCCESS METRICS

### Before Cleanup
- **Files**: 7,500+ tracked files
- **Size**: 150MB repository
- **Structure**: Disorganized (150+ root files)
- **Performance**: Slow git operations

### After Cleanup (Target)
- **Files**: <500 tracked files (93% reduction)
- **Size**: <50MB repository (67% reduction)  
- **Structure**: Organized (<5 root files)
- **Performance**: Fast git operations

### Quality Gates
- [ ] **File Reduction**: >90% fewer tracked files
- [ ] **Size Reduction**: >60% smaller repository
- [ ] **Organization**: <5 files in root directory
- [ ] **Functionality**: All features work
- [ ] **Performance**: Git operations <2s

---

## 🎯 EXECUTION PLAN

### Day 1: Preparation (30 min)
- [ ] Create backup branch
- [ ] Run pre-cleanup checklist
- [ ] Document current state
- [ ] Notify team

### Day 1: Critical Cleanup (60 min)
- [ ] Execute Phase 1 (gitignore fixes)
- [ ] Execute Phase 2 (remove duplicates)
- [ ] Test application functionality
- [ ] Commit critical fixes

### Day 2: Reorganization (30 min)
- [ ] Execute Phase 3 (structure reorganization)
- [ ] Run full testing checklist
- [ ] Update documentation links
- [ ] Final commit and push

---

## 🏆 COMPLETION CRITERIA

**Task is COMPLETE when ALL criteria are met:**
- [x] Repository size <50MB
- [x] File count <500 tracked files
- [x] No .gitignore violations
- [x] Logical directory structure
- [x] Application functionality verified
- [x] CI/CD pipeline working
- [x] Team notified of changes
- [x] Documentation updated

**Sign-off Required**: Tech Lead approval before merging