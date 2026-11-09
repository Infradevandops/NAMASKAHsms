# UI/UX Enhancement Tasks

**Created**: November 2026
**Scope**: Landing page (mobile + desktop + PWA), Auth pages, Pricing, Dashboard, cross-cutting
**Status**: ✅ All tasks complete — committed across `e1e3a3c1` and `HEAD`

---

## STATUS SUMMARY

| ID | Area | Priority | Status | Commit |
|----|------|----------|--------|--------|
| LP-001 | Mobile nav dropdown broken | P0 | ✅ Done | e1e3a3c1 |
| LP-002 | landing.css dead code | P1 | ✅ Done | HEAD — file deleted |
| LP-003 | No stats above fold | P1 | ✅ Done | e1e3a3c1 |
| LP-004 | Placeholder brand icons | P1 | ✅ Done | e1e3a3c1 |
| LP-005 | Code block mobile overflow | P1 | ✅ Done | e1e3a3c1 |
| LP-006 | Footer mobile collapse | P1 | ✅ Done | e1e3a3c1 |
| LP-007 | No pricing teaser | P2 | ✅ Done | HEAD |
| LP-008 | PWA install prompt | P2 | ✅ Done | HEAD |
| LP-009 | Dark mode CTA | P2 | ✅ Done | e1e3a3c1 |
| LP-010 | No testimonials | P2 | ✅ Done | HEAD |
| LP-011 | Hero no visual | P2 | ✅ Done | HEAD |
| AUTH-001 | Register missing nav | P1 | ✅ Done | e1e3a3c1 |
| AUTH-002 | Turnstile hardcoded light | P1 | ✅ Done | e1e3a3c1 |
| AUTH-003 | Register container margin | P1 | ✅ Done | e1e3a3c1 |
| AUTH-004 | Google btn inconsistency | P2 | ✅ Done | e1e3a3c1 |
| AUTH-005 | No signup link on login | P2 | ✅ Done | e1e3a3c1 |
| PRICE-001 | Pricing h1 dark mode | P1 | ✅ Done | e1e3a3c1 |
| PRICE-002 | Comparison table mobile | P1 | ✅ Done | e1e3a3c1 |
| PRICE-003 | selectTier no tier check | P1 | ✅ Done | e1e3a3c1 |
| PRICE-004 | FAQ no accordion | P2 | ✅ Done | e1e3a3c1 |
| DASH-001 | Upgrade btn flash | P1 | ✅ Done | e1e3a3c1 |
| DASH-002 | Mobile cards unstyled | P1 | ✅ Done | e1e3a3c1 |
| DASH-003 | Stats font too small | P2 | ✅ Done | e1e3a3c1 |
| XC-001 | pwa-mobile grid override | P1 | ✅ Done | e1e3a3c1 |
| XC-002 | Turnstile light theme | P1 | ✅ Done | e1e3a3c1 |
| XC-003 | No theme-color meta | P2 | ✅ Done | e1e3a3c1 |
| XC-004 | No lazy loading on imgs | P2 | ✅ Done | e1e3a3c1 |
| XC-005 | Cookie banner z-index | P2 | ✅ Done | HEAD |
| XC-006 | No focus-visible on CTAs | P2 | ✅ Done | e1e3a3c1 |
| XC-007 | Generic page titles | P2 | ✅ Done | e1e3a3c1 |

**30/30 tasks complete.**

---

## PRODUCTION READINESS SCAN (commit 38544b51)

All actionable findings from full codebase scan fixed:

| Finding | Severity | Fix |
|---------|----------|-----|
| IP spoofing in rate limiter (X-Forwarded-For) | High | Fixed trust order in `unified_rate_limiting.py` |
| In-memory CSRF/rate-limit (multi-process) | High | **Fixed — Redis-backed** (see below) |
| Duplicate CSP middleware with `unsafe-inline` | High | **Fixed — `csp.py` deleted** (see below) |
| CI never hard-blocks bad deploy | High | Fixed — smoke-test job added to `ci.yml` |
| SQLAlchemy `is False` bug ×3 | Medium | Fixed in `auth_security.py`, `lifespan.py` |
| JWT hardcoded 30-day expiry | Medium | Fixed — uses `settings.jwt_expiration_hours` |
| CSP missing Turnstile/Google domains | Medium | Fixed in `security.py` |
| Abandoned payment cleanup inverted logic | Medium | Fixed in `lifespan.py` |
| Python 3.11 vs 3.9 mismatch | Medium | Fixed — `Dockerfile` pinned to `3.9-slim` |
| CI artifact JSON files in repo | Medium | Fixed — `.gitignore` updated |
| Month-end revenue monitor crash | Low | Fixed — `timedelta` approach in `lifespan.py` |

---

## POST-SCAN FIXES (current session)

### SEC-001 — `app/middleware/csp.py` deleted
Dead duplicate CSP middleware defining `'unsafe-inline'` with no nonce — weaker than the
active nonce-based policy in `security.py`. Not imported anywhere but dangerous as a landmine.
File deleted.

### SEC-002 — `app/core/security_hardening.py` Redis-backed
`SecurityHardening.csrf_tokens` and `rate_limits` were plain dicts — not shared across
Gunicorn workers (WORKERS=2), making effective limits double and CSRF tokens invisible
cross-worker.

**Fix**:
- `generate_csrf_token` / `validate_csrf_token` → `cache_manager.set/get("csrf:{user_id}", ttl=3600)`
- `check_rate_limit` → Redis `INCR` + `EXPIRE` pipeline on key `rl:{identifier}:{window}` — atomic, shared across all workers
- Pure utility methods (`sanitize_input`, `validate_*`) unchanged — no state involved

---

## REMAINING OPEN ITEMS

| Item | Status |
|------|--------|
| Telegram E2E verification (@vrenum_sms_bot) | ⏳ Pending manual test |
| Python unit-tests `continue-on-error: true` | ⏳ Pre-existing failures need triage |
