# Phase 2: Email Template Testing - Quick Start

**Status**: Ready to Test
**Duration**: 2 hours
**Prerequisites**: Server running, test user with Pro tier

---

## Setup (5 minutes)

### 0. Fix Database Schema (if needed)
```bash
# If you see "no such column: users.terms_accepted" error
python scripts/reset_database.py
# Type 'yes' to confirm
# This creates:
#   - admin@namaskah.app / admin123
#   - test@example.com / testpassword123 (Pro tier)
```

### 1. Install Dependencies
```bash
pip install httpx
```

### 2. Start Server
```bash
# Terminal 1
uvicorn main:app --reload
```

### 3. Create Test User (if needed)
```bash
# Terminal 2
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
user = User(
    email='test@example.com',
    hashed_password=get_password_hash('testpassword123'),
    subscription_tier='pro',  # Pro tier for email templates
    credits=100.0,
    is_active=True
)
db.add(user)
db.commit()
print('Test user created: test@example.com / testpassword123')
"
```

---

## Run Automated Tests (90 minutes)

```bash
python tests/manual/test_email_templates.py
```

**Expected Output**:
```
============================================================
EMAIL TEMPLATE EDITOR - AUTOMATED TEST SUITE
============================================================

Base URL: http://localhost:8000
Test User: test@example.com

Starting tests...

Authenticating...

=== Test 1: Access Page ===
✅ PASS - Page loads without errors
   Status: 200

=== Test 2: List Templates ===
✅ PASS - GET /api/whitelabel/email-templates returns 200
   Found 7 templates
✅ PASS - All 7 templates present
   Found: welcome, verification_code, payment_success, payment_failed, low_balance, tier_upgrade, password_reset
✅ PASS - All templates have available_variables

... (more tests)

============================================================
TEST SUMMARY
============================================================

Total Tests: 20
✅ Passed: 20
❌ Failed: 0
Success Rate: 100.0%

============================================================
✅ ALL TESTS PASSED - Email template editor is working!
✅ Phase 2 Complete - Ready for Phase 3
```

---

## Manual Browser Testing (30 minutes)

### 1. Access Page
```
http://localhost:8000/email-templates
```

### 2. Test Checklist
- [ ] Page loads without errors
- [ ] 7 template cards display
- [ ] Click on "Welcome" template
- [ ] Modal opens with editor
- [ ] Available variables show as chips
- [ ] Click a variable chip to insert
- [ ] Modify subject and HTML
- [ ] Click "Save Template"
- [ ] Success message appears
- [ ] Reload page - changes persist
- [ ] Click "Delete (Revert to Default)"
- [ ] Confirmation dialog appears
- [ ] Confirm deletion
- [ ] Template reverts to default

---

## Troubleshooting

### Issue: 401 Unauthorized
**Cause**: Not logged in
**Fix**: Login at http://localhost:8000/login with test@example.com / testpassword123

### Issue: 402 Payment Required
**Cause**: User not Pro tier
**Fix**: Upgrade test user to Pro tier:
```python
from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.email == 'test@example.com').first()
user.subscription_tier = 'pro'
db.commit()
```

### Issue: 404 Not Found on /email-templates
**Cause**: Route not registered
**Fix**: Already fixed in main_routes.py (line 348+)

### Issue: Template variables not validating
**Cause**: Service validation logic
**Check**: app/services/email_template_service.py line 130

---

## Success Criteria

### Phase 2 Complete When:
- ✅ Automated tests pass (>90% success rate)
- ✅ All 7 templates load correctly
- ✅ Save/edit/delete functionality works
- ✅ Variable validation working
- ✅ No critical bugs found
- ✅ Manual UI testing complete

### Ready for Phase 3 When:
- ✅ All automated tests pass (100%)
- ✅ Manual browser testing complete
- ✅ No blocking issues
- ✅ Email template editor production-ready

---

## Next Steps

### If Tests Pass
1. Mark Phase 2 complete in 12hourstoprod.md
2. Update PHASE2_CHECKLIST.md with results
3. Proceed to Phase 3: Navigation Improvements

### If Tests Fail
1. Review failed tests in output
2. Fix issues
3. Re-run tests
4. Do not proceed until >90% pass rate

---

## Files Created

- `tests/manual/test_email_templates.py` - Automated test suite
- `tests/manual/PHASE2_CHECKLIST.md` - Manual testing checklist
- `tests/manual/PHASE2_QUICKSTART.md` - This file

---

## Time Tracking

| Task | Estimated | Status |
|------|-----------|--------|
| Setup | 5 min | Pending |
| Automated Tests | 90 min | Pending |
| Manual Testing | 30 min | Pending |
| **Total** | **2 hours** | **Pending** |

---

**Ready to test!** 🚀

Run: `python tests/manual/test_email_templates.py`
