# Verification Flow UI/UX Redesign Task

**Status**: 🔴 Open
**Priority**: High
**Created**: November 24, 2026

---

## Problem

### 1. Duplicate Service Selector (J-010)

Two separate UI elements do the same job on Step 1:

| Element | Location | Behaviour |
|---|---|---|
| Loading banner + `Service *` dropdown | Step 1 card (inline) | Fetches services, renders a `<select>` or searchable input |
| "Select Service" modal | Triggered separately | Full-screen dark modal with search, recently used, icons, stock status |

The inline `Service *` field and the modal are redundant. The modal (dark theme, icons, recently used, stock badges) is clearly the better UX — the inline field is a legacy leftover.

### 2. FK Error Still Blocking Purchases

`Textual SQL expression 'UPDATE verifications SET ...' should be explicitly declared as text(...)` — SQLAlchemy 2.x rejects bare string SQL. Fixed in this session with `sa_text()` wrapper.

---

## Root Cause Analysis

- Step 1 was originally a simple inline form (`Service *` dropdown + country select)
- The modal (`Select Service`) was added later as a better UX but was never wired to **replace** the inline form — it was wired to **populate** it
- The loading banner ("Initiating number for verification / SMS") was added on top of the inline form, making it look like a third element
- Result: user sees banner → inline loading field → modal opens on click → confusing

---

## Proposed Redesign

### Flow: Step 0 → Step 1 → Step 2 → Step 3

```
Step 0: Choose Method (SMS / Voice / SMS+Voice)
         ↓ chooseMethod()
Step 1: Service picker — ONLY the modal, no inline form
         - Modal opens immediately after method chosen
         - On service select → close modal → go to Step 2
Step 2: Pricing & Details card (shimmer → real data)
         - Confirm / Back buttons
Step 3: Phone number + polling + code received
```

### Changes Required

**`verify_modern.html`**:
- Remove `Service *` inline field and country select from Step 1 card
- Remove loading banner from Step 1 (it's redundant if modal opens immediately)
- Step 1 card becomes just a container that auto-triggers the modal
- Presets (`+ Save`, `No presets yet`) move into the modal as a tab or section

**`verification-flow.js`**:
- `chooseMethod()` → directly opens service modal instead of showing Step 1 card with inline form
- `confirmService(serviceId, serviceName)` → closes modal, calls `updateProgress(2)`, loads pricing
- Remove `loadServices()` call that populates the inline dropdown (modal has its own loader)
- Presets save/load wired to modal

**Modal** (`Select Service` dark modal):
- Already has: search, recently used, icons, stock status, pin/favourite
- Add: preset save button per service row
- Add: method badge (SMS / Voice) in header based on `chooseMethod()` selection

---

## Acceptance Criteria

- [ ] Step 1 shows no inline `Service *` field — only the modal
- [ ] Modal opens automatically when method is chosen (no extra click)
- [ ] Selecting a service in modal advances directly to Step 2 pricing card
- [ ] Presets accessible from within modal
- [ ] No duplicate service loading (one fetch, shared between modal and flow)
- [ ] FK error resolved (`sa_text()` fix deployed)
- [ ] Zero JS console errors on flow completion

---

## Files to Modify

- `templates/verify_modern.html` — remove inline form from Step 1
- `static/js/verification-flow.js` — rewire `chooseMethod()` → modal → `confirmService()`
- `static/js/verification-templates.js` — check if service modal JS lives here

---

## Related

- J-001: Step 0+1 stacking bug (fixed)
- J-009: Orphan recovery hijack (fixed)
- FK violation: `verifications_debit_transaction_id_fkey` (fixed — `sa_text()`)
