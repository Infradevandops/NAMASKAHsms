# Credential Rotation Checklist

**CRITICAL**: Complete all items in this checklist immediately.

---

## 1. Telegram Bot Token

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Open Telegram and search for `@BotFather`
2. Send `/mybots`
3. Select the bot (vrenum_sms_bot)
4. Select "API Token"
5. Click "Revoke current token"
6. Confirm revocation
7. Copy new token
8. Update in CI/CD secrets: `TELEGRAM_BOT_TOKEN`

**Verification**:
```bash
curl -s https://api.telegram.org/bot<NEW_TOKEN>/getMe | jq .
```

**Status**: [ ] Rotated

---

## 2. TextVerified API Key

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to TextVerified dashboard
2. Go to Settings → API Keys
3. Click "Regenerate" or "Delete" old key
4. Generate new API key
5. Copy new key
6. Update in CI/CD secrets: `TEXTVERIFIED_API_KEY`

**Verification**:
```bash
curl -X GET "https://api.textverified.com/api/user/balance" \
  -H "Authorization: Bearer <NEW_KEY>"
```

**Status**: [ ] Rotated

---

## 3. Paystack Keys

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to Paystack Dashboard
2. Go to Settings → API Keys & Webhooks
3. Click "Revoke" on current keys
4. Generate new keys
5. Copy both public and secret keys
6. Update in CI/CD secrets:
   - `PAYSTACK_PUBLIC_KEY`
   - `PAYSTACK_SECRET_KEY`

**Verification**:
```bash
curl https://api.paystack.co/customer \
  -H "Authorization: Bearer <NEW_SECRET_KEY>"
```

**Status**: [ ] Rotated

---

## 4. Resend API Key

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to Resend Dashboard
2. Go to API Keys
3. Click "Delete" on exposed key
4. Create new API key
5. Copy new key
6. Update in CI/CD secrets: `RESEND_API_KEY`

**Verification**:
```bash
curl https://api.resend.com/emails \
  -H "Authorization: Bearer <NEW_KEY>"
```

**Status**: [ ] Rotated

---

## 5. OneSignal API Key

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to OneSignal Dashboard
2. Go to Settings → Keys & IDs
3. Click "Regenerate" on REST API Key
4. Confirm regeneration
5. Copy new key
6. Update in CI/CD secrets: `ONESIGNAL_API_KEY`

**Verification**:
```bash
curl https://onesignal.com/api/v1/apps \
  -H "Authorization: Basic <NEW_KEY>"
```

**Status**: [ ] Rotated

---

## 6. Google OAuth Credentials

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project
3. Go to Credentials
4. Find OAuth 2.0 Client ID
5. Click "Delete" on exposed credentials
6. Create new OAuth 2.0 Client ID
7. Copy new Client ID and Secret
8. Update in CI/CD secrets:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

**Verification**:
```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=<NEW_ID>&client_secret=<NEW_SECRET>&grant_type=client_credentials"
```

**Status**: [ ] Rotated

---

## 7. Sentry DSN

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to Sentry Dashboard
2. Go to Settings → Projects → vrenum
3. Go to Client Keys (DSN)
4. Click "Disable" on exposed key
5. Create new key
6. Copy new DSN
7. Update in CI/CD secrets: `SENTRY_DSN`

**Verification**:
```bash
# Test by triggering an error in app
# Check Sentry dashboard for new events
```

**Status**: [ ] Rotated

---

## 8. Turnstile Keys

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to Cloudflare Dashboard
2. Go to Turnstile
3. Select site
4. Click "Delete" on exposed keys
5. Create new site
6. Copy new Site Key and Secret Key
7. Update in CI/CD secrets:
   - `TURNSTILE_SITE_KEY`
   - `TURNSTILE_SECRET_KEY`

**Verification**:
```bash
curl -X POST https://challenges.cloudflare.com/turnstile/v0/siteverify \
  -d "secret=<NEW_SECRET>&response=<TOKEN>"
```

**Status**: [ ] Rotated

---

## 9. PostgreSQL Database Password

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to Neon Console
2. Go to Project Settings
3. Find database user
4. Click "Reset password"
5. Generate new password
6. Copy new password
7. Update DATABASE_URL in CI/CD secrets with new password

**Verification**:
```bash
psql "postgresql://neondb_owner:<NEW_PASSWORD>@ep-shy-king-ansjlp5g-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require" -c "SELECT 1;"
```

**Status**: [ ] Rotated

---

## 10. Redis Auth Token

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to Upstash Console
2. Go to Redis database
3. Click "Reset password" or "Regenerate token"
4. Confirm action
5. Copy new token
6. Update in CI/CD secrets:
   - `REDIS_URL`
   - `UPSTASH_REDIS_REST_TOKEN`

**Verification**:
```bash
redis-cli -u "rediss://default:<NEW_TOKEN>@profound-yak-85016.upstash.io:6379" PING
```

**Status**: [ ] Rotated

---

## 11. Admin Account Credentials

**Status**: EXPOSED - Requires immediate rotation

**Rotation Steps**:
1. Log in to application with current credentials
2. Go to Settings → Account
3. Change password to strong, unique password
4. Update in CI/CD secrets: `ADMIN_PASSWORD`
5. Enable 2FA if available

**New Password Requirements**:
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words
- No personal information

**Verification**:
```bash
# Test login with new credentials
curl -X POST https://vrenum.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vrenum.app","password":"<NEW_PASSWORD>"}'
```

**Status**: [ ] Rotated

---

## 12. Update CI/CD Secrets

**GitHub Actions** (if using):
1. Go to repository Settings
2. Go to Secrets and variables → Actions
3. Update each secret:
   - `TELEGRAM_BOT_TOKEN`
   - `TEXTVERIFIED_API_KEY`
   - `PAYSTACK_PUBLIC_KEY`
   - `PAYSTACK_SECRET_KEY`
   - `RESEND_API_KEY`
   - `ONESIGNAL_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `SENTRY_DSN`
   - `TURNSTILE_SITE_KEY`
   - `TURNSTILE_SECRET_KEY`
   - `DATABASE_URL`
   - `REDIS_URL`
   - `ADMIN_PASSWORD`

**Status**: [ ] Updated

---

## 13. Verify All Services Working

After rotation, verify each service:

```bash
# Telegram
curl -s https://api.telegram.org/bot<TOKEN>/getMe | jq .ok

# TextVerified
curl -s -H "Authorization: Bearer <KEY>" https://api.textverified.com/api/user/balance | jq .

# Paystack
curl -s -H "Authorization: Bearer <KEY>" https://api.paystack.co/customer | jq .status

# Resend
curl -s -H "Authorization: Bearer <KEY>" https://api.resend.com/emails | jq .

# OneSignal
curl -s -H "Authorization: Basic <KEY>" https://onesignal.com/api/v1/apps | jq .

# Database
psql "<NEW_URL>" -c "SELECT 1;"

# Redis
redis-cli -u "<NEW_URL>" PING
```

**Status**: [ ] All verified

---

## 14. Audit Logs

Check for unauthorized access:

1. **Telegram**: Check bot message history
2. **TextVerified**: Check API usage logs
3. **Paystack**: Check transaction history
4. **Resend**: Check email sending logs
5. **OneSignal**: Check push notification logs
6. **Google**: Check OAuth consent screen logs
7. **Sentry**: Check error events
8. **Database**: Check query logs
9. **Redis**: Check command logs

**Status**: [ ] Audited

---

## 15. Document Incident

Create incident report:
- [ ] Date/time of discovery
- [ ] Credentials exposed
- [ ] Services affected
- [ ] Actions taken
- [ ] Timeline
- [ ] Root cause
- [ ] Prevention measures

---

## Final Checklist

- [ ] All 11 credentials rotated
- [ ] CI/CD secrets updated
- [ ] All services verified working
- [ ] Audit logs reviewed
- [ ] Team notified
- [ ] Incident documented
- [ ] `.env.production` removed from git history
- [ ] Pre-commit hooks installed
- [ ] GitHub secret scanning enabled

---

## Sign-off

**Completed by**: ________________  
**Date**: ________________  
**Verified by**: ________________  
**Date**: ________________

---

**IMPORTANT**: Keep this checklist for audit purposes. Do not commit to repository.
