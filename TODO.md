# TODO

## CI Fixes (In Progress)

| Job | Status |
|-----|--------|
| Code Quality | ✅ Green |
| Secrets Detection (Gitleaks) | ❌ Fix 1 |
| Security Scan (Bandit + Safety + Semgrep) | ❌ Fix 2 |
| Tests | ❌ Fixes 7b–7e |
| Deployment Readiness | ⏳ Auto-unblocks when above 3 pass |

- [ ] **Fix 7b–7e** — `auto_topup` patch target (`PaymentService→PaystackService`), `access_token` KeyError, `get_current_user_id` import errors (~30 failures)
- [ ] **Fix 1** — Run gitleaks locally, find exact trigger, update `tools/gitleaks.toml`
- [ ] **Fix 2** — Pin `bandit==1.7.6` in CI, verify `safety` + `semgrep` pass
- [ ] **Delete `tests/unit/test_payment_race_condition.py`** — segfault risk; currently only ignored via `--ignore` flag
- [ ] **Raise `--cov-fail-under`** — currently 36%; bump to 60%+ after fixes land (1076 passing now, target ~1700)

---

## Pending Deploy Verification

- [ ] **Admin account tier** — Verify admin dashboard shows `custom` (not Freemium) after next deploy
- [ ] **Cancel subscription** — Verify cancelled users retain pro/custom access until `tier_expires_at` and are not immediately downgraded
- [ ] **CSP inline handlers** — Verify no CSP errors in browser console on any page using `onclick=` handlers

---

## Immediate Actions

- [ ] Configure email service — set `SMTP_USERNAME` + `SMTP_PASSWORD` in Render env
- [ ] Monitor TextVerified initialisation in Render logs after next deploy

---

## Roadmap (Q2–Q4 2026)

### Q2 2026
- [ ] Enhanced analytics dashboard (carrier success rates, user preferences)
- [ ] SDK libraries (Python, JavaScript, Go)
- [ ] API rate limiting improvements
- [ ] Update `NGN_USD_RATE` in Render env if exchange rate drifts from 1600

### Q3 2026
- [ ] Premium tier with Carrier Guarantee feature
- [ ] Multi-region deployment
- [ ] Advanced carrier analytics dashboard

### Q4 2026
- [ ] Commercial APIs (if volume justifies)
- [ ] Enterprise tier features
- [ ] Advanced reporting
