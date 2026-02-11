# API Endpoint Quick Reference

## Fixed 404 Errors ✅

All previously failing endpoints now work via compatibility layer.

### Endpoint Mappings

| Frontend Call (Old/Incorrect) | Backend Implementation | Status |
|-------------------------------|------------------------|--------|
| `GET /api/billing/balance` | → `/api/wallet/balance` | ✅ Fixed |
| `GET /api/user/me` | → `/api/auth/me` | ✅ Fixed |
| `GET /api/tiers/current` | → `/api/billing/tiers/current` | ✅ Fixed |
| `GET /api/tiers/` | → `/api/billing/tiers/available` | ✅ Fixed |
| `GET /api/tiers` | → `/api/billing/tiers/available` | ✅ Fixed |
| `GET /api/notifications/categories` | Stub implementation | ✅ Fixed |
| `GET /api/user/settings` | Stub implementation | ✅ Fixed |

## Correct API Endpoints (Recommended)

For new code, use these correct endpoints:

### Authentication
```
POST   /api/auth/login          # Login
POST   /api/auth/register       # Register
GET    /api/auth/me             # Get current user ✅ Use this
POST   /api/auth/logout         # Logout
```

### Wallet & Balance
```
GET    /api/wallet/balance      # Get balance ✅ Use this
POST   /api/wallet/paystack/initialize
POST   /api/wallet/paystack/verify
GET    /api/wallet/transactions
```

### Tiers
```
GET    /api/billing/tiers/current    # Current tier ✅ Use this
GET    /api/billing/tiers/available  # All tiers ✅ Use this
POST   /api/billing/tiers/upgrade
```

### Notifications
```
GET    /api/notifications              # List notifications
GET    /api/notifications/unread-count # Unread count
GET    /api/notifications/categories   # Categories ✅ New
POST   /api/notifications/{id}/read    # Mark as read
```

### User Settings
```
GET    /api/user/settings       # User settings ✅ New
PUT    /api/user/settings       # Update settings (TODO)
```

## Migration Guide

### Step 1: Update API Client (Optional)
```javascript
// Old (still works via compatibility layer)
const balance = await fetch('/api/billing/balance');

// New (recommended)
const balance = await fetch('/api/wallet/balance');
```

### Step 2: Update User Info Calls
```javascript
// Old (still works)
const user = await fetch('/api/user/me');

// New (recommended)
const user = await fetch('/api/auth/me');
```

### Step 3: Update Tier Calls
```javascript
// Old (still works)
const tier = await fetch('/api/tiers/current');

// New (recommended)
const tier = await fetch('/api/billing/tiers/current');
```

## Testing

### Quick Test
```bash
# Start server
./start.sh

# Test compatibility routes (should all return 200)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/billing/balance
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/user/me
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/tiers/current
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/notifications/categories
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/user/settings
```

### Automated Test
```bash
python3 test_api_fixes.py
```

## Files Changed

1. **New**: `app/api/compatibility_routes.py` (90 lines)
   - Route aliases and stub implementations

2. **Modified**: `main.py` (2 lines)
   - Added compatibility router import and registration

3. **New**: `docs/API_404_FIXES.md`
   - Detailed documentation

4. **New**: `test_api_fixes.py`
   - Verification script

## Rollback

If needed, comment out in `main.py`:
```python
# fastapi_app.include_router(compatibility_router, prefix="/api")
```

## Support

- Full docs: [docs/API_404_FIXES.md](./API_404_FIXES.md)
- API Guide: [docs/API_GUIDE.md](./API_GUIDE.md)
- Issues: Check logs at `logs/app.log`
