# ACTIVE SPRINT — v4.9.7 Coverage Push + Phase 2 Analytics Kickoff

**Updated**: November 1, 2026
**Version**: 4.9.7
**Focus**: Push CI test gate toward 90% coverage, kick off Phase 2 Analytics

---

## Previous Sprint: v4.9.6 ✅ COMPLETE

All tasks done. See `CHANGELOG.md` [4.9.6] for full details.

Commits:
- `4724bbfd` — TV webhook tests, CI gate 24 files, coverage floor 25%
- `24496798` — service_name field fix in Verification fixtures
- `ea07a447` — docs update

---

## Unplanned P0 — TV Stock + Verification Flow Fixes ✅ SHIPPED

**Trigger**: Assessment in `docs/engineering/TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md` identified critical prod gaps where stock shown as available could not actually be purchased.

**Commit**: `47d69fd1`

| Fix | What it does |
|-----|--------------|
| Legacy purchase path availability gate | `POST /verification/request` now calls `check_service_available()` before pricing — fails fast with 422 in <1s instead of burning 5-30s on TV's `verifications.create()` |
| Filter null-price services from picker | `GET /api/services/stock` strips `price=null` services — frontend never receives unpurchasable services |
| Out-of-stock items non-selectable in JS | Services with `available=false` render greyed out (`opacity:0.45`, `pointer-events:none`) in the picker |
| Stock monitor cache warmup | Background loop sleep 120s → 90s so 120s TTL cache is always warm; `price=null` with no quantity now explicitly `available=False` |
| `purchasing` step "still working" timer | After 10s on the `purchasing` SSE step, message changes to "Still working — this can take up to 30 seconds..." |
| `demandBadge` broken ternary | Pre-existing JS syntax error in `renderImmersiveItem` — `demandBadge` had no assignment body, fixed |

**Files changed**: `purchase_endpoints.py`, `services.py`, `stock_monitor.py`, `verification-flow.js`

---

## Sprint Status: 📋 PLANNED

---

## P1 — CI Test Gate: 24 → 60+ files (Coverage Push)

**Goal**: Raise `--cov-fail-under` from 25% toward 60%, then 90%.

**Approach**: Audit existing unit test files for stability, add batches to the CI
`pytest` invocation. Do not write new tests — ~150 files already exist, most are
just not wired to CI.

**Candidate files to add next** (need stability audit first):
```
tests/unit/test_payment_service.py
tests/unit/test_verification_endpoints.py
tests/unit/test_auth_endpoints.py
tests/unit/test_wallet_service.py
tests/unit/test_transaction_service.py
tests/unit/test_analytics_endpoints.py
tests/unit/test_tier_manager.py
tests/unit/test_quota_service.py
tests/unit/test_credit_service.py
tests/unit/test_blacklist.py
tests/unit/test_gdpr.py
tests/unit/test_forwarding.py
tests/unit/test_sms_service.py
tests/unit/test_stock_monitor.py
tests/unit/test_alerting_service.py
```

**Acceptance criteria**:
- All added files pass cleanly in CI
- `--cov-fail-under` raised to match actual coverage from expanded suite
- No flaky tests introduced

---

## P2 — Phase 2 Analytics Kickoff

**Scope** (from PLATFORM_STATUS next steps):
1. Cohort analysis dashboard — user retention by signup week
2. Revenue breakdown charts — by tier, by service, by day
3. Churn prediction model — users with no activity in 14+ days

**Pre-work needed**:
- Assess what data is already in the DB (analytics events table)
- Identify which charts can be served from existing queries vs new aggregations
- Create task doc at `docs/features/PHASE2_ANALYTICS.md`

**This sprint**: Assessment + task doc only. Implementation in v4.9.8.

---

## Next Sprint Candidates

| Item | Priority |
|------|----------|
| Coverage push 60% → 90% (continued) | High |
| Phase 2 Analytics implementation | Medium |
| Remove/wire fake `validating` SSE step | Low |
| Multi-region deployment | Q3 2026 |
