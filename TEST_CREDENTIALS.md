# Test User Credentials

**Last Updated**: February 8, 2026

---

## 🔐 Available Test Accounts

### 1. Admin Account 👑
```
Email: admin@namaskah.app
Password: Admin123456!
Credits: 1000.0
Role: Administrator
```

### 2. Demo Account
```
Email: demo@namaskah.app
Password: Demo123456
Credits: 0.0
Role: User
```

### 3. Test Account
```
Email: test@example.com
Password: Test123456
Credits: 0.0
Role: User
```

### 4. Test User Account
```
Email: testuser@namaskah.app
Password: TestPass123!
Credits: 0.0
Role: User
```

---

## ✅ All Accounts Verified

All accounts have been tested and confirmed working:
- ✅ Login successful
- ✅ JWT token generation working
- ✅ Authenticated requests working
- ✅ Credits displayed correctly

---

## 🧪 Testing Commands

### Login Test
```bash
curl -X POST http://127.0.0.1:9527/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@namaskah.app","password":"Admin123456!"}'
```

### Get User Info
```bash
# First login to get token, then:
curl http://127.0.0.1:9527/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🌐 Access URLs

- **Login Page**: http://127.0.0.1:9527/login
- **Dashboard**: http://127.0.0.1:9527/dashboard
- **API Docs**: http://127.0.0.1:9527/docs

---

## 📝 Notes

- Admin account has 1000 credits pre-loaded
- All passwords follow security requirements (8+ chars, mixed case, numbers)
- Accounts are active and email verified
- JWT tokens expire after 7 days
