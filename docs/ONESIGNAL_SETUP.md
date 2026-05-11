# OneSignal Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create OneSignal Account
1. Go to https://onesignal.com
2. Sign up for free account
3. Create new app: "Namaskah SMS Platform"

### Step 2: Get Credentials
1. In OneSignal dashboard, go to **Settings** → **Keys & IDs**
2. Copy **App ID** (looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
3. Copy **REST API Key** (looks like: `YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=`)

### Step 3: Configure Environment Variables

#### Local Development (.env)
```bash
# Add to .env file
ONESIGNAL_APP_ID=your-app-id-here
ONESIGNAL_API_KEY=your-rest-api-key-here
```

#### Production (Render.com)
1. Go to Render dashboard: https://dashboard.render.com
2. Select your service: `namaskah-sms`
3. Go to **Environment** tab
4. Add environment variables:
   - Key: `ONESIGNAL_APP_ID`, Value: `your-app-id`
   - Key: `ONESIGNAL_API_KEY`, Value: `your-rest-api-key`
5. Click **Save Changes**
6. Service will auto-redeploy

### Step 4: Configure Web Push
1. In OneSignal dashboard, go to **Settings** → **Platforms**
2. Click **Web Push**
3. Configure:
   - **Site Name**: Namaskah
   - **Site URL**: https://vrenum.onrender.com
   - **Auto Resubscribe**: ON
   - **Default Icon**: Upload logo (512x512px)
4. Save configuration

### Step 5: Verify Setup
1. Restart application
2. Check logs for: `[OneSignal] Service initialized`
3. Visit: https://vrenum.onrender.com/push-settings
4. Test subscription

## Configuration Options

### Notification Settings
```python
# In OneSignal dashboard → Settings → Messaging

# Delivery
- Time To Live: 259200 seconds (3 days)
- Throttle Rate: 1000 per minute

# Appearance
- Large Icon: 512x512px PNG
- Small Icon: 96x96px PNG (white on transparent)
- Accent Color: #FE3C72

# Behavior
- Click Action: Open URL
- Badge Count: Enabled
```

### Segments (Optional)
Create user segments for targeted notifications:
- **Active Users**: Last session < 7 days
- **Pro Users**: Tag: tier=pro
- **Inactive Users**: Last session > 30 days

## Testing

### Test Notification
```bash
curl -X POST https://onesignal.com/api/v1/notifications \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic YOUR_REST_API_KEY" \
  -d '{
    "app_id": "YOUR_APP_ID",
    "included_segments": ["Subscribed Users"],
    "contents": {"en": "Test notification from Namaskah!"},
    "headings": {"en": "Test Message"}
  }'
```

### Verify in Application
```python
# Check service status
from app.services.onesignal_service import OneSignalService

service = OneSignalService()
print(f"App ID: {service.app_id}")
print(f"Configured: {service.app_id is not None}")
```

## Troubleshooting

### Issue: Service not initializing
**Solution**: Check environment variables are set correctly
```bash
# Verify in production
curl https://vrenum.onrender.com/api/health
# Should show onesignal: true
```

### Issue: Notifications not sending
**Solution**: Check API key permissions
- Ensure REST API Key has "Create notifications" permission
- Verify App ID matches your OneSignal app

### Issue: Subscription failing
**Solution**: Check HTTPS and service worker
- Site must be served over HTTPS
- Service worker must be accessible at `/OneSignalSDKWorker.js`

## Security Best Practices

1. **Never commit credentials** to git
2. **Use environment variables** for all keys
3. **Rotate API keys** every 90 days
4. **Monitor usage** in OneSignal dashboard
5. **Set up alerts** for unusual activity

## Cost Estimation

OneSignal Free Tier:
- ✅ Unlimited push notifications
- ✅ Up to 10,000 subscribers
- ✅ Basic segmentation
- ✅ Analytics

Paid Tier (if needed):
- $9/month for 10,000+ subscribers
- Advanced segmentation
- A/B testing
- Priority support

## Next Steps

After setup:
1. ✅ Configure environment variables
2. ✅ Test notification sending
3. ✅ Implement subscription UI (Task 5)
4. ✅ Add notification preferences (Task 6)
5. ✅ Monitor delivery rates

## Support

- OneSignal Docs: https://documentation.onesignal.com
- Namaskah Support: support@namaskah.app
- Status Page: https://status.onesignal.com

---

**Setup Time**: ~5 minutes
**Status**: Ready for production
**Last Updated**: May 11, 2026
