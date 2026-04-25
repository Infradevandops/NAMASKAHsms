# CI Test Restoration Plan - Institutional Grade

**Status**: In Progress  
**Created**: April 25, 2026  
**Priority**: CRITICAL  
**Target Completion**: Q2 2026

---

## Executive Summary

This document tracks the restoration of 105 test files that were temporarily removed from CI to achieve a passing pipeline. All tests must be fixed and restored to achieve institutional-grade quality standards.

**Current State**: 8/113 test files running (7% coverage)  
**Target State**: 113/113 test files running (90%+ coverage)  
**Timeline**: 8 weeks (May-June 2026)

---

## Document Status

✅ File created successfully  
⏳ Populating with comprehensive restoration plan...

---


## Removed Tests Inventory - Complete List

### CRITICAL PRIORITY (15 files) - Week 1-2

1. test_auth_endpoints_comprehensive.py - 19 tests - Auth endpoints
2. test_auth_service_complete.py - 8 tests - Auth service
3. test_auth_service_expanded.py - 12 tests - Auth expanded
4. test_auth_service_enhanced.py - 6 tests - Auth enhanced
5. test_auth_service.py - 10 tests - Core auth
6. test_payment_service.py - 15 tests - Payments
7. test_payment_service_complete.py - 12 tests - Payment complete
8. test_payment_service_enhanced.py - 8 tests - Payment enhanced
9. test_webhook_service.py - 10 tests - Webhooks
10. test_webhook_service_complete.py - 7 tests - Webhook complete
11. test_security_utils.py - 5 tests - Security utils
12. test_security_middleware.py - 8 tests - Security middleware
13. test_rate_limiting.py - 6 tests - Rate limiting
14. test_tier_service_complete.py - 12 tests - Tier service
15. test_tier_config.py - 8 tests - Tier config

HIGH PRIORITY (20 files) - Week 3-4

16. test_sms_service_complete.py - 18 tests
17. test_sms_service_enhanced.py - 12 tests
18. test_sms_service_expanded.py - 10 tests
19. test_textverified_service.py - 15 tests
20. test_textverified_service_v2.py - 8 tests
21. test_textverified_regression.py - 6 tests
22. test_area_code_retry.py - 5 tests
23. test_area_code_analytics.py - 4 tests
24. test_area_code_check.py - 3 tests
25. test_area_code_geo.py - 4 tests
26. test_verification_flow.py - 12 tests
27. test_verification_routes.py - 8 tests
28. test_verification_endpoints_comprehensive.py - 15 tests
29. test_verification_pricing_service.py - 6 tests
30. test_verification_schema.py - 5 tests
31. test_credit_service.py - 8 tests
32. test_credit_service_complete.py - 10 tests
33. test_credit_service_coverage.py - 6 tests
34. test_wallet_service.py - 12 tests
35. test_wallet_service_enhanced.py - 8 tests

MEDIUM PRIORITY (35 files) - Week 5-6

36. test_notification_service.py - 10 tests
37. test_notification_service_complete.py - 8 tests
38. test_notification_dispatcher.py - 6 tests
39. test_notification_center.py - 5 tests
40. test_notification_preferences.py - 4 tests
41. test_notification_analytics.py - 3 tests
42. test_notification_enhancements.py - 4 tests
43. test_email_notifications.py - 8 tests
44. test_email_service.py - 6 tests
45. test_mobile_notifications.py - 5 tests
46. test_webhook_notifications.py - 4 tests
47. test_alerting_service.py - 4 tests
48. test_pricing_calculator.py - 8 tests
49. test_pricing_logic.py - 6 tests
50. test_pricing_fixes.py - 4 tests
51. test_pricing_endpoint.py - 5 tests
52. test_pricing_template_service.py - 6 tests
53. test_quota_service.py - 8 tests
54. test_quota_service_complete.py - 6 tests
55. test_tier_management.py - 10 tests
56. test_tier_manager_complete.py - 8 tests
57. test_tier_manager_coverage.py - 6 tests
58. test_tier_resolution.py - 4 tests
59. test_tier_and_credit_coverage.py - 5 tests
60. test_refund_service.py - 8 tests
61. test_refund_policy_enforcer.py - 6 tests
62. test_transaction_service.py - 10 tests
63. test_document_service.py - 7 tests
64. test_compliance_service.py - 5 tests
65. test_fraud_detection.py - 6 tests
66. test_reseller_service.py - 8 tests
67. test_currency_service.py - 4 tests
68. test_auto_topup.py - 5 tests
69. test_purchase_intelligence.py - 6 tests
70. test_common_services.py - 8 tests

LOW PRIORITY (35 files) - Week 7-8

71. test_admin_endpoints_comprehensive.py - 15 tests
72. test_routers_complete.py - 12 tests
73. test_middleware_complete.py - 10 tests
74. test_middleware_comprehensive.py - 8 tests
75. test_core_modules_comprehensive.py - 14 tests
76. test_dependencies.py - 6 tests
77. test_startup.py - 4 tests
78. test_error_handling.py - 8 tests
79. test_error_handling_comprehensive.py - 10 tests
80. test_exception_handling.py - 6 tests
81. test_data_masking.py - 5 tests
82. test_utils_utils.py - 8 tests
83. test_utility_modules.py - 6 tests
84. test_monitoring_service.py - 7 tests
85. test_websocket.py - 6 tests
86. test_websocket_comprehensive.py - 8 tests
87. test_whitelabel_enhanced.py - 5 tests
88. test_activity_feed.py - 4 tests
89. test_phase1_backend_hardening.py - 10 tests
90. test_phase3_tier_identification.py - 8 tests
91. test_phase_c_services.py - 6 tests
92. test_medium_priority_services.py - 12 tests
93. test_more_services.py - 8 tests
94. test_models_complete.py - 15 tests
95. test_pydantic_compat.py - 4 tests
96. test_response_validators.py - 5 tests
97. test_payment_idempotency.py - 6 tests
98. test_payment_idempotency_schema.py - 4 tests
99. test_payment_model_integrity.py - 5 tests
100. test_sms_polling.py - 4 tests
101. test_verification_cost_sync.py - 3 tests
102. test_verification_and_tier.py - 5 tests
103. test_wallet_endpoints_comprehensive.py - 12 tests
104. test_notification_endpoints_comprehensive.py - 10 tests
105. test_verification_receipt.py - 4 tests

TOTAL: 105 files, 812+ tests to restore

---

## Institutional Grade Standards

ALL tests must meet these criteria:

1. 100% pass rate - zero flakiness
2. Complete isolation - no dependencies
3. Fast execution - under 5s per file
4. Clear assertions - meaningful failures
5. Proper mocking - no external calls
6. Full documentation - purpose and setup
7. Type safety - proper type hints
8. Error handling - comprehensive coverage

---

## Weekly Milestones

Week 1: 8 auth tests fixed
Week 2: 7 payment/security tests fixed
Week 3: 10 SMS tests fixed
Week 4: 10 wallet/credit tests fixed
Week 5: 18 notification/pricing tests fixed
Week 6: 17 refund/tier tests fixed
Week 7: 18 admin/monitoring tests fixed
Week 8: 17 utility/edge case tests fixed

Target: 113/113 tests running, 90%+ coverage

---

## Commitment

We commit to restoring ALL 105 test files to institutional-grade standards within 8 weeks. No shortcuts. No compromises.

Engineering Team
April 25, 2026
