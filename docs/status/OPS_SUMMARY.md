# OPS SUMMARY

**Last Updated**: November 10, 2026
**CI Status**: ✅ Green — 25-file gate
**Deploy Status**: ✅ All commits live — HEAD `32d9b500`
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
| Stock monitor | ✅ price-based availability |

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

**Next batch to wire** (run locally first):
```
test_verification_endpoints   test_payment_service    test_auth_endpoints
test_wallet_service           test_transaction_service test_tier_manager
test_quota_service            test_stock_monitor      test_area_code_check
```

---

## KNOWN GAPS

| Gap | Impact | Status |
|-----|--------|--------|
| Area code price display shows base price, user charged base + $0.25 | Medium — UX/trust | 📋 P1 next |
| Telegram E2E not live-tested | Low — code complete | ⏳ Manual test pending |
| Dead code: `_fetch_prices_inline`, `fetch_raw_services_with_quantity` | Low — confusion risk | 📋 P2 delete |
| Coverage 25% vs 90% target | Medium | 📋 Expanding gate each sprint |
| Integration tests non-blocking | Medium | 📋 Stabilise and promote |
| `validating` SSE step does no real work | Low | 📋 P3 open |
| No `transcribing` SSE status for voice | Low | 📋 P3 open |
| Stock monitor docstring says "15-minute" (should be 90s) | Trivial | 📋 P3 1-line fix |
| smsAndVoiceCombo capability unused | Low | 📋 Planned |
| Reuse/Reactivate not surfaced in UI | Low — backend done | 📋 Planned |

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

1. **Fix area code price display** — pass `area_code=True` to `check_service_available()`
   when area code selected so UI price includes the $0.25 surcharge
2. **Telegram E2E** — manual test with real Telegram account
3. **Delete dead code** — `_fetch_prices_inline()` + `fetch_raw_services_with_quantity()`
4. **CI coverage batch 2** — wire 9 more test files, raise floor to 30%
5. **Monitor Sentry** — watch for errors from SDK fixes
