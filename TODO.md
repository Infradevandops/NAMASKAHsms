# TODO

## Current State (March 2026)

✅ **v4.4.1 Complete** — All features implemented and tested  
✅ **Security hardened** — Emergency endpoint removed, JWT revocation, CSP nonce applied to all templates, WebSocket auth fixed  
✅ **Deployed** — Running on Render at https://namaskah.onrender.com  
✅ **TextVerified configured** — `TEXTVERIFIED_API_KEY` + `TEXTVERIFIED_EMAIL` set in Render env  
✅ **Database migrated** — Monetary columns converted to `Numeric(10,4)`  
✅ **Codebase cleaned** — 54 dead files removed, stub services deleted  
✅ **v4.5.0 Tier System Fixed** — All 13 billing/access/runtime issues resolved, 57 tests passing  
✅ **CI Fix Plan created** — Full plan documented in `docs/tasks/CI_FIX_PLAN.md` (8 fixes, ordered by impact)  

---

## CI Fixes (In Progress)

See full plan: [`docs/tasks/CI_FIX_PLAN.md`](./docs/tasks/CI_FIX_PLAN.md)

| Job | Status | Fix # |
|-----|--------|-------|
| Code Quality | ✅ Green | Done |
| Secrets Detection (Gitleaks) | ❌ | Fix 1 |
| Security Scan (Bandit/Safety/Semgrep) | ❌ | Fix 2 |
| Tests | ❌ | Fixes 3–7 |

- [ ] **Fix 3** — Remove `--maxfail=10`, add 6 `--ignore` flags in `ci.yml`
- [ ] **Fix 4** — Add ~30 missing model imports to `conftest.py` (fixes ~76 notification table errors)
- [ ] **Fix 5** — Add 12 missing fixtures to `conftest.py` (`db_session`, `user_token`, `authenticated_regular_client`, `payg_user`, `redis_client`, etc.) — fixes ~500 errors
- [ ] **Fix 6** — Fix UNIQUE email collisions in tests (UUID emails or function-scoped engine)
- [ ] **Fix 7** — Fix code-level bugs: `WhiteLabelEnhancedService` import, `auto_topup` patch target, `access_token` KeyError, `get_current_user_id` import
- [ ] **Fix 1** — Run gitleaks locally, find exact trigger, update `tools/gitleaks.toml`
- [ ] **Fix 2** — Pin `bandit==1.7.8` in CI, verify `safety` + `semgrep` pass

---

## Pending Deploy Verification

These fixes are in code and tested but need a production deploy to confirm end-to-end:

- [ ] **Admin account tier** — Verify admin dashboard shows `custom` (not Freemium) after next deploy. `init_admin.py` clears `tier_expires_at = NULL` on startup and `get_user_tier()` bypasses expiry for admins.

- [ ] **Cancel subscription** — Verify cancelled users retain pro/custom access until `tier_expires_at` and are not immediately downgraded. `subscription_renews_at` should be `NULL` in DB after cancelling.

- [ ] **CSP inline handlers** — Verify no CSP errors in browser console on any page using `onclick=` handlers after 
---

## Immediate Actions

### Required
- [ ] Configure email service (SMTP credentials) — set `SMTP_USERNAME` + `SMTP_PASSWORD` in Render env
- [ ] Monitor first production deployment — check TextVerified initialises cleanly in Render logs

### Optional Enhancements
- [ ] Enable Numverify API for carrier name lookup (AT&T, Verizon, etc.) — set `NUMVERIFY_API_KEY` in Render env. VOIP rejection and mobile/landline detection already work offline via `phonenumbers` library.
- [ ] Setup Prometheus + Grafana monitoring stack
- [ ] Confirm Sentry DSN is active and receiving errors

---

## Roadmap (Q2–Q4 2026)

### Q2 2026
- [ ] Enhanced analytics dashboard (carrier success rates, user preferences)
- [ ] SDK libraries (Python, JavaScript, Go)
- [ ] API rate limiting improvements
- [ ] Update `NGN_USD_RATE` in Render env if exchange rate drifts significantly from 1600

### Q3 2026
- [ ] Premium tier with Carrier Guarantee feature
- [ ] Multi-region deployment
- [ ] Advanced carrier analytics dashboard

### Q4 2026
- [ ] Commercial APIs (if volume justifies)
- [ ] Enterprise tier features
- [ ] Advanced reporting
