# Testing Guide

## Quick Start

```bash
# Start app
python main.py

# Visit dashboard
http://localhost:8000/dashboard
```

---

## Test Admin Access

1. **Login**
   - Email: `admin@namaskah.app`
   - Password: `Namaskah@Admin2024`

2. **Verify Access**
   - Check balance: $10,000
   - Check tier: Turbo
   - Notification bell active
   - All buttons functional

3. **Test Verification Flow**
   - Click "New Verification +"
   - Select service (e.g., Telegram)
   - Select area code (e.g., 555 - New York)
   - See phone number preview
   - Click "Next" to purchase
   - Verify success message

4. **Test Rental Flow**
   - Go to Rentals section
   - Click "Create New Rental"
   - Select service
   - Select area code
   - Choose duration (7, 30, or 90 days)
   - See pricing breakdown
   - Click "Rent Now"

---

## Test Free User

1. **Login**
   - Email: `free_user@test.com`
   - Password: `test123`

2. **Verify Restrictions**
   - Should see random numbers only
   - No area code selector (future)
   - No ISP selector (future)

---

## Test Starter User

1. **Login**
   - Email: `starter_user@test.com`
   - Password: `test123`

2. **Verify Features**
   - Area code selector visible (future)
   - No ISP selector (future)

---

## Test Turbo User

1. **Login**
   - Email: `turbo_user@test.com`
   - Password: `test123`

2. **Verify Features**
   - Area code selector visible (future)
   - ISP selector visible (future)

---

## Features to Test

- [x] Dashboard loads
- [x] Notification bell works
- [x] Balance displays
- [x] Admin balance syncs
- [x] Verification modal opens
- [x] Area code selector shows
- [x] Pricing displays
- [x] Rental modal opens
- [x] Duration options work
- [x] Pricing calculation works
- [ ] Tier-based restrictions (next phase)
- [ ] ISP filtering (next phase)

---

## Known Limitations

- Area codes are mock data (from TextVerified API)
- Tier-based UI restrictions not yet implemented
- ISP filtering not yet implemented
- SMS message display not yet implemented
- Rental renewal not yet implemented

---

## Support

Check logs for errors:
```bash
tail -f logs/app.log
```

Health check:
```bash
curl http://localhost:8000/api/system/health
```
