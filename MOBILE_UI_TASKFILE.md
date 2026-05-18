# Mobile UI Improvement Taskfile
**Version**: 1.0.0
**Created**: May 18, 2026
**Status**: Phase 1 Complete — Phase 2 Complete — Phase 3 In Progress
**Related**: See [docs/MOBILE_UI_AUDIT.md](./docs/MOBILE_UI_AUDIT.md) for full audit and glassmorphism integration plan

## 🎯 Overview
Comprehensive mobile UI enhancement plan with glassmorphism design system integration across all platform pages.

## 📋 Task Categories

### Phase 1: Critical Fixes (Week 1) - P0 Priority
**Estimated Time**: 16 hours
**Impact**: Fixes broken mobile experience

#### Task 1.1: Global CSS Fixes (2 hours)
- [x] **Fix iOS Zoom Issue**
  - File: `static/css/glassmorphism.css`
  - Add: `input, select, textarea { font-size: 16px !important; }`
  - Status: ✅ Complete

- [x] **Implement Touch Target Standards**
  - Minimum 44px height for all `.glass-btn`, `.glass-btn-primary`
  - Status: ✅ Complete

- [x] **Viewport Meta Verification**
  - Global mobile CSS block added to `glassmorphism.css`
  - Status: ✅ Complete

#### Task 1.2: Dashboard Mobile Layout (4 hours)
- [x] **Stats Grid Responsive**
  - File: `templates/dashboard.html`
  - Changed: `minmax(220px)` → `minmax(140px)` → 2-column on iPhone SE
  - Status: ✅ Complete

- [x] **Transaction Table → Cards**
  - `#activity-mobile-cards` div added, JS populates both table + cards
  - Table hidden on mobile via `@media (max-width: 640px)`
  - Status: ✅ Complete

#### Task 1.3: Verify Page Mobile (4 hours)
- [x] **Modal Responsive Design**
  - File: `static/css/verification-design-system.css`
  - Modal slides up from bottom, 88vh max-height, 20px border-radius
  - Status: ✅ Complete

- [x] **Input Field Optimization**
  - `modal-search-input`, `#area-code-search-input`, `#service-search-input` → 16px
  - Progress steps stack vertically, copy buttons full-width stacked
  - Status: ✅ Complete

#### Task 1.4: Wallet Mobile Layout (3 hours)
- [x] **Payment History Cards**
  - File: `templates/wallet.html`
  - `.history-mobile-cards` added, JS renders mobile cards alongside table
  - Status: ✅ Complete

- [x] **QR Code Responsive**
  - QR container → `width: 80%; max-width: 200px`, image scales to 100%
  - Status: ✅ Complete

#### Task 1.5: Settings Mobile Navigation (3 hours)
- [x] **Mobile Sidebar → Bottom Nav**
  - File: `templates/settings.html`
  - Fixed bottom tab bar with horizontal scroll, frosted glass background
  - Content gets `padding-bottom: 72px` to clear nav
  - Status: ✅ Complete

---

### Phase 2: High Priority Pages (Week 2) - P1 Priority
**Estimated Time**: 12 hours
**Impact**: Improves user experience significantly

#### Task 2.1: History Page Mobile (2 hours)
- [x] **History Table → Cards**
  - File: `templates/history.html`
  - Desktop table hidden on mobile, `#history-mobile-cards` shown
  - `renderHistory` populates both table rows and mobile cards
  - Filter bar stacks vertically, all inputs 16px, 44px touch targets
  - Audit modal full-screen on mobile
  - Status: ✅ Complete

#### Task 2.2: Auth Pages Mobile (3 hours)
- [x] **Login/Register Forms**
  - Files: `templates/login.html`, `templates/register.html`
  - `font-size: 15px → 16px` on all inputs (iOS zoom fix)
  - `.btn-auth` gets `min-height: 48px`
  - Container goes edge-to-edge on mobile (no floating card)
  - Status: ✅ Complete

#### Task 2.3: Pricing Page Mobile (2 hours)
- [x] **Pricing Cards Stack**
  - File: `templates/pricing.html`
  - Cards already single-column on mobile (existing rule kept)
  - Hero text scales: `48px → 32px`
  - Comparison table hidden, replaced with compact 2-column grid accordion
  - Sticky bottom CTA bar (Free + Upgrade to Pro) added
  - Status: ✅ Complete

#### Task 2.4: Landing Page Enhancement (3 hours)
- [x] **Hero Section Mobile**
  - File: `templates/landing.html`
  - Status: ✅ Complete (Glassmorphism applied — prior session)

#### Task 2.5: Profile Page Mobile (2 hours)
- [x] **Profile Layout**
  - File: `templates/profile.html`
  - Header stacks vertically on mobile, avatar 96px, centered
  - Avatar overlay always visible on mobile (no hover dependency)
  - Stats grid → `repeat(2, 1fr)` on mobile
  - Save button full-width, `min-height: 48px`
  - All inputs `font-size: 16px` (iOS zoom fix)
  - `profile-user-id` gets `word-break: break-all`
  - Status: ✅ Complete

---

### Phase 3: Polish & Testing (Week 3) - P2 Priority
**Estimated Time**: 12 hours
**Impact**: Final polish and quality assurance

#### Task 3.1: Support Pages (2 hours)
- [x] **Support Mobile UI**
  - File: `templates/support.html`
  - `support-grid` 2-col → single column on mobile
  - `category-grid` 2-col → single column on mobile
  - All form inputs `font-size: 16px` (iOS zoom fix)
  - All interactive elements `min-height: 44px`
  - `btn-submit` gets `min-height: 48px`
  - Status: ✅ Complete

#### Task 3.2: Notifications Mobile (2 hours)
- [x] **Notification Center**
  - File: `templates/notifications.html`
  - Filter buttons `min-height: 40px`, action buttons `min-height: 44px`
  - Header actions full-width on mobile
  - `aria-live="polite"` on unread count
  - `aria-label` on Mark All Read and Refresh buttons
  - Status: ✅ Complete

#### Task 3.3: Cross-Device Testing (4 hours)
- [ ] **Device Testing Matrix**
  - iPhone 12/13/14 (375px, 390px, 393px)
  - Android phones (360px, 412px)
  - iPad (768px, 820px)
  - Desktop (1024px+)
  - Status: ⏳ Pending — requires manual QA on real devices

#### Task 3.4: Performance Optimization (2 hours)
- [x] **Mobile Performance**
  - File: `static/css/glassmorphism.css`
  - `@supports not (backdrop-filter)` fallback → solid opaque backgrounds
  - Mobile: all non-critical components capped to `blur-sm`
  - Hover transforms disabled on mobile (no hover state)
  - `.glass-float` animation disabled on mobile
  - Status: ✅ Complete

#### Task 3.5: Accessibility Audit (2 hours)
- [x] **A11y Compliance**
  - `history.html`: All sortable `<th>` get `scope="col"`, `role="columnheader"`, `aria-sort`, `tabindex="0"`, keyboard Enter handler; sort indicators get `aria-hidden="true"`; `sortHistory` updates `aria-sort` dynamically
  - `notifications.html`: `aria-live="polite" aria-atomic="true"` on unread count; `aria-label` on Mark All Read and Refresh buttons
  - `glassmorphism.css`: `focus-visible` rings (2px #FE3C72 outline + 4px glow) on all interactive glass components
  - Status: ✅ Complete

---

## 🛠️ Implementation Guidelines

### Glassmorphism Integration
```css
/* Use these classes consistently */
.glass-card          /* Standard cards */
.glass-card-dark     /* Dark theme cards */
.glass-btn           /* Standard buttons */
.glass-btn-primary   /* Primary action buttons */
.glass-modal         /* Modal dialogs */
.glass-nav           /* Navigation bars */
```

### Mobile Breakpoints
```css
/* Mobile First Approach */
/* Base: 320px+ (Mobile) */
/* sm: 640px+ (Large Mobile) */
/* md: 768px+ (Tablet) */
/* lg: 1024px+ (Desktop) */
/* xl: 1280px+ (Large Desktop) */
```

### Touch Target Standards
- Minimum 44px height for all interactive elements
- 8px minimum spacing between touch targets
- Visual feedback on touch (hover states)

---

## 📊 Progress Tracking

### Overall Progress: 93% Complete
- ✅ **Phase 1**: 5/5 tasks complete (100%)
- ✅ **Phase 2**: 5/5 tasks complete (100%)
- ✅ **Phase 3**: 4/5 tasks complete (80%) — Testing pending manual QA

### Priority Status
| Priority | Tasks | Complete | Remaining | Est. Hours |
|----------|-------|----------|-----------|------------|
| P0 Critical | 5 | 5 | 0 | 0h |
| P1 High | 5 | 5 | 0 | 0h |
| P2 Polish | 5 | 4 | 1 | 4h |
| **Total** | **15** | **14** | **1** | **4h** |

---

## 🎯 Success Metrics

### Before Implementation
- Mobile bounce rate: ~65%
- Mobile conversion: ~2.1%
- iOS zoom issues: 8 pages affected
- Touch target failures: 12 pages

### Target After Implementation
- Mobile bounce rate: <45%
- Mobile conversion: >4.5%
- iOS zoom issues: 0 pages
- Touch target compliance: 100%

---

## 🚀 Quick Start Commands

### Development Setup
```bash
# Start development server
./start.sh

# Watch CSS changes
npx tailwindcss -i ./static/css/glassmorphism.css -o ./static/css/compiled.css --watch

# Mobile testing
# Use Chrome DevTools device emulation
# Test on actual devices when possible
```

### Testing Checklist
```bash
# Per task completion:
□ Desktop Chrome (1920px)
□ Desktop Safari (1440px)
□ iPad (768px)
□ iPhone 14 (393px)
□ Android (360px)
□ Accessibility check
□ Performance check (<3s load)
```

---

## 📝 Notes & Considerations

### Technical Debt
- Legacy CSS conflicts with glassmorphism
- Some templates use inline styles
- Inconsistent component naming

### Browser Support
- Modern browsers only (CSS backdrop-filter)
- Graceful degradation for older browsers
- Safari-specific webkit prefixes included

### Performance Impact
- Glassmorphism adds GPU load
- Monitor frame rates on older devices
- Consider reduced motion preferences

---

## 🔄 Review & Approval Process

### Task Completion Criteria
1. ✅ Visual design matches mockups
2. ✅ Responsive across all breakpoints
3. ✅ Touch targets meet 44px minimum
4. ✅ No horizontal scroll on mobile
5. ✅ Performance <3s load time
6. ✅ Accessibility compliance
7. ✅ Cross-browser testing complete

### Sign-off Required
- [ ] **Developer**: Technical implementation
- [ ] **Designer**: Visual design approval
- [ ] **QA**: Cross-device testing
- [ ] **Product**: User experience validation

---

**Last Updated**: May 18, 2026
**Next Action**: Task 3.3 — Cross-device testing (manual QA required)
