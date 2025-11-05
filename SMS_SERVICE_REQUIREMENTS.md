# SMS Verification Service Requirements

## 🔑 **Authentication & Secrets**

### API Keys Required
- **Primary SMS Provider**: API key + secret
- **Backup SMS Provider**: API key + secret  
- **JWT Secret**: For user authentication
- **Database Credentials**: Connection string
- **Webhook Secret**: For validating incoming SMS

### Environment Variables
```bash
# SMS Providers
SMS_ACTIVATE_API_KEY=your_sms_activate_key
FIVESIM_API_KEY=your_5sim_key
TEXTVERIFIED_API_KEY=your_textverified_key

# Webhooks
WEBHOOK_SECRET=your_webhook_secret_32_chars
WEBHOOK_URL=https://yourapi.com/webhooks/sms

# Security
JWT_SECRET_KEY=your_jwt_secret_32_chars
API_KEY_SALT=your_api_key_salt

# Database
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://localhost:6379/0
```

## 🌐 **Webhook Configuration**

### Webhook Requirements
- **HTTPS Endpoint**: Must use SSL/TLS
- **Authentication**: Verify webhook signatures
- **Idempotency**: Handle duplicate deliveries
- **Response Time**: <5 seconds response
- **Status Codes**: Return 200 for success

### Webhook Payload Structure
```json
{
  "event": "sms_received",
  "verification_id": "ver_123456",
  "phone_number": "+1234567890",
  "message": "Your code is 123456",
  "timestamp": "2024-01-01T12:00:00Z",
  "signature": "sha256=abc123..."
}
```

### Webhook Security
```python
# Verify webhook signature
def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## 📱 **SMS Provider Integration**

### Provider Requirements
1. **API Access**: REST API with JSON responses
2. **Real-time SMS**: Instant message delivery
3. **Webhook Support**: Incoming SMS notifications
4. **Global Coverage**: Multiple countries
5. **Reliable Uptime**: 99%+ availability

### Required API Endpoints
- `GET /balance` - Check account balance
- `GET /services` - List available services
- `GET /countries` - List supported countries
- `POST /purchase` - Buy phone number
- `GET /messages/{id}` - Get SMS messages
- `POST /webhook` - Configure webhook URL

## 🔧 **Technical Infrastructure**

### Server Requirements
- **HTTPS**: SSL certificate required
- **Static IP**: For webhook whitelisting
- **Uptime**: 99.9% availability target
- **Response Time**: <2 seconds average
- **Concurrent Users**: Support 100+ simultaneous

### Database Schema
```sql
-- Core tables needed
CREATE TABLE users (id, email, api_key, balance);
CREATE TABLE verifications (id, user_id, phone, service, status);
CREATE TABLE sms_messages (id, verification_id, message, received_at);
CREATE TABLE webhook_logs (id, payload, signature, processed_at);
```

### Monitoring & Logging
- **Health Checks**: /health endpoint
- **Metrics**: Response times, success rates
- **Alerts**: Failed webhooks, low balance
- **Logs**: All API calls and webhook events

## 💰 **Billing & Credits**

### Credit System
- **User Balance**: Track credits per user
- **Auto-recharge**: Optional automatic top-up
- **Usage Tracking**: Log all SMS costs
- **Billing History**: Transaction records

### Pricing Structure
```python
PRICING = {
    "whatsapp": 0.15,    # $0.15 per SMS
    "telegram": 0.12,    # $0.12 per SMS
    "discord": 0.10,     # $0.10 per SMS
    "default": 0.08      # $0.08 per SMS
}
```

## 🛡️ **Security Requirements**

### API Security
- **Rate Limiting**: 100 requests/minute per user
- **API Key Authentication**: Required for all endpoints
- **Input Validation**: Sanitize all inputs
- **CORS**: Restrict cross-origin requests

### Data Protection
- **Encryption**: Encrypt sensitive data at rest
- **PII Handling**: Minimal phone number storage
- **Data Retention**: Auto-delete old messages
- **Audit Logs**: Track all data access

## 🚀 **Deployment Checklist**

### Pre-deployment
- [ ] SSL certificate installed
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Webhook endpoints tested
- [ ] Provider API keys validated

### Post-deployment
- [ ] Health checks passing
- [ ] Webhook delivery working
- [ ] SMS sending functional
- [ ] Monitoring alerts configured
- [ ] Backup systems tested

## 📊 **Success Metrics**

### Technical KPIs
- **API Uptime**: 99.9%
- **SMS Success Rate**: 95%+
- **Webhook Delivery**: 99%+
- **Response Time**: <2s average

### Business KPIs
- **User Satisfaction**: >4.5/5 rating
- **Cost per SMS**: <$0.10
- **Revenue Growth**: Month-over-month
- **Customer Retention**: >80%

## 🔄 **Backup & Failover**

### Provider Failover
```python
# Automatic provider switching
PROVIDER_PRIORITY = [
    "sms_activate",    # Primary
    "5sim",           # Backup 1  
    "receive_sms",    # Backup 2
    "manual_entry"    # Last resort
]
```

### Data Backup
- **Database**: Daily automated backups
- **Configuration**: Version controlled
- **Secrets**: Secure key management
- **Logs**: Centralized logging system

TEXTVERIFIED API (NEW)
ildUOUwdp5PjmKVWw74QLZhlo2pKoxXhSs9dMqUYSrSh2Tpbcl2pEu3WPUFWd


5SIM.NET eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTM3MzA0MTEsImlhdCI6MTc2MjE5NDQxMSwicmF5IjoiODMxNjRiN2Q4NjNkZjZjNmUyMTZhZjZiMzUwNzY5MGMiLCJzdWIiOjM1OTA1NjF9.cmtZheF9KcsJ72APv0IIPjlEGNlx_HDBALnOoXGyEK2nctyi6rnrdNHOjchwpACEiyGnrqfqIRqC6gJJWbPxgOzXhyQnNre2s2OUPlAxhBUlCkm3SFDLSGYGLxMCs3N1vV4XTpU3VzTiSx545HZd4Ki-iNp1gNBSlz1ml7tUzY06PY5hZlxCmzbRi7XNYkSoUrHwCo7Z3HuGWdRaU0K-BCFqeLjjmOoiIro_WTpzGpcVgJdKJNG5tkWw_Ip05rBJ3c2eUxH6M2ZNslcljJfAaZ_FY23lWmc0nQxzfZgQal6vBV5wfIyTUriOGQKpiHXRmZhiWsjtnR4qiwdoGRGrXQ


5SIM.NET 5SIM_EMAIL=DIAMONDMAN1960@GMAIL.COM


