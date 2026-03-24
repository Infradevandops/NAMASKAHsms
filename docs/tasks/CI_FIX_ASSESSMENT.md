# CI Fix Assessment

**Date**: March 20, 2026  
**Baseline** (local, with known-bad files ignored): **797 passed, 354 failed, 625 errors, 24 skipped**  
**Target**: ~1700 passed, 0 collection errors, 4/4 CI jobs green

---

## Baseline Discrepancy vs Plan

The CI_FIX_PLAN.md stated baseline of **834 passed** — actual local run shows **797 passed**.  
Difference likely due to 2 newly discovered collection errors (`test_tier_helpers.py`, `test_auth_service_enhanced.py`) that were not in the original plan.

---

## Fix 3 — ci.yml: Remove `--maxfail=10`, add `--ignore` flags

**Plan**: Remove `--maxfail=10`, add 6 ignore flags  
**Status**: ❌ Not done  
**Gap found**: 2 additional files need ignoring beyond the plan:
- `tests/test_tier_helpers.py` — `ModuleNotFoundError: hypothesis` (collection error)
- `tests/unit/test_auth_service_enhanced.py` — `ModuleNotFoundError: jose` (collection error)

**Action**: Add both to `--ignore` list in `ci.yml`, OR install `hypothesis` and `python-jose` in CI (already in `requirements-test.txt` so CI should have them — local venv was missing them, now fixed).

**Updated ignore list for ci.yml**:
```
--ignore=tests/unit/test_payment_race_condition.py
--ignore=tests/test_i18n.py
--ignore=tests/test_i18n_frontend.py
--ignore=tests/unit/test_disaster_recovery.py
--ignore=tests/unit/test_enterprise_service.py
--ignore=tests/unit/test_sms_logic.py
```
Note: `test_tier_helpers.py` and `test_auth_service_enhanced.py` are NOT in this list — they fail locally due to missing venv packages, but CI installs `requirements-test.txt` which includes both `hypothesis` and `python-jose`, so they should collect fine in CI.

---

## Fix 4 — conftest.py: Missing model imports (~76 errors)

**Plan**: Add ~30 model imports before `Base.metadata.create_all()`  
**Status**: ❌ Not done  
**Verified**: `625 errors` in baseline — majority are `no such table` errors from missing model imports  
**Gap**: Plan is accurate. No additional models found beyond what was listed.

---

## Fix 5 — conftest.py: Missing fixtures (~500 errors)

**Plan**: Add 12 missing fixtures  
**Status**: ❌ Not done  
**Verified**: `fixture 'db_session' not found`, `fixture 'user_token' not found` etc. confirmed in error output  
**Gap**: Plan is accurate. All 12 fixtures listed are genuinely missing.

---

## Fix 6 — UNIQUE email collisions (~87 errors)

**Plan**: Replace hardcoded emails with UUID-based emails in offending test files  
**Status**: ❌ Not done  
**Verified**: `UNIQUE constraint failed: users.email` present in failures  
**Gap**: Plan is accurate.

---

## Fix 7 — Code-level errors (~30 failures)

**Plan**: Fix 5 sub-issues (whitelabel import, auto_topup patch, access_token KeyError, get_current_user_id import, missing `db` arg)  
**Status**: ❌ Not done  
**Verified**:
- `test_whitelabel_enhanced.py` — `NameError` confirmed in baseline errors ✅ matches plan
- `test_auto_topup.py` — needs verification
- `access_token` KeyError — needs verification
- `get_current_user_id` import — needs verification

**Gap**: `test_whitelabel_enhanced.py` errors show as `NameError` not `ImportError` — the class exists but is not imported in the test file. Plan fix is correct.

---

## Fix 1 — Gitleaks allowlist

**Plan**: Run gitleaks locally, find trigger, update `tools/gitleaks.toml`  
**Status**: ❌ Not done  
**Gap**: Cannot assess without running gitleaks locally (requires Docker). Plan is correct.

---

## Fix 2 — Bandit/Safety/Semgrep

**Plan**: Pin `bandit==1.7.8` in CI, verify safety + semgrep  
**Status**: ❌ Not done  
**Gap**: `requirements-test.txt` has `bandit==1.7.6` (not 1.7.8 as plan states). Either version should work — use what's already pinned (`1.7.6`) rather than changing to `1.7.8`.  
**Updated action**: Keep `bandit==1.7.6` in `requirements-test.txt`, just ensure CI uses `requirements-test.txt` (it already does).

---

## Additional Issues Not in Plan

### A — `hypothesis` and `python-jose` missing from local venv
**Impact**: 2 collection errors locally (not in CI — CI installs requirements-test.txt)  
**Action**: Already fixed locally (`pip install hypothesis python-jose`). No CI change needed.

### B — `--cov-fail-under=36` in ci.yml
**Plan**: Raise to 60%+ after fixes land  
**Status**: ❌ Not done (intentionally deferred)  
**Action**: Leave at 36% until fixes 3-7 are applied and passing count jumps, then raise.

### C — `test_payment_race_condition.py` segfault
**Plan**: Delete or archive  
**Status**: ❌ Not done — currently only ignored via `--ignore` flag  
**Action**: Should be deleted to prevent accidental re-inclusion.

---

## Execution Checklist (Ordered by Impact)

- [ ] **Fix 3** — Remove `--maxfail=10`, add 6 `--ignore` flags in `ci.yml`
- [ ] **Fix 4** — Add 30 model imports to `tests/conftest.py`
- [ ] **Fix 5** — Add 12 missing fixtures to `tests/conftest.py`
- [ ] **Fix 6** — UUID emails in offending test files
- [ ] **Fix 7a** — Add missing import to `tests/unit/test_whitelabel_enhanced.py`
- [ ] **Fix 7b** — Add `get_current_user_id` import to affected test files
- [ ] **Fix 7c** — Fix `auto_topup` patch target (`PaymentService` → `PaystackService`)
- [ ] **Fix 7d** — Fix `access_token` KeyError in auth test files
- [ ] **Fix 7e** — Fix `__init__()` missing `db` arg
- [ ] **Fix 1** — Run gitleaks locally, update `tools/gitleaks.toml`
- [ ] **Fix 2** — Verify bandit/safety/semgrep pass with current pins
- [ ] **Cleanup** — Delete `tests/unit/test_payment_race_condition.py`
- [ ] **Raise coverage** — Bump `--cov-fail-under` from 36% to 60%+ after above land

---

## Expected Outcome

| Metric | Before | After |
|--------|--------|-------|
| Collection errors | 2 | 0 |
| Test errors | 625 | ~0 |
| Test failures | 354 | <50 |
| Tests passing | 797 | ~1700+ |
| CI jobs green | 1/4 | 4/4 |
