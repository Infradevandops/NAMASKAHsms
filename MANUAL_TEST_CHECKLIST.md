# Dashboard Manual Test Checklist

**Date**: January 2026  
**Tester**: ___________  
**Browser**: ___________  
**Status**: 🔄 In Progress

---

## 🎯 Main Sidebar Tests

### Navigation Links
- [ ] Click "Dashboard" → Navigates to /dashboard
- [ ] Click "SMS Verification" → Navigates to /verify
- [ ] Click "Wallet" → Navigates to /wallet
- [ ] Click "History" → Navigates to /history
- [ ] Click "Analytics" → Navigates to /analytics
- [ ] Click "Pricing" → Navigates to /pricing
- [ ] Click "Notifications" → Navigates to /notifications
- [ ] Click "Settings" → Navigates to /settings

### Sidebar Features
- [ ] Active page is highlighted with gradient
- [ ] Hover effects work on all items
- [ ] Notification badge shows count
- [ ] Language switcher dropdown works
- [ ] Logout button shows confirmation
- [ ] Mobile: Hamburger menu toggles sidebar

### Tier-Gated Items (Check visibility based on tier)
- [ ] Voice Verify (PAYG+) - Hidden for Freemium
- [ ] Bulk Purchase (Pro+) - Hidden for lower tiers
- [ ] API Keys (PAYG+) - Hidden for Freemium
- [ ] Webhooks (PAYG+) - Hidden for Freemium
- [ ] Referrals (PAYG+) - Hidden for Freemium

---

## ⚙️ Settings Page Tests

### Tab Switching
- [ ] Click "Account" tab → Shows account info
- [ ] Click "Security" tab → Shows password reset
- [ ] Click "Notifications" tab → Shows toggles
- [ ] Click "Billing" tab → Shows plans
- [ ] Click "API Keys" tab (PAYG+) → Shows keys
- [ ] Click "SMS Forwarding" tab (PAYG+) → Shows config
- [ ] Click "Blacklist" tab (PAYG+) → Shows numbers

### Account Tab
- [ ] Email address displays correctly
- [ ] User ID displays correctly
- [ ] Account created date displays

### Security Tab
- [ ] "Request Password Reset Email" button works
- [ ] Shows confirmation message

### Notifications Tab
- [ ] Email notifications toggle works
- [ ] SMS alerts toggle works
- [ ] Settings save automatically

### Billing Tab
- [ ] Current tier displays correctly
- [ ] "Upgrade" button redirects to /pricing
- [ ] Payment history table loads
- [ ] "Request Refund" button opens modal
- [ ] Refund modal has all fields
- [ ] Refund submission works

### API Keys Tab (PAYG+)
- [ ] "Generate New Key" button works
- [ ] API keys list displays
- [ ] "Delete" button shows confirmation
- [ ] Key deletion works

### SMS Forwarding Tab (PAYG+)
- [ ] Email forwarding toggle works
- [ ] Email address field appears when enabled
- [ ] Webhook forwarding toggle works
- [ ] Webhook URL field appears when enabled
- [ ] "Generate" secret button works
- [ ] "Save Configuration" button works
- [ ] "Test Forwarding" button works

### Blacklist Tab (PAYG+)
- [ ] "Add Number" button opens modal
- [ ] "Bulk Import" button opens modal
- [ ] Search/filter works
- [ ] Pagination works
- [ ] "Remove" button works per number
- [ ] CSV file upload works
- [ ] Bulk import processes correctly

---

## 💰 Wallet Page Tests

### Payment Buttons
- [ ] "$10" button triggers payment
- [ ] "$25" button triggers payment
- [ ] "$50" button triggers payment (shows +10%)
- [ ] "$100" button triggers payment (shows +15%)
- [ ] Custom amount input works
- [ ] "Add Custom" button works

### Crypto Payment
- [ ] "Crypto" tab switches view
- [ ] Crypto amount buttons work
- [ ] QR code generates
- [ ] "Copy" address button works
- [ ] "I have sent payment" button works

### Features
- [ ] Balance displays correctly
- [ ] Monthly spent displays
- [ ] Total spent displays
- [ ] "📊 View" summary card opens modal
- [ ] Monthly summary modal shows data
- [ ] Credit history table loads
- [ ] Credit type filter works
- [ ] "Export CSV" button works
- [ ] Transactions table loads
- [ ] Pagination works (10 per page)
- [ ] Auto-reload settings display
- [ ] Pending transactions display (if any)
- [ ] Spending alerts settings display

---

## 📱 Verify Page Tests

### Main Form
- [ ] Service search input works
- [ ] Service dropdown appears
- [ ] Service selection works
- [ ] Cost updates when service selected
- [ ] "Get SMS Code" button works
- [ ] Phone number displays after purchase
- [ ] SMS code displays when received
- [ ] "Copy Code" button works
- [ ] "Cancel" button works

### Sidebar Features
- [ ] Favorites list displays
- [ ] Click favorite → Selects service
- [ ] "⭐" button adds to favorites
- [ ] Remove (×) button works
- [ ] Templates list displays
- [ ] "+ Save" button opens modal
- [ ] Template save modal works
- [ ] Click template → Applies settings
- [ ] Template remove (×) works

### Premium Features
- [ ] Area code dropdown (PAYG+)
- [ ] Carrier dropdown (Pro+)
- [ ] Quick presets (Pro+)
- [ ] Lock messages show for lower tiers

---

## 📊 Dashboard Page Tests

### Stat Cards
- [ ] Balance card displays with purple gradient
- [ ] This month card displays with green gradient
- [ ] Total verifications card displays with orange gradient
- [ ] Success rate card displays with blue gradient

### Activity Table
- [ ] Recent activity loads
- [ ] Pagination works (10 per page)
- [ ] Mobile: Converts to card layout

---

## 📈 Analytics Page Tests

### Controls
- [ ] Date range picker works
- [ ] Start date input works
- [ ] End date input works
- [ ] "Export CSV" button works

### Charts
- [ ] Verifications over time chart loads
- [ ] Status breakdown pie chart loads
- [ ] Spending by service bar chart loads
- [ ] Charts are lazy-loaded (check network)

### Tables
- [ ] Top services table displays
- [ ] Data matches selected date range

---

## 🔔 Notification Bell Tests

### Header Notification
- [ ] Bell icon displays in header
- [ ] Badge shows unread count
- [ ] Click bell → Opens dropdown
- [ ] Dropdown shows notifications
- [ ] "Mark all read" button works
- [ ] Click notification → Marks as read
- [ ] Dropdown closes on outside click

---

## 🌐 Global Features Tests

### Error Handling
- [ ] Offline banner appears when offline
- [ ] Retry button works
- [ ] Error toasts display correctly
- [ ] User-friendly error messages

### Loading States
- [ ] Loading skeletons appear
- [ ] Skeletons disappear when loaded
- [ ] Spinner animations work

### Real-time Updates
- [ ] WebSocket connects
- [ ] Balance updates in real-time
- [ ] Notifications arrive instantly
- [ ] SMS codes appear without refresh

### Mobile Responsiveness
- [ ] All pages work on mobile
- [ ] Tables convert to cards
- [ ] Touch targets are 44px minimum
- [ ] No horizontal scrolling
- [ ] Modals fit on screen

### Accessibility
- [ ] Tab navigation works
- [ ] Focus indicators visible
- [ ] ARIA labels present
- [ ] Screen reader compatible
- [ ] Keyboard shortcuts work

---

## 🎯 Critical User Flows

### New User Flow
1. [ ] Register account
2. [ ] Verify email
3. [ ] Add credits
4. [ ] Purchase first verification
5. [ ] Receive SMS code
6. [ ] Copy code

### Payment Flow
1. [ ] Click payment amount
2. [ ] Redirect to Paystack
3. [ ] Complete payment
4. [ ] Return to dashboard
5. [ ] Balance updates
6. [ ] Transaction appears in history

### Verification Flow
1. [ ] Search for service
2. [ ] Select service
3. [ ] Click "Get SMS Code"
4. [ ] Phone number displays
5. [ ] Wait for SMS
6. [ ] Code displays
7. [ ] Copy code
8. [ ] Use code

---

## 📝 Issues Found

### Critical (Blocks functionality)
- Issue 1: ___________
- Issue 2: ___________

### High (Degrades experience)
- Issue 1: ___________
- Issue 2: ___________

### Medium (Minor issues)
- Issue 1: ___________
- Issue 2: ___________

### Low (Cosmetic)
- Issue 1: ___________
- Issue 2: ___________

---

## ✅ Sign-off

**Tester**: ___________  
**Date**: ___________  
**Status**: [ ] PASS [ ] FAIL  
**Notes**: ___________

---

**Total Tests**: 150+  
**Estimated Time**: 2-3 hours  
**Recommended**: Test on Chrome, Firefox, Safari, Mobile
