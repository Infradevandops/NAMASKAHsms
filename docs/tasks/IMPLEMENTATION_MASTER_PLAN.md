# Implementation Master Plan — Full Platform Activation

**Version**: 1.0  
**Created**: March 2026  
**Status**: 🔴 EXECUTION PENDING  
**Total Effort**: 138 hours (~7 weeks at 20h/week)  
**Goal**: Make every documented feature fully functional and accessible

---

## Current Reality

| Metric | Value |
|--------|-------|
| Backend completion | ~95% |
| Frontend completion | ~60% |
| Admin portal | 85% backend, 60% UI |
| Pricing system | 🔴 Broken (losing money on overage) |
| Subscription billing | 🔴 Not implemented (no recurring revenue) |
| Features invisible to users | 40% of backend capabilities |

**Bottom Line**: The platform has strong backend infrastructure but is leaking money, hiding features from users, and missing critical admin tooling.

---

## Phase Overview

| Phase | Focus | Duration | Hours | Priority |
|-------|-------|----------|-------|----------|
| **1** | Critical Fixes & UI Gaps | 1 week | 20h | 🔴 CRITICAL |
| **2** | Admin Portal Completion | 1 week | 22h | 🟡 HIGH |
| **3** | Pricing System Overhaul | 2 weeks | 40h | 🔴 CRITICAL |
| **4** | Subscription Billing & Tier Redesign | 2 weeks | 32h | 🔴 CRITICAL |
| **5** | Stability & Growth | 1 week | 24h | 🟡 HIGH |
| | **TOTAL** | **7 weeks** | **138h** | |

---

## Phase 1: Critical Fixes & UI Gaps (20 hours)

**Goal**: Expose existing backend features to users, unlock Pro tier value.

### Deliverables

| # | Task | Files | Hours | Acceptance Criteria |
|---|------|-------|-------|---------------------|
| 1.1 | Pricing Template Switcher | `alembic/versions/pricing_templates_v2_promo.py`, `static/js/admin/pricing.js`, `templates/admin/pricing_templates.html`, `app/api/admin/pricing_control.py` | 4h | Admin can switch between 3 templates (Standard ✅, Promotional 50% Off, Holiday Special) with one click + confirmation |
| 1.2 | Verification Presets UI | `templates/verify_modern.html`, `static/js/presets.js` | 4h | Pro users can save/load/delete up to 10 presets; quick-launch from dropdown |
| 1.3 | Affiliate Program (functional) | `templates/affiliate_program.html` | 5h | Users can apply for affiliate program (referral/reseller/enterprise); status tracking works |
| 1.4 | User Preferences UI | `templates/settings.html` | 3h | Users can set language (10 options) and currency (10 options); persists on refresh |
| 1.5 | Delete + Rollback API endpoints | `app/api/admin/pricing_control.py` | 1h | `DELETE /templates/{id}` and `POST /pricing/rollback` endpoints functional |
| 1.6 | Seed promo templates | `alembic/versions/pricing_templates_v2_promo.py` | 1h | "Promotional 50% Off" and "Holiday Special" exist in DB with correct tier pricing |
| 1.7 | Fix API Keys endpoint mismatch | `templates/api_keys.html` | 2h | Frontend calls `/api/keys` (not `/api/auth/api-keys`); generate/revoke/rotate all work |

### Phase 1 Exit Criteria
- [ ] All 3 pricing templates visible and switchable from admin
- [ ] Pro users can save and use verification presets
- [ ] Affiliate application form submits successfully
- [ ] Language/currency preferences save and persist
- [ ] API keys fully functional for Pro+ users

---

## Phase 2: Admin Portal Completion (22 hours)

**Goal**: Admin portal reaches institutional grade — full visibility into platform operations.

### Deliverables

| # | Task | Files | Hours | Acceptance Criteria |
|---|------|-------|-------|---------------------|
| 2.1 | Live Provider Prices table | `templates/admin/pricing_live.html` | 4h | Table shows all TextVerified services with provider cost, platform price, markup %, change indicator; auto-refresh 5min; CSV export |
| 2.2 | Price History viewer | `templates/admin/pricing_history.html` | 4h | Chart.js line chart per service; 7/30/90 day range; price change alerts list |
| 2.3 | Audit & Compliance UI | `templates/admin/audit.html` | 8h | Audit log viewer with filtering (user, action, date); compliance dashboard; export |
| 2.4 | Financial Intelligence viz | `templates/admin/dashboard.html` | 4h | Enhanced charts: margin audit, load heatmap, vitality metrics with proper visualizations |
| 2.5 | KYC Management polish | `templates/admin/kyc.html` | 6h | Document viewer, approval/rejection workflow, AML screening results display |

### Dependencies
- Phase 1.1 (pricing templates) should be done first for 2.1/2.2 to make sense

### Phase 2 Exit Criteria
- [ ] Admin can view live prices for all services with one click
- [ ] Price history charts render correctly with date range selection
- [ ] Audit logs searchable and exportable
- [ ] Financial dashboard shows margin health at a glance
- [ ] KYC documents viewable and actionable from admin

---

## Phase 3: Pricing System Overhaul (40 hours)

**Goal**: Stop losing money. Connect real provider prices to billing. Fix the price disconnect.

### Problem Statement

```
CURRENT (BROKEN):
- Display price: TextVerified API × 1.8x markup → shown to user
- Charged price: Hardcoded $2.50 base → actually billed
- Overage: Pro user charged $0.30 for SMS that costs $1.50 from provider
- Result: Platform LOSES $1.20 per overage SMS
```

### Deliverables

| # | Task | Files | Hours | Acceptance Criteria |
|---|------|-------|-------|---------------------|
| 3.1 | Connect provider prices to billing | `app/services/pricing_calculator.py`, `app/services/provider_pricing_service.py` (NEW) | 8h | `calculate_sms_cost()` uses live TextVerified price (cached 1h) instead of hardcoded $2.50; fallback to cache if API fails |
| 3.2 | Fix overage pricing | `app/services/quota_service.py`, `app/services/pricing_calculator.py` | 8h | Overage charges full price (provider cost × tier markup), NOT arbitrary $0.30/$0.20 rates; platform never loses money on any SMS |
| 3.3 | Unified balance system | `app/models/user.py`, `app/services/auth_service.py`, migration | 8h | Remove `bonus_sms_balance`; migrate existing bonus to credits; Freemium users get $2.50 credits on signup; all tiers use single `credits` field |
| 3.4 | Database-only tier config | `app/services/tier_config.py`, migration | 4h | Remove hardcoded fallback config; all tier data from `subscription_tiers` table only; error if DB missing (no silent fallback drift) |
| 3.5 | Dynamic markup service | `app/services/dynamic_markup_service.py` (NEW) | 12h | Tier-aware markup (Freemium 2.0x, PAYG 1.8x, Pro 1.5x, Custom 1.3x); volume discount (up to 30%); minimum 1.2x floor; admin-configurable |

### Critical Financial Impact

| Scenario | Before (broken) | After (fixed) |
|----------|-----------------|---------------|
| Pro user, Telegram overage | Charge $0.30, cost $1.50 = **-$1.20 loss** | Charge $2.25 (1.5x), cost $1.50 = **+$0.75 profit** |
| Custom user, WhatsApp overage | Charge $0.20, cost $2.00 = **-$1.80 loss** | Charge $2.60 (1.3x), cost $2.00 = **+$0.60 profit** |
| Freemium user can't use added credits | Lost conversion | User adds $10, can buy SMS immediately |

### Phase 3 Exit Criteria
- [ ] Displayed price === charged price (no disconnect)
- [ ] Platform profit margin positive on EVERY SMS (including overage)
- [ ] Freemium users can add credits and use them immediately
- [ ] No hardcoded tier config fallback exists
- [ ] Dynamic markup applies per-tier correctly
- [ ] All existing users migrated without balance loss

---

## Phase 4: Subscription Billing & Tier Redesign (32 hours)

**Goal**: Enable recurring revenue. Pro/Custom tiers actually charge monthly fees.

### Problem Statement

```
CURRENT (BROKEN):
- Pro tier: $25/month documented, $0/month collected
- Custom tier: $35/month documented, $0/month collected
- No auto-renewal, no payment failure handling
- Tier expiry is manual
- Result: $0 recurring revenue from subscriptions
```

### Deliverables

| # | Task | Files | Hours | Acceptance Criteria |
|---|------|-------|-------|---------------------|
| 4.1 | Subscription billing service | `app/services/subscription_billing_service.py` (NEW) | 12h | Paystack recurring charges on `next_billing_date`; auto-adds included credits on renewal; generates invoice record; sends confirmation email |
| 4.2 | Payment failure handling | `app/services/subscription_billing_service.py` | 8h | 3-day grace period on failure; email notification on failure; auto-downgrade to Freemium after grace; reactivation flow when user updates payment |
| 4.3 | Tier redesign + migration | `app/services/tier_config.py`, `app/models/user.py`, migration | 12h | New structure: Free ($0, $2.50 credits, 2.0x), Starter ($0, $0, 1.8x), Pro ($25, $30 credits, 1.5x), Business ($99, $150 credits, 1.3x); included credits replace quota; existing users mapped to equivalent new tier |

### New Tier Structure

| Tier | Monthly Fee | Included Credits | Markup | Key Features |
|------|-------------|------------------|--------|--------------|
| **Free** | $0 | $2.50 (signup) | 2.0x | Basic SMS, no filters |
| **Starter** | $0 | $0 | 1.8x | Area code + carrier filters |
| **Pro** | $25 | $30 | 1.5x | API keys, webhooks, presets, priority |
| **Business** | $99 | $150 | 1.3x | Dedicated support, SLA, unlimited keys |

### Database Changes

```sql
-- New fields on users table
ALTER TABLE users ADD COLUMN payment_authorization VARCHAR(255);
ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'active';
ALTER TABLE users ADD COLUMN payment_failed_at TIMESTAMP;
ALTER TABLE users ADD COLUMN next_billing_date TIMESTAMP;

-- Update subscription_tiers table
ALTER TABLE subscription_tiers ADD COLUMN included_credits DECIMAL(10, 2) DEFAULT 0;
ALTER TABLE subscription_tiers ADD COLUMN markup_multiplier DECIMAL(5, 2) DEFAULT 1.8;
ALTER TABLE subscription_tiers DROP COLUMN overage_rate;
```

### Phase 4 Exit Criteria
- [ ] Pro users charged $25/month automatically via Paystack
- [ ] Business users charged $99/month automatically
- [ ] Failed payments trigger email + 3-day grace + auto-downgrade
- [ ] Included credits added on each successful renewal
- [ ] Existing users migrated to new tier names without disruption
- [ ] Subscription status visible in admin portal

---

## Phase 5: Stability & Growth (24 hours)

**Goal**: Production hardening, load testing, and first growth feature (SDK).

### Deliverables

| # | Task | Files | Hours | Acceptance Criteria |
|---|------|-------|-------|---------------------|
| 5.1 | Voice verification stability | Load test scripts, `app/api/verification/purchase_endpoints.py` | 8h | 100 concurrent voice verifications pass; area code mandatory (validated backend); success rate tracked; error rate < 1% |
| 5.2 | Rental services edge cases | Test scripts | 4h | Cancel-after-purchase works; extend-expired rejected; multiple extends work; concurrent message retrieval safe |
| 5.3 | Python SDK | `sdks/python/` (NEW package) | 8h | PyPI-ready package; covers auth, verify, wallet, keys endpoints; async support; type hints; 90%+ test coverage |
| 5.4 | Rate limiting v2 | `app/middleware/rate_limiting.py` | 4h | Tier-based limits (Free: 10/min, Starter: 30/min, Pro: 100/min, Business: 500/min); Redis token bucket; `X-RateLimit-*` headers; admin override |

### Phase 5 Exit Criteria
- [ ] Voice verification handles 100 concurrent requests without failure
- [ ] Rental edge cases all pass (cancel, extend, concurrent)
- [ ] Python SDK installable via pip, all endpoints covered
- [ ] Rate limiting enforced per-tier with proper headers
- [ ] Zero critical errors in 48-hour soak test

---

## Execution Order & Dependencies

```
Phase 1 ──→ Phase 2 ──→ Phase 5
                ↓
Phase 3 ──→ Phase 4
```

- **Phase 1 → 2**: Admin UI completion builds on Phase 1 pricing fixes
- **Phase 3 → 4**: Subscription billing requires fixed pricing system first
- **Phase 5**: Can run in parallel with Phase 4 (independent)
- **Phase 3 is the financial emergency** — consider starting it alongside Phase 1

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 3 migration breaks existing user balances | 🔴 Critical | Run migration on staging first; backup all user credits before migration; rollback script ready |
| Paystack recurring billing fails silently | 🔴 Critical | Webhook verification; daily reconciliation job; admin alert on missed charges |
| Dynamic markup prices users out | 🟡 High | A/B test new markup vs old; monitor conversion rate; admin override capability |
| SDK maintenance burden | 🟢 Low | Auto-generate from OpenAPI spec; minimal manual code |
| Rate limiting blocks legitimate users | 🟡 High | Start with generous limits; monitor 429 rates; admin whitelist |

---

## Success Metrics (Post-Implementation)

| Metric | Current | Target |
|--------|---------|--------|
| Features accessible to users | 60% | 100% |
| Platform profit per SMS (overage) | -$1.20 (loss) | +$0.60 (profit) |
| Monthly recurring revenue | $0 | $2,500+ (100 Pro users) |
| Admin portal completeness | 60% UI | 100% |
| Pricing templates switchable | ❌ | ✅ One-click |
| Subscription auto-billing | ❌ | ✅ Paystack recurring |
| Test coverage | 81% | 90%+ |
| Voice verification success | 85-95% | 99%+ |

---

## Source Documents

This plan consolidates findings from:

| Document | What it contributed |
|----------|---------------------|
| `docs/tasks/ADMIN_PROVIDER_PRICING_MANAGEMENT.md` | Phase 1.1, 1.5, 1.6, Phase 2.1, 2.2 |
| `docs/tasks/BACKEND_FRONTEND_GAP_ANALYSIS.md` | Phase 1.2, 1.3, 1.4, 1.7, Phase 5.1, 5.2 |
| `docs/analysis/PRICING_SYSTEM_ANALYSIS.md` | Phase 3 (all), Phase 4 (all) |
| `docs/analysis/ADMIN_FEATURES_GAP_ANALYSIS.md` | Phase 2.3, 2.4, 2.5 |
| `docs/tasks/INSTITUTIONAL_GRADE_ROADMAP.md` | Phase 5.3, 5.4 |
| `docs/CURRENT_STATE.md` | Current reality baseline |

---

## How to Use This Document

1. **Pick a phase** — start with Phase 1 (quickest wins) or Phase 3 (financial emergency)
2. **Work through tasks in order** within each phase
3. **Check acceptance criteria** before marking complete
4. **Update this doc** as tasks complete (change ❌ to ✅)
5. **Review weekly** — adjust hours if estimates were off

---

**Document Owner**: Engineering  
**Last Updated**: March 2026  
**Next Review**: After Phase 1 completion
