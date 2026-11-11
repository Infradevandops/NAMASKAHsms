# Revenue Features — Implementation Spec

**Created**: November 2026
**Priority**: P1 — Direct Revenue
**Status**: 📋 Planned — not yet implemented
**Source**: `SDK_OPTIMIZATION_OPPORTUNITIES.md`, business model analysis

---

## Overview

Four features that add revenue with minimal engineering. Ranked by effort-to-revenue ratio.

| Feature | Monthly Revenue Potential | Effort | When |
|---------|--------------------------|--------|------|
| Annual plans | 10× upfront cash per Pro/Custom user | Trivial (Paystack config) | Now |
| Reuse surcharge ($0.25) | ~$7.50/1k verifications | Low | Next sprint |
| PAYG API add-on ($10/mo) | Captures segment with no current path | Low | Next sprint |
| Bulk credit discount | Increases avg deposit, reduces Paystack fees | Low | Next sprint |

---

## Feature 1 — Annual Plans

### What
Pro and Custom users can pay annually at a discount. Platform gets 10 months of cash upfront per user.

### Pricing
| Tier | Monthly | Annual | Savings | Platform gets upfront |
|------|---------|--------|---------|----------------------|
| Pro | $25/mo | $250/yr | $50 (2 months free) | $250 vs $25 |
| Custom | $35/mo | $350/yr | $70 (2 months free) | $350 vs $35 |

### Why it works
- Users who commit annually churn at ~40% lower rate than monthly
- Platform gets cash before the service is delivered — improves cash flow
- The "2 months free" framing is standard SaaS and converts well
- Zero new features required — just Paystack plan configuration + a billing UI toggle

### Implementation

**Paystack side**: Create annual plan codes in Paystack dashboard:
- `PLAN_PRO_ANNUAL` — ₦412,500/year (= $250 × ₦1,650)
- `PLAN_CUSTOM_ANNUAL` — ₦577,500/year (= $350 × ₦1,650)

**Backend** (`app/services/payment_service.py`):
```python
PLAN_CODES = {
    "pro_monthly": "PLN_xxx",
    "pro_annual": "PLN_yyy",      # add
    "custom_monthly": "PLN_zzz",
    "custom_annual": "PLN_aaa",   # add
}

# Subscription record needs billing_period field
# "monthly" | "annual"
```

**Schema addition**:
```sql
ALTER TABLE subscriptions ADD COLUMN billing_period VARCHAR(10) NOT NULL DEFAULT 'monthly';
ALTER TABLE subscriptions ADD COLUMN annual_renewal_at TIMESTAMPTZ;
```

**Tier upgrade endpoint** (`app/api/billing/tiers.py`):
```python
class TierUpgradeRequest(BaseModel):
    tier: str
    billing_period: Literal["monthly", "annual"] = "monthly"
```

**UI** (`templates/pricing.html`, `templates/settings.html`):
- Add toggle: "Monthly / Annual (save 2 months)"
- Show annual price prominently when annual selected
- Show "Most popular" badge on Pro annual

### Acceptance Criteria
- [ ] Annual plan options visible on pricing page with toggle
- [ ] Paystack initializes correct plan code based on billing_period selection
- [ ] Subscription record stores `billing_period` and `annual_renewal_at`
- [ ] Tier expiry calculated correctly for annual (365 days, not 30)
- [ ] Renewal reminder email fires 30 days before annual renewal
- [ ] Admin panel shows billing period per user

---

## Feature 2 — Reuse Surcharge ($0.25)

### What
After a verification completes, TV's `VerificationExpanded.reuse.reusable_until` is set for a window (typically 5–15 min). The user can reuse the same number for a different service at lower TV cost. Platform charges $0.25 convenience fee for this.

### Logic
```
Verification completes
→ Check reuse.reusable_until on TV response
→ If in the future AND user balance ≥ $0.25:
    → Push WebSocket event: { type: "reuse_available", fee: 0.25, reusable_until: "..." }
    → Show "Reuse this number for another service — $0.25" in UI
→ If balance < $0.25:
    → Don't show the option (no friction, no failed charge)
→ If reusable_until has passed:
    → Option disappears automatically
```

### Revenue math
- 1,000 verifications/month × 10% reuse offer rate × 30% conversion = 30 reuse events
- 30 × $0.25 = **$7.50/month at 1k verifications**
- 10,000 verifications/month = **$75/month pure margin**
- TV's reuse cost < fresh purchase cost → margin on reuse is higher than base verification

### Implementation

**New endpoint** (`app/api/verification/reuse_endpoint.py`):
```python
@router.post("/api/verification/{id}/reuse")
async def reuse_verification(
    id: UUID,
    service_name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    verification = await get_verification_or_404(id, user.id, db)

    if not verification.reusable_until or datetime.utcnow() > verification.reusable_until:
        raise HTTPException(410, "Reuse window has expired")

    if not await balance_service.check_sufficient_balance(user.id, REUSE_FEE):
        raise HTTPException(402, "Insufficient balance for reuse fee")

    # Deduct fee first
    await balance_service.deduct(user.id, REUSE_FEE, reason="reuse_fee", db=db)

    # Call TV reuse
    result = await tv_service.reuse_verification(verification.activation_id)

    # Create new verification record linked to reuse
    new_verification = Verification(
        user_id=user.id,
        service_name=service_name,
        phone_number=verification.phone_number,
        activation_id=result.id,
        cost=REUSE_FEE,
        reused_from_id=verification.id,
    )
    db.add(new_verification)
    await db.commit()

    return {"verification_id": str(new_verification.id), "phone_number": verification.phone_number}
```

**Config** (`app/core/config.py`):
```python
REUSE_FEE: float = 0.25
```

**Schema addition**:
```sql
ALTER TABLE verifications ADD COLUMN reusable_until TIMESTAMPTZ;
ALTER TABLE verifications ADD COLUMN reused_from_id UUID REFERENCES verifications(id);
```

**`sms_polling_service.py`** — store `reusable_until` after completion:
```python
# After _complete_verification():
if tv_result.reuse and tv_result.reuse.reusable_until:
    verification.reusable_until = tv_result.reuse.reusable_until
    await db.commit()
    await ws_manager.send_to_user(user_id, {
        "type": "reuse_available",
        "verification_id": str(verification.id),
        "reusable_until": tv_result.reuse.reusable_until.isoformat(),
        "fee": settings.REUSE_FEE,
    })
```

**UI** (`static/js/verification-flow.js`, `templates/verify_modern.html`):
- On `reuse_available` WebSocket event, show a dismissible banner below the completed verification
- Banner: "Reuse this number for another service — $0.25 → [Select service]"
- Banner auto-hides when `reusable_until` passes (client-side timer)

### Acceptance Criteria
- [ ] `reusable_until` stored on verification record after completion
- [ ] WebSocket event fires if `reusable_until` is in the future and balance ≥ $0.25
- [ ] No event fires if balance < $0.25
- [ ] Reuse endpoint deducts $0.25 before calling TV
- [ ] Reuse endpoint returns 410 if window expired
- [ ] New verification record created with `reused_from_id` set
- [ ] Banner disappears when `reusable_until` passes
- [ ] Transaction history shows reuse fee as separate line item

---

## Feature 3 — PAYG API Add-On ($10/month)

### What
PAYG users who need API access currently have no path except upgrading to Pro ($25/month). A $10/month add-on gives them 5 API keys without forcing a full tier upgrade.

### Why it doesn't cannibalize Pro
- Pro is $25/month and includes $15 quota + all features (carrier filters, affiliate, priority support)
- PAYG + API add-on = $10/month, no quota, no carrier filters, no affiliate
- Different user: developer who needs API access but doesn't do enough volume to justify Pro
- If they grow, they upgrade to Pro — the add-on is a stepping stone, not a ceiling

### Pricing
| | PAYG | PAYG + API Add-on | Pro |
|--|------|-------------------|-----|
| Monthly fee | $0 | $10 | $25 |
| API keys | 0 | 5 | 10 |
| Monthly quota | None | None | $15 |
| Carrier filters | +$0.50 | +$0.50 | Included |
| Area code | +$0.25 | +$0.25 | Included |

### Implementation

**New subscription add-on model**:
```sql
CREATE TABLE subscription_addons (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    addon_type  VARCHAR(50) NOT NULL,  -- 'api_access'
    price_usd   NUMERIC(10,2) NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ,
    paystack_subscription_code VARCHAR(100),
    UNIQUE(user_id, addon_type)
);
```

**Tier gate update** (`app/services/tier_service.py`):
```python
async def can_use_api_keys(user_id: UUID, db: AsyncSession) -> bool:
    user = await get_user(user_id, db)
    # Pro+ always yes
    if user.subscription_tier in ("pro", "custom"):
        return True
    # PAYG with active API add-on
    addon = await db.execute(
        select(SubscriptionAddon).where(
            SubscriptionAddon.user_id == user_id,
            SubscriptionAddon.addon_type == "api_access",
            SubscriptionAddon.active.is_(True),
        )
    )
    return addon.scalar_one_or_none() is not None
```

**API key limit by source**:
```python
API_KEY_LIMITS = {
    "pro": 10,
    "custom": None,  # unlimited
    "payg_addon": 5,
}
```

**Paystack**: Create `PLAN_PAYG_API_ADDON` plan at ₦16,500/month ($10 × ₦1,650).

**UI** (`templates/api_keys.html`, `templates/settings.html`):
- PAYG users on the API keys page see: "Unlock API access for $10/month → [Subscribe]"
- After subscribing, page refreshes and shows key generation UI

### Acceptance Criteria
- [ ] PAYG users see API add-on upsell on API keys page
- [ ] Subscribing to add-on creates `subscription_addons` record
- [ ] PAYG + add-on users can generate up to 5 API keys
- [ ] Add-on cancellation revokes API keys immediately
- [ ] Admin panel shows add-on status per user
- [ ] Paystack webhook handles add-on subscription events

---

## Feature 4 — Bulk Credit Discount

### What
Users who top up above threshold amounts get bonus credits. Increases average deposit size, reduces Paystack fee frequency (fewer small transactions), and gives users a reason to deposit more at once.

### Tiers
| Deposit Amount | Bonus Credits | Effective Discount |
|---------------|---------------|-------------------|
| $10–$49 | 0% | — |
| $50–$99 | 5% bonus | +$2.50 on $50 |
| $100–$199 | 10% bonus | +$10 on $100 |
| $200+ | 15% bonus | +$30 on $200 |

### Margin check
At 1.8× markup, provider cost is ~$1.46 per $2.63 SMS. Margin is $1.17 (44.5%).
- 5% bonus on $50 = $2.50 extra credits. Cost to platform: $2.50 × ($1.46/$2.63) = **$1.39**
- Net: platform still earns $50 − $1.39 = $48.61 on a $50 deposit. Margin drops from 44.5% to 41.8%.
- Well within acceptable range. The increased deposit size more than compensates.

### Paystack fee impact
Paystack charges 1.5% + ₦100 (~$0.07) per transaction.
- 5 × $10 deposits = 5 × $0.22 fee = **$1.10 in fees**
- 1 × $50 deposit = 1 × $0.82 fee = **$0.82 in fees**
- Bulk discount saves $0.28 in fees per $50 while giving user $2.50 in value — net positive.

### Implementation

**`payment_service.py`** — apply bonus after successful webhook:
```python
BULK_BONUS_TIERS = [
    (200, 0.15),
    (100, 0.10),
    (50, 0.05),
]

def calculate_bonus_credits(amount_usd: float) -> float:
    for threshold, rate in BULK_BONUS_TIERS:
        if amount_usd >= threshold:
            return round(amount_usd * rate, 2)
    return 0.0

# In process_successful_payment():
bonus = calculate_bonus_credits(amount_usd)
if bonus > 0:
    await balance_service.add_credits(
        user_id, bonus, reason="bulk_deposit_bonus", db=db
    )
    await notification_service.send(
        user_id=user_id,
        type="bonus_credits",
        data={"bonus": bonus, "deposit": amount_usd}
    )
```

**UI** (`templates/wallet.html`):
- Show bonus tier table on the top-up page
- Highlight which tier the user's current input amount qualifies for
- Show "You'll receive $X bonus credits" dynamically as user types amount

```javascript
const BONUS_TIERS = [{min: 200, rate: 0.15}, {min: 100, rate: 0.10}, {min: 50, rate: 0.05}];

function getBonusForAmount(amount) {
    for (const tier of BONUS_TIERS) {
        if (amount >= tier.min) return (amount * tier.rate).toFixed(2);
    }
    return 0;
}

amountInput.addEventListener('input', () => {
    const bonus = getBonusForAmount(parseFloat(amountInput.value) || 0);
    bonusDisplay.textContent = bonus > 0 ? `+$${bonus} bonus credits` : '';
});
```

### Acceptance Criteria
- [ ] Bonus credits applied automatically after successful Paystack webhook
- [ ] Bonus transaction recorded separately in transaction history (type: `bonus`)
- [ ] Wallet top-up page shows bonus tier table
- [ ] Bonus amount shown dynamically as user types deposit amount
- [ ] Notification sent when bonus credits are applied
- [ ] Admin panel shows bonus credits separately from purchased credits

---

## Combined Revenue Projection

At 500 users (Month 9 target), assuming:
- 10% of Pro/Custom users switch to annual = 5 users × $250 avg = $1,250 upfront (one-time per user)
- 1,000 verifications/month × 10% reuse offer × 30% conversion = $7.50/month
- 20 PAYG users subscribe to API add-on = $200/month
- 30% of deposits qualify for bulk tier (avg $75 deposit) = increased avg deposit size

**Incremental monthly revenue from these 4 features**: ~$250–$400/month at 500 users
**At 1,000 users**: ~$500–$800/month incremental

These are conservative estimates. The annual plan upfront cash is the biggest single impact — one Pro user switching to annual = $250 vs $25 in the same month.
