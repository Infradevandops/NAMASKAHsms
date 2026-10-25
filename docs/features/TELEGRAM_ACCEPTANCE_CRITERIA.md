# Telegram SMS Forwarding — Acceptance Criteria

**Bot**: [@vrenum_sms_bot](https://t.me/vrenum_sms_bot)
**Status**: ⏳ Code complete — pending end-to-end verification
**Last Updated**: October 25, 2026

---

## Setup Checklist (Already Done)

- [x] Bot created via @BotFather — `@vrenum_sms_bot`
- [x] `TELEGRAM_BOT_TOKEN` set in `.env.production`
- [x] Webhook registered: `https://vrenum.app/api/telegram/webhook`
- [x] Router mounted in `main.py`
- [x] Redis token linking implemented (`tg:connect:{token}`, 10-min TTL)
- [x] Token is one-time use (deleted from Redis after `/start`)
- [x] Settings page live at `https://vrenum.app/telegram`
- [x] Dark theme fixed on settings page

---

## Acceptance Criteria — Must Pass Before Marking Complete

### AC-1: Settings Page Loads
- [ ] Navigate to `https://vrenum.app/telegram` while logged in
- [ ] Page shows "Telegram Integration" card with dark theme
- [ ] Status shows "Not Connected" badge
- [ ] "Generate Connection Token" button is visible

### AC-2: Token Generation
- [ ] Click "Generate Connection Token"
- [ ] Token appears in the display box as `/start <token>`
- [ ] Bot username shown as `@vrenum_sms_bot`
- [ ] Instructions are clear and readable

### AC-3: Bot Connection via /start
- [ ] Open Telegram, search `@vrenum_sms_bot`
- [ ] Send the exact `/start <token>` string shown on the page
- [ ] Bot replies with the success message:
  ```
  ✅ Connection Successful!
  Your vrenum.app account is now connected to Telegram.
  You'll receive SMS verification codes here instantly.
  Use /status to check your connection anytime.
  ```
- [ ] Refresh `vrenum.app/telegram` — status changes to "Connected"
- [ ] Connected username/name shown correctly

### AC-4: Token Expiry
- [ ] Generate a token but wait 11+ minutes without using it
- [ ] Send `/start <expired-token>` to bot
- [ ] Bot replies: `❌ Invalid or expired token. Please generate a new one from vrenum.app/telegram-settings.`

### AC-5: /status Command
- [ ] Send `/status` to `@vrenum_sms_bot`
- [ ] Bot replies with connected account info and last message time

### AC-6: /stop Command
- [ ] Send `/stop` to `@vrenum_sms_bot`
- [ ] Bot replies: `✅ Disconnected from vrenum.app. Use /start to reconnect.`
- [ ] Refresh `vrenum.app/telegram` — status changes back to "Not Connected"

### AC-7: Test Message
- [ ] Reconnect the bot (AC-3)
- [ ] On `vrenum.app/telegram`, click "Send Test Message"
- [ ] Telegram receives the test message within 5 seconds

### AC-8: SMS Code Forwarding (Core Feature)
- [ ] Ensure bot is connected (AC-3)
- [ ] Create a verification at `vrenum.app/verify`
- [ ] When SMS code is received by the platform, Telegram message arrives:
  ```
  🔔 SMS Code Received
  Service: <service name>
  Country: <country> <flag>
  Number: <phone number>
  Code: <sms code>
  Received: just now
  Verification ID: #<id>
  ```
- [ ] Code arrives within 5 seconds of platform receiving it

### AC-9: Forwarding Settings — Forward All (default)
- [ ] On `vrenum.app/telegram`, "Forward all SMS codes" checkbox is checked by default
- [ ] All verifications forward to Telegram

### AC-10: Forwarding Settings — Service Filter
- [ ] Uncheck "Forward all SMS codes"
- [ ] Add "WhatsApp" to service filter
- [ ] Save settings
- [ ] Create a WhatsApp verification — code forwards ✅
- [ ] Create a Google verification — code does NOT forward ✅

### AC-11: Disconnect from Web UI
- [ ] Click "Disconnect" on `vrenum.app/telegram`
- [ ] Confirm dialog appears
- [ ] After confirm, status shows "Not Connected"
- [ ] SMS codes no longer forward to Telegram

### AC-12: Reconnect After Disconnect
- [ ] After AC-11, generate a new token
- [ ] Send `/start <new-token>` to bot
- [ ] Connection re-established successfully

---

## Known Limitations (Acceptable)

- Token expires in 10 minutes — by design (security)
- One Telegram account per Vrenum account — by design
- Bot must be started by user (Telegram policy — bots can't initiate)
- Forwarding only works when Redis is available (graceful failure if Redis down)

---

## How to Re-Register Webhook (if needed)

```bash
curl "https://api.telegram.org/bot8668150393:AAHzemYB0HhHw96KGdO0S6IFiUs7uq_CqUo/setWebhook?url=https://vrenum.app/api/telegram/webhook"
```

Expected response: `{"ok":true,"result":true,"description":"Webhook was set"}`

## How to Check Webhook Status

```bash
curl "https://api.telegram.org/bot8668150393:AAHzemYB0HhHw96KGdO0S6IFiUs7uq_CqUo/getWebhookInfo"
```

---

## Files Involved

| File | Purpose |
|---|---|
| `app/api/core/telegram.py` | API endpoints + webhook handler |
| `app/services/telegram_service.py` | Bot API calls (send_message, send_verification_code) |
| `app/models/telegram.py` | TelegramConnection + TelegramForwardingRule models |
| `app/services/sms_polling_service.py` | Calls `send_verification_code()` on SMS receipt |
| `templates/telegram_settings.html` | Settings UI at /telegram |
| `alembic/versions/add_telegram_tables.py` | DB migration for telegram tables |

---

## Sign-Off

- [ ] All 12 acceptance criteria passing
- [ ] No errors in Sentry during test
- [ ] Feature marked complete in CHANGELOG.md and PLATFORM_STATUS.md
