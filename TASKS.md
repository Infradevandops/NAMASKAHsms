# Namaskah Task Board

---

## ✅ Completed

- [x] Settings page — 6 bugs (API URLs, field mismatches, alert() dialogs) — `70c150d3`
- [x] Sidebar audit — 27 bugs across 9 pages — `70c150d3`
- [x] Dashboard bugs 1–5 (activity table, notification badge, Add Credits, Upgrade modal, Verification modal) — `70c150d3`
- [x] Add Credits 500 error — removed `@limiter.limit` decorators (SlowAPI not configured) — `55ae2536`
- [x] Verification flow cleanup — type-picker modal, `service_name` field fix, `activation_id` set, `GET /verify/{id}/status` endpoint, voice page polling — `927907c4`
- [x] Broken routes — `/verify` + `/voice-verify` serve modern templates, 7 missing page routes added, 8 wrong-destination links fixed, tier modal links fixed — `afcf85fa`

---

## 🔴 Critical

- [ ] **Webhook doesn't set tier after Pro/Custom upgrade**
  - User pays $25/$35, balance credited, but `subscription_tier` never updated
  - Fix: `payment_endpoints.py` webhook handler — after crediting, check `metadata.get('upgrade_to')` → set `user.subscription_tier` + `db.commit()`
  - File: `app/api/billing/payment_endpoints.py`

---

## 🟡 Medium

- [ ] **Analytics charts render empty despite real data**
  - `dashboard_router.py` returns `daily_verifications`, `spending_by_service`, `top_services`
  - Audit `analytics.html` JS field names against actual response shape, patch mismatches
  - File: `templates/analytics.html`

---

## 🟢 Low

- [ ] **Unit tests — verification + tier upgrade (zero coverage)**
  - `POST /api/verify/create` — balance check, capability stored, activation_id set
  - `GET /api/verify/{id}/status` — returns sms_code when completed
  - `POST /api/billing/tiers/upgrade` — PAYG commits to DB, paid returns pending_payment
  - Files: `tests/unit/test_verification_routes.py` (new), `tests/unit/test_tier_endpoints.py` (new)

- [ ] **Test coverage 23% → 50%** (Q1 roadmap)
  - Integration tests: register→verify flow, add credits→webhook, PAYG upgrade
  - File: `tests/integration/test_core_flows.py` (new)

- [ ] **`/blog`, `/careers` links on landing page** — no content, no templates
  - Either remove links or add placeholder pages
  - File: `templates/landing.html`
