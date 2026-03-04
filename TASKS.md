# Settings Page — Fix Tasklist

## Already Fixed ✅

- [x] `GET /api/user/settings` 500 — was using wrong model (`UserPreference` instead of `NotificationSettings`)
- [x] Duplicate tab content on reload — `data-loaded` guard added to `switchTab`
- [x] Broken `switchTab` if/else chain — syntax error fixed
- [x] Duplicate "Notifications" nav label — renamed to "Notification Settings" / "Notifications Center"
- [x] Missing JS functions (`markAllRead`, `loadMoreNotifs`, `applyFilters`, `clearFilters`, `exportHistory`, `showToast`)
- [x] History tab moved out of Settings → sidebar link to `/history`
- [x] Notifications Center tab removed from Settings (it's an inbox, not a setting)
- [x] Referrals added to sidebar footer
- [x] **Register `user_settings` router** in `main.py` — exposes `POST /user/logout-all`, `/user/delete-account`, `/user/change-password`, `/user/settings/*`
- [x] **Register API Keys router** in `main.py` — `app/api/core/api_key_endpoints.py` (prefix `/api/keys`)
- [x] **Register Forwarding router** in `main.py` — `app/api/core/forwarding.py` (prefix `/forwarding`)
- [x] **Register Blacklist router** in `main.py` — `app/api/core/blacklist.py` (prefix `/api/blacklist`)
- [x] **Fix Blacklist frontend URLs** — `/blacklist` → `/api/blacklist` (all 5 occurrences in `settings.html`)
- [x] **Fix Billing refund URLs** — `/api/v1/wallet/refund/history` → `/api/wallet/refund/history`, `/api/v1/wallet/request` → `/api/wallet/refund/request`
- [x] **Password Reset POST** — added `POST /api/auth/forgot-password` via `auth_router` in `user_settings.py`
- [x] **Privacy API** — added `GET /api/user/privacy` and `POST /api/user/privacy` to `user_settings_endpoints.py`
- [x] **Data Export API** — added `POST /api/user/export` to `user_settings_endpoints.py`
- [x] **Referrals API** — added `GET /api/user/referrals` to `user_settings_endpoints.py`
- [x] **Webhooks API** — added `GET /api/user/webhooks` to `user_settings_endpoints.py`
- [x] **Security tab UI** — added Change Password form, Logout All Devices button, Delete Account (danger zone)
- [x] **Security tab JS** — added `changePassword()`, `logoutAll()`, `deleteAccount()` functions
