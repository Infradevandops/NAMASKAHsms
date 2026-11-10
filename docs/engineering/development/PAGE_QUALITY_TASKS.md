# Page Quality & Global Readiness Tasks

**Created**: November 2026
**Scope**: All public-facing pages — auth, legal, marketing, blog, support
**Goal**: Bring every page from placeholder/barely-functional to production-standard
**HEAD at creation**: `55f16c36`

---

## PRIORITY LEGEND
- **P0** — Regulatory / legal risk. Must fix before any growth push.
- **P1** — Broken UX or missing critical content. Blocks user trust.
- **P2** — Substandard content or missing standard SaaS page elements.
- **P3** — Polish, SEO, conversion improvements.

---

## STATUS SUMMARY

| ID | Page / Area | Priority | Status |
|----|-------------|----------|--------|
| REG-001 | Cookie consent — no granular controls, no "Manage" link | P0 | ⬜ |
| REG-002 | Register — no explicit marketing consent checkbox | P0 | ⬜ |
| REG-003 | Privacy policy — lists AWS/SendGrid/GA as processors but app uses Resend/DigitalOcean/Sabilytics | P0 | ⬜ |
| REG-004 | Terms — no jurisdiction named, no governing law country | P0 | ⬜ |
| REG-005 | Terms — "Last Updated: May 2026" is stale, no version number | P0 | ⬜ |
| REG-006 | Refund policy — uses "N" (Naira) currency symbol in examples, inconsistent with USD platform | P0 | ⬜ |
| REG-007 | Cookies page — "Save Preferences" button does nothing (no JS handler) | P0 | ⬜ |
| REG-008 | Privacy — no Data Protection Officer contact or EU representative named | P0 | ⬜ |
| AUTH-001 | Login — no "Forgot password?" flow confirmation (link exists but no feedback if email sent) | P1 | ⬜ |
| AUTH-002 | Register — success redirects to /auth/login after 1.5s with no email verification step shown | P1 | ⬜ |
| AUTH-003 | Register — no age confirmation (service requires 18+, no checkbox or notice) | P1 | ⬜ |
| AUTH-004 | Login/Register — public_base header renders behind auth-nav on these pages (two navs stacked) | P1 | ⬜ |
| AUTH-005 | Register — duplicate VRENUM SMS logo (one in auth-nav, one inside auth-container header) | P1 | ⬜ |
| ABOUT-001 | About — stats are fabricated ("10K+ verifications", "50+ countries", "100+ services") — platform is new | P1 | ⬜ |
| ABOUT-002 | About — "Team" section shows generic role cards with no real info — looks like a template | P1 | ⬜ |
| ABOUT-003 | About — CTA says "Join thousands of users" — inconsistent with honesty stance | P1 | ⬜ |
| CONTACT-001 | Contact — all email addresses (business@, security@, legal@) resolve to support@vrenum.app — misleading | P1 | ⬜ |
| CONTACT-002 | Contact — no GDPR notice on contact form (data collected, how used, retention) | P1 | ⬜ |
| CONTACT-003 | Contact — dark mode: contact-info and form-container backgrounds hardcoded white | P1 | ⬜ |
| FAQ-001 | FAQ — "50+ countries" claim in answer — platform is US numbers only currently | P1 | ⬜ |
| FAQ-002 | FAQ — "AES-256 encryption" claim in security section — not verified/documented anywhere | P1 | ⬜ |
| FAQ-003 | FAQ — payment methods answer says "bank transfers" — Paystack card only currently | P1 | ⬜ |
| REVIEWS-001 | Reviews — "4.8 rating based on verified user feedback" with 5 named reviews — fabricated social proof | P1 | ⬜ |
| REVIEWS-002 | Reviews — uses Tailwind classes (mx-auto, px-4, etc.) but public_base doesn't load Tailwind | P1 | ⬜ |
| REVIEWS-003 | Reviews — CTA links to /register (old path), should be /auth/register | P1 | ⬜ |
| REFUND-001 | Refund — uses "N5", "N1.79" (Naira) in rental refund example — wrong currency | P1 | ⬜ |
| REFUND-002 | Refund — no CSS/styling — renders as unstyled HTML inside public_base | P1 | ⬜ |
| REFUND-003 | Refund — references `.legal-container`, `.legal-header`, `.legal-content`, `.success-box`, `.warning-box`, `.info-box` classes that don't exist anywhere | P1 | ⬜ |
| BLOG-001 | Blog pages — use Tailwind utility classes (text-3xl, font-bold, etc.) but public_base doesn't load Tailwind — renders unstyled | P1 | ⬜ |
| BLOG-002 | Blog — all 5 blog posts are thin SEO pages with minimal content, no author, no date, no schema markup | P2 | ⬜ |
| BLOG-003 | Blog — no blog index page (/blog) — posts exist but are unreachable from nav | P2 | ⬜ |
| AFFILIATE-001 | Affiliate — "Apply Now" links to /dashboard — unauthenticated users get redirected to login with no context | P2 | ⬜ |
| AFFILIATE-002 | Affiliate — commission payout method says "bank transfer or PayPal" — no PayPal integration exists | P2 | ⬜ |
| AFFILIATE-003 | Affiliate — no terms/conditions for the affiliate program linked | P2 | ⬜ |
| STATUS-001 | Status page — extends dashboard_base (requires login) — should be a public page | P2 | ⬜ |
| STATUS-002 | Status page — shows mock data always, no real /api/providers/health endpoint wired | P2 | ⬜ |
| LEGAL-001 | Terms — section 2 "Use License" reads like a generic website template, not an SMS API service ToS | P2 | ⬜ |
| LEGAL-002 | Terms — no section on API usage limits, rate limits, or acceptable use for API customers | P2 | ⬜ |
| LEGAL-003 | Terms — no section on account suspension criteria beyond "breach of terms" | P2 | ⬜ |
| LEGAL-004 | Privacy — third-party list (AWS, SendGrid, GA) doesn't match actual stack (DigitalOcean, Resend, Sabilytics, Cloudflare, Sentry) | P2 | ⬜ |
| LEGAL-005 | Cookies — "Save Preferences" button has no JS — clicking it does nothing | P2 | ⬜ |
| LEGAL-006 | Cookies — dark mode: all sections hardcoded bg-white, border-gray-200 — invisible in dark mode | P2 | ⬜ |
| COOKIES-001 | Cookie consent banner — only Accept/Decline, no "Manage preferences" link to /cookies | P2 | ⬜ |
| COOKIES-002 | Cookie consent — no granular per-category consent (essential always on, analytics/marketing opt-in) | P2 | ⬜ |
| NAV-001 | public_base — mobile menu missing FAQ and Services links (landing has them, public_base doesn't) | P2 | ⬜ |
| NAV-002 | public_base footer — missing FAQ, Cookies, Blog links | P2 | ⬜ |
| NAV-003 | Landing nav — mobile dropdown missing Pricing link (only Services, How It Works, API, FAQ) | P2 | ⬜ |
| PRICING-001 | Pricing — dark mode: tier-card-popular uses background:#37352F (dark) in light mode — contrast issue on popular card text | P2 | ⬜ |
| PRICING-002 | Pricing — sticky mobile CTA has `display:none` inline but media query sets `display:flex !important` — works but fragile | P3 | ⬜ |
| SEO-001 | About, Contact, Affiliate — missing `<meta name="description">` blocks | P3 | ⬜ |
| SEO-002 | Blog posts — no structured data (Article schema, breadcrumbs) | P3 | ⬜ |
| SEO-003 | Reviews page — no AggregateRating schema markup | P3 | ⬜ |
| SEO-004 | FAQ page — no FAQPage schema markup | P3 | ⬜ |
| CONTENT-001 | About — mission section is generic ("increasingly connected world") — needs specific, honest positioning | P3 | ⬜ |
| CONTENT-002 | Contact — "Business Hours: Mon-Fri 9AM-6PM UTC" — if not staffed, remove or change to async-only | P3 | ⬜ |
| CONTENT-003 | Landing — hero stats (1,800+, <30s, 100%) are product claims, not user stats — fine but should be labelled as product specs | P3 | ⬜ |

---

## DETAILED FINDINGS

### P0 — Regulatory / Legal Risk

#### REG-001 — Cookie consent has no granular controls
**File**: `templates/includes/cookie_consent.html`
**Issue**: Banner shows Accept/Decline only. GDPR Article 7 requires granular consent per category (analytics, marketing). Accepting all or nothing is not compliant for EU users.
**Fix**: Add "Manage" button linking to `/cookies`. Wire the cookies page checkboxes to actually save per-category consent to localStorage and conditionally load analytics.

#### REG-002 — No marketing consent on register
**File**: `templates/register.html`
**Issue**: Terms checkbox covers ToS + Privacy Policy but not marketing emails. Sending any promotional email to registered users without explicit opt-in violates CAN-SPAM (US) and GDPR (EU).
**Fix**: Add optional `[ ] I'd like to receive product updates and tips by email` checkbox. Default unchecked. Pass `marketing_consent: bool` to `/api/auth/register`.

#### REG-003 — Privacy policy lists wrong data processors
**File**: `templates/privacy.html` section 7
**Issue**: Lists AWS, SendGrid, Google Analytics as processors. Actual stack: DigitalOcean (hosting), Resend (email), Sabilytics (analytics), Cloudflare (CDN/bot protection), Sentry (error tracking), Paystack (payments).
**Fix**: Replace section 7 with accurate processor list.

#### REG-004 — Terms has no governing jurisdiction
**File**: `templates/terms.html` section 8
**Issue**: "governed by the laws of the jurisdiction in which vrenum.app operates" — this is legally meaningless. Must name a specific country/state.
**Fix**: Name the actual jurisdiction (e.g., "Federal Republic of Nigeria" or wherever the entity is registered).

#### REG-005 — Terms date is stale
**File**: `templates/terms.html`
**Issue**: "Last Updated: May 2026" — it's November 2026. Users checking the date will see a 6-month-old document.
**Fix**: Update to current date. Add version number (e.g., v1.2).

#### REG-006 / REFUND-001 — Naira currency in USD platform
**File**: `templates/refund.html` section 4.2
**Issue**: Example uses "N5", "N1.79" (Nigerian Naira symbol). Platform prices in USD. Confusing and potentially misleading.
**Fix**: Replace with USD example using "$" symbol.

#### REG-007 / LEGAL-005 — Cookies "Save Preferences" does nothing
**File**: `templates/cookies.html`
**Issue**: The "Save Preferences" button has `onmouseover/onmouseout` inline styles but no `onclick` handler. Clicking it does nothing. Users who try to manage their cookie preferences get no feedback.
**Fix**: Add JS that reads the checkbox states and saves to localStorage as `cookie_prefs: {analytics: bool, marketing: bool}`, then shows a success toast.

#### REG-008 — No DPO contact in Privacy Policy
**File**: `templates/privacy.html`
**Issue**: GDPR Article 37 requires a Data Protection Officer contact for organisations processing personal data at scale. Section 12 only lists privacy@vrenum.app with no DPO designation.
**Fix**: Either designate a DPO and name them, or add a note that a DPO has not been designated (acceptable for small organisations) and provide the supervisory authority contact.

---

### P1 — Broken UX / Missing Critical Content

#### AUTH-001 — Password reset has no confirmation feedback
**File**: `templates/login.html`
**Issue**: "Forgot password?" links to `/password-reset` but there's no visible confirmation that an email was sent. Users don't know if it worked.
**Fix**: The password-reset page should show a clear "Check your email" confirmation state after submission.

#### AUTH-002 — Register success skips email verification notice
**File**: `templates/register.html`
**Issue**: On success, shows "Account created successfully! Please log in." and redirects after 1.5s. If email verification is required, users don't know. If it's not required, the message is fine but abrupt.
**Fix**: If email verification is sent, show "Check your email to verify your account before logging in." If not required, current flow is acceptable but add a 2s delay minimum.

#### AUTH-003 — No age gate on registration
**File**: `templates/register.html`
**Issue**: No age confirmation. Privacy policy section 9 says "not intended for children under 13" but there's no checkbox or notice on the form. COPPA (US) and GDPR (EU) require this.
**Fix**: Add `[ ] I confirm I am 13 years of age or older` checkbox, required. Or add a note "By creating an account you confirm you are 13 or older."

#### AUTH-004 — Two navs render on login/register pages
**File**: `templates/login.html`, `templates/register.html`
**Issue**: These pages extend `public_base.html` which renders the public header. They also render their own `.auth-nav`. On desktop both navs are visible — the public header sits above the auth-nav. On mobile the public header hamburger button appears above the auth-nav.
**Fix**: Override `{% block body %}` in login/register to suppress the public-layout wrapper, or add `display:none` to `.public-header` on auth pages via a body class.

#### AUTH-005 — Duplicate logo on register page
**File**: `templates/register.html`
**Issue**: The auth-nav already shows "VRENUM SMS" brand pill. Inside the auth-container there's another `<a>` with the same brand pill above the h1. Two identical logos stacked.
**Fix**: Remove the redundant logo inside the auth-container. The auth-nav brand is sufficient.

#### ABOUT-001 — Fabricated stats
**File**: `templates/about.html`
**Issue**: "10K+ Verifications Completed", "50+ Countries Supported", "100+ Services Available" — these are placeholder numbers. The platform is new. Showing false stats is the same problem as fake testimonials.
**Fix**: Replace with honest product specs: "1,800+ Supported Services", "US Numbers", "< 30s Average Delivery", "100% Auto-Refund". Remove the "Our Impact" stats grid or replace with product capability stats.

#### ABOUT-002 — Generic team section
**File**: `templates/about.html`
**Issue**: Four cards: "Engineering Team", "Security Team", "Operations Team", "Support Team" — each with a one-line description. This is a template placeholder. Every SaaS has this. It adds no trust.
**Fix**: Either remove the team section entirely (honest for a small team) or replace with a single honest paragraph: "Vrenum is built by a small team of developers focused on privacy and reliability. We don't have a large org chart — we have a working product."

#### ABOUT-003 — "Join thousands of users" in CTA
**File**: `templates/about.html`
**Issue**: CTA section says "Join thousands of users who've taken back control of their phone number." Same unverifiable claim we removed from landing.
**Fix**: Replace with "Start protecting your privacy today. Free to try, no credit card required."

#### CONTACT-001 — All contact emails are the same address
**File**: `templates/contact.html`
**Issue**: business@vrenum.app, security@vrenum.app, legal@vrenum.app all show as separate contacts but the href is `support@vrenum.app` for all three. Users who email business@ or legal@ expecting a different team will get the same inbox — fine operationally, but the display is misleading.
**Fix**: Either set up email aliases that actually route differently, or simplify to one contact email with a category selector (which the form already has).

#### CONTACT-002 — No GDPR notice on contact form
**File**: `templates/contact.html`
**Issue**: Contact form collects name, email, message. No notice about how this data is used, stored, or who to contact for deletion. Required under GDPR Article 13.
**Fix**: Add a small note below the submit button: "Your message and contact details are stored securely and used only to respond to your inquiry. See our [Privacy Policy](/privacy)."

#### CONTACT-003 — Contact page dark mode broken
**File**: `templates/contact.html`
**Issue**: `.contact-info` and `.form-container` have `background: white` and `border: 2px solid #e5e7eb` hardcoded. In dark mode these are white boxes on a dark background — unreadable.
**Fix**: Add dark mode overrides for both containers.

#### FAQ-001 — "50+ countries" claim
**File**: `templates/faq.html`
**Issue**: Security section answer says "AES-256 encryption, GDPR compliant, regular security audits. Data stored in secure redundant data centers." — these are aspirational claims, not verified facts for a new platform.
**Fix**: Rewrite to factual: "Data is stored on DigitalOcean infrastructure. Passwords are hashed with bcrypt. All connections use TLS. We are working toward formal security certification."

#### REVIEWS-001 — Fabricated rating and reviews
**File**: `templates/reviews.html`
**Issue**: "4.8 rating based on verified user feedback" with 5 named reviews (Alex M., Tunde O., Sarah K., Dev R., Maria L.) — these are fabricated. Same problem as the testimonials we already fixed on landing.
**Fix**: Replace with the same honest approach used on landing — product stats and a transparency note. Remove the 4.8 rating. If real reviews exist, show them. If not, say so.

#### REVIEWS-002 — Tailwind classes with no Tailwind
**File**: `templates/reviews.html`
**Issue**: Uses `container mx-auto px-4 py-12 max-w-3xl`, `text-3xl font-bold`, `bg-white border border-gray-200 rounded-xl`, `text-5xl font-bold text-indigo-600`, `space-y-6` etc. `public_base.html` does not load Tailwind. The page renders as unstyled HTML.
**Fix**: Replace Tailwind classes with inline styles or a `<style>` block, consistent with other public pages.

#### REVIEWS-003 — CTA links to wrong path
**File**: `templates/reviews.html`
**Issue**: CTA button links to `/register` — the correct path is `/auth/register`.
**Fix**: Update href.

#### REFUND-002/003 — Refund page has no CSS
**File**: `templates/refund.html`
**Issue**: References `.legal-container`, `.legal-header`, `.legal-content`, `.success-box`, `.warning-box`, `.info-box` CSS classes that don't exist in any stylesheet. The page renders as completely unstyled HTML — raw `<h1>`, `<h2>`, `<ul>` with no visual treatment.
**Fix**: Add a `{% block head_extra %}` with styles matching the terms/privacy page pattern.

#### BLOG-001 — Blog pages use Tailwind, no Tailwind loaded
**File**: `templates/blog/*.html`
**Issue**: All 5 blog posts use Tailwind utility classes (`text-3xl font-bold`, `list-decimal pl-6`, `bg-pink-50 border border-pink-200`, etc.). `public_base.html` doesn't load Tailwind. All blog posts render as unstyled HTML.
**Fix**: Add a `{% block head_extra %}` with minimal styles to each blog post, or add a shared blog CSS file.

---

### P2 — Substandard / Missing Standard Elements

#### BLOG-002 — Blog posts are thin, no metadata
**File**: `templates/blog/*.html`
**Issue**: No author, no publish date, no reading time, no breadcrumb, no related posts. Thin content with minimal value beyond the CTA. Not suitable for indexing.
**Fix**: Add article metadata header (date, reading time), breadcrumb (`Home > Blog > [Title]`), and expand content to 600+ words per post.

#### BLOG-003 — No blog index page
**Issue**: 5 blog posts exist at `/blog/whatsapp-verification`, `/blog/how-to-verify-whatsapp-without-phone-number`, etc. but there's no `/blog` index page. Users and search engines can't discover them.
**Fix**: Create `templates/blog/index.html` listing all posts with title, description, date.

#### AFFILIATE-001 — "Apply Now" sends unauthenticated users to /dashboard
**File**: `templates/affiliate_program.html`
**Issue**: CTA button `href="/dashboard"` — unauthenticated users get redirected to login with no context about why. They lose the affiliate page context.
**Fix**: Link to `/auth/register?ref=affiliate` or show a modal explaining they need an account first.

#### AFFILIATE-002 — PayPal payout claim
**File**: `templates/affiliate_program.html`
**Issue**: FAQ says "Commissions paid monthly on the 15th via bank transfer or PayPal." No PayPal integration exists.
**Fix**: Remove PayPal. State actual payout method (wallet credits or bank transfer via Paystack).

#### AFFILIATE-003 — No affiliate program terms
**File**: `templates/affiliate_program.html`
**Issue**: No link to affiliate-specific terms (prohibited promotion methods, cookie stuffing policy, fraud policy). Standard for any affiliate program.
**Fix**: Add a brief "Program Terms" section or link to a dedicated page.

#### STATUS-001 — Status page requires login
**File**: `templates/status.html`
**Issue**: Extends `dashboard_base.html` — requires authentication. A status page should be publicly accessible so users can check if the service is down before logging in.
**Fix**: Create a public version extending `public_base.html`, or add a public `/status` route that doesn't require auth.

#### STATUS-002 — Status page always shows mock data
**File**: `templates/status.html`
**Issue**: `useMockData()` is called as fallback when `/api/providers/health` fails. The API endpoint may not exist or may require auth. The page always shows "Operational" for everything.
**Fix**: Wire to a real public health endpoint, or at minimum show the actual `/health` endpoint data.

#### NAV-001 — Mobile menu missing links
**File**: `templates/public_base.html`
**Issue**: Desktop nav has: Pricing, About, Affiliates, Contact. Mobile menu has the same. But FAQ and Services are not in either — they're only in the landing page nav. Users on /pricing, /about, /faq etc. can't navigate to FAQ from mobile.
**Fix**: Add FAQ link to both desktop nav and mobile menu in public_base.

#### NAV-002 — Footer missing links
**File**: `templates/public_base.html`
**Issue**: Footer has: Pricing, About, Affiliates, Privacy, Terms, Refund, Status. Missing: FAQ, Cookies, Blog, Contact.
**Fix**: Add FAQ, Cookies, Blog, Contact to footer.

#### LEGAL-001/002/003 — Terms needs SMS/API-specific sections
**File**: `templates/terms.html`
**Issue**: Current terms read like a generic website template (sections 2-6 are boilerplate). Missing: API acceptable use policy, rate limit terms, number rental terms, what constitutes abuse of the verification service.
**Fix**: Add sections: "API Usage", "Acceptable Use of Phone Numbers", "Number Rental Terms", "Suspension and Termination Criteria".

#### LEGAL-004 — Privacy processor list is wrong
**File**: `templates/privacy.html` section 7
**Issue**: Lists AWS, SendGrid, Google Analytics. Actual: DigitalOcean, Resend, Sabilytics, Cloudflare, Sentry, Paystack, TextVerified.
**Fix**: Update section 7 with accurate processor list and links to their privacy policies.

#### COOKIES-001/002 — Cookie consent needs granular controls
**File**: `templates/includes/cookie_consent.html`
**Issue**: Binary Accept/Decline. No "Manage" option. No per-category consent.
**Fix**: Add "Manage preferences" link to /cookies. Wire cookies.html checkboxes to save per-category consent. Only load Sabilytics if analytics consent given.

---

### P3 — Polish / SEO / Conversion

#### SEO-001 — Missing meta descriptions
**Files**: `templates/about.html`, `templates/contact.html`, `templates/affiliate_program.html`
**Fix**: Add `{% block meta_description %}` to each.

#### SEO-002/003/004 — Missing structured data
**Files**: Blog posts, reviews.html, faq.html
**Fix**: Add JSON-LD Article schema to blog posts, AggregateRating to reviews, FAQPage to faq.html.

#### CONTENT-001 — About mission is generic
**File**: `templates/about.html`
**Fix**: Rewrite mission to be specific: what the platform does, who it's for, what makes it different from competitors (real SIM cards, auto-refund, Paystack for African users).

#### CONTENT-002 — Contact business hours claim
**File**: `templates/contact.html`
**Fix**: If not staffed Mon-Fri 9-6 UTC, remove the hours. Replace with "We respond to all inquiries within 24 hours."

---

## EXECUTION ORDER

### Sprint 1 — Regulatory (P0, ~4 hours)
1. REG-003/LEGAL-004: Fix privacy policy processor list
2. REG-004/REG-005: Fix terms jurisdiction + date
3. REG-006/REFUND-001: Fix Naira currency in refund policy
4. REG-007/LEGAL-005: Wire cookies.html Save Preferences button
5. REG-002/AUTH-003: Add marketing consent + age confirmation to register
6. REG-001/COOKIES-001/002: Add "Manage" to cookie banner, wire per-category consent

### Sprint 2 — Broken Pages (P1, ~6 hours)
1. REFUND-002/003: Add CSS to refund page
2. REVIEWS-001/002/003: Rewrite reviews page (honest, styled, correct path)
3. BLOG-001: Fix blog post styling (add style blocks)
4. AUTH-004/005: Fix double-nav on login/register, remove duplicate logo
5. ABOUT-001/002/003: Fix fabricated stats and team section
6. CONTACT-001/002/003: Fix contact emails, add GDPR notice, fix dark mode

### Sprint 3 — Standard SaaS (P2, ~8 hours)
1. BLOG-003: Create /blog index page
2. STATUS-001: Make status page public
3. NAV-001/002: Add FAQ + missing links to nav and footer
4. AFFILIATE-001/002/003: Fix CTA path, remove PayPal, add program terms
5. LEGAL-001/002/003: Add API/acceptable use sections to Terms
6. FAQ-001/002/003: Fix inaccurate FAQ answers

### Sprint 4 — SEO + Polish (P3, ~4 hours)
1. SEO-001: Add meta descriptions to about/contact/affiliate
2. SEO-002/003/004: Add structured data to blog/reviews/faq
3. CONTENT-001/002: Rewrite about mission, fix contact hours
4. BLOG-002: Expand blog post content, add metadata

---

## NOTES

- **Cookie consent granularity** is the single highest-risk item for EU users. Sabilytics analytics should only load after explicit analytics consent.
- **Fabricated social proof** (reviews page 4.8 rating, about page stats) is a trust liability. A user who notices these are fake will distrust everything else.
- **Blog pages rendering unstyled** is immediately visible to any user who lands on them from search. Fix before any SEO push.
- **Status page requiring login** means users can't check if the service is down before trying to log in — defeats the purpose.
- **Terms jurisdiction** is a legal requirement, not optional. Without it the ToS is unenforceable.
