# Tier Resolution Bug Fix — March 14, 2026

## Problem
Admin user on "custom" tier with `tier_expires_at=NULL` was blocked from using area code/carrier filtering with `402 Payment Required`. UI showed "CUSTOM" but backend treated user as "freemium".

## Root Causes
1. **Stale SQLAlchemy session** — `TierManager` read from identity map cache instead of DB
2. **Redundant tier checks** — `validate_tier_access()` used stale user object before `TierManager` ran
3. **Incorrect expiry logic** — `if expires and` instead of `if expires is not None and`
4. **TierConfig fallback bug** — always fell back to freemium config instead of requested tier
5. **Carrier endpoint inconsistency** — excluded payg from ISP filtering despite tier config

## Changes
- `tier_manager.py`: Added `db.refresh(user)`, fixed expiry check, added logging
- `purchase_endpoints.py`: Removed redundant `validate_tier_access()`, consolidated to `TierManager`
- `tier_endpoints.py`: Use `TierManager.get_user_tier()` for consistency
- `tier_config.py`: Fixed fallback to use requested tier, not always freemium
- `carrier_endpoints.py`: Include payg in `can_select` for carriers

## Tests
40 new tests in `tests/unit/test_tier_resolution.py` — all pass
- Custom tier with NULL expiry stays custom ✓
- Expired tiers downgrade ✓
- Feature access matrix (12 combinations) ✓
- Tier hierarchy (8 combinations) ✓
- Upgrade/downgrade persistence ✓

## Verification
```bash
pytest tests/unit/test_tier_resolution.py -v  # 40 passed
pytest tests/unit/test_simple.py tests/test_startup_smoke.py -v  # 31 passed
python3 -c "from main import app; print(len(app.routes))"  # 268 routes
```

## Impact
✅ Admin users can use all custom tier features
✅ Tier resolution consistent across all endpoints
✅ No stale session data
✅ Single source of truth (TierManager)
✅ Zero downtime deployment
