# Task: Verification Flow Ensuite Roadmap (Tier-Assigned)

## 🎯 Implementation Objective
Ensure that SMS verification enhancements are delivered in a sequential "ensuite" order, with filtering and features strictly gated by the user's subscription plan.

---

## 💎 Tier 1: Freemium (Baseline)
*   **01. Dynamic Pricing Preview**:
    - [x] Fetch total cost from `/api/v1/verification/pricing` before purchase.
    - [x] Prevents "insufficient funds" errors for all users.
*   **02. Basic US Verification**:
    - [x] Service selection only (Carrier/Area Code locked).

## 💎 Tier 2: PAYG / Starter (+ Geographic Scaling)
*   **03. Multi-Country Selection**:
    - [x] Unlock the Country dropdown.
    - [x] Respect `country_limit` from `TierManager`.
*   **04. Area Code Selection & Search**:
    - [x] Unlock `requested_area_code` filtering.
    - [ ] Implement city/state geolocation search (e.g., "Chicago" -> 312).
*   **05. Geo-UX Improvements**:
    - [x] Show state labels next to area codes (e.g., "NY (212)").

## 💎 Tier 3: Pro (+ Technical Control)
*   **06. ISP / Carrier Filtering**:
    - [x] Unlock `requested_carrier` filtering for US/International.
*   **07. Efficiency Presets**:
    - [x] Allow users to save current Filter + Service as a "Preset" (Backend API Ready).
    - [x] Adds "Favorite Filters" sidebar to the verification view (Frontend Implemented).
*   **08. Success Rate Analytics**:
    - [x] Overlay success percentages on carriers (e.g., "AT&T - 99% Stable").
*   **09. Carrier Mask Unveiling**:
    - [x] Show the delivered number's carrier logo in the reception card (Text Badge Implemented).

## 💎 Tier 4: Custom / Turbo (+ Mission Critical)
*   **10. Intelligent Fallback (Auto-Correction)**:
    - [x] If filtered purchase fails (e.g., specific ISP out of stock), automatically fallback to "Best Effort" within same region.
    - [x] Provide a post-purchase notification of the fallback.
*   **11. Low Inventory Priority**:
    - [ ] (Deferred) Access to "Reserved Pool" numbers during peak traffic.

---

## 🛠️ Global Refactoring Tasks
- [x] Move `verify.html` logic to `api-client.js` (Created `static/js/verification.js` for centralized logic).
- [x] Implement server-side validation in `consolidated_verification.py` for every tier-based toggle.
- [x] Add translation keys for all new tier-based upgrade prompts.

## 💎 UX Polish: Active Monitoring Experience
*   **12. Notification Sound**:
    - [x] Play a crisp notification sound when the SMS code arrives.
    - [x] Ensure audio works even if the tab is in the background (using Audio API).
*   **13. Dynamic Waiting Animation**:
    - [x] Replace the static spinner with a "Pulse" or "Radar" scanning animation during key wait times.
    - [x] Show elapsed time counter with a progress bar (e.g., "Scanning network... 15s").
