# Broken & Dead-End Buttons/Routes — ✅ All Complete

| # | Fix | Files |
|---|-----|-------|
| 1a | `/verify` → `verify_modern.html` | `main_routes.py` |
| 1b | `/voice-verify` → `voice_verify_modern.html` | `main_routes.py` |
| 2a–2f | Added routes: `/about`, `/contact`, `/faq`, `/affiliate`, `/status`, `/password-reset`, `/api-keys` | `main_routes.py` |
| 3a | `/account/api-keys` → `/api-keys` | `api_docs.html` |
| 3b | `/admin-dashboard` → `/admin` | `admin/verification_history.html`, `admin/pricing_templates.html` |
| 3c | `/support` → redirect to `/contact` | `main_routes.py`, `tier_comparison_modal.html` |
| 3d | `/blog`, `/careers` | Left as-is (no content, low priority) |
| 3e | `/gdpr` → redirect to `/privacy-settings` | `main_routes.py`, `landing.html` |
| 3f | `/landing` → redirect to `/` | `main_routes.py`, `public_base.html` |
| 3g | `/api` → `/api-docs` | `landing.html` |
| 3h | `/auth/forgot-password` → `/password-reset` | `main_routes.py`, `login.html` |
| 4 | Tier modals: `/pricing` → `/settings?tab=billing` | `tier_locked_modal.html`, `tier_comparison_modal.html` |
