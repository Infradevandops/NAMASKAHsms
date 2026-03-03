# Broken & Dead-End Buttons/Routes

**Scope**: All navigation links, buttons, and `window.location.href` calls that hit a 404 or wrong page.

---

## Group 1 — Wrong template served (critical, affects all users)

### 1a — `/verify` serves old `verify.html` instead of `verify_modern.html`
**File:** `app/api/main_routes.py` line 127

`verify.html` is a legacy page. Its `purchaseVerification()` function has no `fetch` calls wired — the button is disabled and nothing works. Every link to `/verify` (sidebar, dashboard type-picker, history, analytics, payment_success) lands on a broken page.

`verify_modern.html` is the correct, fully-wired 3-step flow.

**Fix:** Change `"verify.html"` → `"verify_modern.html"` in the `/verify` route handler.

---

### 1b — `/voice-verify` serves old `voice_verify.html` instead of `voice_verify_modern.html`
**File:** `app/api/main_routes.py` line 212

`voice_verify.html` calls:
- `POST /api/verification/voice/create` → **404** (no such route)
- `GET /api/verification/textverified/services` → **404** (no such route)
- Navigates to `/voice-status/{id}` → **404** (no page route)

`voice_verify_modern.html` is the correct page (fixed in previous session to poll `/api/verify/status/{id}`).

**Fix:** Change `"voice_verify.html"` → `"voice_verify_modern.html"` in the `/voice-verify` route handler.

---

## Group 2 — Missing page routes (templates exist, no route)

All of these return 404. Templates exist and just need a route added to `app/api/main_routes.py`.

### 2a — `/about`
Template: `about.html` ✅  
Linked from: `landing.html`, `public_base.html`, footer on 6+ pages

### 2b — `/contact`
Template: `contact.html` ✅  
Linked from: `landing.html`, `public_base.html`, footer on 6+ pages

### 2c — `/faq`
Template: `faq.html` ✅  
Linked from: `landing.html`  
Note: `/faq` exists as an API endpoint under `admin/support.py` — that's under `/api/admin/...` prefix so no conflict.

### 2d — `/affiliate`
Template: `affiliate_program.html` ✅  
Linked from: `landing.html`

### 2e — `/status`
Template: `status.html` ✅  
Linked from: `landing.html`, `public_base.html`

### 2f — `/password-reset`
Templates: `password_reset.html`, `password_reset_confirm.html` ✅  
Linked from: `login.html` as `/auth/forgot-password` → no route exists at that path either.  
**Fix:** Add `/password-reset` page route AND fix `login.html` link from `/auth/forgot-password` → `/password-reset`.

**All Group 2 fix:** Add to `main_routes.py`:
```python
@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@router.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    return templates.TemplateResponse("faq.html", {"request": request})

@router.get("/affiliate", response_class=HTMLResponse)
async def affiliate(request: Request):
    return templates.TemplateResponse("affiliate_program.html", {"request": request})

@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request})

@router.get("/password-reset", response_class=HTMLResponse)
async def password_reset(request: Request):
    return templates.TemplateResponse("password_reset.html", {"request": request})
```

---

## Group 3 — Wrong destination links

### 3a — `/account/api-keys` → 404
**File:** `templates/api_docs.html`  
No route at `/account/api-keys`. API keys page is at `/api-docs` (which serves `api_keys.html`... wait — `/api-docs` serves `api_docs.html`; `api_keys.html` has no route at all).

**Fix:** 
- Add `@router.get("/api-keys")` → `api_keys.html` in `main_routes.py`
- Fix `api_docs.html` link from `/account/api-keys` → `/api-keys`

### 3b — `/admin-dashboard` → 404
**Files:** `templates/admin/verification_history.html`, `templates/admin/pricing_templates.html`  
Admin dashboard is at `/admin`, not `/admin-dashboard`.

**Fix:** Change both links from `/admin-dashboard` → `/admin`.

### 3c — `/support` → 404
**Files:** `landing.html`, `tier_comparison_modal.html`  
No page route. No template either — this is likely meant to be the contact page or an external link.

**Fix:** Redirect `/support` → `/contact` (add a `RedirectResponse` route), or change links to `/contact`.

### 3d — `/blog`, `/careers` → 404
**File:** `landing.html`  
No templates, no routes. These are placeholder links.

**Fix:** Either remove the links or point them to `/` until content exists. Low priority.

### 3e — `/gdpr` → wrong handler
**File:** `landing.html`  
`/gdpr` is mounted as the GDPR router prefix — `GET /gdpr/export` and `DELETE /gdpr/account` are API endpoints. A bare `GET /gdpr` returns 404.

**Fix:** Change `landing.html` link from `/gdpr` → `/privacy-settings` (the actual GDPR settings page).

### 3f — `/landing` → 404
**Files:** `public_base.html`, `welcome.html`  
No route at `/landing`. Home page is at `/`.

**Fix:** Change links from `/landing` → `/`.

### 3g — `/api` → 404
**File:** `landing.html`  
Probably meant `/api-docs`.

**Fix:** Change link from `/api` → `/api-docs`.

---

## Group 4 — Stale `/pricing` links (should go to `/settings?tab=billing`)

These were partially fixed in the sidebar audit but remain in component files:

| File | Location | Fix |
|------|----------|-----|
| `templates/components/tier_locked_modal.html` line 184 | Upgrade button | → `/settings?tab=billing` |
| `templates/components/tier_comparison_modal.html` line 432 | "View Full Pricing" button | → `/pricing` is fine (page exists) |
| `templates/components/tier_comparison_modal.html` line 523 | `selectTier()` redirect | → `/settings?tab=billing` |

Note: `dashboard.js` also has stale `/pricing` refs (lines 986, 1002) but `dashboard.html` loads `dashboard-ultra-stable.js` not `dashboard.js` — dead code, no user impact.

---

## Fix Order

| Priority | Group | Impact |
|----------|-------|--------|
| 🔴 Critical | 1a, 1b | Every verify/voice-verify navigation is broken |
| 🔴 High | 2a–2f | All public footer links 404 |
| 🟡 Medium | 3a–3g | Specific broken links in specific pages |
| 🟢 Low | 4 | Tier modal upgrade flow inconsistency |
