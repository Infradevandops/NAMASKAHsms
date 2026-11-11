# ACTIVE SPRINT

**Updated**: November 2026
**HEAD**: `3b3ae1bd` on origin/main
**CI**: ✅ Passing — smoke-test + frontend-unit-tests (hard gates)
**Deploy**: ⏳ Pending CI pass on `3b3ae1bd` → auto-triggers via deploy.yml

---

## SPRINT JUST COMPLETED ✅

Full UI/UX overhaul + global readiness pass. 53/55 page quality tasks done.
See `docs/engineering/development/PAGE_QUALITY_TASKS.md` for full scorecard.

**Key deliveries:**
- Regulatory compliance: GDPR cookie consent (granular), age gate, marketing consent, correct legal docs (jurisdiction, processor list, DPO note)
- All broken pages fixed: refund CSS, reviews honest, about honest stats, contact dark mode + GDPR notice
- Blog: all 5 posts styled + indexed at `/blog`, route added
- Auth: double-nav eliminated on login/register, duplicate logo removed
- Nav: FAQ in desktop + mobile, Blog/Cookies/Contact in footer
- Status page: now public (no login required)
- FAQPage JSON-LD structured data added

---

## ALL OPEN ITEMS

### 🔴 P1 — Deploy & Verify

| Item | Notes |
|------|-------|
| CI pass on `3b3ae1bd` | Template-only changes — smoke + JS tests should pass |
| Deploy auto-triggers on CI pass | Via `deploy.yml` → SSH → docker compose up --build |
| Confirm server pulls `3b3ae1bd` | SSH: `cd ~/vrenum && git log --oneline -3` |

---

### 🔴 P1 — Email Testing (post-deploy)

Test all transactional emails with existing users on the live server.

| Email | Trigger | How to test |
|-------|---------|-------------|
| Welcome | New registration | Register a test account |
| Password reset | `/password-reset` form submit | Submit with existing email, check inbox |
| Low balance alert | Wallet drops below threshold | Manually deduct credits via admin |
| Verification receipt | Successful SMS verification | Complete a real verification |
| Payment receipt | Paystack payment completes | Make a small test payment |
| Tier upgrade | User upgrades plan | Upgrade a test account |
| Daily digest | Scheduled 08:00 UTC | Check Sentry/logs next morning |

**Email provider**: Resend
**From address**: `FROM_EMAIL_ADDRESS` env var
**Check**: Sentry → https://dev-vp.sentry.io/issues/ for any dispatch errors

---

### 🟡 P1 — Auth UX (deferred from page quality sprint)

| ID | Item | File | Notes |
|----|------|------|-------|
| AUTH-001 | Password reset — no "check your email" confirmation state | `templates/password_reset.html` | After form submit, page should show confirmation, not just reset |
| AUTH-002 | Register success — no email verification notice | `templates/register.html` | If email verification is enabled server-side, show "Check your email" instead of auto-redirecting |

---

### 🟡 P1 — Verification System (open items)

Full context: `docs/engineering/development/VERIFICATION_TASKS.md`

| ID | Item | Severity | File |
|----|------|----------|------|
| OPEN-1 | `validating` SSE step does no real work — fires immediately, misleads users | P3 | `purchase_endpoints.py` |
| OPEN-2 | No `transcribing` status for voice in SSE path — voice shows as `pending` while transcribing | P3 | `purchase_endpoints.py` |
| OPEN-3 | `reuse` + `reactivate` never surfaced in UI — cost-saving TV features unused | P2 | `verification-flow.js`, `verify_modern.html` |
| OPEN-4 | Stock monitor docstring says "15-minute refresh" — should be 90s | P3 | `stock_monitor.py` |

---

### 🟡 P2 — Ops & Infrastructure

| Item | Priority | Notes |
|------|----------|-------|
| Telegram E2E verification | P1 | @vrenum_sms_bot created, webhook registered, not live-tested. Test: connect bot, send a verification, confirm SMS forwarded |
| TextVerified IP whitelist | P2 | Server IP not whitelisted with TV — `quantity: null` on all services. Price-based fallback active. Contact TV support |
| Upstash Redis upgrade | P2 | Free tier 500k req/month. Hit limit once. Upgrade to pay-as-you-go ($0.20/100k) |
| Python unit-tests `continue-on-error` | P2 | Pre-existing failures. Triage: download artifact from last CI run, identify failing tests |
| Dead code cleanup | P2 | `_fetch_prices_inline()` + `fetch_raw_services_with_quantity()` — both superseded by SDK `verifications.pricing()`. Delete. |
| Area code price display | P1 | UI shows base price, user charged base + $0.25 surcharge. Pass `area_code=True` to `check_service_available()` when area code selected |
| CI coverage expansion | P2 | Currently 25% floor. Next batch: `test_verification_endpoints`, `test_payment_service`, `test_auth_endpoints`, `test_wallet_service` |
| Version string | P3 | App reports `4.9.1`, should be `4.9.9`. Update `settings.version` |

---

### 🟢 P3 — Polish

| Item | Notes |
|------|-------|
| SEO-004 FAQPage JSON-LD | ✅ Done this sprint |
| `validating` SSE step | Remove or wire to real work (OPEN-1 above) |
| Stock monitor docstring | 1-line fix (OPEN-4 above) |
| `smsAndVoiceCombo` capability | TV supports it, platform never uses it |
| `ReservationState` full enum handling | Platform only maps 3 of 14 states |

---

## TASK FILE INDEX

| File | What it covers |
|------|---------------|
| `docs/engineering/development/VERIFICATION_TASKS.md` | All TV API gaps, stock accuracy, purchase flow, open items — **single source of truth** |
| `docs/engineering/development/PAGE_QUALITY_TASKS.md` | 53/55 public page quality tasks |
| `docs/engineering/development/UI_UX_TASKS.md` | 30/30 UI/UX tasks (complete) |
| `docs/status/FRONTEND_ACTIVE_TASKS.md` | 10/10 frontend tasks (complete) |
| `docs/status/PLATFORM_STATUS.md` | Current platform state |
| `docs/status/OPS_SUMMARY.md` | CI pipeline, infrastructure, known gaps |

**Superseded (kept for reference only):**
- `docs/engineering/TV_API_FLOW_GAP_ASSESSMENT.md`
- `docs/engineering/TV_API_REAL_FLOW.md`
- `docs/engineering/TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md`
- `docs/engineering/development/TV_PURCHASE_FLOW_ALIGNMENT_TASK.md`
