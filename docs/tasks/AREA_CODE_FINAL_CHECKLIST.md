# Area Code Implementation - Final Checklist

**Start Date**: ___________
**Target Completion**: 2 weeks
**Status**: 🎯 Ready to Start

---

## 📋 Pre-Implementation

- [ ] Read consolidated guide: `docs/tasks/AREA_CODE_IMPLEMENTATION_CONSOLIDATED.md`
- [ ] Review test templates: `tests/unit/test_voice_area_code_gating.py`
- [ ] Create feature branch: `git checkout -b feature/area-code-tier-gating`
- [ ] Set up local environment
- [ ] Verify TextVerified credentials

---

## 🚀 Phase 1: Voice Verification (Days 1-5)

### Day 1: Backend - Cost Calculation
- [ ] Create `calculate_voice_cost()` in `app/services/verification_service.py`
- [ ] Implement tier gating logic (Freemium blocked, PAYG $0.25, Pro/Custom $0)
- [ ] Add error handling for invalid tiers
- [ ] Test locally with all 4 tiers
- [ ] Commit: `feat(voice): add tier-gated area code cost calculation`

### Day 2: Backend - API Endpoint
- [ ] Update `/api/verification/request` in `app/api/core/verification.py`
- [ ] Add tier validation before processing
- [ ] Integrate `calculate_voice_cost()`
- [ ] Add proper error responses (403 for Freemium)
- [ ] Test API with Postman/curl
- [ ] Commit: `feat(voice): add tier validation to verification endpoint`

### Day 3: Frontend - Tier Checks
- [ ] Add `checkUserTier()` to `templates/voice_verify_modern.html`
- [ ] Hide advanced options for Freemium
- [ ] Show upgrade prompt for Freemium
- [ ] Display fee for PAYG (+$0.25)
- [ ] Display "Included" for Pro/Custom
- [ ] Update pricing dynamically
- [ ] Test in browser with all tiers
- [ ] Commit: `feat(voice): add tier-based UI gating`

### Day 4: Testing
- [ ] Run unit tests: `pytest tests/unit/test_voice_area_code_gating.py -v`
- [ ] Fix any failing tests
- [ ] Add integration tests if needed
- [ ] Test manually with all 4 tiers
- [ ] Verify pricing calculations
- [ ] Commit: `test(voice): add area code tier gating tests`

### Day 5: Deploy & Monitor
- [ ] Deploy to staging
- [ ] Run smoke tests on staging
- [ ] Test with real TextVerified API
- [ ] Deploy to production
- [ ] Monitor for 24 hours
- [ ] Check error rates in Sentry
- [ ] Verify no critical issues
- [ ] Commit: `chore(voice): deploy area code tier gating`

**Phase 1 Complete**: ✅ Voice verification area code tier gating live

---

## 🚀 Phase 2: Rentals (Days 6-10)

### Day 6: Backend - TextVerified Service
- [ ] Add `area_code` parameter to `create_reservation()` in `app/services/textverified_service.py`
- [ ] Implement area code preference chain
- [ ] Pass `area_code_select_option` to API
- [ ] Return area code match status
- [ ] Test locally
- [ ] Commit: `feat(rentals): add area code support to create_reservation`

### Day 7: Backend - Cost Calculation & API
- [ ] Create `calculate_rental_cost()` in `app/services/rental_service.py`
- [ ] Implement tier gating (Freemium blocked, PAYG $0.50, Pro/Custom $0)
- [ ] Update `/api/rentals/create` in `app/api/core/rentals.py`
- [ ] Add tier validation
- [ ] Test API with Postman/curl
- [ ] Commit: `feat(rentals): add tier-gated area code pricing`

### Day 8: Frontend - Rentals UI
- [ ] Add advanced options section to `templates/rentals.html`
- [ ] Add area code dropdown
- [ ] Add tier checks (hide for Freemium)
- [ ] Add upgrade prompt
- [ ] Display fee for PAYG (+$0.50)
- [ ] Display "Included" for Pro/Custom
- [ ] Update pricing dynamically
- [ ] Test in browser
- [ ] Commit: `feat(rentals): add area code UI with tier gating`

### Day 9: Testing
- [ ] Run unit tests: `pytest tests/unit/test_rental_area_code_gating.py -v`
- [ ] Fix any failing tests
- [ ] Add integration tests if needed
- [ ] Test manually with all 4 tiers
- [ ] Verify $0.50 fee (not $0.25)
- [ ] Commit: `test(rentals): add area code tier gating tests`

### Day 10: Deploy & Monitor
- [ ] Deploy to staging
- [ ] Run smoke tests on staging
- [ ] Test with real TextVerified API
- [ ] Deploy to production
- [ ] Monitor for 24 hours
- [ ] Check error rates in Sentry
- [ ] Verify no critical issues
- [ ] Commit: `chore(rentals): deploy area code tier gating`

**Phase 2 Complete**: ✅ Rentals area code tier gating live

---

## 📊 Post-Implementation (Days 11-14)

### Day 11: Documentation
- [ ] Update API documentation
- [ ] Update pricing page
- [ ] Update FAQ with tier info
- [ ] Create user guide for area codes
- [ ] Update changelog
- [ ] Commit: `docs: update area code tier gating documentation`

### Day 12: Monitoring
- [ ] Check success rates (voice >80%, rentals >85%)
- [ ] Review error logs
- [ ] Check support tickets
- [ ] Verify revenue tracking
- [ ] Create monitoring dashboard

### Day 13: Optimization
- [ ] Review performance metrics
- [ ] Optimize slow queries if any
- [ ] Improve error messages
- [ ] Add analytics tracking
- [ ] Commit: `perf: optimize area code tier gating`

### Day 14: Wrap-Up
- [ ] Final testing
- [ ] Team demo
- [ ] Update project board
- [ ] Close related issues
- [ ] Celebrate! 🎉

---

## ✅ Acceptance Criteria Verification

### Voice Verification
- [ ] Freemium users see upgrade prompt (no area code access)
- [ ] PAYG users see "+$0.25" fee
- [ ] Pro users see "Included"
- [ ] Custom users see "Included"
- [ ] Pricing updates correctly
- [ ] API blocks Freemium with 403
- [ ] All tests passing
- [ ] No critical errors in production

### Rentals
- [ ] Freemium users see upgrade prompt (no area code access)
- [ ] PAYG users see "+$0.50" fee (not $0.25)
- [ ] Pro users see "Included"
- [ ] Custom users see "Included"
- [ ] Pricing updates correctly
- [ ] API blocks Freemium with 403
- [ ] All tests passing
- [ ] No critical errors in production

### Cross-Cutting
- [ ] Tier validation on backend (never trust frontend)
- [ ] All area code usage logged
- [ ] Success rates tracked
- [ ] Documentation updated
- [ ] Support team briefed

---

## 🧪 Testing Checklist

### Unit Tests (28 tests total)
- [ ] Voice tier gating (8 tests)
- [ ] Voice pricing (4 tests)
- [ ] Voice edge cases (4 tests)
- [ ] Rental tier gating (8 tests)
- [ ] Rental pricing (4 tests)

### Integration Tests
- [ ] Voice end-to-end flow (4 scenarios)
- [ ] Rental end-to-end flow (4 scenarios)

### Manual Tests
- [ ] Freemium blocked (voice + rentals)
- [ ] PAYG fees correct (voice $0.25, rentals $0.50)
- [ ] Pro/Custom included (voice + rentals)
- [ ] Area code matches work
- [ ] Alternatives shown when unavailable
- [ ] Upgrade prompts work
- [ ] Pricing updates dynamically
- [ ] Error messages clear

---

## 📊 Success Metrics Tracking

### Week 1 (Voice)
- [ ] 0 critical errors
- [ ] Area code match rate: ___% (target >80%)
- [ ] Adoption rate: ___% (target >30%)
- [ ] Support tickets: ___ (target <5)

### Week 2 (Rentals)
- [ ] 0 critical errors
- [ ] Area code match rate: ___% (target >85%)
- [ ] Adoption rate: ___% (target >25%)
- [ ] Support tickets: ___ (target <3)

### Month 1
- [ ] Voice revenue: $_____ (target $1,000+)
- [ ] Rental revenue: $_____ (target $300+)
- [ ] Tier upgrades: ___ (target 5+)
- [ ] User satisfaction: ___/5 (target >4.5)

---

## 🚨 Rollback Triggers

**Rollback immediately if**:
- [ ] Critical errors >10/hour
- [ ] Success rate drops >20%
- [ ] Support tickets >10/hour
- [ ] Payment processing fails
- [ ] Data corruption detected

**Rollback procedure**:
1. Disable feature flags
2. Revert deployment
3. Notify team
4. Post-mortem within 24h

---

## 📁 Quick Commands

### Run Tests
```bash
# Voice tests
pytest tests/unit/test_voice_area_code_gating.py -v

# Rental tests
pytest tests/unit/test_rental_area_code_gating.py -v

# All area code tests
pytest tests/ -k "area_code" -v

# With coverage
pytest tests/ -k "area_code" --cov=app --cov-report=html
```

### Deploy
```bash
# Staging
git push origin feature/area-code-tier-gating

# Production (after testing)
git checkout main
git merge feature/area-code-tier-gating
git push origin main
```

### Monitor
```bash
# Check logs
tail -f logs/app.log | grep "area_code"

# Check errors
curl https://sentry.io/api/projects/namaskah/issues/
```

---

## 📞 Support

**Questions?**
- Consolidated guide: `docs/tasks/AREA_CODE_IMPLEMENTATION_CONSOLIDATED.md`
- Test templates: `tests/unit/test_*_area_code_gating.py`
- Slack: #engineering

**Issues?**
- Check Sentry dashboard
- Review error logs
- Contact on-call engineer

---

**Status**: 🎯 Ready to Start
**Next Action**: Check Day 1, Task 1
**Estimated Completion**: 2 weeks from start

---

**Good luck! 🚀**
