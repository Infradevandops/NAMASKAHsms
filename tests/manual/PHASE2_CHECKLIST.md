# Phase 2: Email Template Testing Checklist

**Duration**: 2 hours
**Status**: In Progress
**Started**: [Current Session]

---

## Quick Start

```bash
# 1. Start server
uvicorn main:app --reload

# 2. Run automated tests
python tests/manual/test_email_templates.py

# 3. Manual browser testing (if needed)
open http://localhost:8000/email-templates
```

---

## Automated Tests (90 minutes)

### Test 1: Access Page (5 min)
- [ ] Page loads at `/email-templates`
- [ ] No console errors
- [ ] Template list container renders

**Run**: Automated in `test_email_templates.py`

---

### Test 2: List Templates (10 min)
- [ ] `GET /api/whitelabel/email-templates` returns 200
- [ ] All 7 templates present:
  - [ ] welcome
  - [ ] verification_code
  - [ ] payment_success
  - [ ] payment_failed
  - [ ] low_balance
  - [ ] tier_upgrade
  - [ ] password_reset
- [ ] Each template has `available_variables`
- [ ] Default vs Custom indicator shows

**Run**: Automated in `test_email_templates.py`

---

### Test 3: Get Single Template (20 min)
- [ ] `GET /api/whitelabel/email-template/{name}` returns 200
- [ ] Template has `subject`
- [ ] Template has `html_content`
- [ ] Template has `text_content`
- [ ] Template has `available_variables` array
- [ ] Default template returned if no custom exists

**Run**: Automated in `test_email_templates.py`

---

### Test 4: Save Template (20 min)
- [ ] `POST /api/whitelabel/email-template` returns 200
- [ ] Subject saved correctly
- [ ] HTML content saved correctly
- [ ] Text content auto-generated if empty
- [ ] Template marked as custom after save
- [ ] Reload page shows updated content

**Run**: Automated in `test_email_templates.py`

---

### Test 5: Variable Validation (20 min)
- [ ] Invalid variables rejected (400 error)
- [ ] Error message lists invalid variables
- [ ] Valid variables accepted
- [ ] Template saves successfully with valid vars
- [ ] Variable insertion works in UI

**Run**: Automated in `test_email_templates.py`

---

### Test 6: Delete Template (15 min)
- [ ] `DELETE /api/whitelabel/email-template/{name}` returns 200
- [ ] Template reverts to default
- [ ] Confirmation message shown
- [ ] Reload page shows default template
- [ ] Delete button hidden for default templates

**Run**: Automated in `test_email_templates.py`

---

### Test 7: Edge Cases (30 min)
- [ ] Empty subject handled gracefully
- [ ] Empty HTML content rejected or handled
- [ ] Very long content (>10KB) handled
- [ ] Special characters in content work
- [ ] HTML injection prevented
- [ ] Invalid template name rejected
- [ ] Concurrent edits handled (open 2 tabs)

**Run**: Automated in `test_email_templates.py`

---

## Manual Browser Testing (30 minutes)

### UI/UX Testing
- [ ] Template cards display correctly
- [ ] Modal opens on card click
- [ ] Modal closes on X button
- [ ] Modal closes on Cancel button
- [ ] Variable chips clickable
- [ ] Variable insertion at cursor position
- [ ] Save button shows loading state
- [ ] Success message appears after save
- [ ] Error message appears on failure
- [ ] Delete confirmation dialog works

### Accessibility
- [ ] Keyboard navigation works
- [ ] Tab order logical
- [ ] Escape key closes modal
- [ ] Focus trapped in modal
- [ ] Screen reader friendly

### Responsive Design
- [ ] Works on mobile (375px)
- [ ] Works on tablet (768px)
- [ ] Works on desktop (1920px)
- [ ] Modal scrollable on small screens

---

## Known Issues

### Expected Behaviors
1. **402 Payment Required**: If test user not Pro tier
   - Expected: All endpoints return 402
   - Solution: Upgrade test user to Pro tier

2. **401 Unauthorized**: If no auth token
   - Expected: All endpoints return 401
   - Solution: Create test user and login

3. **404 Not Found**: If `/email-templates` route not registered
   - Expected: Page not found
   - Solution: Add route to main.py

---

## Success Criteria

### Phase 2 Complete When:
- ✅ Automated tests pass (>70% success rate)
- ✅ All 7 templates load correctly
- ✅ Save/edit/delete functionality works
- ✅ Variable validation working
- ✅ No critical bugs found

### Ready for Phase 3 When:
- ✅ All automated tests pass
- ✅ Manual UI testing complete
- ✅ No blocking issues
- ✅ Email template editor production-ready

---

## Test Results

### Automated Test Run 1
**Date**: [Pending]
**Duration**: [Pending]
**Results**: [Pending]

```
Total Tests: 0
✅ Passed: 0
❌ Failed: 0
Success Rate: 0%
```

### Manual Testing
**Date**: [Pending]
**Tester**: [Pending]
**Results**: [Pending]

---

## Next Steps

### If Tests Pass (>90%)
1. ✅ Mark Phase 2 complete
2. ✅ Update 12hourstoprod.md
3. ✅ Proceed to Phase 3: Navigation Improvements

### If Tests Fail (70-90%)
1. Review failed tests
2. Fix issues
3. Re-run tests
4. Proceed when >90% pass

### If Critical Failures (<70%)
1. Stop and investigate
2. Fix blocking issues
3. Re-run full test suite
4. Do not proceed to Phase 3

---

## Time Tracking

| Task | Estimated | Actual | Status |
|------|-----------|--------|--------|
| Automated Tests | 90 min | - | Pending |
| Manual UI Testing | 30 min | - | Pending |
| **Total** | **2 hours** | **-** | **Pending** |

---

## Notes

- Test script requires `httpx` package: `pip install httpx`
- Update `TEST_USER_EMAIL` and `TEST_USER_PASSWORD` in script
- Server must be running on `http://localhost:8000`
- Pro tier required for email template endpoints
