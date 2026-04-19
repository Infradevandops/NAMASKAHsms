# Voice Verification & Rental Features - Current Status

**Date**: April 19, 2026  
**Status**: Partially Implemented

---

## 🎤 Voice Verification

### ✅ What's Implemented

1. **Frontend UI** (`voice_verify_modern.html`)
   - Service selection dropdown
   - Area code selector
   - Carrier selector (UI only - non-functional)
   - Voice/SMS toggle
   - Status polling

2. **Backend Support**
   - Tier gating: Requires PAYG or higher
   - `capability: "voice"` parameter accepted
   - Voice polling service exists
   - Voice status tracking

3. **Provider Integration**
   - TextVerified voice verification supported
   - Voice message polling implemented
   - Transcription support

### ❌ What's NOT Working

1. **Carrier Filtering**
   - Frontend sends `carriers` parameter
   - Backend receives it but **ignores it**
   - Line 232 in `purchase_endpoints.py`: `carrier = getattr(request, "carrier", None)` - never used
   - Line 289: `requested_carrier=None` - hardcoded to None
   - Line 291: `assigned_carrier=None` - hardcoded to None
   - Line 293: `carrier_matched=True` - always true (feature retired)
   - Line 294: `real_carrier=None` - always null

2. **Why Carrier Was Retired**
   - Per `docs/archives/history/BROKEN_ITEMS.md`:
     > "carrier filtering retired, city-level routing, clean errors"
   - Commit: `3bef4bc8`
   - Reason: Carrier filtering was unreliable/not supported by providers

### 🔧 Required Fixes

**Option 1: Remove Carrier UI (Recommended)**
```html
<!-- Remove from voice_verify_modern.html -->
<div>
    <label class="form-label">Carrier (Optional)</label>
    <select class="form-select" id="carrier-select">
        <!-- DELETE THIS ENTIRE DIV -->
    </select>
</div>
```

**Option 2: Re-implement Carrier Filtering**
- Would require provider API support
- TextVerified may not support carrier filtering
- High complexity, low value

---

## 🏠 Number Rentals

### ❌ Status: REMOVED

**Removal Details**:
- Commit: `78277093` - "Remove all SMS providers except TextVerified and delete rental feature"
- Date: Earlier in project
- Reason: Feature scope reduction

**What Was Removed**:
- `app/api/verification/rental_endpoints.py` - Deleted
- `app/services/rental_service.py` - Exists but not used
- `templates/rentals.html` - Removed
- Sidebar navigation entry - Removed
- Database table: `number_rentals` - May still exist but unused

**Current State**:
- Backend code exists (`rental_service.py`, `rental_endpoints.py`) but not registered
- No frontend UI
- No routes exposed
- Feature completely disabled

### 🔧 To Re-enable Rentals

Would require:
1. Re-add rental routes to main router
2. Create frontend UI (or restore old template)
3. Test rental flow end-to-end
4. Update documentation
5. Add to sidebar navigation

**Estimated Effort**: 4-8 hours

---

## 📊 Summary Table

| Feature | Frontend | Backend | Provider | Status |
|---------|----------|---------|----------|--------|
| **Voice Verification** | ✅ Exists | ✅ Works | ✅ TextVerified | ✅ **WORKING** |
| **Voice Area Code** | ✅ Exists | ✅ Works | ✅ Supported | ✅ **WORKING** |
| **Voice Carrier Filter** | ⚠️ UI Only | ❌ Ignored | ❌ Not supported | ❌ **NON-FUNCTIONAL** |
| **Number Rentals** | ❌ Removed | ⚠️ Code exists | ✅ TextVerified | ❌ **DISABLED** |

---

## 🎯 Recommendations

### Immediate Actions

1. **Remove Carrier Selector from Voice UI**
   - File: `templates/voice_verify_modern.html`
   - Remove carrier dropdown
   - Update grid to single column (area code only)
   - Remove carrier from JavaScript request

2. **Update Voice Documentation**
   - Clarify that carrier filtering is not available
   - Document area code filtering as the only location filter

3. **Rentals Decision**
   - **Option A**: Keep disabled (current state)
   - **Option B**: Fully remove backend code
   - **Option C**: Re-implement with proper UI

### Code Cleanup

**Files to Update**:
```
templates/voice_verify_modern.html  - Remove carrier UI
app/models/verification.py          - Mark carrier fields as deprecated
docs/                               - Update feature documentation
```

**Files to Consider Removing** (if rentals stay disabled):
```
app/services/rental_service.py
app/api/verification/rental_endpoints.py
app/models/number_rental.py (if exists)
```

---

## 🐛 Known Issues

1. **Voice UI shows carrier dropdown** but it doesn't work
2. **Rental service code exists** but is unreachable
3. **Database may have rental tables** that are unused
4. **Verification model has carrier fields** that are always null

---

## ✅ What Actually Works

**Voice Verification Flow**:
1. User selects service ✅
2. User selects area code (optional) ✅
3. User clicks "Get Number" ✅
4. Backend purchases voice-capable number ✅
5. User receives voice call ✅
6. System transcribes code ✅
7. User sees verification code ✅

**What Doesn't Work**:
- Carrier selection (UI exists but ignored)
- Number rentals (completely disabled)

---

**Last Updated**: April 19, 2026  
**Needs Action**: Remove carrier UI from voice template
