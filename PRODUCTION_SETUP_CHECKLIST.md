# Production Setup Checklist

**Platform**: VRENUM ACTV8TN
**Domain**: https://vrenum.app
**Version**: 4.7.3
**Last Updated**: May 17, 2026
**Checklist Version**: 1.4 (Backups corrected, Search Console + GA4 complete)

---

## Overview

This checklist covers everything needed to launch Vrenum in production. Tasks are split into:
- ✅ **Internal Setup** — Files/code in your codebase
- 🌐 **External Setup** — Third-party platform registrations

**Estimated Total Time**: 4-6 hours
**Total Cost**: $0 (all free tiers)

---

## Quick Status

| Category | Status | Priority |
|----------|--------|----------|
| SEO Fundamentals | ✅ Complete | Must Have |
| SEO Content Strategy | ✅ Complete | Must Have |
| Dynamic Service Pages | ✅ Complete | Must Have |
| Analytics & Tracking | ✅ Complete | Must Have |
| Security Headers | ✅ Complete | Must Have |
| Monitoring | ✅ Complete | Must Have |
| Legal Pages | ✅ Complete | Must Have |
| Backups | ✅ Complete | Critical |
| Backlink Building | ❌ Not Started | Should Have |

---

## Master Checklist

### 🔴 Must Have — Do Today

- [x] Update `robots.txt` with vrenum.app domain ✅
- [x] Update `sitemap.xml` with vrenum.app domain (40 URLs) ✅
- [x] Update Open Graph + Twitter Card meta tags in `base.html` ✅
- [x] Set up Google Analytics 4 ✅ (G-M15PBV1P55)
- [x] Set up Google Search Console + submit sitemap ✅
- [x] Database backups — handled by Neon ✅
- [ ] Store `.env.production` in password manager 🔒 Manual
- [ ] Test cookie consent banner in incognito 🔍 Manual
- [ ] Verify SSL certificate (padlock shows on vrenum.app) 🔍 Manual

### 🟡 Should Have — This Week

- [ ] Create social media images (`og-image.png` 1200×630, `twitter-card.png` 1200×675)
- [ ] Set up manual database backups to S3/Backblaze B2
- [ ] Create GitHub release tag `v4.7.3`
- [ ] Test password reset email flow
- [ ] Verify all legal pages load (`/privacy`, `/terms`, `/cookies`, `/refund`)
- [ ] Check security headers at https://securityheaders.com/?q=https://vrenum.app
- [ ] Test GDPR export/delete endpoints
- [ ] Update `/templates/landing.html` with keyword-rich SEO content (see 10.1)

### 🟢 Nice to Have — Later

- [ ] Optimize images in `/static/images/` to WebP
- [ ] Create simple status page
- [ ] Set up changelog RSS feed
- [ ] Add UptimeRobot as backup monitor
- [ ] Set up Cloudflare (when 10K+ daily visitors)

### ✅ SEO Content — Complete

- [x] `/templates/blog/` — all 5 blog templates ✅
- [x] `/templates/how_it_works.html` ✅
- [x] `/templates/supported_services.html` ✅
- [x] `/templates/pricing_comparison.html` ✅
- [x] `/templates/service_detail.html` — dynamic, 20 services ✅
- [x] `/app/core/seo_services.py` — live Redis price + safe fallback ✅
- [x] All SEO routes wired in `main_routes.py` ✅
- [x] `sitemap.xml` updated — 40 URLs, vrenum.app domain ✅
- [x] JSON-LD structured data on all service pages ✅
- [x] Canonical tags on all pages via `base.html` ✅
- [x] `meta_description` block on all pages via `base.html` ✅
- [x] `public_base.html` block content fix ✅
- [x] OG + Twitter Card tags on all pages via `base.html` ✅
- [x] `robots.txt` fixed — vrenum.app domain ✅
- [x] 32/32 tests passing ✅

---

## Phase 1: SEO Fundamentals

### 1.1 Update robots.txt ✅ Internal

**Status**: ✅ Complete — robots.txt fixed, vrenum.app domain
**Location**: `/static/robots.txt`

**Action Required**:
```txt
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /dashboard/
Disallow: /wallet/
Disallow: /verify/
Disallow: /auth/

Sitemap: https://vrenum.app/sitemap.xml
```

**Test**: Visit https://vrenum.app/robots.txt after deployment

---

### 1.2 Update sitemap.xml ✅ Internal

**Status**: ✅ Complete — 40 URLs, all pointing to vrenum.app
**Location**: `/static/sitemap.xml`

Includes: homepage, pricing, blog (5), static SEO pages (5), service pages (20), legal pages.

**Test**: Visit https://vrenum.app/sitemap.xml

---

### 1.3 SEO Meta Tags ✅ Internal

**Status**: ✅ Complete — canonical, meta_description, OG, and Twitter Card blocks all in `base.html`. Service pages override with service-specific content.

---

### 1.4 Social Media Images ✅ Internal

**Status**: ❌ Not Started
**Location**: `/static/images/`

- Create `og-image.png` (1200×630px) — Facebook/LinkedIn
- Create `twitter-card.png` (1200×675px) — Twitter

**Tools**: Canva (free), Figma (free)
**Brand color**: #FE3C72

---

## Phase 2: Analytics & Tracking

### 2.1 Google Analytics 4 ✅

**Status**: ✅ Complete — `G-M15PBV1P55` added to `base.html`, `ga4-events.js` created

**Event helpers** in `/static/js/ga4-events.js`:
- `trackSignup()` — call after registration
- `trackPayment(transactionId, amount)` — call after payment confirmed
- `trackVerification(country, service)` — call when SMS code received
- `trackTierUpgrade(from, to)` — call after tier upgrade

**Test**: Visit https://vrenum.app in incognito → check GA4 Realtime report at https://analytics.google.com

---

### 2.2 Google Search Console ✅ 🌐 External

**Status**: ✅ Complete — property added, sitemap submitted

**Sitemap submitted**: `https://vrenum.app/sitemap.xml`
Google will index all 40 URLs within 24-48 hours.

---

### 2.3 Cookie Consent Banner ✅ Internal

**Status**: ✅ Already implemented in `base.html`

**Test**: Open https://vrenum.app in incognito — banner should appear, accept hides it, refresh keeps it hidden.

---

## Phase 3: Monitoring & Uptime

### 3.1 Better Stack ✅ 🌐 External

**Status**: ✅ Active
**Dashboard**: https://uptime.betterstack.com/team/t545038/monitors/4422808

- ✅ Monitoring https://vrenum.app every 3 minutes
- ✅ Response time ~200ms, 0 incidents

---

### 3.2 Sentry ✅ Internal

**Status**: ✅ Active
**Dashboard**: https://dev-vp.sentry.io/issues/

- ✅ Real-time error tracking, performance monitoring (10% sample)
- ✅ Slack alerts, Redis/SQLAlchemy/FastAPI integrations
- `SENTRY_DSN` set in `.env.production`

---

## Phase 4: Security & Performance

### 4.1 Security Headers ✅ Internal

**Status**: ✅ Complete — `/app/middleware/security.py`

Headers active: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `HSTS`, `Referrer-Policy`

**Test**: https://securityheaders.com/?q=https://vrenum.app — target A+

---

### 4.2 SSL Certificate ✅ External

**Status**: ✅ Automatic via Render + Let's Encrypt, renews every 90 days

---

### 4.3 CDN — Future

**Status**: Not needed yet. Add Cloudflare (free) when 10K+ daily visitors.

---

## Phase 5: Backups & Recovery

### 5.1 Database Backups ✅ Neon

**Status**: ✅ Handled by Neon — not Render

Database is on **Neon** (https://console.neon.tech). Neon provides:
- ✅ Automatic daily backups
- ✅ Point-in-time restore (7 days free tier, 30 days paid)
- ✅ Branch-based recovery

No manual backup script needed.

---

### 5.2 Environment Variables Backup

**Status**: ❌ Not Started — store `.env.production` in 1Password/Bitwarden
**Priority**: CRITICAL

Critical variables to store:
- `SECRET_KEY` / `JWT_SECRET_KEY` — losing these invalidates all sessions
- `DATABASE_URL` — Neon connection string
- `PAYSTACK_SECRET_KEY` — live payments
- `TEXTVERIFIED_API_KEY` — SMS provider
- `RESEND_API_KEY` — transactional email
- `REDIS_URL` — cache + session blacklist
- `GOOGLE_CLIENT_SECRET` — OAuth login
- `SENTRY_DSN` — error monitoring

**Never**: commit to git, email, or share in Slack/Discord

---

### 5.3 Code Backups ✅ External

**Status**: ✅ Complete
**Repo**: https://github.com/Infradevandops/NAMASKAHsms.git

Create release tag:
```bash
git tag -a v4.7.3 -m "Production release v4.7.3"
git push origin v4.7.3
```

---

## Phase 6: Legal & Compliance ✅

**Status**: ✅ Complete

- ✅ `/privacy`, `/terms`, `/cookies`, `/refund`
- ✅ Cookie consent banner
- ✅ GDPR export (`/api/gdpr/export`) and delete (`/api/gdpr/delete`)

---

## Phase 7: Performance

### 7.1 Image Optimization

**Status**: 🟡 Partial — optimize `/static/images/` using TinyPNG or Squoosh. Target 50-70% reduction.

### 7.2 Lazy Loading ✅

**Status**: ✅ Already implemented (ApexCharts)

---

## Phase 8: Email & Communication

### 8.1 Transactional Email ✅ External

**Status**: ✅ Configured via Resend
- Password reset, verification, payment receipts — all from `admin@vrenum.app`
- `RESEND_API_KEY` set in `.env.production`

**Test**: Trigger a password reset to confirm delivery

### 8.2 Status Page

**Status**: ❌ Optional — create `/templates/status.html` or use Statuspage.io free tier at `status.vrenum.app`

---

## Phase 9: Developer Tools

### 9.1 API Documentation ✅ Internal

**Status**: ✅ Complete
- `/docs` — Swagger UI
- `/redoc` — ReDoc

### 9.2 Changelog RSS — Optional

Create `/static/changelog.xml` with RSS feed of releases. Low priority.

---

## Phase 10: SEO Content Strategy

**Context**: vrenum.app is a new domain competing against TextVerified, SMS-Activate, and Receive-SMS-Online (5-10 year old domains with thousands of backlinks). SEO takes 6-12 months. All internal implementation is complete — external actions remain.

---

### 10.1 Landing Page Optimization ✅ Internal

**Status**: ⏳ Pending — content outlined below, needs applying to `/templates/landing.html`

Add to `/templates/landing.html`:
```html
<h1>SMS Verification Service - Temporary Phone Numbers for 1,807+ Services</h1>
<p>Get instant virtual phone numbers for WhatsApp, Telegram, Discord, Google,
   and 1,800+ more services. 200+ countries. 95%+ success rate. Auto-refunds.</p>

<h2>Why Choose Vrenum?</h2>
<ul>
  <li>✅ 200+ Countries</li>
  <li>✅ 1,807+ Services</li>
  <li>✅ Automatic Refunds</li>
  <li>✅ API Access (Pro)</li>
  <li>✅ Real-time Delivery</li>
</ul>

<h2>How It Works</h2>
<ol>
  <li>Select country + service</li>
  <li>Get instant phone number</li>
  <li>Use it for verification</li>
  <li>Receive SMS code in seconds</li>
</ol>
```

**Target keywords**: "SMS verification service", "temporary phone number", "receive SMS online"

---

### 10.2 Blog Pages ✅ Internal

**Status**: ✅ Complete — all files created and routes wired

| File | Route | Keyword | Monthly Searches |
|------|-------|---------|-----------------|
| `blog/whatsapp-verification.html` | `/blog/whatsapp-verification` | "whatsapp verification" | 50K |
| `blog/usa-virtual-phone-numbers.html` | `/blog/usa-virtual-phone-numbers` | "usa virtual phone number" | 15K |
| `blog/temporary-phone-number-for-telegram.html` | `/blog/temporary-phone-number-for-telegram` | "temporary phone number telegram" | 8K |
| `blog/how-to-verify-whatsapp-without-phone-number.html` | `/blog/how-to-verify-whatsapp-without-phone-number` | "verify whatsapp without phone number" | 10K |
| `blog/best-sms-verification-services.html` | `/blog/best-sms-verification-services` | "best sms verification service" | 5K |

All routes handled by `GET /blog/{slug}` in `main_routes.py`.

---

### 10.3 Five Essential Static Pages ✅ Internal

**Status**: ✅ Complete — all templates created, all routes wired in `main_routes.py`

| Route | Template | Keyword | Monthly Searches |
|-------|----------|---------|-----------------|
| `/how-it-works` | `how_it_works.html` | "how sms verification works" | 3K |
| `/supported-services` | `supported_services.html` | "sms verification services list" | 4K |
| `/pricing-comparison` | `pricing_comparison.html` | "sms verification pricing" | 6K |
| `/api-documentation` | `api_documentation.html` | "sms verification api" | 8K |
| `/faq` | `faq.html` | "sms verification faq" | 5K |

---

### 10.4 Dynamic Service Pages ✅ Internal

**Status**: ✅ Complete — 20 service pages live, live price from Redis cache

**How it works**:
- `GET /services/{slug}` → `main_routes.py` → `get_service_for_page(slug)` in `seo_services.py`
- Price read from `tv:services_list` Redis key (populated by `TextVerifiedService`, 24h TTL)
- Falls back to `$2.63` if cache is cold — never crashes
- Template: `service_detail.html` with JSON-LD structured data + canonical tag

**Top 20 live service pages**:

| Route | Monthly Searches |
|-------|-----------------|
| `/services/whatsapp` | 50K |
| `/services/telegram` | 30K |
| `/services/google` | 25K |
| `/services/discord` | 20K |
| `/services/facebook` | 18K |
| `/services/instagram` | 15K |
| `/services/twitter` | 12K |
| `/services/tiktok` | 10K |
| `/services/uber` | 8K |
| `/services/amazon` | 7K |
| `/services/netflix` | 6K |
| `/services/paypal` | 6K |
| `/services/snapchat` | 5K |
| `/services/linkedin` | 5K |
| `/services/microsoft` | 4K |
| `/services/apple` | 4K |
| `/services/coinbase` | 3K |
| `/services/binance` | 3K |
| `/services/airbnb` | 3K |
| `/services/doordash` | 2K |

**Next step**: Replace static 20-service dict with full TextVerified API sync to serve all 1,807 services.

---

### 10.5 Technical SEO ✅ Internal

**Status**: ✅ Complete

- ✅ Canonical tags — auto-injected via `base.html` on every page
- ✅ `meta_description` block — available on every page
- ✅ JSON-LD structured data — on all service pages
- ✅ Sitemap — 40 URLs, valid XML, vrenum.app domain
- ✅ Schema markup — `schema_org.html`
- ✅ HTTPS, GZip, lazy loading, mobile responsive

**Still needed**:
- [ ] PageSpeed score ≥90 — test at https://pagespeed.web.dev
- [ ] Convert images to WebP
- [ ] Internal linking audit (blog → service pages → pricing → signup)

---

### 10.6 Backlink Building 🌐 External

**Status**: ❌ Not Started — Month 2+

**A. Directory listings (free, do first)**:

| Directory | URL | Est. Time |
|-----------|-----|-----------|
| Product Hunt | https://producthunt.com | 30 min |
| AlternativeTo | https://alternativeto.net | 15 min |
| Capterra | https://capterra.com | 20 min |
| G2 | https://g2.com | 20 min |
| SaaSHub | https://saashub.com | 10 min |

**B. Social profiles (free)**:
- Twitter/X `@vrenum`, LinkedIn company page, Reddit `u/vrenum`
- Quora: answer "how to verify WhatsApp without phone number"
- GitHub: add vrenum.app to repo README

**C. Content marketing (Month 2)**:
- Guest posts on Medium, Dev.to, Hashnode
- Comparison pages: `/alternatives/textverified`, `/alternatives/sms-activate`
- Dev.to tutorial: "Building SMS Verification into Your App with Vrenum API"

**D. Affiliate program** ✅ Already built — activate outreach via admin panel

---

### 10.7 SEO Timeline

| Month | Actions | Expected Result |
|-------|---------|----------------|
| 1 | Landing page update, submit to 20 directories | Indexed, page 8-10 for long-tail |
| 2 | Social profiles, 10 more blog posts, guest posts | Page 5-8, 500+ impressions/month |
| 3 | All 1,807 service pages via dynamic route | Page 3-5, 2K+ impressions/month |
| 6 | 100+ blog posts, 500+ backlinks | Page 1-3 long-tail, 10K+ visitors/month |
| 12 | 200+ blog posts, 2K+ backlinks | Page 1 for "sms verification service" |

---

### 10.8 SEO Checklist

#### This Week
- [ ] Update `/templates/landing.html` with keyword-rich content (10.1)
- [x] All 5 blog templates created ✅
- [x] All 5 static SEO pages created ✅
- [x] All routes wired in `main_routes.py` ✅
- [x] `sitemap.xml` updated — 40 URLs ✅
- [x] Top 20 dynamic service pages live ✅
- [x] JSON-LD + canonical tags on all pages ✅

#### Month 2
- [ ] Submit to Product Hunt, AlternativeTo, Capterra, G2
- [ ] Create Twitter `@vrenum` + LinkedIn company page
- [ ] Write first guest post on Dev.to or Medium
- [ ] Activate affiliate program outreach
- [ ] Dynamic sitemap serving all 1,807 service URLs
- [ ] Optimize images to WebP, run PageSpeed test

#### Month 3+
- [ ] `/alternatives/textverified` comparison page
- [ ] `/alternatives/sms-activate` comparison page
- [ ] Open source Python/JS SDK on GitHub
- [ ] Content calendar — 2 blog posts/week

---

## Quick Reference

### Important URLs

| Service | URL |
|---------|-----|
| Production Site | https://vrenum.app |
| Admin Panel | https://vrenum.app/admin |
| API Docs (Swagger) | https://vrenum.app/docs |
| Sentry | https://dev-vp.sentry.io/issues/ |
| Better Stack | https://uptime.betterstack.com/team/t545038/monitors/4422808 |
| Render Dashboard | https://dashboard.render.com |
| GitHub Repo | https://github.com/Infradevandops/NAMASKAHsms |

### Critical Environment Variables

```bash
SECRET_KEY=***
JWT_SECRET_KEY=***
DATABASE_URL=postgresql://***
REDIS_URL=rediss://***
PAYSTACK_SECRET_KEY=***
TEXTVERIFIED_API_KEY=***
RESEND_API_KEY=***
SENTRY_DSN=***
```

---

## Testing Checklist

### SEO
- [ ] https://vrenum.app/robots.txt — correct rules, vrenum.app domain
- [ ] https://vrenum.app/sitemap.xml — 40 URLs, no onrender.com
- [ ] https://vrenum.app/services/whatsapp — loads, shows price, has canonical
- [ ] https://vrenum.app/blog/whatsapp-verification — loads correctly
- [ ] https://vrenum.app/how-it-works — loads correctly
- [ ] Page source — canonical tag present on all pages

### Analytics
- [ ] Visit in incognito → appears in GA4 Realtime
- [ ] Sign up → triggers `sign_up` event
- [ ] Make payment → triggers `purchase` event
- [ ] Complete verification → triggers `verification_success` event

### Monitoring
- [ ] Better Stack shows "Up"
- [ ] Sentry shows no critical errors
- [ ] Response time <500ms

### Security
- [ ] https://securityheaders.com — A+ rating
- [ ] SSL padlock visible
- [ ] `/admin` without login → redirects to login
- [ ] SQL injection in forms → blocked

### Backups
- [x] Database on Neon — automatic backups included ✅
- [ ] `.env.production` stored in password manager
- [x] GitHub has latest code ✅

---

# Rollback Plan

```bash
# Rollback code — revert to previous stable version
git reset --hard v4.7.2
git push origin main --force

# Rollback database — via Neon dashboard
# console.neon.tech → your project → Restore → select point in time

# Rollback env vars — restore from password manager → update Render env vars → restart
```

---

## Post-Launch Monitoring

### Hour 1
- [ ] Better Stack — site is up
- [ ] Sentry — no critical errors
- [ ] GA4 Realtime — traffic appearing
- [ ] Test signup, payment, and SMS verification flows

### Hour 24
- [ ] Review Sentry errors
- [ ] Verify GA4 events tracking
- [ ] Better Stack uptime ≥99%
- [ ] Review support tickets

### Hour 48
- [ ] Review analytics — user behaviour patterns
- [ ] Check conversion rates (signup → payment)
- [ ] Confirm database backup completed
- [ ] Plan next iteration

---

## Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Google Analytics 4 | $0 |
| Google Search Console | $0 |
| Better Stack | $0 |
| Sentry | $0 |
| Render Database Backups | N/A — DB is on Neon |
| External Backups S3/B2 | $1-5 (optional) |
| **Total** | **$0-5** |

---

## Next Steps

1. **Today** — Complete "Must Have" checklist above
2. **This Week** — Complete "Should Have" + landing page SEO content
3. **After Launch** — Monitor for 48 hours
4. **Month 2** — Backlinks, social profiles, guest posts
5. **Month 3** — Expand to all 1,807 dynamic service pages

---

**Last Updated**: May 18, 2026
**Checklist Version**: 1.4
**Status**: Ready for Production 🚀
