# Telegram SMS Forwarding Implementation Guide

**Task**: TG-01 through TG-06
**Status**: In Progress
**Started**: May 7, 2026
**Target**: 1-2 weeks

---

## Implementation Checklist

### Phase 1: Bot Setup & Database (TG-01, TG-02)
- [x] Create Telegram bot via @BotFather
- [x] Store bot token in Render secrets
- [x] Create database migration for Telegram tables
- [x] Test bot connectivity

### Phase 2: Service Layer (TG-03)
- [x] Implement TelegramService
- [x] Add message formatting
- [x] Handle rate limits
- [x] Add error handling

### Phase 3: API Layer (TG-04)
- [x] Create connection endpoints
- [x] Add webhook handler
- [x] Implement settings endpoints
- [x] Add security validation

### Phase 4: Integration (TG-05)
- [x] Hook into SMS polling service
- [x] Add forwarding logic
- [x] Test end-to-end flow

### Phase 5: Frontend (TG-06)
- [x] Create settings page
- [x] Add connection flow
- [x] Implement test message
- [x] Add error states

---

## Current Step: TG-01 - Bot Setup

### Manual Steps Required

1. **Create Bot**
   - Open Telegram
   - Search for `@BotFather`
   - Send `/newbot`
   - Name: `Namaskah SMS Bot`
   - Username: `namaskah_sms_bot` (or similar)
   - Save token

2. **Configure Bot**
   ```
   /setdescription - Receive SMS verification codes instantly
   /setabouttext - Forward SMS codes from Namaskah to your Telegram
   /setuserpic - Upload logo
   ```

3. **Set Commands**
   ```
   /start - Connect your Namaskah account
   /status - Check connection status
   /stop - Disconnect from Namaskah
   /help - Get help
   ```

4. **Store Token**
   - Go to Render Dashboard
   - Environment Variables
   - Add: `TELEGRAM_BOT_TOKEN=<your_token>`

### Automated Steps (After Token Available)

Will create migration and service files automatically.

---

## Architecture

```
User SMS Arrives
    ↓
SMS Polling Service detects new message
    ↓
Check if user has Telegram enabled
    ↓
TelegramService.send_verification_code()
    ↓
Format message with markdown
    ↓
Send to user's chat_id via Bot API
    ↓
User receives notification in Telegram
```

---

## Database Schema

```sql
-- telegram_connections
CREATE TABLE telegram_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    chat_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    connected_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP,
    UNIQUE(user_id)
);

-- telegram_forwarding_rules
CREATE TABLE telegram_forwarding_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) UNIQUE,
    forward_all BOOLEAN DEFAULT TRUE,
    service_filter TEXT[],
    country_filter TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

```python
POST   /api/telegram/connect
GET    /api/telegram/status
DELETE /api/telegram/disconnect
PUT    /api/telegram/settings
POST   /api/telegram/webhook  # For bot updates
POST   /api/telegram/test     # Send test message
```

---

## Message Format

```markdown
🔔 **SMS Code Received**

Service: WhatsApp
Country: United States 🇺🇸
Number: +1 (555) 123-4567

Code: **123456**

Received: 2 seconds ago
Verification ID: #12345
```

---

## Security Considerations

1. **Webhook Validation**: Verify requests from Telegram using secret token
2. **User Verification**: Ensure chat_id matches user_id before forwarding
3. **Rate Limiting**: Respect Telegram's 30 msg/sec limit
4. **Data Privacy**: Don't log message content, only metadata
5. **Connection Token**: Generate secure token for initial connection

---

## Testing Plan

1. **Unit Tests** (Target: 85%)
   - TelegramService message formatting
   - Rate limit handling
   - Error scenarios

2. **Integration Tests**
   - Connection flow
   - Message forwarding
   - Webhook handling

3. **E2E Tests**
   - User connects Telegram
   - SMS arrives
   - User receives Telegram notification
   - User disconnects

4. **Manual Testing**
   - Test with real Telegram account
   - Verify message formatting
   - Test rate limits with bulk SMS
   - Test error recovery

---

## Rollback Plan

If issues arise:
1. Remove `TELEGRAM_BOT_TOKEN` from Render
2. Service will gracefully skip Telegram forwarding
3. Users revert to email/webhook notifications
4. No data loss (connections remain in DB)

---

## Next Actions

**Waiting on**: Telegram bot token from @BotFather

Once token is available:
1. Run migration script
2. Implement TelegramService
3. Create API endpoints
4. Hook into SMS polling
5. Build frontend UI

**Estimated Time After Token**: 6-8 hours of development
