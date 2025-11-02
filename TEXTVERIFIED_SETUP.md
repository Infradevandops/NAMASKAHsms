# TextVerified API Setup Guide

## 🚨 **CRITICAL: Real API Key Required**

The Namaskah SMS platform requires a **REAL TextVerified API key** to function. Mock data is only for development testing.

## 📋 **Setup Steps**

### **1. Get TextVerified API Key**

1. **Visit**: https://www.textverified.com/
2. **Sign Up**: Create an account
3. **Add Credits**: Minimum $10 recommended for testing
4. **Get API Key**: Go to API section and copy your API key
5. **Note Email**: Use the email associated with your account

### **2. Update Configuration**

Edit `/Users/machine/Project/GitHub/Namaskah. app/.env`:

```bash
# Replace this line:
TEXTVERIFIED_API_KEY=REPLACE_WITH_REAL_TEXTVERIFIED_API_KEY

# With your real API key:
TEXTVERIFIED_API_KEY=tv_your_real_api_key_here
TEXTVERIFIED_EMAIL=your_textverified_email@domain.com
```

### **3. Verify Setup**

Test the API connection:

```bash
cd "/Users/machine/Project/GitHub/Namaskah. app"
python3 -c "
import asyncio
from app.services.textverified_service import TextVerifiedService

async def test():
    service = TextVerifiedService()
    balance = await service.get_balance()
    print(f'Balance: {balance}')
    
    if 'error' not in balance:
        print('✅ TextVerified API working!')
    else:
        print('❌ API key invalid or no credits')

asyncio.run(test())
"
```

## 💰 **Pricing Information**

### **TextVerified Costs**
- **SMS Verification**: $0.20 - $1.50 per verification
- **Voice Verification**: +$0.30 premium
- **Country Multipliers**: 0.2x - 1.8x based on region

### **Recommended Credits**
- **Testing**: $10 (40-50 verifications)
- **Production**: $50+ (200+ verifications)
- **Enterprise**: $200+ (800+ verifications)

## 🌍 **Supported Services & Countries**

### **Services Available**
- **1,800+ Services**: Telegram, WhatsApp, Discord, Google, Instagram, Facebook, etc.
- **All Major Platforms**: Social media, business, crypto, gaming, e-commerce

### **Countries Supported**
- **70 Countries**: US, UK, Germany, France, Canada, Australia, Japan, etc.
- **Voice Support**: 45 countries (premium markets)
- **SMS Support**: All 70 countries

## 🔧 **Production Deployment**

### **Environment Variables**
Set these in your production environment (Render, Heroku, etc.):

```bash
TEXTVERIFIED_API_KEY=tv_your_real_api_key
TEXTVERIFIED_EMAIL=your_email@domain.com
DATABASE_URL=postgresql://...
SECRET_KEY=your_32_char_secret
JWT_SECRET_KEY=your_32_char_jwt_secret
```

### **Health Monitoring**
The system includes:
- **Circuit Breaker**: Automatic failover protection
- **Health Checks**: Real-time API monitoring
- **Fallback System**: Graceful degradation when API unavailable

## ⚠️ **Important Notes**

1. **No Mock in Production**: The system will NOT work with fake/test keys
2. **Credits Required**: TextVerified requires account credits for verification
3. **Rate Limits**: Respect TextVerified's rate limiting (handled automatically)
4. **Security**: Never commit real API keys to version control

## 🆘 **Troubleshooting**

### **Common Issues**

#### **"Invalid token" Error**
- Check if API key is correctly set in .env
- Verify API key format starts with `tv_`
- Ensure no extra spaces or quotes

#### **"Service health check failed"**
- Verify internet connection
- Check TextVerified service status
- Confirm account has sufficient credits

#### **"Insufficient credits"**
- Add credits to your TextVerified account
- Check account balance via API or dashboard

### **Debug Commands**

```bash
# Check configuration
python3 -c "from app.core.config import settings; print(f'API Key: {settings.textverified_api_key[:10]}...')"

# Test API connection
python3 -c "
import asyncio
from app.services.textverified_service import TextVerifiedService

async def debug():
    service = TextVerifiedService()
    print(f'Using mock: {service.use_mock}')
    
    balance = await service.get_balance()
    print(f'Balance response: {balance}')
    
    services = await service.get_services()
    print(f'Services count: {len(services.get(\"services\", []))}')

asyncio.run(debug())
"
```

## 📞 **Support**

- **TextVerified Support**: https://www.textverified.com/support
- **API Documentation**: https://www.textverified.com/api
- **Status Page**: Check TextVerified service status

---

**Status**: Setup Required ⚠️  
**Priority**: Critical - Required for SMS functionality  
**Estimated Setup Time**: 10 minutes