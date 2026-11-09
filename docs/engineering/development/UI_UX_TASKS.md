# UI/UX Enhancement Tasks

**Created**: November 2026
**Scope**: Landing page (mobile + desktop + PWA), Auth pages, Pricing, Dashboard, cross-cutting
**Status**: All open

---

## LANDING PAGE

### LP-001 — Mobile nav dropdown is broken
**Priority**: P0 — visible to every mobile visitor
**File**: `templates/landing.html`
**Problem**: At ≤768px the hamburger shows but `toggleMobileMenu()` just toggles
`display: flex` on `.nav-links` inline — it appears inside the nav bar, not as a
dropdown panel. No overlay, no close-on-outside-click, no animation.
**Fix**:
- Position `.nav-links` as `position: absolute; top: 100%; left: 0; right: 0`
- Add `background: var(--bg); border-bottom: 1px solid var(--border); padding: 16px 24px; flex-direction: column; gap: 16px;`
- Add overlay div that closes menu on outside click
- Add `aria-expanded` toggle on hamburger button

---

### LP-002 — `landing.css` is dead — HTML/CSS completely out of sync
**Priority**: P1
**Files**: `static/css/landing.css`, `templates/landing.html`
**Problem**: `landing.html` uses inline `<style>` with class names `.site-nav`,
`.hero`, `.shell`, `.platform-card`. `landing.css` defines `.navbar`,
`.hero-container`, `.hero-visual`, `.pricing-card` — none of which exist in the HTML.
`landing.css` is 100% dead code.
**Fix**: Either delete `landing.css` or rewrite it to match the actual HTML classes.
Recommend deleting it — the inline styles are self-contained and work.

---

### LP-003 — No stats / social proof above the fold
**Priority**: P1 — conversion impact
**File**: `templates/landing.html`
**Problem**: Hero has badge + headline + subtext + CTAs but no trust numbers.
`landing.css` defines `.hero-stats` with stat values but the HTML has none.
**Fix**: Add a stats row below the CTAs:
```html
<div class="hero-stats">
  <div class="stat"><span class="stat-num">1,800+</span><span class="stat-label">Supported Services</span></div>
  <div class="stat"><span class="stat-num">< 30s</span><span class="stat-label">Average Delivery</span></div>
  <div class="stat"><span class="stat-num">100%</span><span class="stat-label">Auto-Refund Guarantee</span></div>
</div>
```
Style: `display: flex; gap: 32px; justify-content: center; margin-top: 40px; flex-wrap: wrap;`

---

### LP-004 — Platform card icons are placeholder SVGs
**Priority**: P1 — looks unprofessional
**File**: `templates/landing.html`
**Problem**: Uber, DoorDash, Instacart icons are generic globe/circle/checkmark SVGs,
not actual brand logos. WhatsApp and Telegram have correct brand SVGs.
**Fix**: Replace with SimpleIcons CDN SVGs (already used in `service-store.js`):
- Uber: `https://cdn.simpleicons.org/uber/000000`
- DoorDash: `https://cdn.simpleicons.org/doordash/FF3008`
- Instacart: `https://cdn.simpleicons.org/instacart/43B02A`
Use `<img src="..." width="40" height="40" alt="Uber">` pattern.

---

### LP-005 — API code block overflows on mobile
**Priority**: P1
**File**: `templates/landing.html`
**Problem**: `.code-block code` uses `white-space: pre` with no horizontal scroll
wrapper. On screens <600px the code block overflows the viewport.
**Fix**: Add `overflow-x: auto; -webkit-overflow-scrolling: touch;` to `.code-block`.

---

### LP-006 — Footer collapses badly on mobile
**Priority**: P1
**File**: `templates/landing.html`
**Problem**: `.footer-grid` goes `1fr 1fr` at 768px — the brand column (with logo +
description) sits next to a nav column and both get squished. On 320px it's unreadable.
**Fix**: Add `@media (max-width: 480px) { .footer-grid { grid-template-columns: 1fr; } }`
so footer goes fully single-column on small phones.

---

### LP-007 — No pricing teaser on landing page
**Priority**: P2 — conversion
**File**: `templates/landing.html`
**Problem**: Users have to navigate to `/pricing` to see costs. A simple pricing
summary between Features and the CTA section would reduce drop-off.
**Fix**: Add a minimal 2-column pricing teaser:
- Left: "From $2.63/SMS — no subscription needed"
- Right: "Pro plan $25/mo — includes $15 credit + API access"
- CTA: "See full pricing →" linking to `/pricing`

---

### LP-008 — PWA install prompt missing
**Priority**: P2
**File**: `templates/landing.html`
**Problem**: The app is a PWA (manifest, service worker, icons all present) but there's
no "Add to Home Screen" banner or install button on the landing page. Users won't
discover it's installable.
**Fix**: Add a dismissible banner at the bottom of the hero:
```html
<div id="pwa-install-banner" style="display:none; ...">
  📱 Install Vrenum SMS as an app — works offline
  <button onclick="installPWA()">Install</button>
  <button onclick="dismissBanner()">✕</button>
</div>
```
Wire to `beforeinstallprompt` event. Store dismissal in `localStorage`.

---

### LP-009 — Dark mode CTA section doesn't adapt
**Priority**: P2
**File**: `templates/landing.html`
**Problem**: `.cta { background: var(--primary) }` — the CTA section is always pink
regardless of theme. In dark mode this is jarring against the dark page.
**Fix**: In dark mode, use a darker gradient:
```css
[data-theme="dark"] .cta {
  background: linear-gradient(135deg, #c0284e, #a01e3e);
}
```

---

### LP-010 — No testimonials / reviews section
**Priority**: P2 — conversion
**File**: `templates/landing.html`
**Problem**: `landing.css` has full testimonial card styles but no testimonials exist
on the landing page. There's a `/reviews` page but it's not linked from landing.
**Fix**: Add 3 short testimonials between How It Works and Features. Use the
`.testimonial-card` pattern from `landing.css`. Link "See all reviews →" to `/reviews`.

---

### LP-011 — Hero has no visual element
**Priority**: P2
**File**: `templates/landing.html`
**Problem**: Desktop hero is text-only. `landing.css` defines a floating `.hero-card`
with animation but the HTML doesn't use it. A visual element (phone mockup, code
snippet, or animated verification flow) would significantly improve first impression.
**Fix**: Add a right-side visual to the hero on desktop (≥768px):
- A simple animated card showing "WhatsApp · +1 (555) 123-4567 · Code: 847291 ✓"
- Use the existing `@keyframes float` animation from `landing.css`
- Hide on mobile (single column)

---

## AUTH PAGES

### AUTH-001 — Register page missing top nav
**Priority**: P1
**File**: `templates/register.html`
**Problem**: `login.html` has a proper `.auth-nav` with brand + Home/Pricing/FAQ links.
`register.html` has no nav at all — just the form starting at the top of the page.
Users who land on `/auth/register` directly have no way to navigate back without
the browser back button.
**Fix**: Copy the `.auth-nav` block from `login.html` into `register.html`. Add
`margin-top: 80px` to `.auth-container` to clear the fixed nav.

---

### AUTH-002 — Turnstile widget always renders in light theme
**Priority**: P1
**Files**: `templates/login.html`, `templates/register.html`
**Problem**: Both pages have `data-theme="light"` hardcoded on the Cloudflare Turnstile
widget. In dark mode the white Turnstile box is jarring.
**Fix**: Change to `data-theme="auto"` — Turnstile supports auto theme detection.
```html
<div class="cf-turnstile" data-sitekey="..." data-theme="auto" ...>
```

---

### AUTH-003 — Register page auth-container has no top margin on desktop
**Priority**: P1
**File**: `templates/register.html`
**Problem**: `.auth-container` has `margin: 20px auto` — on desktop this puts the
form very close to the top of the viewport (no nav to push it down). Login has
`margin: 80px auto 20px` which is correct.
**Fix**: Change to `margin: 80px auto 20px` to match login.

---

### AUTH-004 — Google button style inconsistency between login and register
**Priority**: P2
**Files**: `templates/login.html`, `templates/register.html`
**Problem**: Login Google button uses `background: var(--bg-card, white)` (theme-aware).
Register Google button uses `background: white` (hardcoded). In dark mode on register,
the Google button is white-on-dark — jarring.
**Fix**: Change register Google button to use `background: var(--bg-card, white)` and
`color: var(--text-primary, #37352F)` and `border-color: var(--border-color, #e0e0e0)`.

---

### AUTH-005 — No "Sign up" link on login page
**Priority**: P2
**File**: `templates/login.html`
**Problem**: The login page has Login/Sign Up tabs but no explicit "Don't have an
account? Sign up" text link below the form. The tab is the only affordance.
**Fix**: Add below the Google button:
```html
<p style="text-align:center; margin-top:16px; font-size:14px; color:var(--text-muted);">
  Don't have an account? <a href="/auth/register" style="color:#FE3C72;">Sign up free</a>
</p>
```

---

## PRICING PAGE

### PRICE-001 — Pricing hero h1 hardcoded color
**Priority**: P1
**File**: `templates/pricing.html`
**Problem**: `.pricing-hero h1 { color: #37352F }` — hardcoded dark color. In dark
mode the heading is nearly invisible against the dark background.
**Fix**: Change to `color: var(--text-primary, #37352F)` or use the dark mode override
already present at the top of the file: `[data-theme="dark"] h1 { color: #f1f5f9 }`.
The existing override should work — verify it applies to `.pricing-hero h1`.

---

### PRICE-002 — Comparison table has no horizontal scroll on mobile
**Priority**: P1
**File**: `templates/pricing.html`
**Problem**: The comparison table is hidden on mobile (`display: none`) and replaced
with a mobile accordion. But the accordion uses `grid-template-columns: repeat(4,1fr)`
with `font-size: 11px` — on 320px screens the 4 columns are unreadably small.
**Fix**: On the accordion, reduce to 2 columns (feature name + value) and use a
toggle to switch between tiers, OR just make the table horizontally scrollable instead
of hiding it:
```css
.comparison-table { overflow-x: auto; }
.comparison-table table { min-width: 600px; }
```

---

### PRICE-003 — `selectTier()` silently fails for logged-in users on Pro/Custom
**Priority**: P1
**File**: `templates/pricing.html`
**Problem**: `selectTier('pro')` redirects to `/settings?tab=billing` — but if the
user is already on Pro, they land on billing with no feedback. There's no check for
current tier before redirecting.
**Fix**: Pass the tier in the URL: `/settings?tab=billing&upgrade_to=pro` so the
settings page can pre-select the upgrade target.

---

### PRICE-004 — FAQ section has no expand/collapse
**Priority**: P2
**File**: `templates/pricing.html`
**Problem**: All 7 FAQ items are always expanded. On mobile this creates a very long
scroll. Standard pattern is accordion — click to expand.
**Fix**: Add simple accordion with `<details>/<summary>` HTML elements — no JS needed:
```html
<details class="faq-item">
  <summary class="faq-question">Can I change my plan anytime?</summary>
  <p>Yes! You can upgrade...</p>
</details>
```
Style `summary` to look like the current `h3`.

---

## DASHBOARD

### DASH-001 — Four action buttons always visible regardless of tier
**Priority**: P1
**File**: `templates/dashboard.html`
**Problem**: "New Verification", "Add Credits", "View Usage", "Upgrade" are all shown
simultaneously. For a Custom tier user "Upgrade" is hidden via JS after load — but
there's a flash where all 4 show. For Freemium users "View Usage" is irrelevant.
**Fix**: Hide "Upgrade" by default with `style="display:none"` and show it via JS
only when tier is not Custom. This eliminates the flash.

---

### DASH-002 — Activity table hidden on mobile but mobile cards have no styling
**Priority**: P1
**File**: `templates/dashboard.html`
**Problem**: `#activity-table` is hidden at ≤640px and `#activity-mobile-cards` is
shown. But `.mobile-card-item` and `.card-row` / `.card-label` / `.card-value` have
no CSS defined anywhere — the mobile cards render as unstyled divs.
**Fix**: Add to the dashboard `<style>` block:
```css
.mobile-card-item {
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background: var(--bg-card, white);
}
.card-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-color, #f3f4f6); }
.card-row:last-child { border-bottom: none; }
.card-label { font-size: 12px; font-weight: 600; color: var(--text-muted, #9ca3af); text-transform: uppercase; }
.card-value { font-size: 13px; color: var(--text-primary, #1f2937); text-align: right; }
[data-theme="dark"] .mobile-card-item { background: #1e293b; border-color: #334155; }
```

---

### DASH-003 — Stats grid goes 2-column at 640px but 4 stats look cramped
**Priority**: P2
**File**: `templates/dashboard.html`
**Problem**: At 640px the stats grid goes `repeat(2, 1fr)` — 4 stats in 2 rows.
The stat values use `font-size: clamp(16px, 2.5vw, 28px)` which at 320px gives ~8px
— too small. The `word-break: break-all` on the currency stat can split "$2" across
lines.
**Fix**: Set a minimum font size of 18px for stat values on mobile:
```css
@media (max-width: 480px) {
  .nsk-stat-value { font-size: 18px !important; }
}
```

---

## CROSS-CUTTING

### XC-001 — `pwa-mobile.css` grid override too aggressive
**Priority**: P1
**File**: `static/css/pwa-mobile.css`
**Problem**: `[class*="grid"] { grid-template-columns: 1fr !important; }` at 768px
collapses ALL grids to single column — including the platform grid on landing (which
looks fine at 2 columns on tablet) and the stats grid on dashboard.
**Fix**: Scope the override to specific containers or remove the `!important` and let
`auto-fit minmax()` handle it naturally. The `!important` is fighting the intentional
responsive grid definitions.

---

### XC-002 — Turnstile widget hardcoded `data-theme="light"` across all pages
**Priority**: P1
**Files**: `templates/login.html`, `templates/register.html`
**Problem**: See AUTH-002. Affects both auth pages.
**Fix**: `data-theme="auto"` on both.

---

### XC-003 — No `<meta name="theme-color">` in PWA head
**Priority**: P2
**File**: `templates/includes/pwa_head.html`
**Problem**: PWA installed apps show the browser chrome color. Without `theme-color`
the browser bar is white/grey instead of the brand pink.
**Fix**: Add to `pwa_head.html`:
```html
<meta name="theme-color" content="#FE3C72" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)">
```

---

### XC-004 — No `loading="lazy"` on platform card images
**Priority**: P2
**File**: `templates/landing.html`
**Problem**: Once LP-004 is fixed and real `<img>` tags are used for brand logos,
they should have `loading="lazy"` to avoid blocking initial render.
**Fix**: Add `loading="lazy"` to all platform card `<img>` tags.

---

### XC-005 — Cookie consent banner z-index conflicts with mobile nav
**Priority**: P2
**File**: `templates/includes/cookie_consent.html`
**Problem**: The cookie consent banner is fixed at the bottom. The mobile nav dropdown
(once LP-001 is fixed) will be fixed at the top. On small screens both can be visible
simultaneously, reducing usable viewport to ~60%.
**Fix**: Ensure cookie consent has `z-index` lower than the nav dropdown. Add
`padding-bottom: 80px` to the page body when the banner is visible.

---

### XC-006 — `focus-visible` missing on landing page CTAs
**Priority**: P2
**File**: `templates/landing.html`
**Problem**: `.btn-primary` and `.btn-outline` have no `:focus-visible` styles.
Keyboard users tabbing through the landing page get no visible focus indicator.
**Fix**: Add to the inline `<style>`:
```css
.btn:focus-visible {
  outline: 3px solid var(--primary);
  outline-offset: 2px;
}
```

---

### XC-007 — `<title>` tags are generic across public pages
**Priority**: P2
**Files**: `templates/pricing.html`, `templates/login.html`, `templates/register.html`
**Problem**: `{% block page_title %}Pricing{% endblock %}` renders as just "Pricing"
in the browser tab. Should be "Pricing — VRENUM SMS" for SEO and tab clarity.
**Fix**: Update `public_base.html` title block to append brand:
```html
<title>{% block page_title %}VRENUM SMS{% endblock %} — VRENUM SMS</title>
```
Then each page just sets the prefix: `{% block page_title %}Pricing{% endblock %}`.

---

## SUMMARY

| ID | Area | Priority | Effort |
|----|------|----------|--------|
| LP-001 | Mobile nav dropdown broken | P0 | S |
| LP-002 | landing.css dead code | P1 | S |
| LP-003 | No stats above fold | P1 | S |
| LP-004 | Placeholder brand icons | P1 | S |
| LP-005 | Code block mobile overflow | P1 | S |
| LP-006 | Footer mobile collapse | P1 | S |
| AUTH-001 | Register missing nav | P1 | S |
| AUTH-002 | Turnstile hardcoded light | P1 | S |
| AUTH-003 | Register container margin | P1 | S |
| PRICE-001 | Pricing h1 dark mode | P1 | S |
| PRICE-002 | Comparison table mobile | P1 | S |
| PRICE-003 | selectTier no tier check | P1 | S |
| XC-001 | pwa-mobile grid override | P1 | S |
| XC-002 | Turnstile light theme | P1 | S |
| DASH-001 | Upgrade btn flash | P1 | S |
| DASH-002 | Mobile cards unstyled | P1 | S |
| LP-007 | No pricing teaser | P2 | M |
| LP-008 | PWA install prompt | P2 | M |
| LP-009 | Dark mode CTA | P2 | S |
| LP-010 | No testimonials | P2 | M |
| LP-011 | Hero no visual | P2 | L |
| AUTH-004 | Google btn inconsistency | P2 | S |
| AUTH-005 | No signup link on login | P2 | S |
| PRICE-004 | FAQ no accordion | P2 | S |
| DASH-003 | Stats font too small | P2 | S |
| XC-003 | No theme-color meta | P2 | S |
| XC-004 | No lazy loading on imgs | P2 | S |
| XC-005 | Cookie banner z-index | P2 | S |
| XC-006 | No focus-visible on CTAs | P2 | S |
| XC-007 | Generic page titles | P2 | S |

**Effort**: S = <30min, M = 1-2h, L = half day
**P0**: Fix before next deploy. **P1**: Fix this sprint. **P2**: Next sprint.
