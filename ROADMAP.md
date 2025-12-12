# Namaskah Roadmap - TextVerified Integration

## Plan Overview

Namaskah offers 3 subscription tiers based on TextVerified SMS verification capabilities:

### Tier 1: Freemium (Free)
- **Feature**: Random US phone numbers only
- **Limit**: 100 verifications/day
- **API Access**: Web UI only
- **Test Credentials**: `free_user@test.com`

### Tier 2: Starter ($9/mo)
- **Feature**: Area code filtering (US numbers)
- **Limit**: 1,000 verifications/day
- **API Access**: 5 API keys
- **Test Credentials**: `starter_user@test.com`

### Tier 3: Turbo ($13.99/mo)
- **Feature**: Area code + ISP/Carrier filtering (US numbers)
- **Limit**: 10,000 verifications/day
- **API Access**: Unlimited API keys
- **Test Credentials**: `turbo_user@test.com`

---

## Implementation Tasks

### Phase 1: Dashboard UI (Current)
- [x] Sidebar navigation
- [x] 11 dashboard sections
- [ ] Notification bell icon
- [ ] Remove mock data
- [ ] Working buttons
- [ ] Admin balance sync with API

### Phase 2: Tier-Based Features
- [ ] Freemium: Random number selection
- [ ] Starter: Area code selector
- [ ] Turbo: Area code + ISP selector
- [ ] Rate limiting per tier
- [ ] API key management per tier

### Phase 3: Testing
- [ ] Test with 3 user credentials
- [ ] Verify tier restrictions
- [ ] Test API endpoints
- [ ] Load testing

---

## Test Credentials

```
Freemium:
  Email: free_user@test.com
  Password: test123
  Features: Random numbers only

Starter:
  Email: starter_user@test.com
  Password: test123
  Features: Area code filtering

Turbo:
  Email: turbo_user@test.com
  Password: test123
  Features: Area code + ISP filtering
```

---

## Current Status

**Phase 1**: In Progress
- Dashboard UI: ✅ Complete
- Notification bell: ⏳ Pending
- Mock data removal: ⏳ Pending
- Button functionality: ⏳ Pending
- Admin balance sync: ⏳ Pending
