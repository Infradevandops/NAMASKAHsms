# 🎯 Tier Management - Complete Implementation Guide

## Overview

The tier management system provides **3 ways** to manage user subscription tiers:

1. **Web Dashboard** - Visual UI for admins
2. **REST API** - Programmatic access
3. **CLI Tool** - Command-line management

---

## 📊 Tier Structure

| Tier | Price | Quota | API Keys | Features |
|------|-------|-------|----------|----------|
| **Pay-As-You-Go** | $0/mo | None | ❌ | Basic SMS |
| **Starter** | $8.99/mo | $10 | 5 keys | Area code selection |
| **Pro** | $25/mo | $30 | 10 keys | + ISP filtering |
| **Custom** | $35/mo | $50 | Unlimited | All features |

---

## 🌐 Web Dashboard

### Access
```
URL: http://localhost:8000/admin/tier-management
Requires: Admin account
```

### Features
- **View Statistics**: See tier distribution across all users
- **Search & Filter**: Find users by email, ID, or tier
- **Edit Individual Tiers**: Change any user's tier with custom duration
- **Bulk Updates**: Update multiple users at once
- **Expiry Tracking**: Monitor tier expiration dates
- **Real-time Refresh**: Auto-update statistics

### Usage

1. **View Tier Distribution**
   - Dashboard loads automatically with tier statistics
   - Shows user count and percentage for each tier

2. **Search Users**
   - Use search box to find by email or user ID
   - Filter by tier using dropdown

3. **Change User Tier**
   - Click "Edit" button on any user row
   - Select new tier and duration
   - Click "Save Changes"

4. **Bulk Update**
   - Click "📋 Bulk Update" button
   - Enter comma-separated user IDs
   - Select tier and duration
   - Click "Update All"

5. **Reset to Pay-As-You-Go**
   - Click "Reset" button on user row
   - Confirms before resetting

---

## 🔌 REST API

### Base URL
```
http://localhost:8000/api/admin/tiers
```

### Authentication
All endpoints require admin access token:
```bash
Authorization: Bearer <admin_access_token>
```

### Endpoints

#### 1. Get Tier Statistics
```bash
GET /api/admin/tiers/stats

Response:
{
  "stats": [
    {
      "tier": "payg",
      "user_count": 150,
      "percentage": 45.5
    },
    ...
  ],
  "total_users": 330
}
```

#### 2. List Users
```bash
GET /api/admin/tiers/users?tier=starter&limit=50&offset=0

Query Parameters:
- tier: Filter by tier (payg, starter, pro, custom)
- limit: Results per page (1-500, default 50)
- offset: Pagination offset (default 0)

Response:
{
  "total": 100,
  "limit": 50,
  "offset": 0,
  "users": [
    {
      "id": "user123",
      "email": "user@example.com",
      "tier": "starter",
      "tier_expires_at": "2025-01-15T00:00:00Z",
      "credits": 25.50,
      "created_at": "2024-12-01T10:30:00Z"
    },
    ...
  ]
}
```

#### 3. Get User Tier Info
```bash
GET /api/admin/tiers/users/{user_id}/tier

Response:
{
  "user_id": "user123",
  "email": "user@example.com",
  "current_tier": "pro",
  "tier_name": "Pro",
  "expires_at": "2025-01-15T00:00:00Z",
  "is_expired": false,
  "tier_config": {
    "price_monthly": 2500,
    "quota_usd": 30,
    "api_key_limit": 10,
    "has_api_access": true,
    "has_area_code_selection": true,
    "has_isp_filtering": true,
    "support_level": "priority"
  }
}
```

#### 4. Set User Tier
```bash
POST /api/admin/tiers/users/{user_id}/tier

Request Body:
{
  "tier": "pro",
  "duration_days": 30
}

Response:
{
  "success": true,
  "message": "User tier updated from starter to pro",
  "user_id": "user123",
  "new_tier": "pro",
  "expires_at": "2025-01-15T00:00:00Z"
}
```

#### 5. Bulk Update Tiers
```bash
POST /api/admin/tiers/users/bulk/tier

Request Body:
{
  "user_ids": ["user1", "user2", "user3"],
  "tier": "pro",
  "duration_days": 30
}

Response:
{
  "success": true,
  "message": "Updated 3 users to pro tier",
  "updated_count": 3,
  "total_requested": 3
}
```

#### 6. Reset User Tier
```bash
DELETE /api/admin/tiers/users/{user_id}/tier

Response:
{
  "success": true,
  "message": "User tier reset from pro to Pay-As-You-Go",
  "user_id": "user123",
  "new_tier": "payg"
}
```

#### 7. Extend Tier Expiry
```bash
POST /api/admin/tiers/users/{user_id}/tier/extend?days=30

Response:
{
  "success": true,
  "message": "Tier extended by 30 days",
  "user_id": "user123",
  "old_expiry": "2025-01-15T00:00:00Z",
  "new_expiry": "2025-02-14T00:00:00Z"
}
```

#### 8. Get Expiring Tiers
```bash
GET /api/admin/tiers/expiring?days=7

Query Parameters:
- days: Threshold in days (1-90, default 7)

Response:
{
  "expiring_in_days": 7,
  "count": 5,
  "users": [
    {
      "id": "user123",
      "email": "user@example.com",
      "tier": "starter",
      "expires_at": "2025-01-10T00:00:00Z",
      "days_until_expiry": 3
    },
    ...
  ]
}
```

### Example cURL Commands

```bash
# Get tier statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/tiers/stats

# List Pro tier users
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/admin/tiers/users?tier=pro&limit=20"

# Set user to Pro tier
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"pro","duration_days":30}' \
  http://localhost:8000/api/admin/tiers/users/user123/tier

# Bulk update users
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids":["user1","user2","user3"],
    "tier":"starter",
    "duration_days":30
  }' \
  http://localhost:8000/api/admin/tiers/users/bulk/tier

# Get expiring tiers
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/admin/tiers/expiring?days=14"
```

---

## 💻 CLI Tool

### Installation
```bash
cd /path/to/namaskah-app
chmod +x scripts/tier_cli.py
```

### Usage

#### List Available Tiers
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
  ...
```

#### List Users
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
...
```

#### Get User Information
```bash
python scripts/tier_cli.py user-info user123

Output:
📋 User Information:
──────────────────────────────────────────────────
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

#### Set User Tier
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

#### Bulk Set Tier
```bash
python scripts/tier_cli.py bulk-set-tier user1 user2 user3 pro --days 30

Output:
✅ Updated 3 users to pro tier
```

#### Extend Tier
```bash
python scripts/tier_cli.py extend-tier user123 --days 30

Output:
✅ Tier extended by 30 days
   Old expiry: 2025-01-15
   New expiry: 2025-02-14
```

#### Get Expiring Tiers
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
...
```

---

## 🔒 Security & Permissions

### Admin-Only Access
- All tier management endpoints require `is_admin = true`
- Web dashboard checks admin status before rendering
- API returns 403 Forbidden for non-admin users

### Audit Logging
All tier changes are logged:
```
Admin {admin_id} changed user {user_id} tier from {old_tier} to {new_tier}
```

### Validation
- Tier names validated against allowed values
- Duration limited to 1-365 days
- User existence verified before changes
- Bulk operations limited to 1000 users per request

---

## 📈 Common Workflows

### Upgrade User to Pro
```bash
# Via API
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"pro","duration_days":30}' \
  http://localhost:8000/api/admin/tiers/users/user123/tier

# Via CLI
python scripts/tier_cli.py set-tier user123 pro --days 30

# Via Dashboard
1. Go to /admin/tier-management
2. Find user in table
3. Click "Edit"
4. Select "Pro"
5. Click "Save Changes"
```

### Bulk Upgrade Users
```bash
# Via API
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids":["user1","user2","user3"],
    "tier":"starter",
    "duration_days":30
  }' \
  http://localhost:8000/api/admin/tiers/users/bulk/tier

# Via CLI
python scripts/tier_cli.py bulk-set-tier user1 user2 user3 starter --days 30

# Via Dashboard
1. Click "📋 Bulk Update"
2. Enter user IDs (comma-separated)
3. Select tier
4. Click "Update All"
```

### Monitor Expiring Tiers
```bash
# Via API
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/admin/tiers/expiring?days=7"

# Via CLI
python scripts/tier_cli.py expiring --days 7

# Via Dashboard
- Check "Expires" column in user table
- Sort by expiration date
```

---

## 🐛 Troubleshooting

### "Admin access required"
- Verify user has `is_admin = true` in database
- Check authentication token is valid
- Ensure token is passed in Authorization header

### "User not found"
- Verify user ID is correct
- Check user exists in database
- Use CLI to list users: `python scripts/tier_cli.py list-users`

### "Invalid tier"
- Use only: `payg`, `starter`, `pro`, `custom`
- Check spelling and case

### Bulk update fails
- Maximum 1000 users per request
- Verify all user IDs exist
- Check for duplicate IDs

---

## 📝 API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid tier, duration, etc.) |
| 403 | Admin access required |
| 404 | User not found |
| 500 | Server error |

---

## 🚀 Integration Examples

### Python
```python
import requests

headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

# Set user tier
response = requests.post(
    "http://localhost:8000/api/admin/tiers/users/user123/tier",
    headers=headers,
    json={"tier": "pro", "duration_days": 30}
)
print(response.json())
```

### JavaScript
```javascript
const adminToken = localStorage.getItem('access_token');

// Get tier statistics
fetch('/api/admin/tiers/stats', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
})
.then(r => r.json())
.then(data => console.log(data.stats));

// Set user tier
fetch('/api/admin/tiers/users/user123/tier', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ tier: 'pro', duration_days: 30 })
})
.then(r => r.json())
.then(data => console.log(data.message));
```

---

## 📞 Support

For issues or questions:
1. Check logs: `tail -f logs/server.log`
2. Review this documentation
3. Contact admin support

---

**Last Updated**: 2025-01-08  
**Version**: 1.0.0
