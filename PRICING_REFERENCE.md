# PRICING REFERENCE - DEFINITIVE GUIDE

**Version**: 4.7.1
**Last Updated**: May 12, 2026
**Status**: ✅ OFFICIAL PRICING
**Currency**: USD (with NGN equivalent)

---

## 🎯 NEVER GET THIS WRONG AGAIN

This is the **SINGLE SOURCE OF TRUTH** for all Namaskah pricing.

---

## 💰 Base Pricing Configuration

### Provider Costs (TextVerified)
- **Average SMS cost**: $1.46 (varies by service)
- **Voice cost**: ~$1.50-$2.00
- **Rental cost**: ~$3.00-$5.00/day

### Platform Markup
- **Markup multiplier**: 1.8x (180%)
- **Formula**: `provider_cost × 1.8 = platform_price`

### Currency Conversion
- **NGN/USD Rate**: ₦1,650 per $1
- **Formula**: `USD_price × 1650 = NGN_price`

---

## 📊 TIER PRICING STRUCTURE

### 1. FREEMIUM TIER

**Monthly Fee**: $0 (₦0)

**SMS/Voice Base Rate**:
- **USD**: $2.63 per verification
- **NGN**: ₦4,340 per verification
- **Calculation**: $1.46 (provider) × 1.8 = $2.63

**Features**:
- ❌ No area code selection
- ❌ No carrier filtering
- ❌ No API access
- ❌ No webhooks
- ✅ Basic SMS verification
- ✅ Community support

**Limits**:
- Daily: 100 verifications
- Monthly: 3,000 verifications
- Countries: 5
- Retention: 1 day

---

### 2. PAY-AS-YOU-GO (PAYG) TIER

**Monthly Fee**: $0 (₦0)

**SMS/Voice Base Rate**:
- **USD**: $2.63 per verification
- **NGN**: ₦4,340 per verification
- **Same as Freemium** (no base rate difference)

**Area Code Selection Fee**:
- **USD**: +$0.25 per verification
- **NGN**: +₦413 per verification
- **Total with area code**: $2.88 (₦4,753)

**Carrier Filtering Fee**:
- **USD**: +$0.50 per verification
- **NGN**: +₦825 per verification
- **Total with carrier**: $3.13 (₦5,165)

**Both Filters**:
- **USD**: $2.63 + $0.25 + $0.50 = $3.38
- **NGN**: ₦5,578

**Features**:
- ✅ Area code selection (+$0.25)
- ✅ Carrier filtering (+$0.50)
- ❌ No API access
- ❌ No webhooks
- ✅ Extended SMS verification
- ✅ Community support

**Limits**:
- Daily: 500 verifications
- Monthly: 15,000 verifications
- Countries: Unlimited
- Retention: 3 days

---

### 3. PRO TIER

**Monthly Fee**:
- **USD**: $25/month
- **NGN**: ₦41,250/month

**Monthly Quota**:
- **USD**: $15 included
- **NGN**: ₦24,750 included
- **Verifications**: ~6 SMS (at $2.63 each)

**SMS/Voice Base Rate**:
- **USD**: $2.63 per verification (within quota)
- **NGN**: ₦4,340 per verification (within quota)

**Overage Rate** (after quota exhausted):
- **USD**: $0.30 per verification
- **NGN**: ₦495 per verification

**Area Code Selection**:
- **Included** (no additional fee)
- **Value**: Saves $0.25 per verification

**Carrier Filtering**:
- **Included** (no additional fee)
- **Value**: Saves $0.50 per verification

**Features**:
- ✅ Area code selection (included)
- ✅ Carrier filtering (included)
- ✅ API access (10 keys)
- ✅ Webhooks
- ✅ Voice verification
- ✅ Number rentals
- ✅ Priority support

**Limits**:
- Daily: 2,000 verifications
- Monthly: 60,000 verifications
- Countries: Unlimited
- Retention: 7 days

**Break-even Analysis**:
- Monthly fee: $25
- Quota: $15
- Net cost: $10/month
- If using area code + carrier on PAYG: $0.75 per verification
- Break-even: 14 verifications/month with filters
- **Recommendation**: Upgrade if using filters >14 times/month

---

### 4. CUSTOM TIER

**Monthly Fee**:
- **USD**: $35/month
- **NGN**: ₦57,750/month

**Monthly Quota**:
- **USD**: $25 included
- **NGN**: ₦41,250 included
- **Verifications**: ~10 SMS (at $2.63 each)

**SMS/Voice Base Rate**:
- **USD**: $2.63 per verification (within quota)
- **NGN**: ₦4,340 per verification (within quota)

**Overage Rate** (after quota exhausted):
- **USD**: $0.20 per verification
- **NGN**: ₦330 per verification

**Area Code Selection**:
- **Included** (no additional fee)

**Carrier Filtering**:
- **Included** (no additional fee)

**Features**:
- ✅ Area code selection (included)
- ✅ Carrier filtering (included)
- ✅ API access (unlimited keys)
- ✅ Webhooks
- ✅ Voice verification
- ✅ Number rentals
- ✅ Whitelabel/custom branding
- ✅ Dedicated support
- ✅ Live chat

**Limits**:
- Daily: 10,000 verifications
- Monthly: 300,000 verifications
- Countries: Unlimited
- Retention: 30 days

**Break-even Analysis**:
- Monthly fee: $35
- Quota: $25
- Net cost: $10/month
- Better overage rate than Pro ($0.20 vs $0.30)
- **Recommendation**: Upgrade if exceeding Pro quota regularly

---

## 🎯 PRICING COMPARISON TABLE

| Feature | Freemium | PAYG | Pro | Custom |
|---------|----------|------|-----|--------|
| **Monthly Fee** | $0 | $0 | $25 | $35 |
| **Base SMS Rate** | $2.63 | $2.63 | $2.63 | $2.63 |
| **Area Code Fee** | ❌ N/A | +$0.25 | ✅ Free | ✅ Free |
| **Carrier Fee** | ❌ N/A | +$0.50 | ✅ Free | ✅ Free |
| **With Both Filters** | ❌ N/A | $3.38 | $2.63 | $2.63 |
| **Monthly Quota** | None | None | $15 | $25 |
| **Overage Rate** | N/A | N/A | $0.30 | $0.20 |
| **API Access** | ❌ | ❌ | ✅ 10 keys | ✅ Unlimited |
| **Webhooks** | ❌ | ❌ | ✅ | ✅ |
| **Voice/Rentals** | ❌ | ❌ | ✅ | ✅ |
| **Support** | Community | Community | Priority | Dedicated |

---

## 💡 PRICING EXAMPLES

### Example 1: Freemium User (10 SMS/month)
```
10 SMS × $2.63 = $26.30/month
NGN: 10 × ₦4,340 = ₦43,400/month
```

### Example 2: PAYG User (10 SMS/month with area code)
```
10 SMS × ($2.63 + $0.25) = $28.80/month
NGN: 10 × ₦4,753 = ₦47,530/month
```

### Example 3: PAYG User (10 SMS/month with both filters)
```
10 SMS × $3.38 = $33.80/month
NGN: 10 × ₦5,578 = ₦55,780/month
```

### Example 4: Pro User (10 SMS/month)
```
Monthly fee: $25
Quota: $15 (covers ~6 SMS)
Remaining: 4 SMS × $0.30 = $1.20
Total: $25 + $1.20 = $26.20/month
NGN: ₦43,230/month

Savings vs PAYG with filters: $33.80 - $26.20 = $7.60/month
```

### Example 5: Pro User (50 SMS/month)
```
Monthly fee: $25
Quota: $15 (covers ~6 SMS)
Remaining: 44 SMS × $0.30 = $13.20
Total: $25 + $13.20 = $38.20/month
NGN: ₦63,030/month

Savings vs PAYG with filters: (50 × $3.38) - $38.20 = $169 - $38.20 = $130.80/month
```

### Example 6: Custom User (100 SMS/month)
```
Monthly fee: $35
Quota: $25 (covers ~10 SMS)
Remaining: 90 SMS × $0.20 = $18.00
Total: $35 + $18.00 = $53.00/month
NGN: ₦87,450/month

Savings vs Pro: (100 × $0.30) - $18 = $30 - $18 = $12/month additional savings
```

---

## 🔧 VOICE VERIFICATION PRICING

### Base Voice Rate
- **Same as SMS**: $2.63 (₦4,340)
- **Provider cost**: ~$1.46 × 1.8 = $2.63

### Area Code Selection
- **Freemium**: ❌ Not available
- **PAYG**: +$0.25 (₦413)
- **Pro**: ✅ Included
- **Custom**: ✅ Included

### Total Voice Cost
| Tier | Without Area Code | With Area Code |
|------|-------------------|----------------|
| Freemium | $2.63 | ❌ N/A |
| PAYG | $2.63 | $2.88 |
| Pro | $2.63 | $2.63 (included) |
| Custom | $2.63 | $2.63 (included) |

---

## 🏠 NUMBER RENTAL PRICING

### Base Rental Rate
- **Provider cost**: ~$3.00-$5.00/day
- **Platform price**: $5.40-$9.00/day (1.8x markup)
- **Average**: $7.00/day (₦11,550/day)

### Duration Options
| Duration | Cost (USD) | Cost (NGN) | Daily Rate |
|----------|------------|------------|------------|
| 1 day | $7.00 | ₦11,550 | $7.00 |
| 7 days | $45.00 | ₦74,250 | $6.43 (-8%) |
| 14 days | $85.00 | ₦140,250 | $6.07 (-13%) |
| 30 days | $180.00 | ₦297,000 | $6.00 (-14%) |

### Area Code Selection
- **Freemium**: ❌ Not available
- **PAYG**: +$0.50/day (₦825/day)
- **Pro**: ✅ Included
- **Custom**: ✅ Included

### Tier Availability
- **Freemium**: ❌ No rentals
- **PAYG**: ❌ No rentals
- **Pro**: ✅ Available
- **Custom**: ✅ Available

---

## 📐 PRICING FORMULAS

### SMS/Voice Verification
```python
# Base cost
base_cost = provider_cost × 1.8

# Freemium/PAYG
total_cost = base_cost + area_code_fee + carrier_fee

# Pro (within quota)
total_cost = 0  # covered by subscription

# Pro (overage)
total_cost = overage_verifications × 0.30

# Custom (within quota)
total_cost = 0  # covered by subscription

# Custom (overage)
total_cost = overage_verifications × 0.20
```

### Area Code Fee
```python
if tier == "freemium":
    area_code_fee = None  # Not available
elif tier == "payg":
    area_code_fee = 0.25
elif tier in ["pro", "custom"]:
    area_code_fee = 0.00  # Included
```

### Carrier Filtering Fee
```python
if tier == "freemium":
    carrier_fee = None  # Not available
elif tier == "payg":
    carrier_fee = 0.50
elif tier in ["pro", "custom"]:
    carrier_fee = 0.00  # Included
```

### Currency Conversion
```python
ngn_price = usd_price × 1650
```

---

## 🎯 RECOMMENDED PRICING STRATEGY

### For Users
1. **0-10 SMS/month**: Freemium ($2.63/SMS)
2. **10-20 SMS/month with filters**: PAYG ($3.38/SMS)
3. **20+ SMS/month with filters**: Pro ($25/mo + $0.30 overage)
4. **100+ SMS/month**: Custom ($35/mo + $0.20 overage)

### Break-even Points
- **PAYG → Pro**: 14 verifications/month with filters
- **Pro → Custom**: When overage exceeds $10/month (33 overage SMS)

---

## 📝 IMPLEMENTATION CHECKLIST

### Code Files to Update
- [x] `app/core/tier_config.py` - Base SMS cost: 2.12 → 2.63
- [x] `app/services/pricing_calculator.py` - Verify markup calculation
- [x] `.env.production` - PRICE_MARKUP=1.8, NGN_USD_RATE=1650
- [ ] `templates/pricing.html` - Display correct prices
- [ ] `README.md` - Update pricing section
- [ ] All assessment documents - Correct pricing references

### Database Updates
```sql
-- Update subscription_tiers table
UPDATE subscription_tiers SET overage_rate = 2.63 WHERE tier = 'freemium';
UPDATE subscription_tiers SET overage_rate = 2.63 WHERE tier = 'payg';
UPDATE subscription_tiers SET overage_rate = 0.30 WHERE tier = 'pro';
UPDATE subscription_tiers SET overage_rate = 0.20 WHERE tier = 'custom';
```

---

## ⚠️ IMPORTANT NOTES

1. **Provider costs vary** by service (WhatsApp, Google, etc.)
2. **Markup is consistent** at 1.8x across all services
3. **Area code/carrier fees** are fixed regardless of service
4. **Quota is in USD**, not number of verifications
5. **NGN rate** may fluctuate, update as needed
6. **Overage rates** apply only to Pro/Custom tiers
7. **Admin can change pricing dynamically** via admin panel (see ADMIN_PRICING_CONTROL_BRIEF.md)
8. **Active pricing may differ** from this reference - check admin panel for current rates

---

## 🔄 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | May 12, 2026 | Initial pricing reference |
| 1.1 | May 12, 2026 | Corrected base rate from $2.12 to $2.63 |

---

**Status**: ✅ OFFICIAL PRICING REFERENCE
**Authority**: Single Source of Truth
**Next Review**: Monthly or when provider costs change

---

**NEVER REFERENCE ANY OTHER PRICING DOCUMENT**
**THIS IS THE ONLY CORRECT PRICING INFORMATION**
