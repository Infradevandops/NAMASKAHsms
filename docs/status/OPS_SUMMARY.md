# OPS SUMMARY

**Last Updated**: November 2026
**CI Status**: ✅ Green — 25-file gate
**Deploy Status**: `331db1d5` pending CI → auto-deploy
**TV**: ✅ Operational — $42.15 balance, pricing URL confirmed

---

## CURRENT SERVER STATE

| Check | Result |
|-------|--------|
| TV enabled | ✅ True |
| TV balance | $42.15 |
| Pricing URL `/pricing/verifications` | ✅ 200 — `{"serviceName":"whatsapp","price":1.5}` |
| Old URL `/verifications/pricing` | ❌ 404 — confirmed dead |
| Health endpoint | ✅ healthy |
| Stock monitor | ✅ price-based availability, depletion alerts wired |
| Version string | ✅ 4.9.9 |
| Dead code `_fetch_prices_inline` | ✅ Deleted |
| Dead code `fetch_raw_services_with_quantity` | ✅ Deleted |

---

## CI PIPELINE

```
secrets-scan → code-quality → frontend-unit-tests → unit-tests (BLOCKING)
                                                   → integration-tests (non-blocking)
                                                   → e2e-tests (non-blocking, main only)
```

**Blocking gate** (25 test files, --cov-fail-under=25):
```
test_api_key_service        test_analytics_service      test_balance_service
test_cache                  test_models                 test_utils
test_carrier_lookup         test_phone_validator        test_stability_fixes
test_tv_webhook             test_notification_service   test_notification_center
test_email_service          test_auth_service           test_refund_service
test_pricing_calculator     test_tier_service           test_verification_flow
test_sms_polling            test_fraud_detection        test_webhook_notifications
test_security_utils         test_textverified_service   test_startup_smoke
test_mobile_responsiveness
```

**Next batch to wire** (E-003 — run locally first):
```
test_verification_endpoints   test_payment_service    test_auth_endpoints
test_wallet_service           test_transaction_service test_tier_manager
test_quota_service            test_stock_monitor      test_area_code_check
```

---

## KNOWN GAPS

> All gaps tracked in `docs/status/MASTER_TASKS.md`. Summary below.

| Gap | Task ID | Status |
|-----|---------|--------|
| `331db1d5` not confirmed live on server | A-001 | 📋 Manual |
| 8 transactional emails not tested on live server | A-002 | 📋 Manual |
| Area code price display shows base only (not base + $0.25) | A-003 | 📋 |
| Telegram E2E not live-tested | A-005 | 📋 Manual |
| Voice `transcribing` SSE status not emitted | B-002 | 📋 |
| WebSocket `reuse_available` event not pushed | B-004 | 📋 |
| Reuse banner not in UI | B-006 | 📋 |
| `smsAndVoiceCombo` capability unused | B-008 | 📋 |
| Annual plans not implemented | C-001–007 | 📋 |
| PAYG API add-on not implemented | C-010–015 | 📋 |
| Bulk credit discount UI not built | C-018–019 | 📋 |
| Migration `f1a2b3c4d5e6` not run on server | — | 📋 Run post-deploy |
| Stock watch UI (“Notify me” button) | D-005–007 | 📋 |
| `create_reservation()` back-order detection | D-010 | 📋 |
| Rentals back-order UI | D-013–015 | 📋 |
| Rental expiry monitor 24h warning | D-017–020 | 📋 |
| Admin portal inventory wiring | D-021–025 | 📋 |
| Upstash Redis on free tier | E-001 | 📋 Manual |
| TV IP not whitelisted | E-002 | 📋 Manual |
| Coverage 25% vs 90% target | E-003 | 📋 |
| Integration tests non-blocking | E-005 | ⚠️ Blocked on E-004 |

---

## INFRASTRUCTURE

| Component | Status |
|-----------|--------|
| FastAPI app (gunicorn, 2 workers) | ✅ Running |
| PostgreSQL | ✅ Running |
| Redis | ✅ Running |
| TV webhook endpoint | ✅ Live, registered in TV dashboard |
| WebSocket manager | ✅ Active |
| Background services (11 active) | ✅ All running |
| Sentry error tracking | ✅ Active |
| BetterStack uptime | ✅ Active |
| GitHub Actions CI | ✅ Active (25-file gate) |
| Deploy workflow | ✅ CI-gated (deploy.yml) |

---

## NEXT OPS ACTIONS

See `docs/status/MASTER_TASKS.md` for full sprint breakdown. Immediate priorities:

1. **A-001** — confirm `331db1d5` live on server
2. **A-002** — test all 8 transactional emails including OTP
3. **A-003** — fix area code price display (base + $0.25 surcharge)
4. **A-005** — Telegram E2E manual test
5. **Run migration** — `alembic upgrade head` for `f1a2b3c4d5e6` post-deploy
6. **E-001** — upgrade Upstash Redis to pay-as-you-go
7. **E-002** — submit server IP to TV support for whitelist
8. **C-001** — create Paystack annual plan codes (15 min, zero engineering)
