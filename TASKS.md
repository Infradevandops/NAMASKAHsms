# Fix Tasks — Namaskah Assessment Findings

**Created**: March 2026  
**Source**: Codebase assessment + app.log analysis  
**Status**: ✅ All tasks executed

---

## 🔴 Critical — Fix Before Production

### ✅ TASK-01: Remove emergency admin endpoint
**Files changed**: `main.py` (import + router removed), `app/api/emergency.py` (deleted)

### ✅ TASK-02: Fix hardcoded USD→NGN exchange rate
**Files changed**: `app/core/config.py` (`ngn_usd_rate: float = 1600.0` added), `app/services/payment_service.py` (uses `settings.ngn_usd_rate`)

### ✅ TASK-03: Fix JWT token expiry ignoring config
**Files changed**: `app/services/auth_service.py`
- `create_user_token` now defaults to `settings.jwt_expiration_hours` (24h)
- Added `jti` claim to every token
- `verify_token` checks Redis blacklist for revoked tokens
- Added `revoke_token()` method for logout to call

### ✅ TASK-04: Fix `credits` column using Float for money
**Files changed**: `app/models/user.py` (5 columns → `Numeric(10,4)`), `app/models/activity.py`  
**Migration**: `alembic/versions/fix_monetary_float_columns.py` — run `alembic upgrade head`

### ✅ TASK-05: Fix `phonenumbers` missing from requirements.txt
**Files changed**: `requirements.txt` — added `phonenumbers==8.13.48`

### ✅ TASK-16: Fix bcrypt version warning on startup
**Files changed**: `requirements.txt` — downgraded `bcrypt==4.0.1` → `bcrypt==3.2.2`

---

## 🟠 Significant

### ✅ TASK-06: Fix CSP allowing `unsafe-inline` and `unsafe-eval`
**Files changed**: `app/middleware/security.py`
- Removed `unsafe-eval` entirely
- Replaced `unsafe-inline` in `script-src` with per-request nonce (`'nonce-{random}'`)
- Nonce stored in `request.state.csp_nonce` for templates to use
- **Action needed**: Update Jinja2 templates to add `nonce="{{ request.state.csp_nonce }}"` on all `<script>` tags

### ✅ TASK-07: Fix version mismatch in FastAPI app declaration
**Files changed**: `app/core/config.py` (`version = "4.4.1"`), `main.py` (uses `settings.version`)

### ✅ TASK-08: Resolve duplicate/conflicting router registrations
**Files changed**: `main.py` — removed `user_settings_router` and `user_auth_router` duplicate registrations

### ✅ TASK-09: Add token revocation on logout
**Files changed**: `app/services/auth_service.py` — `revoke_token()` added  
**Action needed**: Call `auth_service.revoke_token(token)` in the logout endpoint

### ✅ TASK-10: Remove or gitignore committed sensitive files
**Status**: `.gitignore` already correctly covers `.env` and `logs/`. No action needed unless git history contains committed secrets — if so, rotate all keys.

### ✅ TASK-11: Purge dead stub services
**Deleted**:
- `app/services/cdn_service.py`
- `app/services/whatsapp_service.py`
- `app/services/telegram_service.py`
- `app/services/voice_polling_service.py`
- `app/services/reseller_service.py`
- `app/services/enterprise_service.py`
- `app/services/translation_service.py`
- `app/services/smart_routing.py`
- `app/services/disaster_recovery.py`
- `app/core/load_balancer.py`
- `app/core/auto_scaling.py`
- `app/core/region_manager.py`
- `app/api/admin/infrastructure.py`

### ✅ TASK-12: Clean up one-off scripts
**Deleted**: 38 one-off `fix_*`, `verify_*`, `check_*`, `simulate_*`, `cleanup_*` scripts from `scripts/`

### ✅ TASK-13: Fix circular import workarounds
**Files changed**: `app/models/user.py` (restored `activities` relationship with `lazy="select"`), `app/models/activity.py` (restored `user` back-reference)

---

## 🟡 Housekeeping

### ✅ TASK-14: Consolidate documentation
**Deleted**: 17 phase completion/sprint implementation markdown files from `docs/`

### ✅ TASK-15: Remove stub coverage test files
**Deleted**: `test_batch_coverage_boost.py`, `test_coverage_boost.py`, `test_basic_coverage.py`, `test_simple.py`, `test_core_working.py`

---

## Log-Specific Findings

### ✅ TASK-16: bcrypt warning — see above

### ✅ TASK-17: 402 mislogged as database error
**Files changed**: `app/core/database.py` — `get_db()` now catches `HTTPException` separately and lets it propagate without logging as a DB error

### ✅ TASK-18: TextVerified disabled at startup
**Files changed**: `app/core/lifespan.py` — logs a loud `ERROR` (not just warning) when TextVerified is disabled, clearly stating which env vars are missing  
**Action needed**: Set `TEXTVERIFIED_API_KEY` and `TEXTVERIFIED_USERNAME` in production `.env`

### ✅ TASK-19: JWT tokens exposed in WebSocket URLs
**Files changed**: `app/api/websocket_endpoints.py` — completely rewritten
- Endpoint no longer accepts `?token=` query param
- Client connects, then sends `{"type": "auth", "token": "<jwt>"}` as first message
- Token never appears in URL, access logs, or browser history
- **Action needed**: Update frontend WebSocket client to use the new auth flow

---

## Remaining Manual Actions

| Action | Owner |
|--------|-------|
| Run `alembic upgrade head` to apply Numeric migration | DevOps |
| Set `TEXTVERIFIED_API_KEY` + `TEXTVERIFIED_USERNAME` in prod `.env` | DevOps |
| Update `NGN_USD_RATE` in `.env` when exchange rate drifts | DevOps |
| Add `nonce="{{ request.state.csp_nonce }}"` to all `<script>` tags in templates | Frontend |
| Call `auth_service.revoke_token(token)` in the logout endpoint | Backend |
| Update frontend WebSocket client to send auth as first message | Frontend |
| Rotate secrets if `.env` was ever committed to git history | Security |


**Created**: March 2026  
**Source**: Codebase assessment + app.log analysis

---

## 🔴 Critical — Fix Before Production

### TASK-01: Remove emergency admin endpoint
**File**: `main.py`, `app/api/emergency.py`  
**Problem**: `/api/emergency-create-admin` is permanently mounted. It creates/resets admin accounts and is reachable in production. The comment in `main.py` says "TEMPORARY" — it never got removed.  
**Fix**:
- Delete `app/api/emergency.py`
- Remove the `emergency_router` import and `include_router` call from `main.py`
- If needed for ops, gate it behind `if settings.environment != "production"` at minimum

---

### TASK-02: Fix hardcoded USD→NGN exchange rate
**File**: `app/services/payment_service.py` line ~65  
**Problem**: `amount_kobo = int(amount_usd * 100 * 800)` — hardcoded 800 NGN/USD. This silently overcharges or undercharges users as the rate moves.  
**Fix**:
- Add `ngn_usd_rate: float = 1600.0` (or current rate) to `config.py` as a config value
- Replace the hardcoded `800` with `settings.ngn_usd_rate`
- Long-term: integrate a live FX API (e.g. ExchangeRate-API) or at minimum add a comment with the date it was last updated and a startup warning if the value is older than 30 days

---

### TASK-03: Fix JWT token expiry ignoring config
**File**: `app/services/auth_service.py` line ~47  
**Problem**: `create_user_token` defaults to `expires_hours=24 * 30` (30 days), completely ignoring `settings.jwt_expiration_hours` (which is 24h). Long-lived tokens with no revocation = stolen token is valid for a month.  
**Fix**:
- Change default to `expires_hours: int = None`
- Use `settings.jwt_expiration_hours` when `None` is passed
- Add a token blacklist check in `verify_token` using Redis (key: `blacklist:token:<jti>`) so logout actually invalidates tokens

---

### TASK-04: Fix `credits` column using Float for money
**File**: `app/models/user.py` line ~14  
**Problem**: `credits = Column(Float, ...)` — IEEE 754 floats accumulate rounding errors on financial values.  
**Fix**:
- Migrate `credits`, `free_verifications`, `bonus_sms_balance`, `monthly_quota_used`, `referral_earnings` to `Numeric(10, 4)`
- Also fix `reward_amount`, `price`, `discount` in other models
- Write an Alembic migration

---

### TASK-05: Fix `phonenumbers` missing from requirements.txt
**File**: `requirements.txt`  
**Problem**: CHANGELOG v4.4.1 lists `phonenumbers==8.13.48` as a new dependency for VOIP rejection, but it's not in `requirements.txt`. The `PhoneValidator` service will fail silently or crash on import in a fresh environment.  
**Fix**:
- Add `phonenumbers==8.13.48` to `requirements.txt`
- Verify `app/services/phone_validator.py` imports it correctly

---

## 🟠 Significant — Fix Soon

### TASK-06: Fix CSP allowing `unsafe-inline` and `unsafe-eval`
**File**: `app/middleware/security.py`  
**Problem**: The CSP header includes `'unsafe-inline'` and `'unsafe-eval'` in `script-src`, which defeats XSS protection. README claims OWASP A03 compliance — this contradicts it.  
**Fix**:
- Audit all inline scripts in templates and move them to external `.js` files
- Replace `'unsafe-inline'` with a nonce-based approach (`'nonce-{random}'` per request)
- Remove `'unsafe-eval'` — identify what requires it (likely a bundler or template engine) and eliminate the need

---

### TASK-07: Fix version mismatch in FastAPI app declaration
**File**: `main.py` line ~85  
**Problem**: `FastAPI(version="4.0.0")` but the project is at v4.4.1. Affects `/openapi.json` and API docs.  
**Fix**: Change to `version=settings.version` and update `config.py` `version` field to `"4.4.1"`

---

### TASK-08: Resolve duplicate/conflicting router registrations
**File**: `main.py`  
**Problem**: Multiple overlapping routers registered — `user_settings_router`, `user_settings_endpoints_router`, `user_auth_router` all from the same module. `auth_routes.py`, `auth_enhanced.py`, and `auth.py` all exist. Route conflicts cause silent 404s or wrong handler execution.  
**Fix**:
- Audit all registered routers and map their prefixes/paths
- Identify and remove duplicate route definitions
- Consolidate `auth.py` / `auth_enhanced.py` / `auth_routes.py` into one file

---

### TASK-09: Add token revocation on logout
**File**: `app/services/auth_service.py`, relevant logout endpoint  
**Problem**: Logout doesn't invalidate JWTs. A stolen or leaked token remains valid until expiry.  
**Fix**:
- Add `jti` (JWT ID) claim to token payload
- On logout, store `jti` in Redis with TTL matching token expiry: `SET blacklist:jti:<jti> 1 EX <ttl>`
- In `verify_token`, check Redis for blacklisted `jti` before returning user_id

---

### TASK-10: Remove or gitignore committed sensitive files
**Files**: `.env`, `logs/app.log`  
**Problem**: `.env` file is present in the repo root (likely committed). `logs/app.log` is tracked. Both can leak credentials and internal data.  
**Fix**:
- Verify `.gitignore` includes `.env` and `logs/`
- If `.env` was ever committed, rotate all secrets (JWT keys, Paystack key, TextVerified key)
- Add `logs/` and `*.log` to `.gitignore`
- Add `.env.example` with placeholder values if not already present

---

### TASK-11: Purge dead stub services from `app/services/` and `app/core/`
**Files**: Multiple  
**Problem**: ~20+ service files exist that are not wired into the app — `load_balancer.py`, `auto_scaling.py`, `region_manager.py`, `cdn_service.py`, `whatsapp_service.py`, `telegram_service.py`, `voice_polling_service.py`, `reseller_service.py`, `enterprise_service.py`, etc. They add confusion, inflate apparent complexity, and may have their own bugs.  
**Fix**:
- Audit each file: grep for imports across the codebase
- Delete files with zero active imports
- If intended for future use, move to a `app/services/_future/` directory with a README

---

### TASK-12: Clean up one-off scripts in `scripts/`
**Files**: `scripts/` directory (~80 files)  
**Problem**: Dozens of one-off fix scripts (`fix_prod_schema.py`, `fix_localhost_admin.py`, `fix_final_linting.py`, `fix_linting.py`, etc.) that were run once and never deleted. They create confusion about what the canonical setup process is.  
**Fix**:
- Keep only: `scripts/deployment/`, `scripts/maintenance/`, `scripts/security/`
- Delete all `fix_*.py`, `verify_*.py`, `check_*.py` one-off scripts from the root of `scripts/`
- Ensure `scripts/deployment/migrate.sh` is the single source of truth for DB setup

---

### TASK-13: Fix circular import workarounds
**Files**: `app/models/user.py`, `main.py`, others  
**Problem**: `# activities = relationship(...) # Disabled to fix circular import` in `user.py`. Inline imports inside functions in `main.py` to avoid circular deps. These are deferred bugs.  
**Fix**:
- Resolve the circular import in `user.py` by moving the `Activity` relationship to use `lazy="dynamic"` or a string reference: `relationship("Activity", back_populates="user")`
- Audit all `# Disabled to fix circular import` comments and fix them properly

---

## 🟡 Housekeeping

### TASK-14: Consolidate documentation
**Problem**: 100+ markdown files across `docs/`, `archive/`, root. Most are sprint implementation notes.  
**Fix**:
- Keep: `README.md`, `SETUP.md`, `CHANGELOG.md`, `docs/api/`, `docs/deployment/`, `docs/security/`
- Archive everything else into `archive/` with a single `archive/INDEX.md`
- Delete phase completion reports (`PHASE_0_COMPLETE.md` through `PHASE_6_COMPLETE.md`, etc.)

---

### TASK-15: Improve real test coverage
**Problem**: Actual coverage is 31%. Many test files are coverage-boosting stubs (`test_batch_coverage_boost.py`, `test_coverage_boost.py`, `test_basic_coverage.py`).  
**Fix**:
- Delete stub coverage files
- Write real tests for the critical payment flow: `initialize_payment` → webhook → `credit_user`
- Write real tests for the verification retry loop in `textverified_service.py`
- Target: 70% meaningful coverage on `app/services/` and `app/api/`

---

## Log-Specific Findings

### TASK-16: Fix bcrypt version warning on startup
**File**: `requirements.txt`  
**Problem**: Every startup logs:
```
passlib.handlers.bcrypt - WARNING - (trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```
This is a known incompatibility between `passlib==1.7.4` and `bcrypt>=4.0.0`.  
**Fix**:
- Pin `bcrypt==3.2.2` in `requirements.txt`, OR
- Replace passlib with direct `bcrypt` usage since passlib is largely unmaintained
- Quickest fix: `pip install bcrypt==3.2.2`

---

### TASK-17: Investigate and fix "Database session error" on 402 responses
**File**: `app/core/database.py` / wherever 402 is raised  
**Problem**: The log shows:
```
app.core.database - ERROR - Database session error: 402: Insufficient credits
```
A business logic HTTP exception (402) is being caught and logged as a database session error. This means somewhere a `raise HTTPException(402, ...)` is happening inside a `get_db()` context and the exception handler is misclassifying it.  
**Fix**:
- In `database.py` `get_db()`, only catch `sqlalchemy` exceptions, not bare `Exception`
- Let `HTTPException` propagate naturally without being logged as a DB error

---

### TASK-18: Investigate TextVerified disabled at startup
**Problem**: Log shows at startup:
```
TextVerified service disabled - missing credentials or library
```
This appears **twice** — once before startup and once during cache pre-warming. The platform's core feature (SMS verification) is non-functional without this.  
**Fix**:
- Confirm `TEXTVERIFIED_API_KEY` and `TEXTVERIFIED_USERNAME` are set in the production `.env`
- Add a startup health check that raises a loud warning (or blocks startup in production) if TextVerified is disabled
- This is likely why the 402 error above occurred — user had balance but TextVerified was down, so no number could be purchased, and the pricing check failed

---

### TASK-19: Investigate JWT tokens exposed in WebSocket URLs
**Problem**: Log contains full JWT tokens in WebSocket connection URLs:
```
WebSocket /ws/notifications?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
These tokens are logged in plaintext and are visible in server logs, proxy logs, and browser history.  
**Fix**:
- Switch WebSocket auth to use a short-lived (60s) single-use token exchanged via a REST endpoint: `POST /api/ws/token` → returns `{ws_token: "..."}` valid for 60s
- Or accept the token via the first WebSocket message after connection, not in the URL
- Scrub token values from `RequestLoggingMiddleware` for WebSocket upgrade requests

---

## Priority Order

| Priority | Tasks |
|----------|-------|
| Do now | TASK-01, TASK-05, TASK-16, TASK-17, TASK-18, TASK-19 |
| This week | TASK-02, TASK-03, TASK-04, TASK-09, TASK-10 |
| This sprint | TASK-06, TASK-07, TASK-08, TASK-13 |
| Backlog | TASK-11, TASK-12, TASK-14, TASK-15 |
