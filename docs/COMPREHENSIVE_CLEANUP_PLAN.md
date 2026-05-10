# Comprehensive Cleanup Plan

**Date**: May 10, 2026
**Purpose**: Remove redundant files, cache, and improve codebase cleanliness

---

## 🎯 Cleanup Categories

### 1. Deprecated Files (SAFE TO DELETE)
```
✅ app/api/core/whitelabel_OLD_DEPRECATED.py.bak
✅ app/models/whitelabel_OLD_DEPRECATED.py.bak
✅ app/models/whitelabel_enhanced_OLD_DEPRECATED.py.bak
✅ app/services/whitelabel_enhanced_OLD_DEPRECATED.py.bak
```
**Action**: Delete (already backed up in git history)
**Risk**: None (files are .bak copies)

---

### 2. Python Cache Files (SAFE TO DELETE)
```
✅ __pycache__/ directories (81 found)
✅ *.pyc files
✅ .pytest_cache/
✅ *.egg-info/
```
**Action**: Delete (regenerated automatically)
**Risk**: None (cache files)

---

### 3. System Files (SAFE TO DELETE)
```
✅ .DS_Store files (5 found)
   - ./.DS_Store
   - ./app/.DS_Store
   - ./tests/.DS_Store
   - ./static/.DS_Store
```
**Action**: Delete (macOS metadata)
**Risk**: None (system files)

---

### 4. Empty Directories (SAFE TO DELETE)
```
✅ tests/scratch/ (empty)
```
**Action**: Delete
**Risk**: None (empty directory)

---

### 5. Log Files (REVIEW BEFORE DELETE)
```
⚠️ logs/app.log
```
**Action**: Review size, keep if needed for debugging
**Risk**: Low (can be regenerated)

---

## 🔍 Code Quality Issues Found

### Files with TODO/FIXME markers
```
1. app/utils/phone_formatter.py
2. app/models/verification.py
3. app/api/core/telegram.py
4. app/services/textverified_service.py
```
**Action**: Review and address or document
**Risk**: None (informational)

---

## 🧹 Cleanup Commands

### Phase 1: Delete Deprecated Files
```bash
rm app/api/core/whitelabel_OLD_DEPRECATED.py.bak
rm app/models/whitelabel_OLD_DEPRECATED.py.bak
rm app/models/whitelabel_enhanced_OLD_DEPRECATED.py.bak
rm app/services/whitelabel_enhanced_OLD_DEPRECATED.py.bak
```

### Phase 2: Delete Cache Files
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
```

### Phase 3: Delete System Files
```bash
find . -name ".DS_Store" -delete
```

### Phase 4: Delete Empty Directories
```bash
rmdir tests/scratch/
```

### Phase 5: Review Log Files
```bash
ls -lh logs/app.log
# If large, truncate or delete:
# > logs/app.log  # Truncate
# rm logs/app.log  # Delete
```

---

## 📊 Expected Impact

### Disk Space Saved
- Deprecated files: ~50 KB
- Cache files: ~5-10 MB
- System files: ~100 KB
- **Total**: ~5-10 MB

### Performance Impact
- Faster git operations (fewer files)
- Cleaner directory listings
- Reduced confusion from deprecated files

### Risk Assessment
- **Zero risk**: All files are either backups, cache, or system files
- **Reversible**: All deprecated files are in git history
- **No production impact**: None of these files are used in production

---

## ✅ Verification After Cleanup

### Tests to Run
```bash
# 1. Verify app still loads
python3 -c "from main import app; print('✅ App loads')"

# 2. Run test suite
pytest tests/unit/test_whitelabel_service.py -v

# 3. Check for import errors
python3 -c "
from app.services.telegram_service import telegram_service
from app.services.onesignal_service import onesignal_service
from app.services.whitelabel_service import whitelabel_service
from app.services.email_template_service import email_template_service
print('✅ All services import successfully')
"
```

---

## 🎯 Additional Recommendations

### 1. Add to .gitignore
```
# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
*.egg-info/

# System files
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.bak
*_OLD_DEPRECATED*
```

### 2. Pre-commit Hook Enhancement
Already configured to prevent:
- Trailing whitespace
- Large files
- Merge conflicts
- Private keys

### 3. Regular Cleanup Schedule
- Weekly: Delete cache files
- Monthly: Review log files
- Quarterly: Review TODO/FIXME markers

---

## 📝 Execution Checklist

- [ ] Phase 1: Delete deprecated files
- [ ] Phase 2: Delete cache files
- [ ] Phase 3: Delete system files
- [ ] Phase 4: Delete empty directories
- [ ] Phase 5: Review log files
- [ ] Verify app loads
- [ ] Run test suite
- [ ] Update .gitignore
- [ ] Commit cleanup
- [ ] Push to production

---

## 🚀 Ready to Execute

All cleanup actions are **SAFE** and **REVERSIBLE**. Proceed with confidence.
