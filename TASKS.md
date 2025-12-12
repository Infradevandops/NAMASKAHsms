# Active Tasks - Phase 1

## Dashboard Improvements

### Task 1: Add Notification Bell
- [ ] Add bell icon to dashboard header
- [ ] Connect to `/api/notifications` endpoint
- [ ] Show unread count badge
- [ ] Click to open notifications panel

### Task 2: Remove Mock Data
- [ ] Remove hardcoded fallback countries
- [ ] Remove hardcoded fallback services
- [ ] Remove demo mode responses
- [ ] Use only real API data

### Task 3: Fix Button Functionality
- [ ] New Verification button → SMS Verification section
- [ ] Add Credits button → Billing section
- [ ] Generate API Key button → API Keys section
- [ ] Create Rental button → Rentals section
- [ ] All buttons must work without alerts

### Task 4: Admin Balance Sync
- [ ] Fetch TextVerified API balance
- [ ] Display in dashboard header
- [ ] Update every 30 seconds
- [ ] Show in admin panel

### Task 5: Tier-Based UI
- [ ] Show current tier in header
- [ ] Hide area code selector for Freemium
- [ ] Hide ISP selector for non-Turbo
- [ ] Show tier upgrade button

---

## Test Scenarios

### Freemium User
1. Login with `free_user@test.com`
2. Verify: No area code selector
3. Verify: No ISP selector
4. Verify: Random numbers only

### Starter User
1. Login with `starter_user@test.com`
2. Verify: Area code selector visible
3. Verify: No ISP selector
4. Verify: Can filter by area code

### Turbo User
1. Login with `turbo_user@test.com`
2. Verify: Area code selector visible
3. Verify: ISP selector visible
4. Verify: Can filter by both

---

## API Endpoints Used

- `GET /api/user/tier` - Get current tier
- `GET /api/notifications` - Get notifications
- `GET /api/user/balance` - Get balance
- `POST /api/verification/purchase` - Purchase verification
- `GET /api/countries/` - Get countries
- `GET /api/verification/textverified/services` - Get services
