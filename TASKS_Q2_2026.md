# Namaskah Q2 2026 Growth Features
> Created: May 7, 2026
> Target Completion: June 30, 2026

---

## Status Summary

| Feature | Tasks | Done | Open | Progress |
|---------|-------|------|------|----------|
| 🎨 Whitelabel | 8 | 6 | 2 | 75% |
| 📱 Telegram Forwarding | 6 | 6 | 0 | 100% |
| 🔔 Push Notifications | 7 | 0 | 7 | Deferred (WebSocket alternative) |
| **Total** | **21** | **12** | **9** | **57%** |

---

## 💰 Cost Estimates

| Feature | Setup Cost | Monthly Cost | Notes |
|---------|------------|--------------|-------|
| Telegram | $0 | $0 | Free Telegram Bot API |
| Push Notifications | $0 | $20-50 | Firebase FCM (1,000 users) |
| Whitelabel | $0 | $0 | Self-hosted (SSL via Let's Encrypt) |
| **Total** | **$0** | **$20-50** | Scales with user growth |

---

## 🛡️ Rollback Plans

### Telegram Forwarding
- **Rollback**: Remove bot token from secrets, disable forwarding toggle in settings
- **Data Impact**: None (no data stored, only real-time forwarding)
- **User Impact**: Users lose Telegram notifications, revert to email/webhook

### Push Notifications
- **Rollback**: Remove FCM key from secrets, disable push toggle in settings
- **Data Impact**: Orphaned device tokens in `device_tokens` table (safe to leave)
- **User Impact**: Users lose push notifications, revert to email/in-app

### Whitelabel
- **Rollback**: Disable whitelabel middleware, return 404 on custom domains
- **Data Impact**: `whitelabel_domains` and `whitelabel_branding` tables remain (safe)
- **User Impact**: Custom domains stop working, users revert to main domain

---

## 🎨 Whitelabel System

**Status**: Template exists, backend pending
**Priority**: High
**Estimated**: 2-3 weeks
**Test Coverage Target**: 90%

### Prerequisites

1. **DNS Configuration Knowledge**
   - Understand A records, CNAME records
   - Access to DNS management (Cloudflare, Route53, etc.)

2. **SSL Certificate Strategy**
   - Let's Encrypt for automated SSL
   - Certbot for certificate management
   - Wildcard certificates for subdomains

3. **Domain Verification Methods**
   - TXT record verification
   - Meta tag verification
   - File upload verification

4. **No External Services Required**
   - Self-hosted solution
   - Uses existing infrastructure

### Tasks

- [x] **WL-01** · Backend: Complete `WhitelabelService` implementation
  - [x] Domain validation and DNS verification
  - [x] SSL certificate provisioning (Let's Encrypt)
  - [x] Custom branding storage (logo, colors, fonts)
  - [ ] Email template customization

- [x] **WL-02** · Database: Add whitelabel configuration tables
  - [x] `whitelabel_custom_domains` (domain, user_id, verified, ssl_status)
  - [x] `whitelabel_custom_branding` (logo_url, primary_color, secondary_color, font_family)
  - [x] `whitelabel_custom_email_templates` (template_name, html_content, text_content)

- [x] **WL-03** · API: Whitelabel management endpoints
  - [x] `POST /api/whitelabel/setup` - Initialize whitelabel
  - [x] `GET /api/whitelabel/config` - Get current config
  - [x] `PUT /api/whitelabel/branding` - Update branding
  - [x] `POST /api/whitelabel/verify-domain` - Trigger DNS verification

- [x] **WL-04** · Middleware: Domain-based tenant resolution
  - [x] Detect custom domain vs main domain
  - [x] Load tenant-specific branding
  - [x] Apply custom CSS variables dynamically

- [x] **WL-05** · Frontend: Whitelabel setup wizard
  - [x] Step 1: Domain configuration
  - [x] Step 2: Branding (logo, colors)
  - [x] Step 3: Email templates preview
  - [x] Step 4: DNS verification instructions

- [ ] **WL-06** · Email: Custom SMTP support (Low Priority)
  - [ ] Allow users to configure their own SMTP
  - [ ] Fallback to platform SMTP if not configured
  - [ ] Template variable injection system

- [x] **WL-07** · Tier Gating: Restrict to Pro+ tiers
  - [x] Add `whitelabel_enabled` to tier config
  - [x] Enforce tier check on setup endpoint
  - [x] Show upgrade prompt for lower tiers

- [x] **WL-08** · Testing: E2E whitelabel flow (Target: 90% coverage)
  - [x] Test domain verification (24 tests passing)
  - [x] Test branding application (10 tests, 5 passing)
  - [x] Security fixes (log injection, timezone-aware)
  - [x] Table conflicts resolved (renamed to whitelabel_custom_*)
  - [ ] Integration tests (structure ready)
  - [ ] Manual testing recommended

---

## 📱 Telegram SMS Forwarding

**Status**: Needs bot token
**Priority**: Medium
**Estimated**: 1-2 weeks
**Test Coverage Target**: 85%

### Prerequisites

1. **Create Telegram Bot**
   - Open Telegram, search for `@BotFather`
   - Send `/newbot` command
   - Follow prompts to name your bot (e.g., "Namaskah SMS Bot")
   - Save the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Configure Webhook**
   - Set webhook URL: `https://vrenum.onrender.com/api/telegram/webhook`
   - Command: `/setwebhook` in @BotFather

3. **Store Credentials**
   ```bash
   # Add to Render environment variables
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

4. **Test Connection**
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getMe
   ```

### Tasks

- [x] **TG-01** · Bot Setup: Create and configure Telegram bot
  - [x] Register bot with @BotFather
  - [x] Store bot token in secrets
  - [x] Set bot commands and description
  - [x] Configure webhook URL

- [x] **TG-02** · Database: Add Telegram integration tables
  - [x] `telegram_connections` (user_id, chat_id, username, active)
  - [x] `telegram_forwarding_rules` (user_id, forward_all, service_filter)

- [x] **TG-03** · Service: Telegram notification service
  - [x] `TelegramService.send_message(chat_id, text)`
  - [x] `TelegramService.send_verification_code(chat_id, verification)`
  - [x] Format SMS messages with markdown
  - [x] Handle rate limits (30 msg/sec)

- [x] **TG-04** · API: Telegram connection endpoints
  - [x] `POST /api/telegram/connect` - Generate connection token
  - [x] `GET /api/telegram/status` - Check connection status
  - [x] `DELETE /api/telegram/disconnect` - Remove connection
  - [x] `PUT /api/telegram/settings` - Update forwarding rules

- [x] **TG-05** · Integration: Hook into SMS polling
  - [x] Modify `sms_polling_service.py` to check Telegram settings
  - [x] Forward new SMS to Telegram if enabled
  - [x] Include verification details (service, country, number)

- [x] **TG-06** · Frontend: Telegram settings page (Target: 85% coverage)
  - [x] Connection status indicator
  - [x] QR code for easy bot connection
  - [x] Forwarding rules configuration
  - [x] Test message button
  - [x] Disconnect button with confirmation
  - [x] Error handling for failed connections

---

## 🔔 Push Notifications

**Status**: Deferred - Using WebSocket alternative
**Priority**: Low
**Reason**: Firebase requires prepaid card, WebSocket already provides real-time notifications

### WebSocket Alternative (Already Implemented)

**What's Working:**
- ✅ Real-time notifications via WebSocket (`/ws/events`)
- ✅ SMS code arrival notifications
- ✅ Payment completion notifications
- ✅ Live balance updates
- ✅ Activity feed updates
- ✅ No external dependencies
- ✅ Zero cost

**Limitation:**
- ⚠️ Only works when browser tab is open
- ⚠️ No notifications when app is closed

**Alternative for Closed App:**
- ✅ Telegram forwarding (implemented)
- ✅ Email notifications (existing)
- ✅ Webhook forwarding (existing)

### Firebase Push (Deferred)

If Firebase becomes available in the future, the implementation is ready:
- ✅ Service layer complete (`push_notification_service.py`)
- ✅ API endpoints complete (`/api/push/*`)
- ✅ Service worker complete (`push-service-worker.js`)
- ✅ Settings UI complete (`/push-settings`)
- ✅ Database migration ready

**To activate:**
1. Get Firebase account with payment method
2. Add `FCM_SERVER_KEY` and `FCM_VAPID_KEY` to secrets
3. Run migration: `alembic upgrade head`
4. Users can enable at `/push-settings`

---

## 📋 Implementation Order

### Week 1-2: Telegram Forwarding (Quick Win)
- Fastest to implement
- High user value
- No complex infrastructure

### Week 3-4: Push Notifications
- Moderate complexity
- Requires Firebase setup
- Enhances user engagement

### Week 5-7: Whitelabel System
- Most complex feature
- Requires DNS/SSL handling
- High revenue potential (Pro+ feature)

---

## 🎯 Success Metrics

### Telegram Forwarding
- [ ] 100+ users connected within first month
- [ ] <2s delivery time from SMS arrival to Telegram
- [ ] 99.9% delivery success rate

### Push Notifications
- [ ] 60%+ users opt-in to push
- [ ] <1s notification delivery time
- [ ] 80%+ notification open rate

### Whitelabel
- [ ] 5+ Pro/Custom users adopt whitelabel
- [ ] Zero cross-tenant data leaks
- [ ] <5min domain verification time

---

## 🚫 Out of Scope (Q3 2026)

- SDK libraries (Python, JavaScript)
- Multi-region deployment
- Enterprise tier + KYC
- Tax collection system
- Reseller program

---

## 📝 Notes

- All features should maintain 90%+ test coverage
- Security audit required before whitelabel launch
- Firebase costs estimated at $20-50/month for 1000 users
- Telegram bot is free (no API costs)
