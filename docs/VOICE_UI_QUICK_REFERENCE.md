# Voice UI Quick Reference Card

**Last Updated**: May 10, 2026
**Status**: Production Ready

---

## 🚀 Quick Start

### Key Functions

```javascript
// Toggle advanced options
toggleVoiceAdvanced()

// Check area code availability
await checkVoiceAreaCode(areaCode)

// Update pricing display
updatePricing()

// Create verification
await createVerification()

// Start polling
startWaiting()
```

---

## 🎨 Design Tokens

```css
/* Colors */
--primary: #FE3C72
--success: #10b981
--error: #ef4444

/* Spacing */
--spacing-md: 16px
--spacing-lg: 24px

/* Radius */
--radius-lg: 12px
```

---

## 📡 API Endpoints

```javascript
// Area codes list
GET /api/area-codes?country=US

// Availability check
GET /api/area-codes/check?area_code=213&service=google

// Create verification
POST /api/verification/request
{
  "service": "google",
  "country": "US",
  "capability": "voice",
  "area_codes": ["213"]
}

// Check status
GET /api/verification/status/{id}

// Get balance
GET /api/billing/balance
```

---

## 🔧 Common Tasks

### Add New Service Icon
```javascript
const iconMap = {
  servicename: 'simpleicons-slug'
};
// Icon URL: https://cdn.simpleicons.org/{slug}/E8003D
```

### Update Pricing
```javascript
let basePrice = selectedServicePrice || 0;
let filterFee = areaCode ? 0.25 : 0;
let totalPrice = basePrice + filterFee;
```

### Show Error
```javascript
showError('Title', 'Message');
// Displays error container and toast
```

### Reset Flow
```javascript
resetFlow();
// Clears state, returns to step 1
```

---

## 🐛 Debugging

### Check Service Load
```javascript
console.log('Services:', _voiceServices.length);
// Should be > 0
```

### Check Area Code Status
```javascript
console.log('Area code:', document.getElementById('area-code-select').value);
// Empty = "Any", otherwise specific code
```

### Check Verification State
```javascript
console.log('Verification ID:', verificationId);
console.log('Current step:', currentStep);
console.log('Elapsed:', elapsedSeconds);
```

---

## ⚠️ Common Issues

### Services Not Loading
```javascript
// Check ServiceStore
await window.ServiceStore.init();
const services = window.ServiceStore.getAll();
console.log('Loaded:', services.length);
```

### Area Code Check Failing
```javascript
// Check API response
const res = await fetch('/api/area-codes/check?...');
console.log('Status:', res.status);
const data = await res.json();
console.log('Available:', data.available);
```

### Timer Not Updating
```javascript
// Check interval
console.log('Interval:', scanInterval);
// Should be a number, not null
```

---

## 📋 Testing Checklist

```
[ ] Service modal opens
[ ] Search filters work
[ ] Area code is optional
[ ] Availability check works
[ ] Alternatives display
[ ] Pricing updates
[ ] Timer ring animates
[ ] Code displays correctly
[ ] Copy button works
[ ] Error handling works
```

---

## 🎯 Key Differences from SMS

| Feature | SMS | Voice |
|---------|-----|-------|
| Capability | `sms` | `voice` |
| Delivery | 30-60s | 2-5min |
| Base Price | $2.22 | $3.50 |
| Success Rate | 95% | 92% |
| Carrier Filter | ✅ | ❌ |

---

## 🔗 Related Files

- Template: `templates/voice_verify_modern.html`
- CSS: `/static/css/verification-design-system.css`
- Service Store: `/static/js/service-store.js`
- Backend: `app/services/textverified_service.py`

---

## 📞 Support

- **Docs**: `docs/VOICE_UI_IMPROVEMENTS_COMPLETE.md`
- **Visual**: `docs/VOICE_UI_VISUAL_COMPARISON.md`
- **Summary**: `docs/VOICE_UI_EXECUTIVE_SUMMARY.md`

---

**Quick Tip**: Voice uses the same area code logic as SMS - check `textverified_service.py` for implementation details.
