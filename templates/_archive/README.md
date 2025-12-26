# 📦 Archived Templates

**Date**: 2025-12-25  
**Reason**: Cleanup - Unused template versions

## Files Archived

### Verify Templates (4 files)
- `verify_modern.html` (420 lines)
- `verify_simple.html` (710 lines)
- `verify_stable.html` (308 lines)
- `verify_connected.html` (447 lines)

**Active**: `verify.html` (renamed from `verify_standard.html`)

### Auth Templates (1 file)
- `auth.html` (393 lines - old version)

**Active**: `auth.html` (renamed from `auth_simple.html`)

## Why Archived

These templates were not referenced in `main.py` or any router files. They appear to be:
- Old design iterations
- Experimental versions
- Deprecated implementations

## Restoration

To restore any template:
```bash
cp templates/_archive/[filename] templates/[filename]
```

## Deletion

If confirmed unused after 30 days, delete with:
```bash
rm -rf templates/_archive
```

---

**Note**: All code preserved. No data loss.
