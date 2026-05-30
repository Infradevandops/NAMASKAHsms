# Verification Flow and Onboarding UI Upgrades

This document serves as the historical record of the recent frontend upgrades, combining the implementation plan and the executed task checklist.

---

## Implementation Plan

This plan details the frontend UI upgrades to the verification flow and the user onboarding wizard, ensuring correct backend alignment, active service preference selection, and tier enforcement.

### Proposed Changes

#### 1. UI Components / CSS

**[MODIFY] verification-design-system.css**
- **Add Skeleton Loader Classes**: Define `.skeleton-loader` and `.shimmer` keyframes to use for loading states.
- **Add Dynamic Button States**: Define styles for buttons in a `loading` state (e.g., pulsing pill shape, disabled styling with an embedded micro-spinner).
- **Add Polling Animations**: Define CSS for the dynamic pulsing radar/scanning animation to replace the basic SVG ring during SMS polling.

#### 2. Verification Flow Frontend JavaScript

**[MODIFY] verify_modern.html**
- **Initial Load State**: Add a skeleton loader placeholder to the "Select Service" input and modal list. Update `loadServices()` to show this skeleton while data is fetching and transition to the actual data smoothly.
- **Requesting Number (Step 2 to Step 3)**: Update the `createVerification()` function to add a `.loading` class to the "Get Number ->" button. Update the button's inner HTML to a branded spinner instead of just changing the text to "Creating...".
- **Staggered SMS Polling**: Update the `startPolling()` and `poll()` logic to implement staggered UI updates. Instead of static "Scanning for SMS..." text, dynamically update the text based on `VerificationFlow.elapsedSeconds`:
  - 0-5s: "Establishing secure connection..."
  - 5-15s: "Awaiting response from service..."
  - 15s+: "Listening for incoming SMS..."

#### 3. Onboarding Wizard Enhancements

**[MODIFY] welcome.html**
- **Select Preferred Service (Step 3 Upgrade)**: Convert Step 3 from a static text guide into an interactive service selection card. Allow users to choose their main platform of interest (e.g. Google, WhatsApp, OpenAI, Telegram). Store this preference in the user's profile.
- **Interactive Plan Selection (Step 2 Upgrade)**: Add an interactive plan picker directly in the onboarding wizard:
  - Freemium (Default)
  - Pay-As-You-Go (Calls `POST /api/billing/upgrade?target_tier=payg` to instantly upgrade the user for free)
  - Pro / Custom (Directs them to billing checkout with Paystack)
- **Country Selection & Auto-Detection (Step 1 Upgrade)**:
  - Add a **Country** dropdown to Step 1.
  - Implement a JavaScript auto-detection engine mapping browser timezones (`Intl.DateTimeFormat().resolvedOptions().timeZone`) and navigator languages to default countries.
  - Automatically map the selected country to auto-select the corresponding default Language and Currency dropdown values (e.g. selecting Spain auto-selects Spanish language and Euro currency).
- **Aesthetic Alignments**: Update progress dots and button elements to use the branded `#FE3C72` primary color scheme (currently uses `#06b6d4` / cyan).

#### 4. Backend API Alignments

**[MODIFY] auth_routes.py**
- **`/me` Endpoint**: Update to return `"tier": user.subscription_tier` in the user payload so the onboarding UI correctly identifies and renders premium steps.
- **`PUT /onboarding-status` Endpoint**: Add a PUT route to accept `{ "step": int }` and update the database column `onboarding_step` dynamically as the user progresses.

#### 5. Extra Upgrades & Optimizations

**[MODIFY] wallet.html**
- **Preset Currency Conversion**: Convert payment presets from static USD text (e.g., `$10`, `$25`) to use dynamic currency selector conversions by adding `data-usd-amount` attributes, ensuring the amounts accurately show the user's preferred local currency.

**[NEW] Client-side Translation Helper (i18n.js)**
- Build a lightweight frontend localization script that intercepts elements and updates text based on the user's saved language preference (e.g. translating dashboard elements to Spanish or French when selected).

#### 6. Broad Skeleton Loader Implementations

**[MODIFY] dashboard.html & activity_feed.js**
- **Dashboard Metrics**: While fetching `/api/activities/summary/overview`, apply the `.skeleton-stat` class to the primary metric blocks (Total Spent, Active Numbers) to replace the blank areas.
- **Activity Feed**: While fetching `/api/activities`, render `.skeleton-card` or `.skeleton-row` placeholders in the feed container until the JSON response populates the DOM.

**[MODIFY] verify_modern.html**
- **Service Tier Pricing**: When a user selects a service, `fetchTierPricing()` takes time to retrieve the cost. Inject a `<div class="skeleton-tier-card"></div>` placeholder in the pricing block before resolving the data to ensure smooth transitions.

**[MODIFY] wallet.html**
- **Transaction History**: Add `.skeleton-row` blocks to the table body during the async fetch for `/api/wallet/transactions` so the table doesn't collapse or appear empty during loading.

**[MODIFY] admin-dashboard.js**
- **Admin Stats**: Apply skeleton classes (`.skeleton-stat`) to high-level admin metrics while `statsResponse` is fetching `/api/admin/stats`.

#### 7. Global Walkthrough Wizard Enforcement

**[MODIFY] app/api/auth_routes.py**
- **Login Redirect**: Update the `/login` route to check the `onboarding_completed` flag and explicitly return `"redirect": "/welcome"` for any user (new or old) who hasn't completed it.

**[MODIFY] static/js/auth-check.js & app/api/core/user_profile.py**
- **Session Interceptor**: Update the `/api/user/me` endpoint to return the `onboarding_completed` status. Inject a global frontend check to intercept active sessions lacking completion and forcefully redirect them to the wizard.

---

## Tasks Checklist

### 1. Backend & API Adjustments
- [x] Return user tier in `/api/auth/me` (`app/api/auth_routes.py`)
- [x] Implement `PUT /api/auth/onboarding-status` endpoint (`app/api/auth_routes.py`)

### 2. Onboarding Wizard Upgrades (`templates/welcome.html`)
- [x] Align welcome page colors to branded `#FE3C72` primary palette
- [x] Integrate interactive tier selection in step 2 (with instant PAYG activation and Pro checkout paths)
- [x] Add preferred service/platform interactive selection card in step 3
- [x] Integrate step persistence checking and state restoration using updated backend endpoints
- [x] Add Country selection dropdown to Step 1
- [x] Implement browser timezone/locale auto-detection to default the Country selection
- [x] Map country selection to pre-select default Language and Currency automatically

### 3. Verification Flow UI & Loading States
- [x] Define skeleton loaders, pulsing scanning animations, and dynamic button states in `static/css/verification-design-system.css`
- [x] Implement Skeleton Loader for Initial Service Loading in `verify_modern.html`
- [x] Upgrade "Get Number" button loading interactions in `verify_modern.html`
- [x] Implement Staggered Polling Messages in SMS polling loops in `verify_modern.html`

### 4. Recommended Upgrades & Optimizations
- [x] Enable dynamic currency conversions for wallet presets (`templates/wallet.html`) using `data-usd-amount` attributes
- [x] Design and implement a client-side i18n overlay mapping Spanish, French, and Yoruba translation strings for the dashboard views

### 5. Verification & Testing
- [x] Run unit and integration tests for onboarding flows
- [ ] Manually test the full end-to-end user onboarding, country-based auto-detection, and plan selection wizard
- [ ] Manually test verification flow skeleton loaders and dynamic buttons under throttled network conditions

### 6. Expanded Skeleton Loading Enhancements
- [x] Apply skeleton loaders to Dashboard metrics and activity feed (`dashboard.html`, `activity_feed.js`)
- [x] Apply skeleton loaders to Service Tier Pricing (`verify_modern.html`) (Confirmed synchronous/cached via ServiceStore)
- [x] Apply skeleton loaders to Wallet Transaction History (`wallet.html`)
- [x] Apply skeleton loaders to Admin Dashboard charts/stats (`admin-dashboard.js`)

### 7. Global Walkthrough Wizard Enforcement
- [x] Update `app/api/auth_routes.py` to return `redirect: "/welcome"` for logins where `onboarding_completed` is `False`.
- [x] Update frontend `/api/auth/me` fetcher (in `auth-helpers.js` or similar) to globally intercept active sessions and redirect to `/welcome` if `onboarding_completed` is `False`.
