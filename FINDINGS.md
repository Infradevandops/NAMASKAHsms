# Findings

Assessment: March 7, 2026

---

## 🔴 CRITICAL — Manual Action Required on Render

- [ ] **Update `DATABASE_URL`** — go to Render Dashboard → PostgreSQL → Connection → copy Internal URL → paste into namaskah-sms → Environment → `DATABASE_URL`
- [ ] **Rotate exposed secrets** — these appeared in `logs/app.log` in plain text:
  - `PAYSTACK_SECRET_KEY` → revoke at dashboard.paystack.com
  - `TEXTVERIFIED_API_KEY` → revoke at textverified.com
  - `DATABASE_URL` password → rotate on Render PostgreSQL
  - `JWT_SECRET_KEY` + `SECRET_KEY` → replace with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- [ ] **Set distinct `SECRET_KEY` and `JWT_SECRET_KEY`** — both are currently the same value
- [ ] **Set `CORS_ORIGINS=https://namaskah.onrender.com`** on Render (code-side wildcard guard already added)
- [ ] **Set `EMERGENCY_SECRET=<random>`** on Render, or leave unset to disable the endpoint

---

## ✅ All Code Fixes Applied (this session)

- `safe_add_tiers` — `NoSuchTableError: users` → added `if "users" not in inspector.get_table_names(): return`
- `add_user_preferences` — same crash → same guard added
- `quota_pricing_v3_1` — `CREATE TABLE quota_transactions` FK to `users` before it exists → covered by same early-return guard; `subscription_tier` queries wrapped in column-existence check
- `add_preferred_area_codes` — no idempotency guard → added `_column_exists()` check
- Security middleware (`CSRFMiddleware`, `SecurityHeadersMiddleware`, `XSSProtectionMiddleware`, `RequestLoggingMiddleware`, `setup_unified_middleware`, `setup_unified_rate_limiting`) — re-enabled in `main.py`
- `app/middleware/logging.py.broken` + `security.py.broken` — deleted
- Pricing router — re-enabled in `main.py`
- Emergency endpoint — hardcoded secret `"namaskah-emergency-reset-2026"` moved to `EMERGENCY_SECRET` env var
- `CORS_ORIGINS=*` — blocked in production via `config.py` validator, falls back to `BASE_URL`
- Stale generated files deleted (`CRITICAL_FIXES_TASKFILE.md`, `IMPLEMENTATION_GUIDE.md`, `QUICK_FIX_GUIDE.md`, `fix_critical_issues.sh`, `scripts/improve_coverage.py`)
- App imports clean: `python3 -c "from main import create_app"` → OK
