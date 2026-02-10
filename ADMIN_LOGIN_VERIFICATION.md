# Admin Login Verification Guide

**Quick verification of admin credentials**

---

## ✅ Verified Credentials

```
Email: admin@namaskah.app
Password: Namaskah@Admin2024
```

**Status**: ✅ All checks passed (4/4)

---

## 🧪 Verification Tests

### 1. Database Check
```bash
python3 scripts/verify_admin_login.py
```

**Expected Output**:
```
✅ Database connected
✅ User exists
✅ User is active
✅ User is admin
✅ Password hash exists
✅ Password matches!
📊 RESULT: 4/4 checks passed
```

### 2. API Test (requires server running)
```bash
# Start server
./start_local.sh

# Test API
python3 scripts/test_admin_api.py
```

**Expected Output**:
```
✅ Login successful!
✅ User info retrieved!
✅ Admin access confirmed!
```

### 3. Browser Test
1. Open: http://localhost:9876/login
2. Enter credentials:
   - Email: `admin@namaskah.app`
   - Password: `Namaskah@Admin2024`
3. Click "Login"
4. Should redirect to `/dashboard`

---

## 🔧 Troubleshooting

### Issue: User not found
```bash
python3 scripts/create_admin_user.py
```

### Issue: Password doesn't match
```bash
# Reset password
psql $DATABASE_URL -c "UPDATE users SET password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJfLKZvSu' WHERE email='admin@namaskah.app';"
```

### Issue: User not admin
```bash
psql $DATABASE_URL -c "UPDATE users SET is_admin=true WHERE email='admin@namaskah.app';"
```

### Issue: User not active
```bash
psql $DATABASE_URL -c "UPDATE users SET is_active=true WHERE email='admin@namaskah.app';"
```

### Fix all at once
```bash
psql $DATABASE_URL -c "UPDATE users SET is_admin=true, is_active=true, email_verified=true WHERE email='admin@namaskah.app';"
```

---

## 📊 Verification Results

**Date**: January 2026  
**Database**: PostgreSQL (local)  
**User ID**: ecd733ac-11f7-4964-94ff-deb09d4be042

| Check | Status |
|-------|--------|
| User exists | ✅ Pass |
| User active | ✅ Pass |
| User is admin | ✅ Pass |
| Password hash | ✅ Pass |
| Password match | ✅ Pass |

**Overall**: ✅ **SUCCESS** - Admin login working correctly

---

## 🎯 Quick Test Commands

```bash
# 1. Verify database
python3 scripts/verify_admin_login.py

# 2. Test API (server must be running)
python3 scripts/test_admin_api.py

# 3. Manual API test
curl -X POST http://localhost:9876/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@namaskah.app","password":"Namaskah@Admin2024"}'
```

---

## 🔐 Security Notes

- Password uses bcrypt hashing
- JWT tokens expire after 30 days
- Tokens stored in httponly cookies
- Admin access checked via `is_admin` flag
- All admin endpoints require authentication

---

**Last Verified**: January 2026  
**Status**: ✅ Working
