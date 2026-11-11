# OTP Login — Task File

**Status**: ✅ Implemented — pending E2E test on live server
**Added**: November 2026
**Purpose**: Prove email delivery works end-to-end; provide passwordless login option

---

## What Was Built

### Backend — `app/api/auth_routes.py`
- `POST /api/auth/otp/request` — generates 6-digit OTP, stores in Redis with 10-min TTL, emails it
  - Rate-limited: 3 requests per email per 15-minute window (Redis counter)
  - Returns 200 even for unknown emails (prevents email enumeration)
  - Only sends to active users
- `POST /api/auth/otp/verify` — validates OTP, deletes it from Redis, returns JWT (same shape as `/login`)
  - Side effect: marks `email_verified = True` on success (proves inbox access)
  - Tracks login event via `EventTrackingService`

### Email — `app/services/email_service.py`
- `send_otp_email(user_email, otp)` — branded Vrenum email with large monospace OTP code, 10-min expiry notice

### Frontend — `templates/login.html`
- "Login with email code" link under the Sign In button
- OTP request view: email input → Send Code
- OTP verify view: 6-digit input → Sign In
- Back/resend navigation between views
- Enter key support on both inputs
- Pre-fills saved email from localStorage

---

## Redis Key Schema

| Key | TTL | Value |
|-----|-----|-------|
| `otp:{email}` | 600s (10 min) | 6-digit string |
| `otp_rate:{email}` | 900s (15 min) | request count (int) |

---

## Open Items

- [ ] **E2E test**: trigger OTP on live server, confirm email arrives via Resend, confirm JWT returned
- [ ] **AUTH-002**: register page should show "check your inbox" notice after signup (separate task)
- [ ] Consider: add OTP option to register flow as email verification step (deferred)

---

## Test Trigger (manual)

```bash
# 1. Request OTP
curl -X POST https://vrenum.app/api/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com"}'

# 2. Verify OTP (use code from email)
curl -X POST https://vrenum.app/api/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "otp": "123456"}'
```

Expected: step 1 returns `{"message": "If that email exists, a code has been sent."}`, email arrives within ~5s via Resend. Step 2 returns `access_token`.

---

## Files Changed

- `app/api/auth_routes.py` — 2 new endpoints
- `app/services/email_service.py` — `send_otp_email()`
- `templates/login.html` — OTP UI + JS
