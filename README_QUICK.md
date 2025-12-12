# Namaskah - Quick Start

## What is Namaskah?

SMS verification platform with 3 subscription tiers based on TextVerified offerings.

## Tiers

| Tier | Price | Features | Limit |
|------|-------|----------|-------|
| Freemium | Free | Random US numbers | 100/day |
| Starter | $9/mo | Area code filtering | 1,000/day |
| Turbo | $13.99/mo | Area code + ISP filtering | 10,000/day |

## Test Now

```bash
# Start app
python main.py

# Visit dashboard
http://localhost:8000/dashboard

# Login with any test user
Email: free_user@test.com
Password: test123
```

## Dashboard Features

- 📊 Analytics dashboard
- 🔔 Notifications bell
- 💳 Balance management
- 🔑 API key generation
- 📱 SMS verification
- 🎙️ Voice verification
- 📋 Rental management
- ⚙️ Settings & profile

## Files

- **Dashboard**: `/templates/dashboard.html`
- **Roadmap**: `/ROADMAP.md`
- **Tasks**: `/TASKS.md`
- **Status**: `/IMPLEMENTATION_STATUS.md`

## Next Steps

1. Test with 3 user credentials
2. Implement tier-based UI
3. Add area code selector (Starter+)
4. Add ISP selector (Turbo)
5. Implement rate limiting
