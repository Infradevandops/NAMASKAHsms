# Sidebar Navigation Assessment - VRENUM ACTV8TN

**Date**: Current
**Status**: Comprehensive Backend Integration Analysis
**Version**: 4.7.1

---

## 📋 Executive Summary

The sidebar navigation is a **tier-aware, dynamically enriched component** that serves as the primary navigation hub for the platform. It features **6 main sections** with **23 navigation items**, intelligent tier-gating, and real-time backend synchronization.

---

## 🏗️ Architecture Overview

### Component Structure
- **Location**: `/templates/components/sidebar.html`
- **Type**: Jinja2 Template with embedded JavaScript
- **Backend Integration**: REST API calls to `/api/v1/billing/tiers/current`
- **State Management**: localStorage + sessionStorage
- **Tier System**: 4-tier hierarchy (Freemium → PAYG → Pro → Custom)

### Key Features
1. **Tier-Based Access Control** - Features locked/unlocked based on subscription
2. **Dynamic Visibility** - Items shown with upgrade prompts for locked features
3. **Real-time Sync** - User tier loaded on page load
4. **Internationalization** - Multi-language support (9 languages)
5. **Accessibility** - ARIA labels, keyboard navigation, screen reader support
6. **Responsive Design** - Mobile-friendly with collapsible sidebar

---

## 🎯 Sidebar Sections & Backend Integration

### 1️⃣ **MAIN SECTION**

#### Dashboard
- **Route**: `/dashboard`
- **Backend API**: `/api/analytics/summary`
- **Data Enrichment**:
  - Total verifications count
  - Success rate percentage
  - Total spent (from Balance Ledger)
  - Recent activity (last 10 verifications)
  - Daily verification trends (30 days)
  - Top services by usage
  - Monthly spending with change percentage
- **Database Tables**:
  - `verifications` - SMS verification records
  - `balance_transactions` - Financial ledger (single source of truth)
  - `users` - User credits balance
- **Real-time Updates**: Refreshes every 30 seconds
- **Widgets**:
  - Tier information card (current plan, features, pricing)
  - Quota usage bar (for Pro/Custom tiers)
  - API usage stats (for Pro+ tiers)
  - 4 stat cards (Total SMS, Successful, Net Spent, Success Rate)
  - Recent activity table with pagination

---

### 2️⃣ **SERVICES SECTION**

#### SMS Verification
- **Route**: `/verify`
- **Backend API**:
  - `POST /api/verify/create` - Create new verification
  - `GET /api/verify/status/{id}` - Check verification status
  - `GET /api/verify/{id}/messages` - Get SMS messages
  - `POST /api/verify/{id}/cancel` - Cancel verification
  - `POST /api/verify/{id}/timeout` - Report timeout
  - `POST /api/verify/{id}/error` - Report error
  - `POST /api/verify/{id}/sms-received` - Confirm SMS receipt
- **Data Enrichment**:
  - Available countries (8+ countries)
  - Available services (1,807+ services)
  - Real-time pricing calculation
  - Carrier lookup (Google libphonenumber)
  - Area code validation
  - Tier-based pricing (Freemium: $2.22, PAYG: $2.50, Pro: $0.30 overage)
- **Database Tables**:
  - `verifications` - Main verification records
  - `purchase_outcomes` - Detailed outcome tracking
  - `balance_transactions` - Debit/refund records
- **Features**:
  - Country/service selection
  - Area code selection (tier-gated: PAYG+)
  - Carrier selection (tier-gated: PAYG+)
  - Real-time SMS polling
  - Automatic refunds on timeout/failure
  - Error categorization (7 categories)
- **Provider Integration**: TextVerified API

#### Voice Verification
- **Route**: `/voice-verify`
- **Tier Requirement**: Premium (Pro+)
- **Backend API**:
  - `POST /api/voice/create` - Create voice verification
  - `GET /api/voice/status/{id}` - Check status
  - `GET /api/voice/audio/{id}` - Get audio file
- **Data Enrichment**:
  - Voice call transcription
  - Audio file URL
  - Call duration tracking
  - Verification code extraction
- **Database Tables**:
  - `verifications` (type='voice')
  - `balance_transactions`
- **Features**:
  - Audio player with playback controls
  - Transcription display
  - Timeout handling (extended to 120 seconds)
  - Area code selection (tier-gated)

#### Number Rentals
- **Route**: `/rentals`
- **Tier Requirement**: Premium (Pro+)
- **Backend API**:
  - `POST /api/rentals/create` - Rent a number
  - `GET /api/rentals/active` - List active rentals
  - `GET /api/rentals/{id}/messages` - Get messages
  - `POST /api/rentals/{id}/extend` - Extend rental
  - `POST /api/rentals/{id}/cancel` - Cancel rental
- **Data Enrichment**:
  - Rental duration (7/14/30 days)
  - Expiry monitoring (background job)
  - Message history
  - Renewal pricing
- **Database Tables**:
  - `rentals` - Rental records
  - `rental_messages` - Received messages
  - `balance_transactions` - Payment records
- **Features**:
  - Multi-day rental periods
  - Automatic expiry notifications
  - Message forwarding
  - Renewal reminders
  - Area code selection (tier-gated)

#### History
- **Route**: `/history`
- **Backend API**: `/api/verify/history`
- **Data Enrichment**:
  - Paginated verification list (50 per page)
  - Multi-status filtering (completed, failed, pending, cancelled, timeout)
  - Phone number search
  - SMS code search
  - Export to CSV
- **Database Tables**:
  - `verifications` - All verification records
- **Features**:
  - Advanced filtering
  - Sortable columns
  - Status badges with color coding
  - Refund indicators
  - Carrier/area code display
  - Latency metrics
  - Export functionality

---

### 3️⃣ **FINANCE SECTION**

#### Wallet
- **Route**: `/wallet`
- **Backend API**:
  - `GET /api/wallet/balance` - Get current balance
  - `GET /api/wallet/transactions` - Transaction history
  - `POST /api/wallet/paystack/initialize` - Start payment
  - `POST /api/wallet/paystack/verify` - Verify payment
  - `POST /api/wallet/paystack/webhook` - Payment webhook
  - `GET /api/wallet/transactions/export` - Export CSV
- **Data Enrichment**:
  - Real-time balance from `users.credits`
  - Transaction history from `balance_transactions` (The Single Source of Truth)
  - Transaction types: CREDIT, DEBIT, REFUND, ADJUSTMENT
  - Payment status tracking
  - Audit trail with immutable records
- **Database Tables**:
  - `users` - Current balance
  - `balance_transactions` - Complete financial ledger
  - `transactions` - Legacy payment records
- **Features**:
  - Paystack payment integration
  - Automatic credit addition
  - Transaction filtering by type/date
  - CSV export with audit metadata
  - Real-time balance updates via WebSocket
  - Currency conversion (15+ currencies)
  - Institutional audit logging

---

### 4️⃣ **DEVELOPER SECTION** (Tier-Gated)

#### API Keys
- **Route**: `/api-keys`
- **Tier Requirement**: Pro+ (10 keys for Pro, unlimited for Custom)
- **Backend API**:
  - `GET /api/keys` - List API keys
  - `POST /api/keys/generate` - Generate new key
  - `DELETE /api/keys/{id}` - Revoke key
  - `GET /api/keys/{id}/usage` - Usage statistics
- **Data Enrichment**:
  - Key generation with secure hashing
  - Usage tracking (calls, SMS sent, errors)
  - Rate limiting per key
  - Last used timestamp
  - IP address logging
- **Database Tables**:
  - `api_keys` - Key records
  - `api_key_usage` - Usage logs
- **Features**:
  - Secure key generation (bcrypt hashed)
  - Usage analytics
  - Rate limit configuration
  - Key expiration
  - Revocation with audit trail

#### API Documentation
- **Route**: `/api-documentation`
- **Tier Requirement**: Pro+
- **Backend API**: Static content with live examples
- **Data Enrichment**:
  - Interactive API explorer
  - Code examples (cURL, Python, JavaScript, PHP)
  - Live request/response examples
  - Authentication guide
  - Error code reference
- **Features**:
  - RESTful API documentation
  - Webhook setup guide
  - Rate limit information
  - Best practices
  - Changelog

#### Webhooks
- **Route**: `/webhooks-management`
- **Tier Requirement**: PAYG+
- **Backend API**:
  - `GET /api/webhooks` - List webhooks
  - `POST /api/webhooks` - Create webhook
  - `PUT /api/webhooks/{id}` - Update webhook
  - `DELETE /api/webhooks/{id}` - Delete webhook
  - `POST /api/webhooks/{id}/test` - Test webhook
- **Data Enrichment**:
  - Event types (sms.completed, payment.success, rental.expiring)
  - Delivery status tracking
  - Retry logic (3 attempts)
  - Signature verification (HMAC-SHA256)
- **Database Tables**:
  - `webhooks` - Webhook configurations
  - `webhook_deliveries` - Delivery logs
- **Features**:
  - Event subscription
  - Automatic retries
  - Delivery logs
  - Test mode
  - Signature verification

---

### 5️⃣ **INTEGRATIONS SECTION**

#### Whitelabel
- **Route**: `/whitelabel`
- **Tier Requirement**: Pro+
- **Backend API**:
  - `GET /api/whitelabel/config` - Get configuration
  - `PUT /api/whitelabel/config` - Update configuration
  - `POST /api/whitelabel/logo` - Upload logo
- **Data Enrichment**:
  - Custom domain setup
  - Brand colors (primary, secondary, accent)
  - Logo upload (PNG, SVG)
  - Custom email templates
  - CNAME configuration
- **Database Tables**:
  - `whitelabel_configs` - Brand configurations
- **Features**:
  - Custom domain mapping
  - Brand color customization
  - Logo upload
  - Email template editor (Pro+ feature)
  - DNS configuration guide

#### Telegram
- **Route**: `/telegram`
- **Tier Requirement**: All tiers
- **Backend API**:
  - `POST /api/telegram/connect` - Connect bot
  - `GET /api/telegram/status` - Connection status
  - `POST /api/telegram/disconnect` - Disconnect bot
- **Data Enrichment**:
  - Bot connection status
  - Chat ID verification
  - Message forwarding settings
- **Database Tables**:
  - `telegram_connections` - User connections
- **Features**:
  - SMS forwarding to Telegram
  - Real-time notifications
  - Bot command interface
  - Connection verification

#### Push Setup
- **Route**: `/push-settings`
- **Tier Requirement**: All tiers
- **Backend API**:
  - `POST /api/push/subscribe` - Subscribe to push
  - `GET /api/push/status` - Subscription status
  - `DELETE /api/push/unsubscribe` - Unsubscribe
- **Data Enrichment**:
  - Browser push subscription
  - Notification preferences
  - Device registration
- **Database Tables**:
  - `push_subscriptions` - Device subscriptions
- **Features**:
  - Browser push notifications
  - OneSignal integration
  - Notification preferences
  - Device management

---

### 6️⃣ **ACCOUNT SECTION**

#### Usage Insights
- **Route**: `/insights`
- **Backend API**: `/api/analytics/insights`
- **Data Enrichment**:
  - Usage trends (daily, weekly, monthly)
  - Cost breakdown by service
  - Success rate trends
  - Peak usage times
  - Carrier performance
  - Area code success rates
- **Database Tables**:
  - `verifications` - Historical data
  - `balance_transactions` - Spending data
- **Features**:
  - Interactive charts (Chart.js)
  - Date range filtering
  - Export to PDF/CSV
  - Trend analysis
  - Recommendations

#### Analytics
- **Route**: `/analytics`
- **Backend API**: `/api/analytics/advanced`
- **Data Enrichment**:
  - Conversion funnel (number assigned → SMS received)
  - Service performance metrics
  - Geographic distribution
  - Time-based analysis
  - Cost optimization insights
- **Database Tables**:
  - `verifications` - Event data
  - `purchase_outcomes` - Outcome tracking
- **Features**:
  - Funnel visualization
  - Cohort analysis
  - A/B testing results
  - Performance benchmarks

#### Support
- **Route**: `/support`
- **Backend API**:
  - `GET /api/support/tickets` - List tickets
  - `POST /api/support/tickets` - Create ticket
  - `GET /api/support/tickets/{id}` - Get ticket details
  - `POST /api/support/tickets/{id}/reply` - Reply to ticket
- **Data Enrichment**:
  - Ticket status (open, in_progress, resolved, closed)
  - Priority levels
  - Response time tracking
  - Agent assignment
- **Database Tables**:
  - `support_tickets` - Ticket records
  - `support_messages` - Ticket messages
- **Features**:
  - Ticket creation
  - File attachments
  - Priority support (Pro+)
  - Live chat (Custom tier)
  - Knowledge base

#### Profile
- **Route**: `/profile`
- **Backend API**:
  - `GET /api/user/profile` - Get profile
  - `PUT /api/user/profile` - Update profile
  - `POST /api/user/avatar` - Upload avatar
  - `PUT /api/user/password` - Change password
- **Data Enrichment**:
  - User details (name, email, phone)
  - Account creation date
  - Last login timestamp
  - Email verification status
  - MFA status
- **Database Tables**:
  - `users` - User records
- **Features**:
  - Profile editing
  - Avatar upload
  - Password change
  - Email verification
  - Account deletion

#### Notification Center
- **Route**: `/notifications`
- **Backend API**:
  - `GET /api/notifications` - List notifications
  - `GET /api/notifications/unread-count` - Unread count
  - `POST /api/notifications/{id}/read` - Mark as read
  - `POST /api/notifications/mark-all-read` - Mark all read
  - `DELETE /api/notifications/{id}` - Delete notification
- **Data Enrichment**:
  - Notification types (sms_completed, payment_success, refund_issued, etc.)
  - Read/unread status
  - Priority levels
  - Action links
  - Timestamps
- **Database Tables**:
  - `notifications` - Notification records
- **Features**:
  - Real-time notifications (WebSocket)
  - Unread badge counter
  - Notification preferences
  - Bulk actions
  - Auto-dismiss after 30 days

#### Settings
- **Route**: `/settings`
- **Backend API**:
  - `GET /api/user/preferences` - Get preferences
  - `PUT /api/user/preferences` - Update preferences
  - `GET /api/user/sessions` - Active sessions
  - `POST /api/user/logout-all` - Logout all devices
- **Data Enrichment**:
  - Language preference (9 languages)
  - Currency preference (15+ currencies)
  - Timezone
  - Notification preferences
  - Privacy settings
  - Active sessions with device info
- **Database Tables**:
  - `user_preferences` - User settings
  - `user_sessions` - Active sessions (Redis)
- **Features**:
  - Multi-language support
  - Currency selection
  - Notification toggles
  - Session management
  - Privacy controls
  - GDPR data export
  - Account deletion

---

### 7️⃣ **ADMIN SECTION** (Admin Only)

#### Admin Dashboard
- **Route**: `/admin`
- **Tier Requirement**: Admin role (`user.is_admin = True`)
- **Backend API**: `/api/admin/dashboard`
- **Data Enrichment**:
  - Platform-wide statistics
  - Revenue metrics (MRR, ARR, churn)
  - User growth (DAU, MAU, new signups)
  - System health metrics
  - Top users by spending
  - Service performance
  - Fraud detection alerts
- **Database Tables**: All tables (read access)
- **Features**:
  - Real-time metrics
  - User management
  - Tier management
  - KYC verification
  - Support ticket management
  - Refund monitoring
  - Pricing template editor
  - Affiliate program management
  - Audit log viewer

---

### 8️⃣ **SIDEBAR FOOTER**

#### Referrals
- **Route**: `/referrals`
- **Backend API**:
  - `GET /api/referrals/stats` - Referral statistics
  - `GET /api/referrals/code` - Get referral code
  - `POST /api/referrals/generate` - Generate new code
- **Data Enrichment**:
  - Referral code
  - Total referrals
  - Earnings (commission)
  - Conversion rate
  - Pending payouts
- **Database Tables**:
  - `referrals` - Referral records
  - `referral_earnings` - Commission tracking
- **Features**:
  - Unique referral code
  - Commission tracking (10% for Pro, 15% for Custom)
  - Payout management
  - Referral analytics

#### Language Switcher
- **Type**: Dropdown selector
- **Backend API**: `/api/user/preferences` (syncs selection)
- **Supported Languages**:
  1. English (en)
  2. Español (es)
  3. Français (fr)
  4. Deutsch (de)
  5. Português (pt)
  6. 中文 (zh)
  7. 日本語 (ja)
  8. العربية (ar)
  9. हिन्दी (hi)
- **Storage**: localStorage + backend sync
- **Features**:
  - Instant language switching
  - Persistent across sessions
  - RTL support for Arabic

#### Logout
- **Action**: Logout user
- **Backend API**: `POST /api/auth/logout`
- **Process**:
  1. Invalidate JWT token (Redis blacklist)
  2. Clear localStorage
  3. Clear sessionStorage
  4. Redirect to landing page
- **Features**:
  - Confirmation dialog
  - Session cleanup
  - Secure token invalidation

---

## 🔐 Tier-Based Access Control

### Tier Hierarchy
```javascript
const TIER_HIERARCHY = {
    'freemium': 0,  // Free tier
    'payg': 1,      // Pay-As-You-Go
    'pro': 2,       // Pro ($25/mo)
    'custom': 3     // Custom ($35/mo)
};
```

### Access Control Logic
```javascript
function hasTierAccess(userTier, requiredTier) {
    const userLevel = TIER_HIERARCHY[userTier] || 0;
    const requiredLevel = TIER_HIERARCHY[requiredTier] || 0;
    return userLevel >= requiredLevel;
}
```

### Tier-Gated Features

| Feature | Freemium | PAYG | Pro | Custom |
|---------|----------|------|-----|--------|
| SMS Verification | ✅ | ✅ | ✅ | ✅ |
| Voice Verification | ❌ | ❌ | ✅ | ✅ |
| Number Rentals | ❌ | ❌ | ✅ | ✅ |
| Area Code Selection | ❌ | ✅ (+$0.25) | ✅ (included) | ✅ (included) |
| Carrier Selection | ❌ | ✅ (+$0.50) | ✅ (included) | ✅ (included) |
| API Keys | ❌ | ❌ | ✅ (10 keys) | ✅ (unlimited) |
| API Documentation | ❌ | ❌ | ✅ | ✅ |
| Webhooks | ❌ | ✅ | ✅ | ✅ |
| Whitelabel | ❌ | ❌ | ✅ | ✅ |
| Email Templates | ❌ | ❌ | ✅ | ✅ |
| Priority Support | ❌ | ❌ | ✅ | ✅ |
| Dedicated Support | ❌ | ❌ | ❌ | ✅ |

### Locked Feature Behavior
When a user clicks a locked feature:
1. **Visual Indicator**: 🔒 icon appears
2. **Opacity**: Item dimmed to 60%
3. **Click Handler**: Shows upgrade prompt
4. **Prompt Message**: "Feature requires [Tier] tier. Upgrade now?"
5. **Action**: Redirects to `/pricing` if confirmed

---

## 🔄 Backend Synchronization

### On Page Load
1. **Fetch User Tier**: `GET /api/v1/billing/tiers/current`
2. **Update Sidebar Visibility**: Apply tier-based access control
3. **Load Unread Notifications**: `GET /api/notifications/unread-count`
4. **Sync Preferences**: Load language/currency from backend

### Real-time Updates
- **WebSocket Events**: Payment success, SMS completion, rental expiry
- **Notification Badge**: Updates on new notifications
- **Balance Updates**: Reflects in header balance component
- **Tier Changes**: Immediately unlocks/locks features

### Data Flow
```
User Action → Frontend → API Endpoint → Service Layer → Database
                ↓
         Update UI ← WebSocket ← Event Emitter ← Service Layer
```

---

## 📊 Database Tables Used

### Core Tables
1. **users** - User accounts, credits, tier
2. **verifications** - SMS/voice verification records
3. **balance_transactions** - Financial ledger (SSOT)
4. **transactions** - Legacy payment records
5. **notifications** - User notifications
6. **api_keys** - API key management
7. **webhooks** - Webhook configurations
8. **rentals** - Number rental records
9. **referrals** - Referral tracking
10. **support_tickets** - Support system

### Admin Tables
11. **subscription_tiers** - Tier definitions
12. **pricing_templates** - Dynamic pricing
13. **audit_logs** - Admin action logs
14. **fraud_scores** - Fraud detection
15. **affiliate_programs** - Affiliate management

---

## 🎨 UI/UX Features

### Visual Design
- **Color Scheme**: White background, pink primary (#FE3C72)
- **Typography**: 15px body, 18px headings, 800 weight
- **Spacing**: 12px padding, 12px gaps
- **Border Radius**: 12px for items, 8px for logo
- **Shadows**: Soft shadows on active items

### Interactions
- **Hover**: Pink background (#FFF5F7), pink text
- **Active**: Gradient background, white text, shadow
- **Tooltips**: Show on hover when collapsed
- **Transitions**: 0.2s smooth transitions

### Accessibility
- **ARIA Labels**: All items have proper labels
- **Keyboard Navigation**: Tab/Enter support
- **Screen Reader**: Semantic HTML, role attributes
- **Focus Indicators**: 2px pink outline
- **Color Contrast**: WCAG AA compliant

### Responsive Behavior
- **Desktop**: Fixed sidebar, 260px width
- **Tablet**: Collapsible sidebar
- **Mobile**: Off-canvas sidebar, hamburger menu
- **Breakpoint**: 768px

---

## 🚀 Performance Optimizations

### Caching Strategy
- **User Tier**: Cached in memory after first load
- **Service Names**: Cached in ServiceStore
- **Translations**: Embedded in page, no network call
- **Icons**: Inline SVG, no external requests

### Lazy Loading
- **Notifications**: Loaded on demand
- **Activity Feed**: Paginated, 10 items per page
- **Transaction History**: Paginated, 50 items per page

### Network Optimization
- **Batch Requests**: Multiple stats in single API call
- **Debouncing**: Search inputs debounced 300ms
- **Abort Controllers**: Cancel pending requests on navigation
- **Timeouts**: 8-second timeout for tier API

---

## 🔧 Technical Implementation

### JavaScript Architecture
```javascript
// Tier loading
async function loadUserTierForSidebar() {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/v1/billing/tiers/current', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    currentUserTier = data.current_tier || 'freemium';
    updateSidebarVisibility(currentUserTier);
}

// Visibility update
function updateSidebarVisibility(userTier) {
    document.querySelectorAll('.nav-item.tier-gated').forEach(item => {
        const requiredTier = item.dataset.minTier;
        const hasAccess = hasTierAccess(userTier, requiredTier);

        if (!hasAccess) {
            item.classList.add('locked');
            item.onclick = (e) => {
                e.preventDefault();
                showUpgradePrompt(requiredTier, item.textContent.trim());
            };
        }
    });
}
```

### Backend API Pattern
```python
@router.get("/api/v1/billing/tiers/current")
async def get_current_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    tier = user.subscription_tier or 'freemium'

    return {
        "current_tier": tier,
        "features": get_tier_features(tier),
        "limits": get_tier_limits(tier)
    }
```

---

## 📈 Analytics & Monitoring

### Tracked Metrics
- **Navigation Clicks**: Track which tabs are most used
- **Tier Upgrade Prompts**: Track locked feature clicks
- **API Call Success Rate**: Monitor backend health
- **Load Times**: Track sidebar initialization time
- **Error Rates**: Track failed API calls

### Logging
- **Frontend Logger**: Logs tier loads, API calls, errors
- **Backend Logger**: Logs authentication, authorization, data access
- **Audit Trail**: All admin actions logged

---

## 🎯 Key Takeaways

### Strengths
✅ **Comprehensive Feature Set** - 23 navigation items covering all platform features
✅ **Intelligent Tier Gating** - Smooth upgrade prompts, no broken links
✅ **Real-time Sync** - WebSocket updates, live notifications
✅ **Accessibility** - WCAG compliant, keyboard navigation
✅ **Internationalization** - 9 languages supported
✅ **Performance** - Optimized caching, lazy loading
✅ **Security** - JWT authentication, tier-based authorization

### Backend Integration Quality
- **API Coverage**: 50+ endpoints powering sidebar features
- **Data Consistency**: Single source of truth (Balance Ledger)
- **Error Handling**: Graceful degradation, fallback values
- **Real-time Updates**: WebSocket for instant notifications
- **Audit Trail**: Complete logging for compliance

### User Experience
- **Discoverability**: All features visible, locked items show upgrade path
- **Feedback**: Clear status indicators, loading states
- **Responsiveness**: Mobile-friendly, touch-optimized
- **Consistency**: Unified design language across all tabs

---

**End of Assessment**

**Total Navigation Items**: 23
**Backend APIs**: 50+
**Database Tables**: 15+
**Supported Languages**: 9
**Tier Levels**: 4
**Real-time Features**: 5 (WebSocket, notifications, balance, tier changes, SMS status)
