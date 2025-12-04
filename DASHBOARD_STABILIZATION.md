# Dashboard Stabilization Plan

**Project:** Namaskah SMS Platform  
**Goal:** Stabilize dashboard to industry-standard, functional state  
**Approach:** Surgical fixes only - NO refactoring, NO breaking changes  
**Priority:** Fix what's broken, then polish

---

## Phase 1: Critical Bug Fixes
**Timeline:** Immediate  
**Risk:** Low

### 1.1 Fix Modal Close Button (X)
- [ ] Ensure X button has consistent styling across all modals
- [ ] Add `z-index` to prevent button from being hidden
- [ ] Test on mobile and desktop

**Acceptance Criteria:**
- X button visible at all times in modal header
- Clicking X closes modal and resets state
- Works on all screen sizes

**Files:** `static/css/verification-modal.css`, `static/css/dashboard.css`

### 1.2 Remove Duplicate Code
- [ ] Remove inline `loadBalance()` from `dashboard.html` (keep in `dashboard.js`)
- [ ] Remove embedded verification modal from `dashboard.html` (use include or single source)
- [ ] Consolidate duplicate CSS rules

**Acceptance Criteria:**
- No duplicate function definitions
- Single source of truth for modal HTML
- No console errors about redefined functions

**Files:** `templates/dashboard.html`, `static/js/dashboard.js`

### 1.3 Fix JWT Token Issue
- [x] Use `jwt_secret_key` consistently for token creation/verification
- [ ] Verify token persists across page navigation
- [ ] Test login → dashboard → API calls flow

**Acceptance Criteria:**
- User stays logged in after login
- All API calls return 200 (not 401)
- Balance and activity load correctly

**Files:** `app/utils/security.py`, `app/core/dependencies.py`

---

## Phase 2: Header & Navigation
**Timeline:** 1 day  
**Risk:** Low

### 2.1 Header Right Section
- [ ] Add notification bell icon (with badge for unread count)
- [ ] Add user avatar/initials circle
- [ ] Add dropdown menu on user click (Profile, Settings, Logout)
- [ ] Style balance display consistently

**Acceptance Criteria:**
- Header shows: Balance | Notifications | User Avatar
- Notification badge shows count (or hidden if 0)
- User dropdown works on click
- Responsive on mobile (icons collapse to menu)

**Files:** `templates/dashboard.html`, `static/css/dashboard.css`, `static/js/dashboard.js`

### 2.2 Sidebar Polish
- [ ] Active state highlights correctly on all nav items
- [ ] Collapsed state works properly
- [ ] Icons visible in collapsed mode
- [ ] Smooth transitions

**Acceptance Criteria:**
- Current page highlighted in sidebar
- Sidebar toggle remembers state (localStorage)
- No layout shift on toggle
- Touch-friendly on mobile

**Files:** `static/css/dashboard.css`, `static/js/dashboard.js`

---

## Phase 3: Home Tab
**Timeline:** 1 day  
**Risk:** Low

### 3.1 Stats Cards
- [ ] Connect to real API endpoints for stats
- [ ] Show loading skeleton while fetching
- [ ] Handle API errors gracefully
- [ ] Format numbers properly (commas, decimals)

**API Endpoints:**
- `GET /api/dashboard/stats` → total verifications, success rate, active rentals
- `GET /api/user/balance` → account balance

**Acceptance Criteria:**
- Stats load within 2 seconds
- Loading state shown during fetch
- Error state if API fails (not blank)
- Numbers formatted: 1,234 not 1234

**Files:** `static/js/dashboard.js`, `templates/dashboard.html`

### 3.2 Recent Activity
- [ ] Load from `/api/dashboard/activity/recent`
- [ ] Show service name, phone, cost, status, time
- [ ] Status badges (completed=green, pending=yellow, failed=red)
- [ ] "No activity" message if empty
- [ ] Pagination or "View All" link

**Acceptance Criteria:**
- Shows last 10 activities
- Each item shows: Service | Phone | Cost | Status | Time
- Clickable to view details (optional)
- Empty state message if no activity

**Files:** `static/js/dashboard.js`

### 3.3 Quick Actions
- [ ] "New Verification" button opens modal
- [ ] "Add Credits" button opens wallet modal
- [ ] Buttons disabled during loading states

**Acceptance Criteria:**
- Buttons clearly visible
- Hover states work
- Loading spinner when processing

---

## Phase 4: Verification Flow
**Timeline:** 1-2 days  
**Risk:** Medium

### 4.1 Modal Stability
- [ ] Single modal instance (not duplicated)
- [ ] Cancel button on all steps
- [ ] X button always visible
- [ ] Escape key closes modal
- [ ] Click outside closes modal (optional)

**Acceptance Criteria:**
- Modal opens/closes without errors
- State resets when closed
- No memory leaks (polling cleared)

**Files:** `templates/dashboard.html`, `static/js/verification-modal.js`

### 4.2 Step 1: Country Selection
- [ ] Load countries from `/api/countries/`
- [ ] Show loading state while fetching
- [ ] Search/filter countries (optional)
- [ ] Cancel and Next buttons

**Acceptance Criteria:**
- Countries load and display in dropdown
- User can select country
- Next disabled until country selected
- Cancel closes modal

### 4.3 Step 2: Service Selection
- [ ] Load services from `/api/countries/{code}/services`
- [ ] Show service name and price
- [ ] Back and Next buttons

**Acceptance Criteria:**
- Services load for selected country
- Price displayed for each service
- User can go back to change country

### 4.4 Step 3: Confirmation
- [ ] Show summary: Country, Service, Cost, Balance
- [ ] Warn if insufficient balance
- [ ] Back and Purchase buttons

**Acceptance Criteria:**
- All details displayed correctly
- "Insufficient balance" warning if needed
- Purchase button disabled if insufficient funds

### 4.5 Step 4: Code Retrieval
- [ ] Show phone number with copy button
- [ ] Poll for SMS code every 3 seconds
- [ ] Show spinner while waiting
- [ ] Display code when received
- [ ] Copy code button
- [ ] Close button

**Acceptance Criteria:**
- Phone number displayed immediately
- Polling starts automatically
- Code appears when SMS received
- Copy buttons work
- Polling stops after 5 minutes or on close

---

## Phase 5: Wallet Tab
**Timeline:** 1 day  
**Risk:** Medium

### 5.1 Balance Display
- [ ] Large balance display at top
- [ ] Formatted with currency symbol
- [ ] Auto-refresh on focus

**Acceptance Criteria:**
- Balance prominent and readable
- Updates after transactions
- Shows $0.00 not blank if zero

### 5.2 Add Credits Modal
- [ ] Package selection ($10, $25, $50, $100)
- [ ] Custom amount input
- [ ] Bonus display (+$1, +$3, etc.)
- [ ] Proceed and Cancel buttons

**Acceptance Criteria:**
- Packages clickable and highlight when selected
- Custom amount overrides package
- Total calculated correctly

### 5.3 Payment Integration
- [ ] Connect to `/api/billing/add-credits` or Paystack
- [ ] Handle success response
- [ ] Handle error response
- [ ] Update balance after success

**Acceptance Criteria:**
- Payment initiates without error
- Success: balance updates, modal closes, success message
- Error: clear error message, modal stays open

### 5.4 Transaction History
- [ ] Load from `/api/billing/transactions`
- [ ] Show type, amount, date, status
- [ ] Pagination or infinite scroll

**Acceptance Criteria:**
- Transactions load and display
- Positive amounts green, negative red
- Date formatted nicely
- Empty state if no transactions

---

## Phase 6: Rentals Tab
**Timeline:** 1 day  
**Risk:** Low

### 6.1 Rentals List
- [ ] Load active rentals from `/api/rentals/active`
- [ ] Show phone number, service, expiry, status
- [ ] Renew and Cancel actions

**Acceptance Criteria:**
- Active rentals displayed
- Expiry countdown or date shown
- Actions work correctly

### 6.2 New Rental Modal
- [ ] Country and service selection
- [ ] Duration selection (1 day, 7 days, 30 days)
- [ ] Price display
- [ ] Purchase flow

**Acceptance Criteria:**
- Modal opens from "New Rental" button
- Duration affects price
- Purchase deducts credits

### 6.3 Rental Messages
- [ ] View received SMS for rental
- [ ] Copy message content
- [ ] Mark as read

**Acceptance Criteria:**
- Messages load for selected rental
- New messages highlighted
- Copy works

---

## Phase 7: Profile Tab
**Timeline:** 0.5 day  
**Risk:** Low

### 7.1 Profile Form
- [ ] Display current user info (email, name, phone, country)
- [ ] Email field disabled (not editable)
- [ ] Save and Cancel buttons
- [ ] Connect to `/api/user/profile` PUT

**Acceptance Criteria:**
- Current data loads into form
- Changes save successfully
- Success/error feedback shown
- Cancel reverts changes

### 7.2 Avatar (Optional)
- [ ] Show user initials or uploaded avatar
- [ ] Upload new avatar
- [ ] Remove avatar option

**Acceptance Criteria:**
- Avatar displays in header and profile
- Upload works (if implemented)

---

## Phase 8: Settings Tab
**Timeline:** 0.5 day  
**Risk:** Low

### 8.1 Notification Settings
- [ ] Email notifications toggle
- [ ] SMS notifications toggle
- [ ] Save preference to API

**Acceptance Criteria:**
- Toggles reflect current settings
- Changes persist after page reload

### 8.2 Security Settings
- [ ] Change password button/form
- [ ] Current password required
- [ ] New password validation (8+ chars)

**Acceptance Criteria:**
- Password change works
- Validation errors shown
- Success message on change

### 8.3 Data Export
- [ ] Export my data button
- [ ] Downloads JSON file

**Acceptance Criteria:**
- Button triggers download
- File contains user data

---

## Phase 9: Polish & UX
**Timeline:** 1 day  
**Risk:** Low

### 9.1 Loading States
- [ ] Skeleton loaders for cards
- [ ] Spinner for buttons during action
- [ ] Disabled state during loading

**Acceptance Criteria:**
- No blank screens during load
- User knows something is happening
- Can't double-click buttons

### 9.2 Error Handling
- [ ] Toast notifications for errors
- [ ] Retry buttons where appropriate
- [ ] Graceful degradation

**Acceptance Criteria:**
- Errors don't crash the page
- User gets actionable feedback
- Can retry failed actions

### 9.3 Empty States
- [ ] "No verifications yet" with CTA
- [ ] "No transactions" message
- [ ] "No rentals" with CTA

**Acceptance Criteria:**
- Empty states have helpful message
- CTA buttons to take action

### 9.4 Mobile Responsiveness
- [ ] Test all views on mobile
- [ ] Sidebar collapses properly
- [ ] Modals fit screen
- [ ] Touch targets 44px minimum

**Acceptance Criteria:**
- Usable on 375px width
- No horizontal scroll
- All buttons tappable

---

## API Endpoints Required

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/user/balance` | GET | Get user credits | ✅ Exists |
| `/api/user/profile` | GET/PUT | Get/update profile | ✅ Exists |
| `/api/dashboard/stats` | GET | Dashboard statistics | ⚠️ Verify |
| `/api/dashboard/activity/recent` | GET | Recent activity | ✅ Exists |
| `/api/countries/` | GET | List countries | ✅ Exists |
| `/api/countries/{code}/services` | GET | Services by country | ✅ Exists |
| `/api/verify/create` | POST | Create verification | ✅ Exists |
| `/api/verify/{id}/status` | GET | Check SMS status | ✅ Exists |
| `/api/billing/add-credits` | POST | Add credits | ⚠️ Fix needed |
| `/api/billing/transactions` | GET | Transaction history | ⚠️ Verify |
| `/api/rentals/active` | GET | Active rentals | ⚠️ Verify |
| `/api/rentals/create` | POST | Create rental | ⚠️ Verify |
| `/api/notifications/unread` | GET | Unread count | ❌ May need |

---

## Testing Checklist

### Functional Tests
- [ ] Login → Dashboard loads
- [ ] All sidebar links work
- [ ] Balance displays correctly
- [ ] Verification flow completes
- [ ] Add credits works
- [ ] Profile saves
- [ ] Logout works

### Cross-Browser
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### Mobile
- [ ] iOS Safari
- [ ] Android Chrome

### Performance
- [ ] Page load < 3 seconds
- [ ] No memory leaks
- [ ] Smooth animations

---

## Success Criteria

**Dashboard is considered stable when:**

1. ✅ User can login and stay logged in
2. ✅ All navigation works without errors
3. ✅ Balance displays and updates correctly
4. ✅ Verification flow works end-to-end
5. ✅ Credits can be added (test mode OK)
6. ✅ Profile can be viewed and edited
7. ✅ No console errors in normal usage
8. ✅ Mobile-friendly
9. ✅ Loading states prevent confusion
10. ✅ Errors are handled gracefully

---

## Notes

- **DO NOT** refactor backend APIs
- **DO NOT** change database schema
- **DO NOT** restructure file organization
- **ONLY** fix frontend bugs and connect to existing APIs
- **TEST** each change before moving to next task
- **COMMIT** after each completed task
