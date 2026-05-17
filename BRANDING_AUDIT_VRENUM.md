# VRENUM ACTV8TN — Branding Audit

**Production Domain**: vrenum.app
**Brand Title**: VRENUM ACTV8TN
**Date**: Current
**Status**: Comprehensive Frontend Audit

---

## 📋 Summary

**Total Files Requiring Updates**: 68
**Total Occurrences**: 150+

| Category | Files | Occurrences |
|----------|-------|-------------|
| Templates (HTML) | 47 | ~120 |
| JavaScript | 9 | ~15 |
| CSS | 7 | ~9 (comments only) |
| Manifest/Config | 1 | 2 |
| Dist (built) | 1 | rebuild needed |

---

## ⭐ CRITICAL — Home Button & Navigation

### 1. Sidebar (Home Button)
**File**: `templates/components/sidebar.html`
| Line | Current | Replace With |
|------|---------|--------------|
| 4 | `<div class="sidebar-logo">N</div>` | `<div class="sidebar-logo">V</div>` |
| 5 | `<h2>Namaskah</h2>` | `<h2>VRENUM ACTV8TN</h2>` |

### 2. Public Base (Logo + Footer)
**File**: `templates/public_base.html`
| Line | Current | Replace With |
|------|---------|--------------|
| 25 | `<a href="/" class="logo">Namaskah</a>` | `<a href="/" class="logo">VRENUM ACTV8TN</a>` |
| 50 | `© 2026 Namaskah SMS. All rights reserved.` | `© 2026 vrenum.app. All rights reserved.` |

### 3. Landing Page
**File**: `templates/landing.html`
| Line | Current | Replace With |
|------|---------|--------------|
| 6 | `<title>Namaskah - Keep Your Real Number Private</title>` | `<title>VRENUM ACTV8TN - Keep Your Real Number Private</title>` |
| 42 | `<span class="font-bold text-xl tracking-tight">Namaskah</span>` | `VRENUM ACTV8TN` |
| 194 | `<!-- Why Namaskah Section -->` | `<!-- Why Vrenum Section -->` |
| 198 | `Why Namaskah?` | `Why Vrenum?` |
| 378 | `<span class="font-bold text-xl">Namaskah</span>` | `VRENUM ACTV8TN` |
| 410 | `© 2026 Namaskah. All rights reserved.` | `© 2026 vrenum.app. All rights reserved.` |
| 412 | `https://twitter.com/namaskah` | Update to new handle |
| 413 | `https://github.com/namaskah` | Update to new repo |

### 4. Navbar Brands (Multiple Public Pages)
These pages all have `<div class="navbar-brand">Namaskah</div>`:
| File | Line |
|------|------|
| `templates/cookies.html` | 180 |
| `templates/affiliate_program.html` | 215 |
| `templates/services.html` | 192 |
| `templates/reviews.html` | 203 |
| `templates/whitelabel_setup.html` | 152 |

**Replace all with**: `<div class="navbar-brand">VRENUM ACTV8TN</div>`

---

## ⭐ SEO & Meta

### 5. Base Template
**File**: `templates/base.html`
| Line | Current | Replace With |
|------|---------|--------------|
| 10 | `<title>{% block title %}Namaskah SMS{% endblock %}</title>` | `VRENUM ACTV8TN` |
| 61 | `<!-- Namaskah UI Design System -->` | Comment only |
| 65 | `href="/static/css/namaskah-ui.css"` | Keep or rename file |

### 6. Meta Tags
**File**: `templates/meta_tags.html`
| Line | Current | Replace With |
|------|---------|--------------|
| 2 | `Namaskah SMS - Instant SMS Verification for 1,807+ Services` | `VRENUM ACTV8TN - Instant SMS Verification for 1,807+ Services` |
| 8 | Same (og:title) | Same replacement |
| 16 | `Namaskah SMS` (twitter:title) | `VRENUM ACTV8TN` |
| 24 | `<meta name="author" content="Namaskah SMS">` | `vrenum.app` |

### 7. Schema.org Structured Data
**File**: `templates/schema_org.html`
| Line | Current | Replace With |
|------|---------|--------------|
| 6 | `"name": "Namaskah SMS"` | `"name": "VRENUM ACTV8TN"` |
| 7 | `"url": "https://namaskah.app"` | `"url": "https://vrenum.app"` |
| 8 | `"logo": "https://namaskah.app/static/images/og-image.png"` | `https://vrenum.app/...` |
| 14 | `"email": "support@namaskah.app"` | `support@vrenum.app` |
| 17 | `"https://twitter.com/namaskahsms"` | New handle |
| 18 | `"https://github.com/Infradevandops/NAMASKAHsms"` | New repo |
| 27 | `"name": "Namaskah SMS"` | `"name": "VRENUM ACTV8TN"` |
| 28 | `"url": "https://namaskah.app"` | `https://vrenum.app` |
| 32 | `"target": "https://namaskah.app/app?q=..."` | `https://vrenum.app/app?q=...` |
| 46 | `"name": "Namaskah SMS"` | `"name": "VRENUM ACTV8TN"` |

### 8. Web Manifest
**File**: `static/manifest.json`
| Line | Current | Replace With |
|------|---------|--------------|
| 2 | `"name": "Namaskah SMS Verification"` | `"name": "VRENUM ACTV8TN"` |
| 3 | `"short_name": "Namaskah"` | `"short_name": "Vrenum"` |

---

## 📄 Authentication Pages

| File | Line | Current | Replace With |
|------|------|---------|--------------|
| `templates/login.html` | 199 | `Sign in to your Namaskah account` | `Sign in to your vrenum.app account` |
| `templates/welcome.html` | 6 | `<title>Welcome - Namaskah</title>` | `Welcome - VRENUM ACTV8TN` |
| `templates/welcome.html` | 22 | `Welcome to Namaskah` | `Welcome to VRENUM ACTV8TN` |
| `templates/password_reset.html` | 6 | `Reset your Namaskah password` | `Reset your vrenum.app password` |
| `templates/password_reset.html` | 7 | `<title>Password Reset - Namaskah</title>` | `Password Reset - VRENUM ACTV8TN` |
| `templates/password_reset_confirm.html` | 6 | `Confirm your new password for Namaskah` | `...for vrenum.app` |
| `templates/password_reset_confirm.html` | 7 | `<title>Confirm Password Reset - Namaskah</title>` | `...VRENUM ACTV8TN` |
| `templates/email_verify.html` | 6 | `Verify your email address for Namaskah` | `...for vrenum.app` |
| `templates/email_verify.html` | 7 | `<title>Email Verification - Namaskah</title>` | `...VRENUM ACTV8TN` |

---

## 📊 Dashboard Pages

| File | Line | Current |
|------|------|---------|
| `templates/notification_center.html` | 6 | `<title>Notification Center - Namaskah</title>` |
| `templates/webhooks_management.html` | 6 | `<title>Webhooks \| Namaskah</title>` |
| `templates/activity_feed.html` | 6 | `<title>Activity Feed - Namaskah</title>` |
| `templates/billing_history.html` | 6 | `<title>Billing History - Namaskah</title>` |
| `templates/billing_history.html` | 308 | `<h3>Namaskah SMS</h3>` |
| `templates/usage_quotas.html` | 6 | `<title>Usage Quotas - Namaskah</title>` |
| `templates/waitlist.html` | 6 | `<title>Join the Waitlist \| Namaskah</title>` |
| `templates/disputes.html` | 6 | `<title>Disputes - Namaskah</title>` |
| `templates/support.html` | 6 | `<title>Support \| Namaskah</title>` |
| `templates/voice_status.html` | 6 | `<title>Voice Status - Namaskah</title>` |

**Replace all**: `Namaskah` → `VRENUM ACTV8TN` in titles

---

## ⚙️ Settings & Features Pages

| File | Line | Current |
|------|------|---------|
| `templates/telegram_settings.html` | 3 | `Telegram Settings - Namaskah` |
| `templates/telegram_settings.html` | 203 | `@namaskah_sms_bot` |
| `templates/push_settings.html` | 3 | `Push Notifications - Namaskah` |
| `templates/onesignal_settings.html` | 6 | `Push Notifications - Namaskah` |
| `templates/email_templates.html` | 6 | `Email Templates - Namaskah` |
| `templates/settings.html` | 654 | `Connect your apps to Namaskah...` |
| `templates/settings.html` | 664 | `Integrate Namaskah SMS verification...` |
| `templates/settings.html` | 2165 | `a.download = 'namaskah-data.json'` |
| `templates/webhooks.html` | 189 | `Connect your apps to Namaskah...` |

---

## 🔐 Admin Pages

| File | Line | Current | Replace With |
|------|------|---------|--------------|
| `templates/admin/dashboard.html` | 6 | `Namaskah \| Institutional Control Center` | `VRENUM ACTV8TN \| Institutional Control Center` |
| `templates/admin/verification_history.html` | 6 | `Namaskah \| Verification History` | `VRENUM ACTV8TN \| Verification History` |
| `templates/admin/tier_management.html` | 6 | `Namaskah \| Tier Management` | `VRENUM ACTV8TN \| Tier Management` |
| `templates/admin/rentals.html` | 6 | `Namaskah \| Rental Overview` | `VRENUM ACTV8TN \| Rental Overview` |
| `templates/admin/pricing_templates.html` | 6 | `Namaskah \| Institutional Pricing Control` | `VRENUM ACTV8TN \| Institutional Pricing Control` |
| `templates/admin/alerts.html` | 188 | `admin@namaskah.app` | `admin@vrenum.app` |

---

## 📜 Legal & Info Pages

### `templates/terms.html` (14 occurrences)
| Line | Reference |
|------|-----------|
| 6 | Title |
| 36, 41, 54, 59 (×3), 64 (×3), 69 (×2), 74, 79, 124, 130 (×2) | Body text — "Namaskah" |
| 138 | `legal@namaskah.app` |
| 139 | `www.namaskah.app` |

### `templates/privacy.html` (5 occurrences)
| Line | Reference |
|------|-----------|
| 6 | Title |
| 36 | `Namaskah ("we," "us," "our," or "Company")` |
| 112 | `privacy@namaskah.app` |
| 158 | `privacy@namaskah.app` |
| 159 | `Namaskah Inc., Global Headquarters` |

### `templates/cookies.html` (4 occurrences)
| Line | Reference |
|------|-----------|
| 6-7 | Meta + Title |
| 180 | Navbar brand |
| 351 | `privacy@namaskah.app` |
| 371 | `© 2025 Namaskah` |

### `templates/refund.html` (6 occurrences)
| Line | Reference |
|------|-----------|
| 6-7 | Title + Meta |
| 149 | `Namaskah wallet` |
| 161 | `support@namaskah.app` |
| 168 | `support@namaskah.app` |
| 226 | `support@namaskah.app` |

### `templates/faq.html` (5 occurrences)
| Line | Reference |
|------|-----------|
| 6 | Title |
| 37 | `Namaskah SMS verification service` |
| 203 | `Is Namaskah GDPR compliant?` |
| 224 | `integrate Namaskah into your application` |
| 264 | `support@namaskah.app` |

### `templates/about.html` (7 occurrences)
| Line | Reference |
|------|-----------|
| 3 | `About Namaskah` (page title block) |
| 177 | `<h1>About Namaskah</h1>` |
| 183 | `Namaskah is dedicated to...` |
| 184 | `Namaskah has you covered` |
| 188 | `Why Choose Namaskah?` |
| 241 | `Namaskah is built by a team...` |

### `templates/info.html` (6 occurrences)
| Line | Reference |
|------|-----------|
| 6-7 | Meta + Title |
| 209 | `About Namaskah` |
| 210 | `Namaskah is a leading SMS...` |
| 228 | `support@namaskah.app` |
| 254 | `By using Namaskah...` |

### `templates/contact.html` (8 occurrences)
| Line | Reference |
|------|-----------|
| 200 | `support@namaskah.app` |
| 207 | `business@namaskah.app` |
| 213 | `security@namaskah.app` |
| 219 | `legal@namaskah.app` |
| 231 | `https://twitter.com/namaskah` |
| 232 | `https://github.com/Infradevandops/NAMASKAHsms` |
| 313 | `support@namaskah.app` (error fallback) |
| 317 | `support@namaskah.app` (error fallback) |

---

## 🛒 Marketing Pages

| File | Lines | References |
|------|-------|------------|
| `templates/affiliate_program.html` | 6-7, 215, 229, 361 | Meta, title, navbar, body, footer |
| `templates/services.html` | 6-7, 192, 306, 315 | Meta, title, navbar, body, footer |
| `templates/reviews.html` | 6-7, 203, 313, 324 | Meta, title, navbar, textarea placeholder, footer |
| `templates/whitelabel_setup.html` | 6-7, 152, 239, 293 | Meta, title, navbar, CNAME example (`→ namaskah.app`), footer |

---

## 📖 API Documentation

### `templates/api_docs.html`
| Line | Reference |
|------|-----------|
| 6-7 | Meta + Title |
| 231 | `integrating with Namaskah API` |
| 240 | `The Namaskah API provides...` |
| 241 | `https://api.namaskah.com/v1` → `https://api.vrenum.app/v1` |

### `templates/api_documentation.html`
| Line | Reference |
|------|-----------|
| 6 | Title |
| 62 | `integrating Namaskah SMS verification` |
| 97 | `The Namaskah API allows you to...` |
| 101 | `https://namaskah.app/api` → `https://vrenum.app/api` |
| 135 | `curl` example URL |
| 155 | Python example URL |
| 169 | JS `fetch` example URL |
| 459 | `integrate Namaskah into your application` |

---

## 🔧 JavaScript Files

| File | Line | Current | Replace With |
|------|------|---------|--------------|
| `static/js/theme-manager.js` | 8 | `'namaskah-theme-preference'` | `'vrenum-theme-preference'` |
| `static/js/service-worker.js` | 6 | `'namaskah-v1'` | `'vrenum-v1'` |
| `static/js/service-worker.js` | 90 | `'Namaskah Notification'` | `'Vrenum Notification'` |
| `static/js/push-service-worker.js` | 4 | `'namaskah-v1'` | `'vrenum-v1'` |
| `static/js/push-service-worker.js` | 36 | `title: 'Namaskah'` | `title: 'Vrenum'` |
| `static/js/admin-dashboard.js` | 22 | `'admin@namaskah.app'` | `'admin@vrenum.app'` |
| `static/js/admin/pricing.js` | 187 | `namaskah_pricing_${date}.csv` | `vrenum_pricing_${date}.csv` |
| `static/js/onesignal-manager.js` | 195 | `'test notification from Namaskah'` | `'...from Vrenum'` |
| `static/js/dashboard.js` | 2 | Comment: `Namaskah Dashboard` | Comment only |
| `static/js/dashboard-ultra-stable.js` | 2 | Comment: `NAMASKAH DASHBOARD` | Comment only |
| `static/js/sms-arrival-sound.js` | 2 | Comment: `Namaskah — SMS Arrival Sound` | Comment only |

### Inline JS in Templates
| File | Line | Current | Replace With |
|------|------|---------|--------------|
| `templates/dashboard_base.html` | 24 | `name.includes('namaskah')` | `name.includes('vrenum')` |
| `templates/gdpr_settings.html` | 461 | `namaskah-data-export-${date}.json` | `vrenum-data-export-${date}.json` |
| `templates/history.html` | 406 | `'NAMASKAH_NET'` | `'VRENUM_NET'` |
| `templates/history.html` | 504 | `namaskah-audit-trail-${date}.csv` | `vrenum-audit-trail-${date}.csv` |
| `templates/wallet.html` | 765 | `Namaskah Audit System` | `Vrenum Audit System` |
| `templates/wallet.html` | 793 | `namaskah_audit_${date}.csv` | `vrenum_audit_${date}.csv` |
| `templates/settings.html` | 2165 | `'namaskah-data.json'` | `'vrenum-data.json'` |

---

## 🎨 CSS Files (Comments Only — Low Priority)

| File | Line | Reference |
|------|------|-----------|
| `static/css/admin_premium.css` | 1 | `/* Namaskah Premium Admin Design System (V2) */` |
| `static/css/namaskah-ui.css` | 2 | `* Namaskah UI — Unified Design System` |
| `static/css/dashboard.css` | 2 | `* Namaskah Dashboard Styles` |
| `static/css/verification-design-system.css` | 7 | `/* Primary Colors (Namaskah Brand) */` |
| `static/css/sms-polling-ui.css` | 2 | `* Namaskah — SMS Polling UI` |
| `static/css/themes/dark.css` | 1 | `/* NAMASKAH THEME: DARK */` |
| `static/css/themes/minimal.css` | 1 | `/* NAMASKAH THEME: MINIMAL */` |
| `static/css/themes/soft.css` | 1 | `/* NAMASKAH THEME: SOFT */` |

**Note**: Consider renaming `static/css/namaskah-ui.css` → `static/css/vrenum-ui.css` (requires updating `templates/base.html` line 65).

---

## 📧 Email Addresses — Full Replacement Map

| Current | Replace With | Found In |
|---------|--------------|----------|
| `support@namaskah.app` | `support@vrenum.app` | contact, info, refund, faq, schema_org, contact error handlers |
| `business@namaskah.app` | `business@vrenum.app` | contact |
| `security@namaskah.app` | `security@vrenum.app` | contact |
| `legal@namaskah.app` | `legal@vrenum.app` | terms, contact |
| `privacy@namaskah.app` | `privacy@vrenum.app` | cookies, privacy |
| `admin@namaskah.app` | `admin@vrenum.app` | admin/alerts, admin-dashboard.js |

---

## 🔗 URLs & External Links

| Current | Replace With | Found In |
|---------|--------------|----------|
| `https://namaskah.app` | `https://vrenum.app` | schema_org (×4) |
| `https://api.namaskah.com/v1` | `https://api.vrenum.app/v1` | api_docs |
| `https://namaskah.app/api` | `https://vrenum.app/api` | api_documentation (×4) |
| `www.namaskah.app` | `www.vrenum.app` | terms |
| `→ namaskah.app` (CNAME) | `→ vrenum.app` | whitelabel_setup |
| `https://twitter.com/namaskah` | New handle | landing, contact |
| `https://twitter.com/namaskahsms` | New handle | schema_org |
| `https://github.com/namaskah` | New repo | landing |
| `https://github.com/Infradevandops/NAMASKAHsms` | New repo | schema_org, contact |
| `@namaskah_sms_bot` | New bot username | telegram_settings |

---

## 🏗️ Built Assets (Rebuild Required)

| File | Note |
|------|------|
| `static/dist/js/dashboard.CIgkGDLr.js.map` | Contains "namaskah" — will be fixed on rebuild |

After updating source files, run the build step to regenerate dist files.

---

## ✅ Replacement Rules

1. **Page `<title>` tags**: Use `VRENUM ACTV8TN` as the brand
2. **Navbar / Logo / Home button**: Use `VRENUM ACTV8TN`
3. **Body copy** (sentences like "integrate Namaskah into..."): Use `vrenum.app`
4. **Email addresses**: `*@namaskah.app` → `*@vrenum.app`
5. **URLs**: `namaskah.app` → `vrenum.app`
6. **JS identifiers/keys** (localStorage, cache names, filenames): `namaskah` → `vrenum`
7. **CSS file rename**: `namaskah-ui.css` → `vrenum-ui.css` (optional)
8. **Comments**: Low priority, replace at discretion


---

## 🐍 BACKEND — Python Application Code

### `main.py` (Entry Point)
| Line | Current |
|------|---------|
| 2 | `Namaskah SMS - Optimized Application Factory` (comment) |
| 111 | `title="Namaskah SMS API"` |

### `app/core/config.py`
| Line | Current |
|------|---------|
| 16 | `app_name: str = "Namaskah SMS"` |
| 37 | `database_url: str = "sqlite:///./data/namaskah.db"` |

### `app/core/openapi.py`
| Line | Current |
|------|---------|
| 13 | `title="Namaskah SMS Verification API"` |

### `app/core/security_config.py`
| Line | Current |
|------|---------|
| 54 | `"api.namaskah.com"` (CORS allowed origin) |

### `app/core/exceptions.py` + `app/core/unified_error_handling.py`
**Class name**: `NamaskahException` — used as base exception class throughout the codebase.

Files importing/using `NamaskahException`:
- `app/core/__init__.py` (lines 12, 25)
- `app/core/exceptions.py` (lines 6-7, 18, 24, 30, 36, 66, 107, 152, 170, 182, 195, 212, 218)
- `app/core/unified_error_handling.py` (lines 26-27, 43, 53, 61, 71, 84, 94, 104, 116, 126, 136, 146, 326, 328, 330, 568)
- `app/middleware/exception_handler.py` (lines 16, 46, 173)
- `app/api/core/wallet.py` (lines 16, 47, 64, 81, 92)
- `app/utils/exception_handling.py` (lines 27, 34, 45, 56)
- `tests/unit/test_error_handling.py` (lines 5, 31, 32)

⚠️ **Decision needed**: Rename `NamaskahException` → `VrenumException`? This is a breaking change affecting ~30 files. Could keep as-is internally.

### `app/core/lifespan.py`
| Line | Current |
|------|---------|
| 28 | `"🚀 Starting Namaskah SMS API..."` |
| 285 | `"🛑 Shutting down Namaskah SMS API..."` |

### `app/core/startup.py`
| Line | Current |
|------|---------|
| 212 | `admin_email = os.getenv("ADMIN_EMAIL", "admin@namaskah.app")` |

### `app/core/init_admin.py`
| Line | Current |
|------|---------|
| 19 | `ADMIN_EMAIL = settings.admin_email or "admin@namaskah.app"` |

### `app/core/feature_flags.py`
| Line | Current |
|------|---------|
| 59 | `{"users": ["admin@namaskah.app"]}` |

### `app/core/database.py`
| Line | Current |
|------|---------|
| 81 | `"application_name": "namaskah_sms"` |
| 137 | `fallback_db = "sqlite:///./namaskah_fallback.db"` |

### `app/core/config_secrets.py`
| Line | Current |
|------|---------|
| 81 | `secret_name = f"namaskah/{provider_name}"` |
| 99 | `secret_name = f"namaskah/payment/{provider_name}"` |
| 117 | `secret_name = f"namaskah/oauth/{provider_name}"` |

### `app/core/secrets_manager.py`
| Line | Current |
|------|---------|
| 113 | `Tags=[{"Key": "Application", "Value": "Namaskah"}]` |

### `app/core/logging.py`
| Line | Current |
|------|---------|
| 1 | `"""Logging configuration for Namaskah application."""` |

---

## 📡 API Routers

### `app/api/main_routes.py`
| Line | Current |
|------|---------|
| 139 | `{"status": "healthy", "service": "namaskah-sms"}` |

### `app/api/admin/admin.py`
| Line | Current |
|------|---------|
| 504 | `subject=f"Re: Support Request #{ticket.id} - Namaskah SMS"` |
| 511 | `"Namaskah Support Team"` |
| 714 | `"Namaskah Team"` |

### `app/api/billing/invoice_endpoints.py`
| Line | Current |
|------|---------|
| 52 | `Paragraph("Namaskah", styles["Title"])` |
| 86 | `"Thank you for using Namaskah."` |

### `app/api/billing/payment_endpoints.py`
| Line | Current |
|------|---------|
| 88 | `metadata.get("namaskah_amount", 0)` |
| 178 | `metadata.get("namaskah_amount", 0)` |

### `app/api/billing/wallet_endpoints.py`
| Line | Current |
|------|---------|
| 80 | `namaskah_amount=request.amount_usd` |
| 240 | `filename = f"namaskah_wallet_audit_{...}.csv"` |

### `app/api/core/contact.py`
| Line | Current |
|------|---------|
| 32 | `to_email="support@namaskah.app"` |

### `app/api/core/forwarding.py`
| Line | Current |
|------|---------|
| 214 | `"Sent via Namaskah SMS Forwarding"` |
| 238 | `"User-Agent": "Namaskah-SMS-Forwarding/1.0"` |

### `app/api/core/onesignal.py`
| Line | Current |
|------|---------|
| 30 | `"This is a test notification from Namaskah"` |

### `app/api/core/setup.py`
| Line | Current |
|------|---------|
| 20 | `admin_email = os.getenv("ADMIN_EMAIL", "admin@namaskah.app")` |

### `app/api/core/system.py`
| Line | Current |
|------|---------|
| 88 | `"service_name": "Namaskah SMS"` |

### `app/api/core/telegram.py`
| Line | Current |
|------|---------|
| 130 | `"namaskah_sms_bot"` (fallback bot username) |
| 336 | `"Connected to Namaskah account"` |
| 355 | `"Disconnected from Namaskah"` |

### `app/api/core/user_settings.py`
| Line | Current |
|------|---------|
| 271 | `subject="Password Reset - Namaskah"` |

### `app/api/core/user_settings_endpoints.py`
| Line | Current |
|------|---------|
| 187 | `filename=namaskah-data.json` |

### `app/api/core/whitelabel_endpoints.py`
| Line | Current |
|------|---------|
| 366 | `Host: _namaskah-verify.{domain}` |
| 376 | `<meta name="namaskah-verification" ...>` |
| 383 | `/.well-known/namaskah-verification.txt` |

⚠️ **Decision needed**: The whitelabel verification system uses `_namaskah-verify` as a DNS TXT record prefix and `namaskah-verification` as a meta tag name. Changing these would break existing whitelabel customers' DNS records.

### `app/api/notifications/email_endpoints.py`
| Line | Current |
|------|---------|
| 42 | `"test email from Namaskah SMS"` |

### `app/api/notifications/push_endpoints.py`
| Line | Current |
|------|---------|
| 246 | `"test push notification from Namaskah"` |

---

## 📬 Services Layer

### `app/services/email_service.py`
| Line | Current |
|------|---------|
| 27 | `self.from_name = "Namaskah"` |
| 99 | `"Payment Receipt — Namaskah"` |
| 108 | `"Payment Failed — Namaskah"` |
| 117 | `"Refund Processed — Namaskah"` |
| 132 | `"verify your Namaskah account"` |
| 138 | `"Verify your Namaskah email"` |
| 151 | `"reset your Namaskah password"` |
| 157 | `"Reset your Namaskah password"` |

### `app/services/email_notification_service.py` (20+ occurrences)
| Lines | Current |
|-------|---------|
| 111, 156, 200, 243, 289 | Email subjects with `"- Namaskah SMS"` |
| 318 | `"from": f"Namaskah <{self.from_email}>"` |
| 374, 376, 417, 419, 474, 476, 533, 535, 590, 592, 653, 655 | `https://namaskah.app/...` URLs |
| 434 | `"Enter the code in the Namaskah app"` |
| 440, 560, 621, 704 | `https://namaskah.app/...` button links |

### `app/services/telegram_service.py`
| Line | Current |
|------|---------|
| 168 | `"Your Namaskah account is now connected to Telegram."` |

### `app/services/payment_service.py`
| Line | Current |
|------|---------|
| 65 | `reference = f"namaskah_{user_id}_{...}"` |
| 74 | `namaskah_amount=amount_usd` |
| 89 | `"namaskah_amount": amount_usd` |

### `app/services/webhook_notification_service.py`
| Line | Current |
|------|---------|
| 36 | `"User-Agent": "Namaskah/1.0"` |

### `app/services/mfa_service.py`
| Line | Current |
|------|---------|
| 20 | `issuer_name="Namaskah SMS"` |

⚠️ **Note**: Changing MFA issuer_name will invalidate existing users' TOTP authenticator entries.

### `app/services/compliance_service.py`
| Line | Current |
|------|---------|
| 107 | `"compliance_framework": "SOC 2 Type II (Namaskah Institutional)"` |

### `app/services/financial_statements_service.py`
| Lines | Current |
|-------|---------|
| 98, 201, 299 | `reporting_entity="Namaskah SMS"` |

### `app/services/whitelabel_service.py`
| Line | Current |
|------|---------|
| 89-90 | `_namaskah-verify` DNS prefix |
| 133 | `namaskah-verification` meta tag |
| 162 | `/.well-known/namaskah-verification.txt` |

### `app/services/auto_topup_service.py`
| Line | Current |
|------|---------|
| 60 | `namaskah_amount=topup_amount` |

---

## 💾 Models

### `app/models/transaction.py`
| Line | Current |
|------|---------|
| 45 | `namaskah_amount = Column(Float)` |

⚠️ **Database column**: Renaming this requires a migration. Consider keeping as-is or adding an alias.

---

## 📧 Email Utilities

### `app/utils/email.py`
| Lines | Current |
|-------|---------|
| 100 | `"Welcome to Namaskah SMS - $name"` |
| 102, 104 | `"Welcome to Namaskah SMS!"` |
| 111, 128, 129, 142, 160 | `"Namaskah Team"` |
| 134 | `"Password Reset - Namaskah SMS"` |
| 138 | `"your Namaskah SMS account"` |
| 147 | `"Payment Receipt - Namaskah SMS"` |

---

## ⚙️ Environment Files

### `.env`
| Line | Current |
|------|---------|
| 1 | `DATABASE_URL=sqlite:///./data/namaskah_local.db` |
| 4 | `ADMIN_EMAIL=admin@namaskah.app` |

### `.env.example`
| Line | Current |
|------|---------|
| 2 | `# Namaskah SMS — Environment Template` |
| 15 | `DATABASE_URL=sqlite:///./data/namaskah.db` |
| 21 | `ADMIN_EMAIL=admin@namaskah.app` |

### `.env.development`
| Line | Current |
|------|---------|
| 5 | `DATABASE_URL=sqlite:///./data/namaskah_local.db` |
| 39 | `SMTP_FROM=noreply@namaskah.app` |

### `.env.production`
| Line | Current |
|------|---------|
| 7 | `SECRET_KEY=Namaskah2024SecureJWTKeyForProductionUse32Chars` |
| 8 | `JWT_SECRET_KEY=Namaskah2024SecureJWTKeyForProductionUse32Chars` |
| 9 | `DATABASE_URL=postgresql://namaskahdb:...` |
| 11 | `ADMIN_EMAIL=admin@namaskah.app` |
| 12 | `ADMIN_PASSWORD=Namaskah@Admin2024` |
| 35 | `CORS_ORIGINS=...,https://namaskah.app` |

⚠️ **Security**: Secrets/passwords containing "Namaskah" should be rotated regardless.

---

## 🚢 Deployment Configs

### `render.yaml` (Staging)
| Lines | Current |
|-------|---------|
| 4 | `name: namaskah-api-staging` |
| 12 | `name: namaskah-db-staging` |
| 16 | `name: namaskah-redis-staging` |
| 26 | `name: namaskah-db-staging` |
| 32 | `name: namaskah-redis-staging` |

### `deploy/render/render.production.yaml`
| Lines | Current |
|-------|---------|
| 4 | `name: namaskah-api-prod` |
| 18 | `name: namaskah-db-prod` |
| 22 | `name: namaskah-redis-prod` |
| 51 | `name: namaskah-db-prod` |
| 59 | `name: namaskah-redis-prod` |
| 68 | `name: namaskah-prometheus-prod` |
| 86 | `name: namaskah-grafana-prod` |

### `docker-compose.yml`
| Line | Current |
|------|---------|
| 38 | `POSTGRES_DB: namaskah_dev` |
| 39 | `POSTGRES_USER: namaskah` |

### `deploy/docker/docker-compose.production.yml`
| Lines | Current |
|-------|---------|
| 8, 25, 35, 44, 53, 58, 67, 79, 86 | `namaskah-app`, `namaskah-db`, `namaskah-redis`, `namaskah-nginx`, `namaskah-network` |

### `deploy/docker/docker-compose.test.yml`
| Line | Current |
|------|---------|
| 20 | `POSTGRES_DB: namaskah_test` |

### `deploy/k8s/namaskah_deploy.yaml` (50+ occurrences)
Namespace: `namaskah-prod`, resources: `namaskah-app`, `namaskah-config`, `namaskah-secrets`, `namaskah-service`, `namaskah-hpa`, `namaskah-ingress`, `namaskah-network-policy`, `namaskah-pdb`, `namaskah-metrics`
- Line 22: `APP_NAME: "Namaskah SMS"`
- Lines 73, 75, 98, 100, 110, 112: DB name `namaskah_prod`, user `namaskah_user`
- Lines 403, 406: `api.namaskah.app`
- Line 290: `image: namaskah-app:2.4.0`
- Line 404: `secretName: namaskah-tls`

### `deploy/digitalocean/` (setup.sh, deploy.sh, nginx.conf, supervisor.conf)
- User: `namaskah` (Linux user)
- Paths: `/home/namaskah/app`, `/var/log/namaskah/`
- Nginx: `server_name namaskah.app www.namaskah.app`
- Supervisor: `[program:namaskah]`
- Git clone: `NAMASKAHsms.git`

### `config/nginx.conf`
| Lines | Current |
|-------|---------|
| 45 | `server_name api.namaskah.app` |
| 48-49 | `ssl_certificate /etc/ssl/certs/namaskah.crt` / `.key` |

### `config/nginx-production.conf`
| Lines | Current |
|-------|---------|
| 1 | Comment: `Namaskah SMS` |
| 64 | `upstream namaskah_app` |
| 135 | `server_name api.namaskah.app` |
| 138-139 | SSL cert paths |
| 169, 187, 205, 218, 235, 259 | `proxy_pass http://namaskah_app` |

### `config/nginx-multi-region.conf`
| Lines | Current |
|-------|---------|
| 7 | `server namaskah-us-east:8000` |
| 11 | `server namaskah-eu-west:8000` |

---

## 📊 Monitoring

### `monitoring/config/prometheus.yml`
| Lines | Current |
|-------|---------|
| 8 | `monitor: 'namaskah-sms'` |
| 29 | `job_name: 'namaskah-app'` |

### `monitoring/config/prometheus-config.yml`
| Lines | Current |
|-------|---------|
| 15-16 | `job_name: 'namaskah-api'` |
| 18 | `targets: ['namaskah-us-east:8000', 'namaskah-eu-west:8000']` |

### `monitoring/docker-compose.yml`
| Line | Current |
|------|---------|
| 152 | `DATA_SOURCE_NAME=...namaskah_user...namaskah_prod...` |

### `monitoring/grafana/provisioning/dashboards/dashboards.yml`
| Line | Current |
|------|---------|
| 4 | `name: 'Namaskah Dashboards'` |

---

## 🧪 Tests

### Unit Tests
| File | Lines | Reference |
|------|-------|-----------|
| `tests/unit/test_error_handling.py` | 5, 31-32 | `NamaskahException` |
| `tests/unit/test_payment_model_integrity.py` | 33, 49, 81 | `namaskah_amount` field |
| `tests/unit/test_verification_and_tier.py` | 343, 377 | `namaskah_amount` in metadata |
| `tests/unit/test_email_service.py` | 17 | `test@namaskah.com` |
| `tests/unit/test_whitelabel_service.py` | 113 | `namaskah-verification` meta tag |
| `tests/unit/test_whitelabel_middleware.py` | 54-199 | `namaskah.app` as base_domain (8 refs) |

### Integration Tests
| File | Lines | Reference |
|------|-------|-----------|
| `tests/integration/test_webhook_security.py` | 23, 39, 78, 104, 147 | `namaskah_amount` |
| `tests/integration/test_database_operations.py` | 76 | `namaskah_amount` |
| `tests/integration/test_whitelabel_api.py` | 256 | `_namaskah-verify` |

### E2E Tests
| File | Lines | Reference |
|------|-------|-----------|
| `tests/e2e/conftest.py` | 38 | `admin@namaskah.app` |
| `tests/e2e/test_welcome_flow.py` | 11 | `"Welcome to Namaskah"` |
| `tests/e2e/test_critical_paths.py` | 11 | `to_have_title("Namaskah")` |
| `tests/e2e/test_critical_journeys.py` | 21 | `title == "Namaskah SMS"` |
| `tests/e2e/test_verification_flow.py` | 279 | `admin@namaskah.app` |
| `tests/e2e/test_verification_flow_v2.py` | 17 | `admin@namaskah.app` |

### Frontend Tests
| File | Lines | Reference |
|------|-------|-----------|
| `tests/frontend/test_login_page.spec.js` | 42-43, 158-159 | `admin@namaskah.app`, `Namaskah@Admin2024` |
| `tests/frontend/e2e/dashboard.spec.js` | 33 | `test@namaskah.app` |
| `tests/frontend/e2e/settings.spec.js` | 23, 76 | `test@namaskah.app` |

### Load Tests
| File | Lines | Reference |
|------|-------|-----------|
| `tests/load/locustfile.py` | 1, 6 | `NamaskahUser` class |

### Other Test Files
| File | Reference |
|------|-----------|
| `tests/test_forwarding_email.py` | `noreply@namaskah.app` (4 refs) |
| `tests/admin/test_intelligence_graduation.py` | `test@namaskah.com` |

---

## 📜 Scripts (40+ files)

### High Priority (Production-facing)
| File | Key References |
|------|---------------|
| `scripts/start.sh` | `"Starting Namaskah SMS API..."` |
| `scripts/start_production.sh` | `"Starting Namaskah SMS..."` |
| `scripts/restart.sh` | `namaskah_sms` DB name |
| `scripts/fix_production_issues.sh` | `/root/NAMASKAHsms`, `systemctl restart namaskah` |
| `scripts/deploy_refund_fix.sh` | `/root/NAMASKAHsms`, `systemctl restart namaskah` |
| `scripts/deploy_area_code_feature.sh` | `staging.namaskah.app`, `namaskah.app` |
| `scripts/setup_uptimerobot.sh` | `namaskah.onrender.com`, `admin@namaskah.app` |
| `scripts/deployment/deploy_production.sh` | `namaskah_user`, `namaskah_prod` |
| `scripts/deployment/setup-cicd.sh` | `"Setting up CI/CD for Namaskah SMS"` |
| `scripts/deployment/backup_rclone.sh` | `namaskah-backup`, `namaskah-backups` |

### Medium Priority (Dev/Maintenance)
| File | Key References |
|------|---------------|
| `scripts/backup_database.py` | `namaskah_backup_` prefix |
| `scripts/backup_rclone.py` | `namaskah-backup`, `namaskah-backups`, `namaskah_backup_` |
| `scripts/backup_free_tier.py` | `Namaskah-Backups`, `namaskah_backup_` |
| `scripts/backup_render_emergency.py` | DB URL, `Namaskah SMS Platform` |
| `scripts/backup_render_interactive.py` | `Namaskah SMS Platform`, `namaskahdb` |
| `scripts/reset_database.py` | `admin@namaskah.app` (6 refs) |
| `scripts/reset_admin_account.py` | `namaskah.db`, `admin@namaskah.app` |
| `scripts/create_admin_user.py` | `namaskah.db`, `admin@namaskah.app`, `Welcome to Namaskah!` |
| `scripts/setup_new_database.sh` | DB URL, `admin@namaskah.app` |
| `scripts/set_user_passwords.py` | `test@namaskah.app`, `admin@namaskah.app` |
| `scripts/setup_test_tiers.py` | `admin@namaskah.app` |
| `scripts/update_balance.py` | `admin@namaskah.app` |
| `scripts/security/` | Various comments + `namaskah` references |
| `scripts/development/` | Various `admin@namaskah.app`, URLs, paths |
| `scripts/maintenance/restore_backup.sh` | `namaskah_prod`, `namaskah_user` |
| `scripts/sql/create_payment_tables.sql` | `namaskah_amount` column |
| `scripts/sql/create_admin.sql` | `admin@namaskah.app` |

---

## 🔧 CI/CD

### `.github/workflows/ci.yml`
| Lines | Current |
|-------|---------|
| 84, 213, 290 | `POSTGRES_DB: namaskah_test` |
| 146, 172, 249, 261, 325, 335, 370 | `DATABASE_URL: ...namaskah_test` |
| 161-163, 255-256, 327 | `CREATE/DROP DATABASE namaskah_test` |
| 377 | `TEST_USER_EMAIL: admin@namaskah.app` |

---

## 📖 API Spec

### `docs/engineering/api/api_v2_spec.yaml`
| Line | Current |
|------|---------|
| 3 | `title: Namaskah SMS API` |
| 7 | `name: Namaskah Support` |
| 8 | `url: https://namaskah.app` |
| 13 | `url: https://namaskah.app/api/v1` |

---

## 🧰 Tools

### `tools/postman/Namaskah_API.json`
| Lines | Current |
|-------|---------|
| 3 | `"name": "Namaskah SMS API"` |
| 4 | `"description": "Test collection for Namaskah SMS verification platform"` |

**Also rename file**: `Namaskah_API.json` → `Vrenum_API.json`

---

## 📚 Documentation (Markdown files — Low Priority)

These are internal docs and don't affect production:
- `README.md`, `CHANGELOG.md`, `PLATFORM_STATUS.md`, `STATUS.md`, `STABILITY.md`, `ACTIVE_TASKS.md`
- `docs/INDEX.md`, `docs/PLATFORM_ASSESSMENT.md`, `docs/UI_UX_ASSESSMENT.md`
- `docs/business/` (3 files)
- `docs/engineering/` (3 files)
- `docs/operations/` (3 files)
- `docs/tasks/` (3 files)
- `docs/knowledge/BUSINESS_LOGIC.md`
- `docs/archive/` (12+ files)
- `config/README.md`, `static/css/README.md`
- `tests/manual/` (2 files)

---

## 📊 GRAND TOTAL

| Category | Files | Occurrences | Priority |
|----------|-------|-------------|----------|
| Frontend (HTML/JS/CSS/JSON) | 68 | ~165 | 🔴 High |
| Backend Python (app/) | 28 | ~95 | 🔴 High |
| Environment files | 4 | ~15 | 🔴 High |
| Deployment configs | 14 | ~80 | 🟡 Medium |
| CI/CD | 1 | ~18 | 🟡 Medium |
| Scripts | 30+ | ~70 | 🟡 Medium |
| Tests | 15 | ~40 | 🟢 Low |
| Documentation (MD) | 25+ | ~100+ | 🟢 Low |
| **TOTAL** | **~185 files** | **~580+ occurrences** | |

---

## ⚠️ Breaking Change Warnings

1. **`NamaskahException` class** — Renaming affects 30+ files and all error handling. Consider keeping internally or doing a careful refactor.
2. **`namaskah_amount` DB column** — Requires Alembic migration. Could alias instead.
3. **MFA `issuer_name`** — Changing invalidates all existing TOTP setups for users.
4. **Whitelabel DNS** (`_namaskah-verify`) — Changing breaks existing customers' domain verification.
5. **Service worker cache names** — Changing forces full cache invalidation for all users.
6. **`localStorage` keys** — Changing loses users' theme preferences.
7. **Payment references** (`namaskah_{user_id}_...`) — Historical transaction references in Paystack.
8. **AWS Secrets Manager paths** (`namaskah/...`) — Requires secret recreation.
9. **Kubernetes namespace** (`namaskah-prod`) — Requires full redeployment.
10. **Database names** (`namaskah_test`, `namaskah_prod`, `namaskahdb`) — Requires DB recreation or rename.
