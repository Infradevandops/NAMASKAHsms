# Tier Management API & Dashboard

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
- View tier distribution statistics
- Search & filter users by email, ID, or tier
- Edit individual user tiers with custom duration
- Bulk update multiple users
- Monitor tier expiration dates
- Real-time statistics refresh

### Usage

1. **View Tier Distribution** - Dashboard loads with tier statistics
2. **Search Users** - Use search box to find by email or user ID
3. **Change User Tier** - Click "Edit", select new tier and duration, click "Save Changes"
4. **Bulk Update** - Click "📋 Bulk Update", enter comma-separated user IDs, select tier and duration
5. **Reset to Pay-As-You-Go** - Click "Reset" button on user row

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

#### Get Tier Statistics
```bash
GET /api/admin/tiers/stats

Response:
{
  "stats": [
    {"tier": "payg", "user_count": 150, "percentage": 45.5},
    ...
  ],
  "total_users": 330
}
```

#### List Users
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
    }
  ]
}
```

#### Get User Tier Info
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

#### Set User Tier
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

#### Bulk Update Tiers
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

#### Reset User Tier
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

#### Extend Tier Expiry
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

#### Get Expiring Tiers
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
    }
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
  -d '{"user_ids":["user1","user2","user3"],"tier":"starter","duration_days":30}' \
  http://localhost:8000/api/admin/tiers/users/bulk/tier

# Get expiring tiers
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/admin/tiers/expiring?days=14"
```

---

## 🔑 API Key Management

### List API Keys
```bash
GET /api/keys

Authentication: Required
Tier Requirement: Starter or higher

Response:
[
  {
    "id": "key-id-123",
    "name": "Production API Key",
    "key_preview": "...a1b2",
    "is_active": true,
    "request_count": 1523,
    "last_used": "2025-12-07T19:30:00Z",
    "created_at": "2025-11-01T10:00:00Z"
  }
]
```

### Generate API Key
```bash
POST /api/keys/generate

Request Body:
{
  "name": "My Development Key"
}

Response (201):
{
  "id": "key-id-456",
  "name": "My Development Key",
  "key": "nmsk_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456",
  "key_preview": "...3456",
  "created_at": "2025-12-07T20:57:00Z"
}
```

⚠️ **IMPORTANT:** The full API key is only returned once during creation. Store it securely!

### Revoke API Key
```bash
DELETE /api/keys/{key_id}

Response:
{
  "success": true,
  "message": "API key revoked successfully"
}
```

### Rotate API Key
```bash
POST /api/keys/{key_id}/rotate

Response:
{
  "id": "new-key-id",
  "name": "My Development Key",
  "key": "nmsk_newKeyGoesHere123",
  "key_preview": "...e123",
  "created_at": "2025-12-07T21:00:00Z"
}
```

---

## 🔐 Feature Access

### Get Available Area Codes
```bash
GET /api/verification/area-codes/{country}

Tier Requirement: Starter or higher

Example: GET /api/verification/area-codes/US

Response:
{
  "success": true,
  "country": "US",
  "area_codes": ["212", "310", "415", "646", "917"],
  "tier": "starter"
}
```

### Get Available Carriers
```bash
GET /api/verification/carriers/{country}

Tier Requirement: Pro or higher

Example: GET /api/verification/carriers/US

Response:
{
  "success": true,
  "country": "US",
  "carriers": ["Verizon", "AT&T", "T-Mobile", "Sprint"],
  "tier": "pro"
}
```

---

## 🔒 Security & Permissions

- All tier management endpoints require `is_admin = true`
- Web dashboard checks admin status before rendering
- API returns 403 Forbidden for non-admin users
- All tier changes are logged with admin ID and timestamp
- Tier names validated against allowed values
- Duration limited to 1-90 days
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
```

### Bulk Upgrade Users
```bash
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_ids":["user1","user2","user3"],"tier":"starter","duration_days":30}' \
  http://localhost:8000/api/admin/tiers/users/bulk/tier
```

### Monitor Expiring Tiers
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/admin/tiers/expiring?days=7"
```

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

fetch('/api/admin/tiers/stats', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
})
.then(r => r.json())
.then(data => console.log(data.stats));
```

---

**Last Updated**: 2025-01-08  
**Version**: 2.0.0
