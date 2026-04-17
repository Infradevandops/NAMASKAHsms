# Multi-Provider Routing — Quick Start Guide

**Status**: ✅ DEPLOYED  
**Commit**: e230fed0  
**Date**: March 26, 2026

---

## 🚀 What's New

Your SMS verification platform now supports **3 providers**:
- **TextVerified** (US, proven)
- **Telnyx** (Enterprise, 190+ countries)
- **5sim** (Cost-effective international)

**Smart routing** automatically selects the best provider based on country.

---

## 📋 Current State

### Default Configuration (Safe)

```bash
# All providers disabled except TextVerified
TELNYX_ENABLED=false
FIVESIM_ENABLED=false
ENABLE_PROVIDER_FAILOVER=true
```

**Result**: All requests use TextVerified (existing behavior). Zero impact.

---

## 🔧 Enabling Providers

### Option 1: Enable Telnyx (Enterprise)

```bash
# Add to .env
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_ENABLED=true

# Restart application
./start.sh
```

**What happens**:
- US requests → TextVerified (unchanged)
- International requests → Telnyx
- Failover to 5sim if Telnyx fails (if 5sim enabled)

### Option 2: Enable 5sim (Cost-Effective)

```bash
# Add to .env
FIVESIM_API_KEY=your_5sim_api_key_here
FIVESIM_ENABLED=true

# Restart application
./start.sh
```

**What happens**:
- US requests → TextVerified (unchanged)
- International requests → 5sim
- Failover to Telnyx if 5sim fails (if Telnyx enabled)

### Option 3: Enable Both (Recommended)

```bash
# Add to .env
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_ENABLED=true
FIVESIM_API_KEY=your_5sim_api_key_here
FIVESIM_ENABLED=true
PREFER_ENTERPRISE_PROVIDER=false  # Use 5sim first (cheaper)

# Restart application
./start.sh
```

**What happens**:
- US requests → TextVerified
- International requests → 5sim (primary)
- Failover to Telnyx if 5sim fails
- Failover to TextVerified if both fail

---

## 🎯 Routing Logic

### By Country

| Country | Primary | Secondary | Tertiary |
|---------|---------|-----------|----------|
| US | TextVerified | - | - |
| GB, DE, FR, etc. | 5sim | Telnyx | TextVerified |

### By Preference

```bash
# Cost-optimized (default)
PREFER_ENTERPRISE_PROVIDER=false
# Routes: 5sim → Telnyx → TextVerified

# Enterprise-first
PREFER_ENTERPRISE_PROVIDER=true
# Routes: Telnyx → 5sim → TextVerified
```

---

## 🔍 Monitoring

### Check Provider Status

```bash
# View logs
tail -f logs/app.log | grep "Routing to"

# Example output:
# Routing to TextVerified for US request
# Routing to 5sim for GB (cost-effective)
# Routing to Telnyx for DE (enterprise preference)
```

### Check Provider Balances

```bash
# API endpoint (admin only)
curl http://localhost:8000/api/admin/provider-balances \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response:
{
  "textverified": 100.50,
  "telnyx": 250.00,
  "5sim": 75.25
}
```

### Check Enabled Providers

```bash
# API endpoint
curl http://localhost:8000/api/admin/providers \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response:
{
  "enabled": ["textverified", "telnyx", "5sim"],
  "disabled": []
}
```

---

## 🐛 Troubleshooting

### Issue: International requests still use TextVerified

**Check 1**: Are providers enabled?
```bash
echo $TELNYX_ENABLED  # Should be "true"
echo $FIVESIM_ENABLED  # Should be "true"
```

**Check 2**: Are API keys set?
```bash
echo $TELNYX_API_KEY  # Should not be empty
echo $FIVESIM_API_KEY  # Should not be empty
```

**Check 3**: Restart application
```bash
./start.sh
```

### Issue: Verification fails with "Provider not configured"

**Solution**: Provider is enabled but API key is invalid
```bash
# Test Telnyx API key
curl https://api.telnyx.com/v2/balance \
  -H "Authorization: Bearer $TELNYX_API_KEY"

# Test 5sim API key
curl https://5sim.net/v1/user/profile \
  -H "Authorization: Bearer $FIVESIM_API_KEY"
```

### Issue: Polling never completes

**Check**: Provider-specific polling is working
```bash
# View polling logs
tail -f logs/app.log | grep "Polling"

# Should see:
# Polling textverified for verification 123
# Polling telnyx for verification 456
# Polling 5sim for verification 789
```

---

## 🔄 Rollback

### Instant Rollback (No Deploy)

```bash
# Disable all new providers
export TELNYX_ENABLED=false
export FIVESIM_ENABLED=false

# Restart application
./start.sh
```

**Result**: All requests route to TextVerified (original behavior).

### Full Rollback (Revert Code)

```bash
# Revert to previous commit
git revert e230fed0
git push origin main
```

---

## 📊 Cost Comparison

### Per-SMS Cost (Approximate)

| Provider | US | UK | Germany | India |
|----------|----|----|---------|-------|
| TextVerified | $2.22 | Limited | Limited | Limited |
| Telnyx | $0.01 | $0.10 | $0.15 | $0.05 |
| 5sim | N/A | $0.50 | $0.75 | $0.30 |

**Recommendation**: Use 5sim for low-volume international, Telnyx for high-volume.

---

## 🎯 Best Practices

### For Development

```bash
# Use only TextVerified (free tier)
TELNYX_ENABLED=false
FIVESIM_ENABLED=false
```

### For Staging

```bash
# Enable all providers, test routing
TELNYX_ENABLED=true
FIVESIM_ENABLED=true
ENABLE_PROVIDER_FAILOVER=true
```

### For Production

```bash
# Enable all providers, cost-optimized
TELNYX_ENABLED=true
FIVESIM_ENABLED=true
PREFER_ENTERPRISE_PROVIDER=false
ENABLE_PROVIDER_FAILOVER=true
```

---

## 📞 Support

### Provider Documentation

- **TextVerified**: https://textverified.com/docs
- **Telnyx**: https://developers.telnyx.com/docs/api/v2/messaging
- **5sim**: https://5sim.net/docs

### Internal Documentation

- **Implementation**: `docs/implementation/MULTI_PROVIDER_ROUTING_COMPLETE.md`
- **Architecture**: `docs/tasks/SMART_MULTI_PROVIDER_ROUTING.md`
- **Code**: `app/services/providers/`

---

## ✅ Verification Checklist

Before enabling in production:

- [ ] Telnyx API key tested and valid
- [ ] 5sim API key tested and valid
- [ ] Provider balances > $50 each
- [ ] Monitoring alerts configured
- [ ] Tested US request (should use TextVerified)
- [ ] Tested UK request (should use Telnyx/5sim)
- [ ] Tested failover (disable primary, verify secondary works)
- [ ] Rollback plan documented and tested

---

**Ready to go global? Enable providers and start routing! 🌍**
