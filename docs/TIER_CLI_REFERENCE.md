# Tier Management CLI Reference

## Installation

```bash
cd /path/to/namaskah-app
chmod +x scripts/tier_cli.py
```

---

## Commands

### List Available Tiers
```bash
python scripts/tier_cli.py list-tiers

Output:
📊 Available Tiers:
────────────────────────────────────────────────────────────────────────────────

  PAY-AS-YOU-GO
    Price: $0.00/month
    Quota: $0
    API Keys: 0
    Features:
      - API Access: ✗
      - Area Code Selection: ✗
      - ISP Filtering: ✗

  STARTER
    Price: $8.99/month
    Quota: $10
    API Keys: 5
    Features:
      - API Access: ✓
      - Area Code Selection: ✓
      - ISP Filtering: ✗
```

### List Users
```bash
# All users
python scripts/tier_cli.py list-users

# Filter by tier
python scripts/tier_cli.py list-users --tier starter

# Limit results
python scripts/tier_cli.py list-users --tier pro --limit 100

Output:
👥 Users (20 shown):
────────────────────────────────────────────────────────────────────────────────────────────────────
Email                          Tier         Expires         Credits    Joined
────────────────────────────────────────────────────────────────────────────────────────────────────
user1@example.com              starter      2025-01-15      25.50      2024-12-01
user2@example.com              pro          2025-02-20      100.00     2024-11-15
```

### Get User Information
```bash
python scripts/tier_cli.py user-info user123

Output:
📋 User Information:
──────────────────────────────────────────────────────
  ID: user123
  Email: user@example.com
  Tier: PRO
  Tier Name: Pro
  Credits: $100.00
  Admin: No
  Created: 2024-12-01 10:30:00
  Last Login: 2025-01-08 15:45:30
  Tier Expires: 2025-02-20 00:00:00

  Tier Features:
    - API Access: ✓
    - Area Code Selection: ✓
    - ISP Filtering: ✓
    - API Key Limit: 10
```

### Set User Tier
```bash
# Set to Pro for 30 days
python scripts/tier_cli.py set-tier user123 pro --days 30

# Set to Starter for 60 days
python scripts/tier_cli.py set-tier user123 starter --days 60

# Reset to Pay-As-You-Go
python scripts/tier_cli.py set-tier user123 payg

Output:
✅ User user@example.com tier updated: starter → pro
   Expires: 2025-02-08
```

### Bulk Set Tier
```bash
python scripts/tier_cli.py bulk-set-tier user1 user2 user3 pro --days 30

Output:
✅ Updated 3 users to pro tier
```

### Extend Tier
```bash
python scripts/tier_cli.py extend-tier user123 --days 30

Output:
✅ Tier extended by 30 days
   Old expiry: 2025-01-15
   New expiry: 2025-02-14
```

### Get Expiring Tiers
```bash
# Tiers expiring in 7 days
python scripts/tier_cli.py expiring

# Tiers expiring in 14 days
python scripts/tier_cli.py expiring --days 14

Output:
⏰ Tiers Expiring in 7 Days (5 users):
────────────────────────────────────────────────────────────────────────────────────────────────────
Email                          Tier         Expires         Days Left
────────────────────────────────────────────────────────────────────────────────────────────────────
user1@example.com              starter      2025-01-10      3
user2@example.com              pro          2025-01-12      5
```

---

## Common Workflows

### Upgrade User to Pro
```bash
python scripts/tier_cli.py set-tier user123 pro --days 30
```

### Bulk Upgrade Users
```bash
python scripts/tier_cli.py bulk-set-tier user1 user2 user3 starter --days 30
```

### Monitor Expiring Tiers
```bash
python scripts/tier_cli.py expiring --days 7
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "User not found" | Verify user ID is correct with `list-users` |
| "Invalid tier" | Use only: `payg`, `starter`, `pro`, `custom` |
| "Permission denied" | Ensure script is executable: `chmod +x scripts/tier_cli.py` |
| Bulk update fails | Maximum 1000 users per request; verify all IDs exist |

---

**Last Updated**: 2025-01-08  
**Version**: 1.0.0
