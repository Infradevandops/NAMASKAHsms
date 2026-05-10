# Whitelabel Redundancy Cleanup Plan

**Date**: May 10, 2026
**Issue**: Duplicate whitelabel implementations causing confusion

---

## 🔍 Findings

### Duplicate Files Identified

**API Endpoints** (2 files):
1. ❌ `app/api/core/whitelabel.py` - OLD (3 routes, uses WhiteLabelConfig)
2. ✅ `app/api/core/whitelabel_endpoints.py` - NEW (11 routes, uses WhitelabelDomain/Branding/EmailTemplate)

**Models** (3 files):
1. ❌ `app/models/whitelabel.py` - OLD (WhiteLabelConfig)
2. ❌ `app/models/whitelabel_enhanced.py` - OLD (WhiteLabelDomain, WhiteLabelTheme, WhiteLabelAsset, PartnerFeature)
3. ✅ `app/models/whitelabel_models.py` - NEW (WhitelabelDomain, WhitelabelBranding, WhitelabelEmailTemplate)

**Services** (2 files):
1. ❌ `app/services/whitelabel_enhanced.py` - OLD (uses WhiteLabelConfig)
2. ✅ `app/services/whitelabel_service.py` - NEW (uses WhitelabelDomain/Branding)

---

## 📊 Usage Analysis

### OLD Implementation (whitelabel.py)
- **Registered in**: `main.py` line 213
- **Routes**: 3 (GET, POST, DELETE `/api/whitelabel`)
- **Tables**: `whitelabel_config`, `whitelabel_domains`, `whitelabel_themes`, `whitelabel_assets`, `partner_features`
- **Migration**: None found (tables may not exist in production)
- **Used by**: Only `app/api/core/whitelabel.py` and `app/services/whitelabel_enhanced.py`

### NEW Implementation (whitelabel_endpoints.py)
- **Registered in**: `app/api/core/router.py` line 59
- **Routes**: 11 (full CRUD for domains, branding, email templates)
- **Tables**: `whitelabel_custom_domains`, `whitelabel_custom_branding`, `whitelabel_custom_email_templates`
- **Migration**: `add_whitelabel_custom_tables.py` (exists, ready to deploy)
- **Used by**: Active Q2 2026 implementation

---

## ⚠️ Conflict Analysis

### Route Conflicts
Both routers use the same prefix `/api/whitelabel`:
- OLD: `GET /api/whitelabel`, `POST /api/whitelabel`, `DELETE /api/whitelabel`
- NEW: `GET /api/whitelabel/config`, `POST /api/whitelabel/setup`, etc.

**Impact**: OLD routes may shadow NEW routes or cause confusion

### Model Conflicts
- OLD uses `WhiteLabelConfig` with `partner_id`
- NEW uses `WhitelabelDomain/Branding/EmailTemplate` with `user_id`
- Table names don't conflict (different names)

**Impact**: No database conflicts, but code confusion

---

## 🎯 Cleanup Actions

### Phase 1: Remove OLD API Endpoint ✅
- [x] Remove `app/api/core/whitelabel.py`
- [x] Remove import from `main.py`
- [x] Remove router registration from `main.py`

### Phase 2: Remove OLD Models ✅
- [x] Remove `app/models/whitelabel.py`
- [x] Remove `app/models/whitelabel_enhanced.py`
- [x] Remove imports from `app/models/__init__.py`

### Phase 3: Remove OLD Service ✅
- [x] Remove `app/services/whitelabel_enhanced.py`

### Phase 4: Verify No References ✅
- [x] Search codebase for `WhiteLabelConfig` references
- [x] Search codebase for `whitelabel_enhanced` references
- [x] Ensure no broken imports

---

## 🧪 Testing Plan

### Before Cleanup
- [x] Run whitelabel service tests: 24/24 passing
- [x] Verify NEW implementation works

### After Cleanup
- [ ] Run full test suite
- [ ] Verify no import errors
- [ ] Check application starts successfully
- [ ] Verify whitelabel routes still work

---

## 🚀 Rollback Plan

If cleanup causes issues:
1. Restore files from git: `git checkout HEAD~1 app/api/core/whitelabel.py app/models/whitelabel*.py app/services/whitelabel_enhanced.py`
2. Restore imports in `main.py`
3. Restart application

---

## 📝 Notes

- OLD implementation appears to be from an earlier phase
- NEW implementation is part of Q2 2026 (v4.6.0)
- No production data at risk (different table names)
- Cleanup will reduce confusion and maintenance burden
