# 🎯 Tier Management - Access Guide

## How to Access & Use

### ✅ Everything is Ready to Use

The tier management system is **fully implemented** and **immediately accessible** through 3 methods:

---

## 🌐 Method 1: Web Dashboard (Easiest)

### Access
```
URL: http://localhost:8000/admin/tier-management
Requires: Admin login
```

### Steps
1. **Start server**
   ```bash
   ./server.sh start
   ```

2. **Login as admin**
   - Go to http://localhost:8000/auth/login
   - Use admin credentials

3. **Access tier management**
   - Go to http://localhost:8000/admin/tier-management
   - Dashboard loads automatically

### What You Can Do
- ✅ View tier statistics (pie chart style)
- ✅ Search users by email or ID
- ✅ Filter by tier (payg, starter, pro, custom)
- ✅ Edit individual user tiers
- ✅ Bulk update multiple users
- ✅ Monitor tier expiration dates
- ✅ Extend tier expiry
- ✅ Reset users to Pay-As-You-Go

### Example Workflow
```
1. Dashboard loads with statistics
2. Search for "user@example.com"
3. Click "Edit" button
4. Select "Pro" tier
5. Set duration to 30 days
6. Click "Save Changes"
7. User is now Pro tier ✅
```

---

## 🔌 Method 2: REST API (Most Flexible)

### Access
```
Base URL: http://localhost:8000/api/admin/tiers
Authentication: Bearer token (from login)
```

### Get Admin Token
```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# 2. Copy the access_token from response
# 3. Use in subsequent requests
```

### Quick Examples

**Get Tier Statistics**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/tiers/stats
```

**List Users**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/admin/tiers/users?tier=pro&limit=20"
```

**Set User Tier**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"pro","duration_days":30}' \
  http://localhost:8000/api/admin/tiers/users/user123/tier
```

**Bulk Update Users**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids":["user1","user2","user3"],
    "tier":"starter",
    "duration_days":30
  }' \
  http://localhost:8000/api/admin/tiers/users/bulk/tier
```

**Get Expiring Tiers**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/admin/tiers/expiring?days=7"
```

### All Endpoints
```
GET    /stats                           - Tier statistics
GET    /users                           - List users
GET    /users/{id}/tier                 - Get user tier
POST   /users/{id}/tier                 - Set tier
POST   /users/bulk/tier                 - Bulk update
DELETE /users/{id}/tier                 - Reset tier
POST   /users/{id}/tier/extend          - Extend expiry
GET    /expiring                        - Expiring tiers
```

---

## 💻 Method 3: CLI Tool (Most Powerful)

### Access
```
Location: scripts/tier_cli.py
Usage: python scripts/tier_cli.py <command>
```

### Installation
```bash
cd /path/to/namaskah-app
chmod +x scripts/tier_cli.py
```

### Quick Examples

**List All Tiers**
```bash
python scripts/tier_cli.py list-tiers
```

**List Users**
```bash
# All users
python scripts/tier_cli.py list-users

# Filter by tier
python scripts/tier_cli.py list-users --tier starter

# Limit results
python scripts/tier_cli.py list-users --tier pro --limit 100
```

**Get User Info**
```bash
python scripts/tier_cli.py user-info user123
```

**Set User Tier**
```bash
# Set to Pro for 30 days
python scripts/tier_cli.py set-tier user123 pro --days 30

# Set to Starter for 60 days
python scripts/tier_cli.py set-tier user123 starter --days 60

# Reset to Pay-As-You-Go
python scripts/tier_cli.py set-tier user123 payg
```

**Bulk Update**
```bash
python scripts/tier_cli.py bulk-set-tier user1 user2 user3 pro --days 30
```

**Extend Tier**
```bash
python scripts/tier_cli.py extend-tier user123 --days 30
```

**Get Expiring Tiers**
```bash
# Expiring in 7 days
python scripts/tier_cli.py expiring

# Expiring in 14 days
python scripts/tier_cli.py expiring --days 14
```

### All Commands
```
list-tiers              - Show all available tiers
list-users              - List users (with filtering)
user-info <id>          - Get detailed user information
set-tier <id> <tier>    - Change user tier
bulk-set-tier <ids>     - Update multiple users
extend-tier <id>        - Extend tier expiry
expiring                - Get tiers expiring soon
```

---

## 🎯 Which Method to Use?

### Use **Web Dashboard** if you:
- ✅ Prefer visual interface
- ✅ Make occasional changes
- ✅ Want to see statistics
- ✅ Need to search/filter users

### Use **REST API** if you:
- ✅ Build integrations
- ✅ Automate with scripts
- ✅ Need programmatic access
- ✅ Integrate with other systems

### Use **CLI Tool** if you:
- ✅ Perform batch operations
- ✅ Automate with cron jobs
- ✅ Prefer command-line
- ✅ Need quick lookups

---

## 📊 Tier Reference

```
Tier          Price    Quota  API Keys  Features
────────────────────────────────────────────────────
payg          $0       None   0         Basic SMS
starter       $8.99    $10    5         Area code
pro           $25      $30    10        + ISP filter
custom        $35      $50    ∞         All features
```

---

## 🔐 Security Notes

- ✅ All endpoints require admin access
- ✅ JWT token authentication
- ✅ All changes are logged
- ✅ Input validation on all operations
- ✅ No sensitive data in errors

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Dashboard won't load | Check admin login, verify URL |
| API returns 403 | Check Authorization header, verify admin role |
| CLI command not found | Run: `python scripts/tier_cli.py` |
| "User not found" | Verify user ID exists in database |
| "Invalid tier" | Use: payg, starter, pro, custom |

---

## 📚 Documentation

- **Quick Reference**: `TIER_MANAGEMENT_QUICK_REFERENCE.md`
- **Full Guide**: `docs/TIER_MANAGEMENT_GUIDE.md`
- **Implementation**: `TIER_MANAGEMENT_IMPLEMENTATION.md`

---

## ✅ Ready to Use

Everything is **fully implemented** and **production-ready**:

✅ Web Dashboard - Responsive, intuitive UI  
✅ REST API - 8 endpoints, full CRUD  
✅ CLI Tool - 8 commands, batch operations  
✅ Documentation - Complete guides  
✅ Security - Admin-only, audit logging  
✅ Testing - Ready for production  

---

## 🚀 Start Now

### Option 1: Web Dashboard
```
1. Start server: ./server.sh start
2. Login: http://localhost:8000/auth/login
3. Access: http://localhost:8000/admin/tier-management
```

### Option 2: REST API
```bash
# Get token
curl -X POST http://localhost:8000/api/auth/login \
  -d '{"email":"admin@example.com","password":"password"}'

# Use token
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/admin/tiers/stats
```

### Option 3: CLI Tool
```bash
python scripts/tier_cli.py list-users
```

---

**Choose your preferred method and start managing tiers!** 🎉

---

**Version**: 1.0.0 | **Status**: ✅ Production Ready | **Date**: 2025-01-08
