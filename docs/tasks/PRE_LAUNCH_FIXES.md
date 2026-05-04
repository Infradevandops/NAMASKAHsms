# Pre-Launch Platform Fixes

**Created**: May 3, 2026
**Status**: In Progress
**Priority**: CRITICAL — Must complete before launch

---

## 🔴 CRITICAL (Blocks Launch)

### 1. Registration backend ignores `terms_accepted`
- **File**: `app/api/auth_routes.py`
- **Issue**: `RegisterRequest` model doesn't include `terms_accepted`. Frontend sends it, backend drops it. User model has no `terms_accepted` column.
- **Fix**: Add `terms_accepted` to RegisterRequest, add column to User model, store on registration.
- **Status**: ✅ FIXED

### 2. Old URL in auth_routes.py verification email
- **File**: `app/api/auth_routes.py:170`
- **Issue**: Fallback URL is `https://namaskahsms.onrender.com` instead of `https://vrenum.onrender.com`
- **Fix**: Update fallback URL.
- **Status**: ✅ FIXED

### 3. Old URL in security_config.py
- **File**: `app/core/security_config.py:54`
- **Issue**: `namaskah.onrender.com` in allowed hosts instead of `vrenum.onrender.com`
- **Fix**: Replace with correct hostname.
- **Status**: ✅ FIXED

### 4. Missing `docs.html` template
- **File**: `app/api/main_routes.py:100` → `templates/docs.html`
- **Issue**: Route renders `docs.html` which doesn't exist. Landing nav links to `/docs`. 500 error.
- **Fix**: Create `docs.html` template (API documentation page).
- **Status**: ✅ FIXED

### 5. Missing admin templates
- **Files**: `templates/admin/tier_management.html`, `templates/admin/verification_history.html`
- **Issue**: Routes exist but templates don't. 500 error for admin users.
- **Fix**: Create both admin templates.
- **Status**: ✅ FIXED

### 6. No `/api/contact/send` endpoint
- **File**: `templates/contact.html` POSTs to `/api/contact/send`
- **Issue**: No backend endpoint exists. Contact form silently fails.
- **Fix**: Create contact endpoint.
- **Status**: ✅ FIXED

### 7. Cookie missing `Secure` flag
- **Files**: `templates/login.html:257,323`
- **Issue**: `access_token` cookie set without `Secure` flag in production.
- **Fix**: Add `Secure` flag when on HTTPS.
- **Status**: ✅ FIXED

### 8. Login placeholder exposes admin email
- **File**: `templates/login.html:212`
- **Issue**: `placeholder="admin@namaskah.app"` reveals admin email.
- **Fix**: Change to generic placeholder.
- **Status**: ✅ FIXED

---

## 🟡 IMPORTANT (Should fix before launch)

### 9. Inconsistent email domains in legal pages
- **Files**: `templates/terms.html`, `templates/privacy.html`, `templates/cookies.html`
- **Issue**: Mix of `@namaskah.com` and `@namaskah.app` domains.
- **Fix**: Standardize to `@namaskah.app`.
- **Status**: ✅ FIXED

### 10. Outdated dates on legal pages
- **Files**: `templates/terms.html`, `templates/privacy.html`
- **Issue**: "Last Updated: December 2024" — should be 2026.
- **Fix**: Update dates.
- **Status**: ✅ FIXED

### 11. Footer copyright year
- **Files**: `templates/landing.html`, `templates/public_base.html`
- **Issue**: Says "© 2025", should be 2026.
- **Fix**: Update year.
- **Status**: ✅ FIXED

### 12. Sitemap/robots.txt wrong domain
- **Files**: `static/robots.txt`, `static/sitemap.xml`
- **Issue**: References `https://namaskah.app/` but production is `https://vrenum.onrender.com`
- **Fix**: Update domain.
- **Status**: ✅ FIXED

### 13. manifest.json wrong theme_color
- **File**: `static/manifest.json`
- **Issue**: Uses `#6366f1` (indigo) but brand is `#FE3C72`.
- **Fix**: Update theme_color.
- **Status**: ✅ FIXED

### 14. Missing PWA screenshots
- **File**: `static/manifest.json`
- **Issue**: References screenshots that don't exist.
- **Fix**: Remove screenshot entries from manifest.
- **Status**: ✅ FIXED

### 15. No cookie consent banner
- **Issue**: Uses cookies but no GDPR consent banner.
- **Fix**: Add cookie consent banner to `base.html`.
- **Status**: ✅ FIXED

### 16. Wallet audit modal visible on load
- **File**: `templates/wallet.html`
- **Issue**: Conflicting `display: none` and `display: flex` on modal.
- **Fix**: Remove the `display: flex`.
- **Status**: ✅ FIXED

---

## 🟢 NICE TO HAVE (Post-launch)

### 17. Email verification not enforced
- Users can use platform without verifying email.

### 18. Password reset end-to-end verification
- Forgot-password API exists but full flow needs E2E testing.

### 19. Landing page social links placeholder
- `twitter.com/namaskah` and `github.com/namaskah` may not exist.

### 20. Auth endpoint rate limiting verification
- Backend rate limiting should be verified for auth endpoints.

### 21. `.backup` files in templates
- `affiliate_program.html.backup`, `api_docs.html.backup`, etc. should be cleaned up.
