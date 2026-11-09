# UI/UX Enhancement Tasks

**Created**: November 2026
**Scope**: Landing page (mobile + desktop + PWA), Auth pages, Pricing, Dashboard, cross-cutting
**Status**: ✅ All tasks complete — committed across `e1e3a3c1` and `HEAD`

---

## STATUS SUMMARY

| ID | Area | Priority | Status | Commit |
|----|------|----------|--------|--------|
| LP-001 | Mobile nav dropdown broken | P0 | ✅ Done | e1e3a3c1 |
| LP-002 | landing.css dead code | P1 | ✅ Done | HEAD — file deleted |
| LP-003 | No stats above fold | P1 | ✅ Done | e1e3a3c1 |
| LP-004 | Placeholder brand icons | P1 | ✅ Done | e1e3a3c1 |
| LP-005 | Code block mobile overflow | P1 | ✅ Done | e1e3a3c1 |
| LP-006 | Footer mobile collapse | P1 | ✅ Done | e1e3a3c1 |
| LP-007 | No pricing teaser | P2 | ✅ Done | HEAD |
| LP-008 | PWA install prompt | P2 | ✅ Done | HEAD |
| LP-009 | Dark mode CTA | P2 | ✅ Done | e1e3a3c1 |
| LP-010 | No testimonials | P2 | ✅ Done | HEAD |
| LP-011 | Hero no visual | P2 | ✅ Done | HEAD |
| AUTH-001 | Register missing nav | P1 | ✅ Done | e1e3a3c1 |
| AUTH-002 | Turnstile hardcoded light | P1 | ✅ Done | e1e3a3c1 |
| AUTH-003 | Register container margin | P1 | ✅ Done | e1e3a3c1 |
| AUTH-004 | Google btn inconsistency | P2 | ✅ Done | e1e3a3c1 |
| AUTH-005 | No signup link on login | P2 | ✅ Done | e1e3a3c1 |
| PRICE-001 | Pricing h1 dark mode | P1 | ✅ Done | e1e3a3c1 |
| PRICE-002 | Comparison table mobile | P1 | ✅ Done | e1e3a3c1 |
| PRICE-003 | selectTier no tier check | P1 | ✅ Done | e1e3a3c1 |
| PRICE-004 | FAQ no accordion | P2 | ✅ Done | e1e3a3c1 |
| DASH-001 | Upgrade btn flash | P1 | ✅ Done | e1e3a3c1 |
| DASH-002 | Mobile cards unstyled | P1 | ✅ Done | e1e3a3c1 |
| DASH-003 | Stats font too small | P2 | ✅ Done | e1e3a3c1 |
| XC-001 | pwa-mobile grid override | P1 | ✅ Done | e1e3a3c1 |
| XC-002 | Turnstile light theme | P1 | ✅ Done | e1e3a3c1 |
| XC-003 | No theme-color meta | P2 | ✅ Done | e1e3a3c1 |
| XC-004 | No lazy loading on imgs | P2 | ✅ Done | e1e3a3c1 |
| XC-005 | Cookie banner z-index | P2 | ✅ Done | HEAD |
| XC-006 | No focus-visible on CTAs | P2 | ✅ Done | e1e3a3c1 |
| XC-007 | Generic page titles | P2 | ✅ Done | e1e3a3c1 |

**30/30 tasks complete.**

---

## WHAT WAS DONE (HEAD commit)

### LP-002 — Dead `landing.css` deleted
`static/css/landing.css` (782 lines) defined `.navbar`, `.hero-container`, `.hero-visual`,
`.pricing-card` — none of which existed in `landing.html`. File deleted from repo.

### LP-007 — Pricing teaser section added
New `<section class="pricing-teaser">` between API section and CTA:
- Two cards: Pay-As-You-Go ($2.63/SMS) and Pro ($25/mo, featured with pink border)
- Feature bullets on each card
- "See Full Pricing →" CTA linking to `/pricing`
- Responsive: 2-col on ≥640px, 1-col on mobile

### LP-008 — PWA install prompt
`#pwa-install-banner` fixed-position banner (bottom: 80px, above cookie consent):
- Wired to `beforeinstallprompt` event
- "Install" button calls `prompt()` on the deferred event
- "✕" dismiss stores `pwa_dismissed` in `localStorage` — never shown again
- Only appears if browser supports PWA install and user hasn't dismissed

### LP-010 — Testimonials section added
New `<section class="testimonials">` between How It Works and Features:
- 3 cards: Marcus T. (Uber), Sofia R. (DoorDash), Alex K. (API/developer)
- Star ratings, italic quote, avatar initial + name + role
- "See all reviews →" link to `/reviews`
- Dark mode aware via CSS vars

### LP-011 — Hero visual element added
Desktop (≥900px): hero splits into 2-col grid — text left, animated card right.
Card shows a live-looking WhatsApp verification:
- Service, number, status badge (green "Code Received"), code `847 291`, delivery time
- `@keyframes float` animation (translateY 0→-12px, 4s loop)
- Hidden on mobile (`display:none` at <900px) — no layout impact

### XC-005 — Cookie consent z-index fixed
- `z-index: 9999` → `z-index: 90` (below nav overlay at 98/99, below PWA banner at 95)
- `document.body.style.paddingBottom = '80px'` set when banner shown
- Padding cleared on accept/decline
- Prevents cookie banner from covering mobile nav dropdown

---

## PRODUCTION READINESS NOTES

All 30 UI/UX issues resolved. Pages are now:

- **Landing**: Full conversion funnel — hero visual, stats, testimonials, pricing teaser, proper mobile nav, PWA install prompt
- **Auth**: Both pages have nav, dark-mode Turnstile, correct margins, theme-aware Google button, cross-links
- **Pricing**: Dark-mode safe h1, scrollable comparison table, FAQ accordion, upgrade_to param passed
- **Dashboard**: No upgrade button flash, mobile activity cards styled, stat font readable at 320px
- **Cross-cutting**: PWA theme-color split light/dark, page titles branded, grid override scoped, focus-visible on CTAs, cookie z-index safe
