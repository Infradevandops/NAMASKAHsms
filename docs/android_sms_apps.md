# Android SMS Gateway Apps

## 1. SMS Gateway API (Most Popular)
- **Play Store**: "SMS Gateway API"
- **Features**: REST API, webhooks, message history
- **Cost**: Free
- **Setup**: Install → Configure webhook URL → Get API key

## 2. SMS Gateway Ultimate
- **Features**: Multiple SIM support, scheduling
- **API**: HTTP REST endpoints
- **Cost**: Free with ads, $5 pro version

## 3. SMS Forwarder
- **Features**: Auto-forward SMS to webhook
- **Use Case**: Receive-only setup
- **Cost**: Free

## 4. Tasker + AutoRemote
- **Features**: Advanced automation
- **Complexity**: High (requires scripting)
- **Cost**: $3-5

## Setup Example (SMS Gateway API):

1. Install app on Android phone
2. Enable "Start on Boot"
3. Set webhook URL: `https://yourapi.com/sms/webhook`
4. Note the API key and phone IP
5. Test with curl command

## API Endpoints:
- `POST /send` - Send SMS
- `GET /messages` - Get message history  
- `POST /webhook` - Configure webhook URL
- `GET /status` - Check service status