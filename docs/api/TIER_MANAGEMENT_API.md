# Tier Management

Manage user subscription tiers through web dashboard or API.


## Tier Types

**Freemium** - Free forever
- $2.22 per SMS
- No API access
- No special features

**Pay-As-You-Go** - No monthly fee  
- $2.50 per SMS
- Area code selection costs extra
- No API access

**Pro** - $25/month
- $15 monthly SMS credit
- 10 API keys included
- All features included
- Priority support

**Custom** - $35/month
- $25 monthly SMS credit  
- Unlimited API keys
- All features included
- Dedicated support


## Web Dashboard

**Access:** Go to /admin/tier-management (admin only)

**What you can do:**
- See how many users are on each tier
- Search for users by email
- Change a user's tier
- Update multiple users at once
- See which tiers are expiring soon


## API Endpoints

**Base URL:** /api/admin/tiers

**Authentication:** Add admin token to headers

### Get Statistics
```
GET /stats
```
Shows user count for each tier.

### List Users  
```
GET /users?tier=pro&limit=50
```
Shows users on specific tier.

### Change User Tier
```
POST /users/{user_id}/tier
Body: {"tier": "pro", "duration_days": 30}
```
Upgrades or downgrades a user.

### Bulk Update
```
POST /users/bulk/tier  
Body: {"user_ids": ["user1", "user2"], "tier": "pro", "duration_days": 30}
```
Updates multiple users at once.

### Reset User
```
DELETE /users/{user_id}/tier
```
Resets user back to Pay-As-You-Go.


## API Key Management

**Who can use:** Pro and Custom tier users only

### List Keys
```
GET /api/keys
```
Shows user's API keys.

### Create Key
```
POST /api/keys/generate
Body: {"name": "My API Key"}
```
Creates new API key. Save the key - you only see it once!

### Delete Key
```
DELETE /api/keys/{key_id}
```
Removes an API key.


## Feature Access

**Area Codes** - Requires Pay-As-You-Go or higher
```
GET /api/verification/area-codes/US
```

**Carrier Selection** - Requires Pro or higher  
```
GET /api/verification/carriers/US
```


## Security

- Only admins can manage tiers
- All changes are logged
- Tier names are validated
- Duration limited to 90 days max
- Bulk operations limited to 1000 users


## Common Tasks

**Upgrade user to Pro for 30 days:**
Use web dashboard or POST to /users/{id}/tier with tier="pro" and duration_days=30

**Find expiring tiers:**
GET /expiring?days=7 shows tiers expiring in next 7 days

**Reset user to free tier:**
DELETE /users/{id}/tier


## Response Codes

- 200 = Success
- 400 = Bad request  
- 403 = Admin access required
- 404 = User not found
- 500 = Server error


## System Details

**Database:** User tier stored in users.subscription_tier field
**Caching:** Tier checks cached for 60 seconds  
**Performance:** Tier check takes less than 1ms
**Hierarchy:** custom > pro > payg > freemium