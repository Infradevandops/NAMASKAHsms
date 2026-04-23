# CI FAILURE - Circular Import Issue

**Date**: March 20, 2026  
**Severity**: 🔴 CRITICAL - Blocks all tests  
**Status**: Identified, fix needed

---

## 🐛 Problem

**Error**: `ImportError: cannot import name 'Base' from partially initialized module 'app.core.database'`

**Root Cause**: Circular import between:
```
app/core/database.py → app/models/base.py → app/models/__init__.py → 
app/models/pricing_template.py → app/core/database.py
```

**Impact**:
- ❌ All unit tests fail to run
- ❌ CI pipeline blocked
- ❌ Cannot validate code changes
- ❌ Deployment blocked

---

## 📊 Import Chain

```
tests/conftest.py
  ↓
app/core/database.py (imports Base from models.base)
  ↓
app/models/base.py
  ↓
app/models/__init__.py (line 34: imports pricing_template)
  ↓
app/models/pricing_template.py (line 18: imports Base from core.database)
  ↓
CIRCULAR IMPORT! ❌
```

---

## 🔧 Solution Options

### Option 1: Move Base to Separate File (RECOMMENDED)
**Action**: Create `app/models/base.py` with only Base class  
**Impact**: Breaks circular dependency  
**Effort**: 15 minutes  
**Risk**: Low

```python
# app/models/base.py (should only contain)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

### Option 2: Lazy Import in pricing_template.py
**Action**: Import Base inside functions instead of module level  
**Impact**: Fixes immediate issue  
**Effort**: 5 minutes  
**Risk**: Medium (may hide other issues)

### Option 3: Remove pricing_template from __init__.py
**Action**: Don't auto-import pricing_template in models/__init__.py  
**Impact**: Requires explicit imports elsewhere  
**Effort**: 10 minutes  
**Risk**: Medium (may break existing code)

---

## ✅ Recommended Fix (Option 1)

### Step 1: Verify Base Location
```bash
grep -n "class Base" app/models/base.py
grep -n "Base = " app/models/base.py
```

### Step 2: Check pricing_template Import
```bash
grep -n "from app.core.database import Base" app/models/pricing_template.py
```

### Step 3: Fix Import
```python
# app/models/pricing_template.py
# CHANGE FROM:
from app.core.database import Base

# CHANGE TO:
from app.models.base import Base
```

### Step 4: Verify Fix
```bash
python3 -m pytest tests/unit/ --collect-only
```

### Step 5: Run Tests
```bash
python3 -m pytest tests/unit/ -v --maxfail=5
```

---

## 🎯 Quick Fix (5 minutes)

```bash
# 1. Check current import
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"
grep "from app.core.database import Base" app/models/pricing_template.py

# 2. Fix import
sed -i.bak 's/from app.core.database import Base/from app.models.base import Base/g' app/models/pricing_template.py

# 3. Verify fix
python3 -m pytest tests/unit/ --collect-only

# 4. If successful, run tests
python3 -m pytest tests/unit/ -v --maxfail=5
```

---

## 📋 Verification Checklist

- [ ] Circular import resolved
- [ ] Tests can collect
- [ ] Tests can run
- [ ] No new import errors
- [ ] CI pipeline passes

---

## 🚨 Prevention

### Rule: Import Hierarchy
```
app/models/base.py (Base class only)
  ↑
app/models/*.py (all models import from base)
  ↑
app/core/database.py (imports Base from models.base)
  ↑
app/services/*.py (imports from core.database)
```

### Pre-commit Hook
```bash
# Add to .git/hooks/pre-commit
python3 -c "import app.models" || exit 1
```

---

## 📊 Impact Assessment

### Before Fix
- ✅ Application runs (import happens at runtime)
- ❌ Tests fail (import happens at collection)
- ❌ CI blocked
- ❌ Cannot validate changes

### After Fix
- ✅ Application runs
- ✅ Tests run
- ✅ CI passes
- ✅ Can validate changes

---

**Next Action**: Execute Quick Fix (5 minutes)
