# Mobile Responsiveness Remediation Taskfile

**Project:** Namaskah PWA Mobile Optimization
**Assessment Date:** May 21, 2026
**Status:** Planning Phase
**Estimated Duration:** 5-7 days (4-6 hours/day)
**Priority:** HIGH - Affects 60%+ of public pages

---

## 📋 Executive Summary

The Namaskah app PWA has systematic mobile responsiveness issues affecting **18-22 templates**. The platform renders clearly on desktop but becomes cramped and unreadable on mobile devices due to:

1. Fixed pixel typography not scaling to viewport
2. Excessive padding/margins (40px) on small screens
3. Non-stacking grids and 2-column layouts
4. Tables that don't adapt to mobile
5. Inline styles blocking media query overrides
6. Missing mobile breakpoints (only 768px and 375px)

**Current State:** 60%+ of public pages broken on mobile (320-425px range)
**Solution Approach:** Mobile-first responsive design fixes across 4 phases

---

## 🎯 Implementation Phases

## PHASE 1: Foundation & Global CSS (Estimated: 1-2 days)

**Objective:** Update design system and create responsive infrastructure

### 1.1 - Add Mobile Breakpoints to CSS

**File:** `static/css/responsive.css`

Add new breakpoint sections after existing 768px and 375px rules:

```css
/* ─── SMALL PHONE (≤320px) ─────────────────────────────────── */
@media (max-width: 320px) {
    :root {
        --font-size-4xl: 22px;      /* 48px desktop → 22px mobile */
        --font-size-3xl: 20px;      /* 36px desktop → 20px mobile */
        --font-size-2xl: 16px;      /* 24px desktop → 16px mobile */
        --font-size-xl: 14px;       /* 18px desktop → 14px mobile */
        --font-size-lg: 13px;       /* 16px desktop → 13px mobile */
        --space-10: 20px;           /* 40px desktop → 20px mobile */
        --space-8: 16px;            /* 32px desktop → 16px mobile */
        --space-6: 12px;            /* 24px desktop → 12px mobile */
    }

    /* Override all headings for 320px */
    h1 { font-size: var(--font-size-4xl) !important; }
    h2 { font-size: var(--font-size-3xl) !important; }
    h3 { font-size: var(--font-size-2xl) !important; }
    h4 { font-size: var(--font-size-xl) !important; }

    /* All containers max-width 100vw with padding */
    .container, .public-content, main, section {
        max-width: 100vw;
        padding-left: 16px !important;
        padding-right: 16px !important;
    }

    /* Single column everything */
    [class*="grid"], [class*="Grid"] {
        grid-template-columns: 1fr !important;
    }

    /* Reduce all margins */
    section { margin-bottom: 32px !important; }
    .section { margin-bottom: 32px !important; }
}

/* ─── SMALL-MEDIUM ANDROID (≤360px) ──────────────────────── */
@media (max-width: 360px) {
    :root {
        --font-size-4xl: 24px;      /* 48px → 24px */
        --font-size-3xl: 22px;      /* 36px → 22px */
        --font-size-2xl: 18px;      /* 24px → 18px */
        --space-10: 24px;           /* 40px → 24px */
        --space-8: 20px;            /* 32px → 20px */
    }

    h1 { font-size: var(--font-size-4xl) !important; }
    h2 { font-size: var(--font-size-3xl) !important; }
    h3 { font-size: var(--font-size-2xl) !important; }
}

/* ─── MEDIUM PHONE (≤425px) ─────────────────────────────── */
@media (max-width: 425px) {
    :root {
        --font-size-4xl: 28px;      /* 48px → 28px */
        --font-size-3xl: 24px;      /* 36px → 24px */
        --font-size-2xl: 20px;      /* 24px → 20px */
        --space-10: 28px;           /* 40px → 28px */
        --space-8: 24px;            /* 32px → 24px */
    }

    h1 { font-size: var(--font-size-4xl) !important; }
    h2 { font-size: var(--font-size-3xl) !important; }
    h3 { font-size: var(--font-size-2xl) !important; }
}

/* ─── LARGE PHONE / SMALL TABLET (≤768px) ───────────────── */
@media (max-width: 768px) {
    /* Existing rules stay, add these */
    h1 { font-size: var(--font-size-4xl) !important; }
    h2 { font-size: var(--font-size-3xl) !important; }

    /* Force all grids to 1 column */
    [class*="grid"] {
        grid-template-columns: 1fr !important;
    }
}
```

**Tasks:**
- [ ] Add 320px breakpoint with typography scale overrides
- [ ] Add 360px breakpoint for Android devices
- [ ] Add 425px breakpoint for medium phones
- [ ] Update 768px breakpoint with forced single-column grids
- [ ] Test CSS compiles without errors

---

### 1.2 - Create Responsive Utility Classes

**File:** `static/css/responsive.css` (add new section)

```css
/* ─── RESPONSIVE UTILITY CLASSES ─────────────────────────── */

/* Text sizing utilities */
.text-hero { font-size: var(--font-size-4xl); }
.text-section-title { font-size: var(--font-size-3xl); }
.text-subsection { font-size: var(--font-size-2xl); }
.text-body { font-size: var(--font-size-base); }

/* Padding utilities (responsive) */
.p-section { padding: var(--space-10); }
.p-card { padding: var(--space-8); }
.p-container { padding: var(--space-6) var(--space-6); }

@media (max-width: 768px) {
    .p-section { padding: var(--space-6) var(--space-4); }
    .p-card { padding: var(--space-6); }
}

@media (max-width: 425px) {
    .p-section { padding: var(--space-4) var(--space-3); }
    .p-card { padding: var(--space-4); }
}

/* Grid utilities (responsive) */
.grid-auto-fit {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
}

@media (max-width: 768px) {
    .grid-auto-fit {
        grid-template-columns: 1fr;
        gap: 16px;
    }
}

/* Flexbox utilities (responsive) */
.flex-col-mobile {
    flex-direction: row;
}

@media (max-width: 768px) {
    .flex-col-mobile {
        flex-direction: column;
    }
}

/* Hide/show utilities */
.hide-mobile { display: none; }
.show-mobile { display: block; }

@media (min-width: 769px) {
    .hide-mobile { display: block; }
    .show-mobile { display: none; }
}
```

**Tasks:**
- [ ] Create responsive text sizing classes
- [ ] Create responsive padding classes
- [ ] Create responsive grid classes
- [ ] Create hide/show mobile utilities
- [ ] Document utility usage in code comments

---

### 1.3 - Update Design System Variables

**File:** `static/css/design-system.css`

Update the CSS variables section to include mobile variants:

```css
@media (max-width: 768px) {
    :root {
        /* Mobile Typography Override */
        --font-size-4xl: 28px;      /* Hero h1 */
        --font-size-3xl: 24px;      /* Section h2 */
        --font-size-2xl: 20px;      /* Card h3 */
        --font-size-xl: 16px;       /* Regular text */
        --font-size-lg: 15px;
        --font-size-base: 14px;

        /* Mobile Spacing Override */
        --space-10: 28px;           /* Large sections */
        --space-8: 20px;            /* Cards */
        --space-6: 16px;            /* Subsections */
        --space-5: 12px;            /* Small gaps */
        --space-4: 12px;            /* Minimum padding */
    }
}

@media (max-width: 425px) {
    :root {
        --font-size-4xl: 24px;
        --font-size-3xl: 20px;
        --font-size-2xl: 18px;
        --space-10: 20px;
        --space-8: 16px;
        --space-6: 12px;
    }
}

@media (max-width: 320px) {
    :root {
        --font-size-4xl: 22px;
        --font-size-3xl: 18px;
        --font-size-2xl: 16px;
        --space-10: 16px;
        --space-8: 12px;
    }
}
```

**Tasks:**
- [ ] Add mobile typography overrides to design-system.css
- [ ] Add mobile spacing overrides
- [ ] Verify CSS variables are applied globally
- [ ] Test dark mode still works with new variables

---

## PHASE 2: Public Pages (Estimated: 2-3 days)

**Objective:** Fix all public-facing pages (9-10 templates)

### 2.1 - Affiliate Program Page

**File:** `templates/affiliate_program.html`

**Current Issues:**
- H1: 48px (too large for mobile)
- H2 "Commission Structure": 28px (doesn't fit)
- Table: 4 columns force horizontal scroll
- Padding: 40px on 320px screen = wasted space
- Card grid: minmax(280px) leaves no margin at 320px

**Tasks:**
- [ ] Reduce h1 from 48px (inline) - create responsive override
- [ ] Reduce h2 from 28px - add media query
- [ ] Convert benefit cards grid to single column on mobile
- [ ] Add responsive table layout (card-style stacking)
- [ ] Reduce padding 40px → 16px on mobile
- [ ] Add media queries for CTA section (60px padding → 24px)
- [ ] Test at 320px, 375px, 425px, 768px viewports

**Specific Changes:**

```html
<!-- Change from: -->
<h1 style="font-size: 48px; font-weight: 800; margin: 0 0 16px 0; color: #21262D;">Affiliate Program</h1>

<!-- To: -->
<h1 class="text-hero" style="font-weight: 800; margin: 0 0 16px 0; color: #21262D;">Affiliate Program</h1>
<!-- CSS handles sizing via breakpoints -->

<!-- Change from: -->
<div style="max-width: 1200px; margin: 0 auto; padding: 40px 20px;">

<!-- To: -->
<div class="p-section" style="max-width: 1200px; margin: 0 auto;">

<!-- Change table to responsive: -->
<!-- Add CSS to handle table stacking on mobile -->
```

**Add to affiliate_program.html `<style>` block:**
```css
@media (max-width: 768px) {
    .commission-table {
        display: block;
        width: 100%;
    }
    .commission-table thead {
        display: none;
    }
    .commission-table tbody tr {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 12px;
        margin-bottom: 16px;
        padding: 16px;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }
    .commission-table td {
        display: contents;
    }
    .commission-table td::before {
        content: attr(data-label);
        font-weight: 600;
        color: #6b7280;
    }
}
```

---

### 2.2 - Pricing Page

**File:** `templates/pricing.html`

**Current Issues:**
- H1: 48px (same as affiliate)
- Tier cards: padding 40px/30px
- Grid: minmax(280px) doesn't collapse
- Price: 48px (too large)

**Tasks:**
- [ ] Change h1 to use responsive class/override
- [ ] Reduce tier-card padding 40px/30px → 20px/16px on mobile
- [ ] Force tier-cards grid to 1 column on mobile
- [ ] Scale price amount 48px → 28px on mobile
- [ ] Reduce section margins 60px → 32px on mobile
- [ ] Make comparison table responsive
- [ ] Test CTA buttons at 320px (should not wrap)

**Specific Changes:**

```css
/* Add to pricing.html <style> block */
@media (max-width: 768px) {
    .pricing-hero h1 { font-size: 28px; }
    .pricing-hero p { font-size: 16px; }

    .tier-cards {
        grid-template-columns: 1fr;
        gap: 16px;
    }

    .tier-card {
        padding: 20px 16px;
        transform: scale(1) !important;
    }

    .price-amount { font-size: 32px; }

    .btn-cta {
        padding: 12px 16px;
        font-size: 14px;
    }
}

@media (max-width: 425px) {
    .pricing-hero h1 { font-size: 24px; }
    .tier-card { padding: 16px 12px; }
    .price-amount { font-size: 28px; }
}
```

---

### 2.3 - About Page

**File:** `templates/about.html`

**Current Issues:**
- H1: 48px in gradient hero
- H2: 36px (largest heading issue)
- Feature cards: minmax(300px)
- Padding: 80px top/bottom

**Tasks:**
- [ ] Reduce about-hero h1 48px → 24px on mobile
- [ ] Reduce section h2 36px → 20px on mobile
- [ ] Stack feature-grid to 1 column
- [ ] Reduce about-hero padding 80px → 32px on mobile
- [ ] Stack stats-grid to 1 column
- [ ] Stack team-grid to 1 column
- [ ] Test 320px-768px

**Specific Changes:**

```css
/* Add to about.html <style> block */
@media (max-width: 768px) {
    .about-hero {
        padding: 32px 16px;
        border-radius: 16px;
    }

    .about-hero h1 { font-size: 28px; }
    .about-hero p { font-size: 16px; }

    .section h2 { font-size: 24px; }
    .section p { font-size: 16px; }

    .features-grid,
    .stats-grid,
    .team-grid {
        grid-template-columns: 1fr;
        gap: 16px;
    }

    .feature-card,
    .stat-box {
        padding: 20px;
    }
}

@media (max-width: 425px) {
    .about-hero h1 { font-size: 24px; }
    .section h2 { font-size: 20px; }
}
```

---

### 2.4 - Contact Page

**File:** `templates/contact.html`

**Current Issues:**
- H1: 42px
- Grid: `grid-template-columns: 1fr 1fr` (never stacks!)
- Form elements: Not optimized for touch
- Contact info cards: padding 40px

**Tasks:**
- [ ] Reduce contact-hero h1 42px → 24px on mobile
- [ ] Stack contact-grid from 2 columns to 1 on mobile
- [ ] Increase form input height to 44px (touch target)
- [ ] Reduce form container padding 40px → 20px on mobile
- [ ] Add responsive form styling
- [ ] Ensure form labels visible on mobile

**Specific Changes:**

```css
/* Add to contact.html <style> block */
@media (max-width: 768px) {
    .contact-hero {
        padding: 40px 16px;
        border-radius: 16px;
    }

    .contact-hero h1 { font-size: 28px; }
    .contact-hero p { font-size: 16px; }

    .contact-grid {
        grid-template-columns: 1fr;
        gap: 24px;
    }

    .contact-info,
    .form-container {
        padding: 20px 16px;
    }

    .form-group input,
    .form-group textarea,
    .form-group select {
        padding: 12px;
        font-size: 16px;
        min-height: 44px;
    }

    .form-group label { font-size: 14px; }
}

@media (max-width: 425px) {
    .contact-hero h1 { font-size: 24px; }
}
```

---

### 2.5 - Landing Page

**File:** `templates/landing.html`

**Current Issues:**
- Multiple heading sizes not responsive
- Padding: 40px sections
- Hero section: Not optimized
- CTA buttons: Fixed sizing

**Tasks:**
- [ ] Review all heading sizes in landing page
- [ ] Apply responsive typography classes
- [ ] Reduce section padding 40px → 20px on mobile
- [ ] Ensure hero fits viewport on mobile
- [ ] Make CTA buttons mobile-friendly
- [ ] Test 320px-768px viewports

---

### 2.6 - FAQ Page

**File:** `templates/faq.html`

**Current Issues:**
- Search box: 15px font (small)
- FAQ items: padding 24px
- Accordion: font-size 15px

**Tasks:**
- [ ] Increase search box font 15px → 16px
- [ ] Adjust search box padding for touch
- [ ] Increase FAQ item padding for mobile
- [ ] Test accordion on mobile (open/close)
- [ ] Ensure readable at 320px

---

### 2.7 - How It Works Page

**File:** `templates/how_it_works.html`

**Tasks:**
- [ ] Read and assess page structure
- [ ] Identify oversized headings
- [ ] Fix non-stacking grids
- [ ] Apply responsive padding
- [ ] Test all breakpoints

---

### 2.8 - Privacy & Terms Pages

**File:** `templates/privacy.html`, `templates/terms.html`

**Tasks:**
- [ ] Ensure readable at 320px
- [ ] Check heading sizes
- [ ] Verify link readability
- [ ] Test dark mode

---

### 2.9 - Payment Success Page

**File:** `templates/payment_success.html`

**Current Issues:**
- Grid: `grid-template-columns: 1fr 1fr` (doesn't stack)
- Large emoji: 80px
- Text: 24px/18px/14px not responsive

**Tasks:**
- [ ] Stack 2-column grid to 1 column on mobile
- [ ] Scale emoji 80px → 48px on mobile
- [ ] Adjust text sizes for mobile
- [ ] Test on 320px-768px

---

## PHASE 3: Dashboard Pages (Estimated: 3-4 days)

**Objective:** Fix complex layouts and tables in authenticated pages

### 3.1 - Responsive Table Component

**File:** Create new file or add to `static/css/responsive.css`

Create a reusable responsive table pattern:

```css
/* ─── RESPONSIVE TABLE LAYOUT ──────────────────────────── */

@media (max-width: 768px) {
    /* Convert tables to card layout */
    table {
        display: block;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    table thead {
        display: none;
    }

    table tbody {
        display: block;
    }

    table tbody tr {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 12px;
        margin-bottom: 16px;
        padding: 16px;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: white;
    }

    [data-theme="dark"] table tbody tr {
        background: #1e293b;
        border-color: #334155;
    }

    table td {
        display: contents;
    }

    table td::before {
        content: attr(data-label);
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        font-size: 12px;
    }

    table td:first-child::before {
        content: "";
    }
}
```

**Tasks:**
- [ ] Create responsive table CSS pattern
- [ ] Add data-label attributes to all tables requiring mobile support
- [ ] Document pattern for template developers

---

### 3.2 - Verify Modern Page

**File:** `templates/verify_modern.html`

**Current Issues:**
- Service grid complex layout
- Dropdown overlays
- Multiple input fields
- Large padding sections

**Tasks:**
- [ ] Assess current mobile layout
- [ ] Identify specific breakpoint issues
- [ ] Create responsive service grid
- [ ] Ensure dropdowns work on mobile
- [ ] Test touch interactions at 320px
- [ ] Verify service list readable

---

### 3.3 - Referrals Page

**File:** `templates/referrals.html`

**Current Issues:**
- Referral table: 4 columns
- Form inputs: padding 10px (too small)
- Padding: 40px sections

**Tasks:**
- [ ] Apply responsive table pattern
- [ ] Increase form input min-height to 44px
- [ ] Reduce section padding 40px → 16px on mobile
- [ ] Stack form inputs to full width
- [ ] Test referral table at 320px
- [ ] Ensure readable referral data

---

### 3.4 - API Keys Page

**File:** `templates/api_keys.html`

**Current Issues:**
- Key management table
- Button groups: padding 6px 12px
- Font sizes: 12px, 13px, 15px (too small)

**Tasks:**
- [ ] Apply responsive table pattern to keys table
- [ ] Increase button padding 6px 12px → 10px 16px on mobile
- [ ] Increase all font sizes by 2px on mobile
- [ ] Ensure key copy functionality works on touch
- [ ] Test at 320px-768px

---

### 3.5 - Support Page

**File:** `templates/support.html`

**Current Issues:**
- Support ticket table/list
- Modal overlay for ticket details
- H2: 20px (acceptable)
- Form: input padding 10px

**Tasks:**
- [ ] Apply responsive table pattern
- [ ] Ensure modal responsive and full-screen on mobile
- [ ] Increase form input touch targets to 44px
- [ ] Stack ticket details layout
- [ ] Test modal interaction on 320px

---

### 3.6 - API Documentation Page

**File:** `templates/api_documentation.html`

**Current Issues:**
- Grid: `grid-template-columns: repeat(2, 1fr)` (SDK examples)
- Font sizes: 13px
- Code blocks: may overflow

**Tasks:**
- [ ] Stack 2-column grid to 1 column on mobile
- [ ] Increase code block font size for readability
- [ ] Ensure code blocks don't overflow
- [ ] Add horizontal scroll for code if needed
- [ ] Test at 320px

---

### 3.7 - Disputes Page

**File:** `templates/disputes.html`

**Current Issues:**
- Dispute history table
- Font size: 14px (borderline small)

**Tasks:**
- [ ] Apply responsive table pattern
- [ ] Increase font sizes 14px → 16px on mobile
- [ ] Test at 320px
- [ ] Ensure dispute status visible

---

### 3.8 - Settings Page

**File:** `templates/settings.html`

**Tasks:**
- [ ] Assess current layout
- [ ] Identify form/grid issues
- [ ] Apply responsive fixes
- [ ] Increase form input heights
- [ ] Test all sections at 320px

---

### 3.9 - Notifications Page

**File:** `templates/notifications.html`

**Tasks:**
- [ ] Check notification list layout
- [ ] Ensure readable at 320px
- [ ] Test notification styling
- [ ] Verify dark mode

---

### 3.10 - Other Dashboard Pages

**Files:** `insights.html`, `billing_history.html`, `activity_feed.html`, `webhooks.html`

**Generic Tasks:**
- [ ] Read each page structure
- [ ] Identify responsive issues
- [ ] Apply responsive patterns
- [ ] Test at 320px, 375px, 425px, 768px

---

## PHASE 4: Testing & Validation (Estimated: 1-2 days)

**Objective:** Comprehensive testing across all devices and breakpoints

### 4.1 - Breakpoint Testing

**Test each breakpoint on all modified pages:**

- [ ] 320px (iPhone SE, smallest devices)
  - [ ] All text readable
  - [ ] No horizontal scroll
  - [ ] Touch targets ≥44px
  - [ ] Tables/grids stack properly

- [ ] 375px (iPhone 8/X/11)
  - [ ] Content fits without scroll
  - [ ] Spacing looks proportional
  - [ ] Grids and tables display correctly

- [ ] 425px (iPhone 14, Pixel 4)
  - [ ] Larger screens feel spacious
  - [ ] Typography looks good
  - [ ] No layout regressions

- [ ] 768px (iPad mini, tablets)
  - [ ] Desktop-like experience
  - [ ] 2-column layouts return
  - [ ] Proper spacing restored

---

### 4.2 - Page Testing Checklist

**For each modified page:**

- [ ] Page loads without errors
- [ ] Typography scales correctly
- [ ] Padding/margins apply correctly
- [ ] Grids and tables responsive
- [ ] Images scale properly
- [ ] Forms are touch-friendly (44px min)
- [ ] Buttons clickable at 320px
- [ ] Dark mode works
- [ ] No console errors

---

### 4.3 - Device Testing

**Test on actual devices or emulators:**

- [ ] iOS Safari (iPhone 12 Pro Max)
- [ ] iOS Safari (iPhone SE)
- [ ] Android Chrome (Galaxy S23)
- [ ] Android Chrome (Pixel 4)
- [ ] iPad mini (768px landscape)
- [ ] PWA Standalone mode (iOS)
- [ ] PWA Standalone mode (Android)

---

### 4.4 - Functionality Testing

- [ ] Hamburger menu works at all breakpoints
- [ ] Theme toggle works at all sizes
- [ ] Forms submit correctly
- [ ] Links navigate properly
- [ ] Modals display full-screen on mobile
- [ ] Dropdowns/selects work on touch
- [ ] Tables scroll/collapse correctly
- [ ] Copy buttons work
- [ ] All CTAs visible and clickable

---

### 4.5 - Performance Testing

- [ ] CSS loads without blocking
- [ ] Breakpoint media queries don't cause layout shift
- [ ] No jank on scroll at 320px
- [ ] Images load correctly
- [ ] Font sizes apply instantly
- [ ] Dark mode switch is smooth

---

### 4.6 - Accessibility Testing

- [ ] Text contrast ≥4.5:1 at all sizes
- [ ] Form labels associated with inputs
- [ ] Touch targets ≥44x44px
- [ ] Focus states visible
- [ ] Keyboard navigation works
- [ ] Screen reader compatible

---

## 📋 File Modification Checklist

### CSS Files to Modify

- [ ] `static/css/responsive.css` - Add breakpoints, utilities
- [ ] `static/css/design-system.css` - Add mobile variable overrides
- [ ] `static/css/pwa-mobile.css` - Already good, minor enhancements

### Template Files to Modify

**Public Pages (9-10 files):**
- [ ] `templates/affiliate_program.html`
- [ ] `templates/pricing.html`
- [ ] `templates/about.html`
- [ ] `templates/contact.html`
- [ ] `templates/landing.html`
- [ ] `templates/how_it_works.html`
- [ ] `templates/faq.html`
- [ ] `templates/privacy.html`
- [ ] `templates/payment_success.html`

**Dashboard Pages (10+ files):**
- [ ] `templates/verify_modern.html`
- [ ] `templates/referrals.html`
- [ ] `templates/api_keys.html`
- [ ] `templates/api_documentation.html`
- [ ] `templates/disputes.html`
- [ ] `templates/support.html`
- [ ] `templates/settings.html`
- [ ] `templates/notifications.html`
- [ ] `templates/insights.html`
- [ ] `templates/billing_history.html`
- [ ] `templates/activity_feed.html`
- [ ] `templates/webhooks.html`

---

## 🎯 Success Criteria

### Phase 1 Complete
- [ ] All new breakpoints added (320px, 360px, 425px)
- [ ] CSS compiles without errors
- [ ] Typography scales across breakpoints
- [ ] No layout breaks at any size

### Phase 2 Complete
- [ ] All 9-10 public pages responsive
- [ ] Text readable at 320px
- [ ] No horizontal scroll
- [ ] Grids stack properly
- [ ] Touch targets ≥44px
- [ ] Tables display as cards on mobile

### Phase 3 Complete
- [ ] All 12+ dashboard pages responsive
- [ ] Complex layouts adapt to mobile
- [ ] Forms are touch-friendly
- [ ] Modals full-screen on mobile
- [ ] Tables/dropdowns work on touch

### Phase 4 Complete
- [ ] All tests passed on 320px, 375px, 425px, 768px
- [ ] Tested on iOS and Android devices
- [ ] PWA standalone mode works
- [ ] Dark mode works at all sizes
- [ ] No console errors
- [ ] Accessibility standards met

---

## ⚠️ Important Notes

### Avoid Breaking Changes
- Do NOT remove existing desktop styles
- Use media queries to OVERRIDE, not replace
- Test desktop (1920px+) after changes
- Verify no regressions on tablet (768px-1024px)

### Browser Compatibility
- Support iOS Safari (Apple native features)
- Support Android Chrome (90%+ market share)
- Support PWA standalone mode
- Support landscape orientation

### Dark Mode Integration
- Apply `[data-theme="dark"]` to all new rules
- Test both themes at all breakpoints
- Maintain sufficient contrast (4.5:1)

### Performance Considerations
- Breakpoint media queries are efficient
- CSS variables are well-supported
- No JavaScript needed for responsive
- Minimize !important declarations
- Prioritize critical breakpoints

---

## 📞 Reference Information

**Breakpoints Summary:**
- 320px: Small phones (iPhone SE)
- 360px: Android devices (Samsung A series)
- 425px: Medium phones (iPhone 14, Pixel 6)
- 768px: Tablets (iPad mini)
- 1024px+: Desktop

**Typography Scale:**

| Element | Desktop | 425px | 375px | 320px |
|---------|---------|-------|-------|-------|
| H1 | 48px | 28px | 24px | 22px |
| H2 | 36px | 24px | 22px | 20px |
| H3 | 24px | 20px | 18px | 16px |
| Paragraph | 16-18px | 15px | 14px | 13px |

**Spacing Scale:**

| Element | Desktop | Mobile |
|---------|---------|--------|
| Section padding | 40px | 16px |
| Card padding | 32px | 20px |
| Section margin | 60px | 32px |
| Gap (grids) | 24px | 16px |

---

## 🚀 Getting Started

### Day 1 - Foundation
1. Start with Phase 1.1 (Add Mobile Breakpoints)
2. Add 320px, 360px, 425px breakpoints to responsive.css
3. Test changes don't break desktop (1920px)
4. Commit: "feat: Add mobile breakpoints (320px, 360px, 425px)"

### Day 2 - Utilities & Variables
1. Complete Phase 1.2 (Responsive Utility Classes)
2. Complete Phase 1.3 (Design System Variables)
3. Test all utilities across breakpoints
4. Commit: "feat: Add responsive utility classes and design system overrides"

### Days 3-4 - Public Pages
1. Follow Phase 2.1-2.9 in order
2. Test each page after modification
3. Commit separately for each page group
4. Example: "fix: Make affiliate page responsive (mobile)"

### Days 5-6 - Dashboard Pages
1. Follow Phase 3.1-3.10
2. Test tables and complex layouts
3. Commit dashboard fixes
4. Example: "fix: Make verify page responsive"

### Day 7 - Testing & Refinement
1. Complete Phase 4 testing
2. Fix any regressions
3. Test on actual devices
4. Final commit: "test: Comprehensive mobile responsiveness validation"

---

## 📊 Progress Tracking

Use this to track daily progress:

**Week 1:**
- [ ] Day 1: Foundation - Breakpoints (Phase 1.1)
- [ ] Day 2: Utilities & Variables (Phase 1.2, 1.3)
- [ ] Day 3-4: Public Pages Group 1 (Phase 2.1-2.5)
- [ ] Day 5: Public Pages Group 2 (Phase 2.6-2.9)
- [ ] Day 6-7: Dashboard Pages (Phase 3)
- [ ] Day 8: Testing & Validation (Phase 4)

---

## 📝 Maintenance Notes

After completion, remember to:
- Document responsive patterns for new pages
- Enforce 44px minimum touch targets
- Test mobile at 320px before submitting PRs
- Keep breakpoints consistent (320px, 360px, 425px, 768px)
- Maintain dark mode support
- Update this taskfile with lessons learned
