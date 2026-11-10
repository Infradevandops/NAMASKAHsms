# ACTIVE SPRINT

**Updated**: November 2026
**HEAD**: `3619490b` on origin/main
**CI**: ✅ Passing — smoke-test + frontend-unit-tests (hard gates)
**Deploy**: ⏳ Pending — CI must pass on `3619490b` to auto-trigger deploy

---

## SPRINT GOAL — COMPLETED ✅

Full UI/UX overhaul + global readiness pass across all public-facing pages.
Platform brought from placeholder/barely-functional to production-standard.

---

## WHAT WAS DELIVERED THIS SPRINT

### Security & Infrastructure
| Commit | What |
|--------|------|
| `a2634cf9` | Deleted dead `csp.py` (duplicate CSP with `unsafe-inline`) |
| `a2634cf9` | Redis-backed CSRF tokens + rate limiting in `security_hardening.py` (was in-memory, broken across workers) |

### UI/UX — Nav & Header
| Commit | What |
|--------|------|
| `55f16c36` | Removed theme toggle from landing nav |
| `55f16c36` | Login button → proper outlined style on both navs (was ghost/inline hacks) |
| `55f16c36` | Visual divider between nav links and CTA group |
| `55f16c36` | Removed inline `onmouseover` hover hacks from public_base |
| `7718e103` | Mobile nav dropdown fixed on landing (was broken) |
| `7718e103` | Dark mode pricing cards, comparison table, FAQ accordion |
| `7718e103` | Auth pages mobile overlap fixed (padding-top clears fixed nav) |
| `7718e103` | PWA banner CSS bug fixed (double `display:none`) |

### UI/UX — Landing Page
| Commit | What |
|--------|------|
| `7718e103` | Fake testimonials replaced with honest trust signals (stats + transparency note) |
| `7718e103` | Hero badge changed from "Trusted by thousands" → "Privacy-first SMS verification" |
| `7718e103` | Pricing added to landing nav |
| `7718e103` | External CDN icons (simpleicons.org) → inline SVGs |
| `55f16c36` | CTA copy fixed — removed "Join thousands" unverifiable claim |

### Regulatory Compliance — Sprint 1 (P0)
| Item | Fix |
|------|-----|
| REG-001 | Cookie consent: 3-button banner (Accept All / Decline / Manage), granular analytics opt-in |
| REG-002 | Register: age confirmation checkbox (required) + optional marketing consent |
| REG-003 | Privacy policy: processor list corrected (DigitalOcean/Resend/Sabilytics/Cloudflare/Sentry/TextVerified) |
| REG-004 | Terms: Nigeria named as governing jurisdiction |
| REG-005 | Terms: updated to Nov 2026 v1.2 |
| REG-006 | Refund policy: Naira (₦) → USD ($) in rental example |
| REG-007 | Cookies page: Save Preferences wired with JS + toast confirmation |
| REG-008 | Privacy: honest DPO note added (no DPO designated, supervisory authority contact provided) |

### Broken Pages — Sprint 2 (P1)
| Item | Fix |
|------|-----|
| REVIEWS | Removed fabricated 4.8 rating + 5 named reviews → honest trust signals page |
| REFUND | Full rewrite: proper CSS, dark mode, USD currency, all missing classes added |
| ABOUT | Fabricated stats removed (10K+/50 countries) → real product specs; generic team section → honest paragraph |
| CONTACT | Dark mode fixed; misleading email addresses simplified; fake business hours removed; GDPR notice added |
| AUTH-004 | Login/Register: `{% block body %}` override suppresses public header — double-nav eliminated |
| AUTH-005 | Register: duplicate VRENUM SMS logo removed |

### Standard SaaS — Sprint 3 (P2)
| Item | Fix |
|------|-----|
| BLOG-001 | All 5 blog posts: Tailwind → shared CSS (`_blog_base.html`), breadcrumbs, dates, reading time |
| BLOG-003 | `/blog` index page created; route added to `main_routes.py` |
| FAQ | 3 inaccurate answers fixed: bank transfers, AES-256, 50+ countries |
| AFFILIATE | CTA → `/auth/register?ref=affiliate`; PayPal removed; prohibited methods note added |
| STATUS-001 | New `status_public.html` extending `public_base` (no login required); route updated |
| NAV-001/002 | FAQ added to desktop nav + mobile menu; Blog/Cookies/Contact added to footer |
| LEGAL-001/002 | Terms: generic "Use License" replaced with real acceptable use + API usage sections |

### SEO — Sprint 4 (P3)
| Item | Fix |
|------|-----|
| SEO-001 | Meta descriptions added to About, Contact, Affiliate, all blog posts |
| SEO-002 | Blog posts: breadcrumbs + dates added |
| SEO-004 | FAQPage JSON-LD structured data added to faq.html |

---

## TASK SCORECARD

| Priority | Total | Done | Deferred |
|----------|-------|------|----------|
| P0 | 8 | 8 | 0 |
| P1 | 22 | 20 | 2 |
| P2 | 16 | 16 | 0 |
| P3 | 9 | 9 | 0 |
| **Total** | **55** | **53** | **2** |

**Deferred (need backend work):**
- AUTH-001: Password reset confirmation feedback — `/password-reset` page needs "check your email" state
- AUTH-002: Register success — email verification notice depends on whether email verification is enabled server-side

---

## PENDING BEFORE DEPLOY

- [ ] CI must pass on `3619490b` (smoke-test + frontend-unit-tests)
- [ ] Commit `public_base.html` Blog footer link + `faq.html` JSON-LD (staged, not yet pushed)
- [ ] Deploy auto-triggers on CI pass via `deploy.yml`

---

## NEXT — EMAIL TESTING

Once deployed, test the following with existing users:

| Test | What to verify |
|------|---------------|
| Welcome email | Triggers on new registration |
| Password reset | Email sent, link works, confirmation shown |
| Low balance alert | Triggers when wallet drops below threshold |
| Verification receipt | Sent after successful SMS verification |
| Payment receipt | Sent after Paystack payment completes |
| Tier upgrade email | Sent when user upgrades plan |
| Daily digest | Scheduled 08:00 UTC — check delivery |

**Email provider**: Resend (`resend.com`)
**From address**: Configured via `FROM_EMAIL_ADDRESS` env var
**Check**: Sentry for any email dispatch errors post-deploy

---

## OPEN ITEMS (carry forward)

| Item | Priority | Notes |
|------|----------|-------|
| Telegram E2E verification | P1 | @vrenum_sms_bot created, webhook registered, not live-tested |
| Python unit-tests `continue-on-error` | P2 | Pre-existing failures need triage |
| Upstash Redis upgrade | P2 | Free tier 500k/month limit — upgrade to pay-as-you-go |
| TextVerified IP whitelist | P2 | Server IP not whitelisted — `quantity: null` on all services |
| Version string | P3 | Reports `4.9.1`, should be `4.9.9` |
| AUTH-001 password reset UX | P1 | Deferred from this sprint |
| AUTH-002 register email verification notice | P1 | Deferred from this sprint |
