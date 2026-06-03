# Driver.js Onboarding Tour - Production Implementation Taskfile

**Version**: 4.8.2
**Created**: May 18, 2026
**Status**: ✅ IMPLEMENTED - Testing Phase
**Estimated Time**: 3-4 hours
**Target**: Non-intrusive tooltip-style onboarding with arrows pointing to UI elements

---

## 🎯 Objective

Replace the full-screen `/welcome` wizard with a **non-intrusive driver.js tooltip tour** that:
- Guides users with **arrows pointing** to currency selector, language selector, and key features
- Allows users to **interact with real UI elements** during the tour
- Is **dismissible** at any point without blocking dashboard access
- Auto-starts on first login, never shows again after completion
- Is **production-stable** with proper error handling and CSP compliance

---

## 📋 Pre-Implementation Checklist

- [ ] Backup current working state: `git commit -am "checkpoint: before driver.js tour"`
- [ ] Verify driver.js CDN availability: https://cdn.jsdelivr.net/npm/driver.js@1.3.1/
- [ ] Check CSP policy allows CDN scripts or use nonce
- [ ] Test on Chrome, Firefox, Safari (desktop + mobile)
- [ ] Ensure database has `onboarding_completed` column in users table

---

## Phase 1: Audit Current State (30 min)

### Task 1.1: Identify Current Welcome Flow
**Goal**: Map how users currently experience onboarding

**Steps**:
1. [ ] Check login redirect logic in `app/api/auth_routes.py` or `app/api/core/auth.py`
   - Find: `if not user.onboarding_completed: return RedirectResponse("/welcome")`
   - Note: Line number and file path

2. [ ] Verify `/welcome` route registration
   - File: `app/api/main_routes.py` or `main.py`
   - Confirm route exists: `@app.get("/welcome")`

3. [ ] Check `User` model for onboarding fields
   - File: `app/models/user.py`
   - Confirm fields: `onboarding_completed`, `onboarding_step`

4. [ ] Verify backend API endpoints exist
   - `GET /api/auth/onboarding-status` - returns `{completed: bool, step: int}`
   - `PUT /api/auth/onboarding-complete` - marks tour done

**Output**: Document current flow in comments

---

### Task 1.2: Identify Dashboard UI Elements
**Goal**: Find exact selectors for tour targets

**File**: `templates/dashboard_base.html`

1. [ ] Find currency selector button
   - Current ID: `__________________` (fill in)
   - If no ID, note element type and classes

2. [ ] Find language selector button (if exists)
   - Current ID: `__________________`
   - Location: Header / Settings dropdown

3. [ ] Find tier/plan badge
   - Current ID: `__________________`
   - Text content: "Freemium" / "Pro" / etc.

4. [ ] Find primary action button (Verify/Start)
   - Current ID: `__________________`
   - Location: Sidebar or hero section

5. [ ] Find History link
   - Current ID: `__________________`
   - Sidebar nav item

6. [ ] Find API Keys link (Pro feature)
   - Current ID: `__________________`
   - Sidebar nav item

**Output**: List of 6 selectors with IDs or fallback queries

---

## Phase 2: Install Driver.js (30 min)

### Task 2.1: Add Driver.js to Dashboard Base Template
**File**: `templates/dashboard_base.html`

**Location**: Inside `<head>` section, before closing `</head>`

```html
<!-- Driver.js - Product Tour Library -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/driver.js@1.3.1/dist/driver.css">
<script src="https://cdn.jsdelivr.net/npm/driver.js@1.3.1/dist/driver.js.iife.js"></script>
```

**CSP Compliance Check**:
- [ ] If CSP blocks CDN, add to `app/middleware/csp.py`:
  ```python
  "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
  "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
  ```

**Alternative (Self-hosted)**:
1. [ ] Download driver.js files:
   ```bash
   cd static/js/vendor
   wget https://cdn.jsdelivr.net/npm/driver.js@1.3.1/dist/driver.js.iife.js
   cd ../../css/vendor
   wget https://cdn.jsdelivr.net/npm/driver.js@1.3.1/dist/driver.css
   ```

2. [ ] Update `dashboard_base.html`:
   ```html
   <link rel="stylesheet" href="/static/css/vendor/driver.css">
   <script src="/static/js/vendor/driver.js.iife.js"></script>
   ```

**Test**: Open dashboard, check browser console for driver.js loaded:
```javascript
console.log(typeof window.driver); // Should output: "object"
```

---

### Task 2.2: Add Element IDs to Dashboard
**File**: `templates/dashboard_base.html`

**Ensure these IDs exist** (add if missing):

```html
<!-- Header Section -->
<button id="currency-selector-btn" ...>
  <span id="selected-currency-display">USD</span>
</button>

<!-- Language Selector (if exists in header) -->
<button id="language-selector-btn" ...>
  <span id="selected-language-display">English</span>
</button>

<!-- Tier Badge (usually near user profile) -->
<div id="tier-badge" class="...">
  <span>Freemium</span>
</div>

<!-- Sidebar Navigation -->
<nav>
  <a href="/verify" id="sidebar-verify-link">Verify</a>
  <a href="/history" id="sidebar-history-link">History</a>
  <a href="/api-keys" id="sidebar-api-keys-link">API Keys</a>
  <a href="/webhooks" id="sidebar-webhooks-link">Webhooks</a>
  <a href="/wallet" id="sidebar-wallet-link">Wallet</a>
</nav>
```

**Fallback Plan**: If elements don't have IDs, use fallback selectors:
- Currency: `document.querySelector('[data-currency-selector]')`
- Language: `document.querySelector('[data-language-selector]')`
- Tier: `document.querySelector('.tier-badge')`

---

## Phase 3: Create Tour Implementation (90 min)

### Task 3.1: Create Onboarding Tour Module
**File**: `static/js/onboarding-tour.js` (NEW)

```javascript
/**
 * Onboarding Tour - Driver.js Implementation
 * Version: 4.8.2
 * Status: Production Ready
 */

(function() {
    'use strict';

    class OnboardingTour {
        constructor() {
            this.driver = null;
            this.isRunning = false;
            this.completionEndpoint = '/api/auth/onboarding-complete';
            this.statusEndpoint = '/api/auth/onboarding-status';
        }

        async init() {
            console.log('[OnboardingTour] Initializing...');

            if (!this.isDashboardPage()) {
                console.log('[OnboardingTour] Not on dashboard, skipping');
                return;
            }

            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('[OnboardingTour] No auth token, skipping');
                return;
            }

            const shouldRun = await this.shouldRunTour();
            if (!shouldRun) {
                console.log('[OnboardingTour] Already completed, skipping');
                return;
            }

            if (document.readyState === 'complete') {
                setTimeout(() => this.start(), 1500);
            } else {
                window.addEventListener('load', () => {
                    setTimeout(() => this.start(), 1500);
                });
            }
        }

        isDashboardPage() {
            const path = window.location.pathname;
            return path === '/dashboard' || path === '/';
        }

        async shouldRunTour() {
            const token = localStorage.getItem('access_token');
            if (!token) return false;

            const cachedCompletion = localStorage.getItem('onboarding_tour_completed');
            if (cachedCompletion === 'true') {
                return false;
            }

            try {
                const response = await fetch(this.statusEndpoint, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    console.warn('[OnboardingTour] Status check failed, assuming not completed');
                    return true;
                }

                const data = await response.json();
                const completed = data.completed || false;

                if (completed) {
                    localStorage.setItem('onboarding_tour_completed', 'true');
                }

                return !completed;
            } catch (error) {
                console.error('[OnboardingTour] Error checking status:', error);
                return !sessionStorage.getItem('tour_attempted_this_session');
            }
        }

        start() {
            if (this.isRunning) {
                console.log('[OnboardingTour] Already running');
                return;
            }

            console.log('[OnboardingTour] Starting tour...');
            sessionStorage.setItem('tour_attempted_this_session', 'true');

            if (typeof window.driver === 'undefined') {
                console.error('[OnboardingTour] driver.js not loaded!');
                return;
            }

            const steps = this.buildTourSteps();
            if (steps.length === 0) {
                console.error('[OnboardingTour] No valid tour steps found');
                return;
            }

            try {
                this.driver = window.driver({
                    showProgress: true,
                    showButtons: ['next', 'previous', 'close'],
                    nextBtnText: 'Next →',
                    prevBtnText: '← Back',
                    doneBtnText: 'Done ✓',
                    closeBtnText: 'Skip',
                    progressText: 'Step {{current}} of {{total}}',

                    popoverClass: 'onboarding-tour-popover',
                    animate: true,
                    overlayOpacity: 0.75,

                    onDestroyStarted: () => {
                        console.log('[OnboardingTour] Tour ended by user');
                        this.handleTourEnd();
                    },

                    onDestroyed: () => {
                        this.isRunning = false;
                        console.log('[OnboardingTour] Tour destroyed');
                    },

                    steps: steps
                });

                this.driver.drive();
                this.isRunning = true;

                console.log('[OnboardingTour] Tour started successfully');
            } catch (error) {
                console.error('[OnboardingTour] Error starting tour:', error);
                this.isRunning = false;
            }
        }

        buildTourSteps() {
            const allSteps = [
                {
                    popover: {
                        title: '👋 Welcome to VRENUM SMS',
                        description: 'Let\'s take a quick tour to help you get started. This will only take 30 seconds!',
                        side: 'over',
                        align: 'center'
                    }
                },
                {
                    element: '#currency-selector-btn',
                    popover: {
                        title: '🌍 Choose Your Currency',
                        description: 'Click here to select your preferred currency. All prices throughout the platform will be automatically converted.',
                        side: 'bottom',
                        align: 'start'
                    }
                },
                {
                    element: '#language-selector-btn',
                    popover: {
                        title: '🗣️ Select Your Language',
                        description: 'Choose your preferred language here. The entire interface will be translated automatically.',
                        side: 'bottom',
                        align: 'start'
                    }
                },
                {
                    element: '#tier-badge',
                    popover: {
                        title: '⚡ Your Current Plan',
                        description: 'You\'re currently on the Freemium plan. Click here anytime to see upgrade options for API access, webhooks, and lower SMS rates.',
                        side: 'left',
                        align: 'start'
                    }
                },
                {
                    element: '#sidebar-verify-link',
                    popover: {
                        title: '📱 Start Verifying',
                        description: 'Click here to get a temporary phone number and receive SMS verification codes instantly.',
                        side: 'right',
                        align: 'start'
                    }
                },
                {
                    element: '#sidebar-history-link',
                    popover: {
                        title: '📋 View Your History',
                        description: 'All your past verifications, received codes, and spending are logged here for easy reference.',
                        side: 'right',
                        align: 'start'
                    }
                },
                {
                    element: '#sidebar-wallet-link',
                    popover: {
                        title: '💰 Manage Your Wallet',
                        description: 'Add credits here to pay for verifications. We support multiple payment methods based on your location.',
                        side: 'right',
                        align: 'start'
                    }
                },
                {
                    popover: {
                        title: '🎉 You\'re All Set!',
                        description: 'You can restart this tour anytime from your Settings page. Happy verifying!',
                        side: 'over',
                        align: 'center'
                    }
                }
            ];

            const validSteps = allSteps.filter(step => {
                if (!step.element) return true;

                const element = document.querySelector(step.element);
                if (!element) {
                    console.warn(`[OnboardingTour] Element not found: ${step.element}`);
                    return false;
                }

                return true;
            });

            console.log(`[OnboardingTour] Built ${validSteps.length}/${allSteps.length} steps`);
            return validSteps;
        }

        async handleTourEnd() {
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('[OnboardingTour] No token, skipping backend update');
                return;
            }

            try {
                const response = await fetch(this.completionEndpoint, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    console.log('[OnboardingTour] Marked as completed in backend');
                    localStorage.setItem('onboarding_tour_completed', 'true');
                } else {
                    console.warn('[OnboardingTour] Failed to mark completed:', response.status);
                }
            } catch (error) {
                console.error('[OnboardingTour] Error marking completed:', error);
            }
        }

        restart() {
            console.log('[OnboardingTour] Manual restart requested');

            localStorage.removeItem('onboarding_tour_completed');
            sessionStorage.removeItem('tour_attempted_this_session');

            this.start();
        }

        destroy() {
            if (this.driver) {
                this.driver.destroy();
                this.driver = null;
            }
            this.isRunning = false;
        }
    }

    function initTour() {
        window.onboardingTour = new OnboardingTour();
        window.onboardingTour.init();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTour);
    } else {
        initTour();
    }

    console.log('[OnboardingTour] Module loaded');
})();
```

---

### Task 3.2: Add Custom Styling
**File**: `static/css/onboarding-tour.css` (NEW)

```css
/**
 * Onboarding Tour - Custom Styling
 */

.driver-popover {
    background: linear-gradient(135deg, rgba(11, 15, 25, 0.98), rgba(20, 25, 40, 0.98)) !important;
    border: 1px solid rgba(254, 60, 114, 0.3) !important;
    border-radius: 16px !important;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(254, 60, 114, 0.2) !important;
    color: #ffffff !important;
    max-width: 400px !important;
    backdrop-filter: blur(20px) !important;
}

.driver-popover-title {
    color: #ffffff !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    margin-bottom: 12px !important;
}

.driver-popover-description {
    color: rgba(255, 255, 255, 0.85) !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}

.driver-popover-btn {
    background: rgba(254, 60, 114, 0.1) !important;
    border: 1px solid rgba(254, 60, 114, 0.3) !important;
    color: #FE3C72 !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.driver-popover-btn:hover {
    background: rgba(254, 60, 114, 0.2) !important;
    border-color: #FE3C72 !important;
    transform: translateY(-1px) !important;
}

.driver-popover-next-btn {
    background: #FE3C72 !important;
    border-color: #FE3C72 !important;
    color: #ffffff !important;
}

.driver-popover-next-btn:hover {
    background: #ff5784 !important;
    box-shadow: 0 0 20px rgba(254, 60, 114, 0.4) !important;
}

.driver-popover-close-btn {
    color: rgba(255, 255, 255, 0.5) !important;
    transition: color 0.2s ease !important;
}

.driver-popover-close-btn:hover {
    color: #FE3C72 !important;
}

.driver-popover-progress-text {
    color: rgba(255, 255, 255, 0.6) !important;
    font-size: 12px !important;
}

.driver-active-element {
    z-index: 10000 !important;
}

.driver-overlay {
    background: rgba(0, 0, 0, 0.75) !important;
}

@media (max-width: 768px) {
    .driver-popover {
        max-width: 90vw !important;
        margin: 10px !important;
    }

    .driver-popover-title {
        font-size: 16px !important;
    }

    .driver-popover-description {
        font-size: 13px !important;
    }
}

@keyframes driverFadeIn {
    from {
        opacity: 0;
        transform: scale(0.95);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

.driver-popover {
    animation: driverFadeIn 0.3s ease-out !important;
}
```

---

### Task 3.3: Load Tour Script in Dashboard
**File**: `templates/dashboard_base.html`

**Location**: Before closing `</body>` tag, after other scripts

```html
    <!-- Onboarding Tour -->
    <link rel="stylesheet" href="/static/css/onboarding-tour.css">
    <script src="/static/js/onboarding-tour.js"></script>
</body>
```

---

## Phase 4: Backend Integration (30 min)

### Task 4.1: Verify Onboarding Status Endpoint
**File**: `app/api/auth_routes.py` or `app/api/core/auth.py`

**Check endpoint exists**:
```python
@router.get("/api/auth/onboarding-status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's onboarding completion status."""
    return {
        "completed": current_user.onboarding_completed or False,
        "step": current_user.onboarding_step or 0
    }
```

---

### Task 4.2: Verify Completion Endpoint
**Check endpoint exists**:
```python
@router.put("/api/auth/onboarding-complete")
async def mark_onboarding_complete(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark user's onboarding as completed."""
    current_user.onboarding_completed = True
    current_user.onboarding_step = 99
    db.commit()

    return {"message": "Onboarding marked as complete", "completed": True}
```

---

### Task 4.3: Remove Welcome Page Redirect
**File**: `app/api/auth_routes.py` (login endpoint)

**Find and comment out**:
```python
# OLD CODE - REMOVE/COMMENT:
# if not user.onboarding_completed:
#     return RedirectResponse("/welcome", status_code=302)

# NEW CODE - Direct to dashboard:
return RedirectResponse("/dashboard", status_code=302)
```

---

## Phase 5: Testing & Quality Assurance (60 min)

### Task 5.1: Unit Testing (Manual)

**Test Scenario 1: Fresh User (First Login)**
1. [ ] Create new test account: `test_tour_user_1@example.com`
2. [ ] Login and verify redirect to `/dashboard`
3. [ ] Wait 1.5 seconds for tour to auto-start
4. [ ] Verify first step shows welcome message
5. [ ] Click "Next" through all steps
6. [ ] Verify arrows point correctly to each element
7. [ ] Click "Done" on final step
8. [ ] Verify tour doesn't show again on page refresh

**Test Scenario 2: Returning User (Tour Completed)**
1. [ ] Login with account that completed tour
2. [ ] Verify tour does NOT auto-start
3. [ ] Check localStorage: `onboarding_tour_completed === 'true'`
4. [ ] Check backend: `GET /api/auth/onboarding-status` returns `{completed: true}`

**Test Scenario 3: Skip Tour**
1. [ ] Create new test account: `test_tour_user_2@example.com`
2. [ ] Login, wait for tour to start
3. [ ] Click "Skip" button
4. [ ] Verify tour closes immediately
5. [ ] Verify backend marked as completed
6. [ ] Refresh page, verify tour doesn't restart

---

### Task 5.2: Cross-Browser Testing

**Desktop Browsers**:
- [ ] Chrome 120+ (primary)
- [ ] Firefox 121+ (secondary)
- [ ] Safari 17+ (macOS)
- [ ] Edge 120+ (Windows)

**Mobile Browsers**:
- [ ] Chrome Mobile (Android)
- [ ] Safari Mobile (iOS)
- [ ] Firefox Mobile (Android)

---

### Task 5.3: Error Handling Testing

**Test Scenario 1: Network Failure**
1. [ ] Start tour on fresh account
2. [ ] Open DevTools → Network → Toggle "Offline"
3. [ ] Complete tour (click through all steps)
4. [ ] Click "Done"
5. [ ] Verify console shows error but tour closes gracefully

**Test Scenario 2: Driver.js Fails to Load**
1. [ ] Block driver.js CDN in DevTools → Network
2. [ ] Refresh dashboard
3. [ ] Verify console logs error but page loads normally
4. [ ] Verify no JavaScript errors break page

---

## Phase 6: Production Deployment (30 min)

### Task 6.1: Final Pre-Deployment Checklist
- [ ] All files created and tested
- [ ] No console errors on fresh account
- [ ] Tour completes successfully
- [ ] Backend endpoints working
- [ ] Mobile responsive verified
- [ ] Cross-browser compatibility confirmed

### Task 6.2: Deploy to Production
1. [ ] Commit all changes: `git add . && git commit -m "feat: add driver.js onboarding tour"`
2. [ ] Push to main: `git push origin main`
3. [ ] Deploy to production environment
4. [ ] Monitor Sentry for any errors
5. [ ] Test with real fresh account in production

---

## Success Metrics

**Completion Criteria**:
- ✅ Fresh user logs in → Tour auto-starts on dashboard
- ✅ Arrows point correctly to each UI element
- ✅ User can click buttons during tour (non-blocking)
- ✅ Tour completes → Never shows again
- ✅ Returning users don't see tour
- ✅ Skip button works immediately
- ✅ Mobile responsive
- ✅ No errors in Sentry
- ✅ Page load time unchanged (< 50ms difference)

**Files Created/Modified**:
- CREATE: `static/js/onboarding-tour.js` (main tour logic)
- CREATE: `static/css/onboarding-tour.css` (styling)
- MODIFY: `templates/dashboard_base.html` (load scripts + add IDs)
- MODIFY: `app/api/auth_routes.py` (remove welcome redirect)

---

**Total Estimated Time**: 3-4 hours
**Risk Level**: LOW (graceful degradation)
**Status**: Ready to implement ✅

**Last Updated**: May 18, 2026
**Next Actions**: Begin Phase 1 - Audit Current State
