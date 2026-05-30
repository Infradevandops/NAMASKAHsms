# Test Suite Remediation Plan — Institutional Grade

**Status**: 419 failed, 2059 passed, 50 errors (83% pass rate)
**Target**: 95%+ pass rate (2400+ passing)
**Approach**: Systematic, data-driven, best practices
**Timeline**: 18-20 hours (2.5 days)

---

## Phase 0: Setup & Infrastructure (1 hour)

### Task 0.1: Create Test Analysis Tools

**File**: `scripts/analyze_tests.py`
```python
#!/usr/bin/env python3
"""Analyze test failures and categorize by root cause."""

import subprocess
import re
import json
from collections import defaultdict
from pathlib import Path

def run_tests_with_json_report():
    """Run pytest with JSON report."""
    subprocess.run([
        "python3", "-m", "pytest", "tests/",
        "--json-report", "--json-report-file=test_report.json",
        "--tb=short", "-v"
    ], timeout=900)

def categorize_failures():
    """Categorize failures by error type."""
    with open("test_report.json") as f:
        report = json.load(f)

    categories = defaultdict(list)

    for test in report.get("tests", []):
        if test["outcome"] == "failed":
            error = test.get("call", {}).get("longrepr", "")

            if "404" in error or "Not Found" in error:
                categories["404_missing_routes"].append(test["nodeid"])
            elif "AssertionError" in error:
                categories["assertion_errors"].append(test["nodeid"])
            elif "TypeError" in error:
                categories["type_errors"].append(test["nodeid"])
            elif "AttributeError" in error:
                categories["attribute_errors"].append(test["nodeid"])
            else:
                categories["other"].append(test["nodeid"])

    return categories

def generate_report(categories):
    """Generate markdown report."""
    with open("test_analysis_report.md", "w") as f:
        f.write("# Test Failure Analysis\n\n")
        for category, tests in sorted(categories.items(), key=lambda x: -len(x[1])):
            f.write(f"## {category.replace('_', ' ').title()}: {len(tests)} failures\n\n")
            for test in tests[:10]:
                f.write(f"- {test}\n")
            if len(tests) > 10:
                f.write(f"\n... and {len(tests)-10} more\n")
            f.write("\n")

if __name__ == "__main__":
    print("Running tests with JSON report...")
    run_tests_with_json_report()
    print("Categorizing failures...")
    categories = categorize_failures()
    print("Generating report...")
    generate_report(categories)
    print("Done. See test_analysis_report.md")
```

### Task 0.2: Install Dependencies
```bash
pip install pytest-json-report pytest-xdist pytest-timeout
```

### Task 0.3: Update pytest.ini
```ini
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --maxfail=1000
    -n auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PytestCollectionWarning
```

---

## Phase 1: Fix Collection Errors (2 hours)

**Priority**: CRITICAL - Blocks 50 tests from running

### Task 1.1: Fix Test Class Naming Conflicts

**File**: `tests/manual/test_email_templates.py`
```python
# BEFORE (causes collection error)
class TestResult:
    def __init__(self):
        self.success = False

# AFTER (institutional grade)
class EmailTemplateTestResult:
    """Result container for email template tests.

    Note: Not a test class - renamed to avoid pytest collection.
    """
    def __init__(self):
        self.success = False
        self.message = ""
        self.data = None
```

**File**: `tests/unit/test_pydantic_compat.py`
```python
# BEFORE
class TestModel(BaseModel):
    name: str

# AFTER
class PydanticCompatTestModel(BaseModel):
    """Test model for Pydantic compatibility checks.

    Note: Not a test class - renamed to avoid pytest collection.
    """
    name: str
    value: Optional[int] = None
```

### Task 1.2: Fix Import Errors

**File**: `tests/unit/test_common_services.py`
```python
# Add missing imports at top
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

# Fix function signatures
def test_audit_log_and_retrieve(db: Session):
    """Test audit logging with proper type hints."""
    # ... implementation
```

**File**: `tests/unit/test_compliance_service.py`
```python
# Add missing service import
from app.services.compliance_service import ComplianceService

class TestComplianceService:
    """Compliance service test suite."""

    def test_assess_compliance(self, db: Session):
        """Test compliance assessment."""
        service = ComplianceService(db)
        # ... implementation
```

### Task 1.3: Fix Async Test Issues

**File**: `tests/e2e/test_verification_flow.py`
```python
import pytest

class TestVerificationFlow:
    @pytest.mark.asyncio
    async def test_progress_indicator_updates(self, client):
        """Test progress indicator updates during verification."""
        # ... implementation
```

---

## Phase 2: Fix Missing Routes (404 Errors) - 6 hours

**Priority**: HIGH - Fixes ~200 tests (48% of failures)

### Task 2.1: Audit Missing Endpoints

**Script**: `scripts/find_missing_routes.py`
```python
#!/usr/bin/env python3
"""Find all 404 errors and extract missing routes."""

import re
import json

with open("test_report.json") as f:
    report = json.load(f)

missing_routes = set()

for test in report.get("tests", []):
    if test["outcome"] == "failed":
        error = test.get("call", {}).get("longrepr", "")
        # Extract route from 404 error
        match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)', error)
        if match and "404" in error:
            missing_routes.add(f"{match.group(1)} {match.group(2)}")

with open("missing_routes.txt", "w") as f:
    for route in sorted(missing_routes):
        f.write(f"{route}\n")

print(f"Found {len(missing_routes)} missing routes")
```

### Task 2.2: Create Missing Analytics Endpoints

**File**: `app/api/core/analytics.py` (create if missing)
```python
"""Analytics API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id, get_db
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/real-time-stats")
async def get_real_time_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get real-time user statistics.

    Returns:
        dict: Current balance and pending verifications count
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        pending_count = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.status == "pending"
        ).count()

        return {
            "balance": float(user.credits) if user.credits else 0.0,
            "pending_verifications": pending_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching real-time stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status-updates")
async def get_status_updates(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get recent status updates for user verifications.

    Returns:
        dict: List of recent verification status changes
    """
    try:
        recent_verifications = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.updated_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(Verification.updated_at.desc()).limit(10).all()

        updates = [
            {
                "id": v.id,
                "service": v.service_name,
                "status": v.status,
                "updated_at": v.updated_at.isoformat() if v.updated_at else None
            }
            for v in recent_verifications
        ]

        return {"updates": updates}

    except Exception as e:
        logger.error(f"Error fetching status updates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary")
async def get_analytics_summary(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get analytics summary with optional date filtering.

    Args:
        from_date: Start date (ISO format)
        to_date: End date (ISO format)

    Returns:
        dict: Analytics summary including counts and spending
    """
    try:
        # Default to last 30 days
        if not from_date:
            from_dt = datetime.utcnow() - timedelta(days=30)
        else:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))

        if not to_date:
            to_dt = datetime.utcnow()
        else:
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))

        # Query verifications in date range
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= from_dt,
            Verification.created_at <= to_dt
        ).all()

        total_verifications = len(verifications)
        successful = sum(1 for v in verifications if v.status == "completed")
        failed = sum(1 for v in verifications if v.status in ["failed", "timeout", "cancelled"])

        # Calculate spending
        total_spent = sum(v.cost for v in verifications if v.cost)

        # Top services
        service_counts = {}
        for v in verifications:
            service_counts[v.service_name] = service_counts.get(v.service_name, 0) + 1

        top_services = [
            {"name": service, "count": count}
            for service, count in sorted(service_counts.items(), key=lambda x: -x[1])[:5]
        ]

        # Daily breakdown
        daily_verifications = []
        current_date = from_dt.date()
        while current_date <= to_dt.date():
            count = sum(1 for v in verifications if v.created_at.date() == current_date)
            daily_verifications.append({
                "date": current_date.isoformat(),
                "count": count
            })
            current_date += timedelta(days=1)

        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful,
            "failed_verifications": failed,
            "total_spent": total_spent,
            "top_services": top_services,
            "daily_verifications": daily_verifications,
            "date_range": {
                "from": from_dt.isoformat(),
                "to": to_dt.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Task 2.3: Register Analytics Router

**File**: `main.py`
```python
# Add import
from app.api.core import analytics

# Register router
app.include_router(analytics.router)
```

### Task 2.4: Create Missing Page Routes

**File**: `app/api/main_routes.py`
```python
@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, user_id: str = Depends(get_current_user_id)):
    """Analytics dashboard page."""
    return templates.TemplateResponse("analytics.html", {"request": request})
```

---

## Phase 3: Fix Assertion Errors (Logic Bugs) - 6 hours

**Priority**: HIGH - Fixes ~150 tests (36% of failures)

### Task 3.1: Fix Test Isolation Issues

**Pattern**: Tests failing due to data pollution from previous tests

**Solution**: Add proper cleanup in conftest.py

**File**: `tests/conftest.py`
```python
import pytest
from sqlalchemy.orm import Session

@pytest.fixture(autouse=True)
def clean_database(db: Session):
    """Clean database before each test.

    This fixture runs automatically before every test to ensure isolation.
    """
    yield

    # Cleanup after test
    from app.models.verification import Verification
    from app.models.transaction import Transaction
    from app.models.notification import Notification
    from app.models.activity import Activity

    try:
        db.query(Activity).delete()
        db.query(Notification).delete()
        db.query(Verification).delete()
        db.query(Transaction).delete()
        db.commit()
    except Exception:
        db.rollback()


@pytest.fixture
def isolated_user(db: Session, regular_user):
    """User with guaranteed clean state.

    Use this fixture when you need a user with no existing data.
    """
    # Clean user's data
    db.query(Verification).filter_by(user_id=regular_user.id).delete()
    db.query(Transaction).filter_by(user_id=regular_user.id).delete()
    db.commit()

    return regular_user
```

### Task 3.2: Fix Date Filter Test

**File**: `tests/test_analytics_enhanced.py`
```python
def test_analytics_date_filter(client, db: Session, isolated_user):
    """Test analytics date filtering with proper isolation."""
    # Ensure clean state
    db.query(Verification).filter_by(user_id=isolated_user.id).delete()
    db.commit()

    # Add old verification (outside default 30-day range)
    old_date = datetime.utcnow() - timedelta(days=60)
    v_old = Verification(
        user_id=isolated_user.id,
        phone_number="+1111111111",
        service_name="facebook",
        status="completed",
        cost=0.0,
        created_at=old_date
    )
    db.add(v_old)
    db.commit()
    db.refresh(v_old)

    token = create_test_token(isolated_user.id, isolated_user.email)
    headers = {"Authorization": f"Bearer {token}"}

    # Query default range (30 days) - should not see old verification
    response = client.get("/api/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_verifications"] == 0, \
        f"Expected 0 verifications in last 30 days, got {data['total_verifications']}"

    # Query extended range (90 days) - should see old verification
    from_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
    response = client.get(
        f"/api/analytics/summary?from_date={from_date}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_verifications"] == 1, \
        f"Expected 1 verification in last 90 days, got {data['total_verifications']}"
```

---

## Phase 4: Fix Type Errors - 3 hours

**Priority**: MEDIUM - Fixes ~50 tests (12% of failures)

### Task 4.1: Add Null Safety to Services

**File**: `app/services/common_services.py`
```python
from typing import Optional, Dict, Any
from datetime import datetime

def audit_log_and_retrieve(
    db: Session,
    user_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Log audit event and retrieve recent logs.

    Args:
        db: Database session
        user_id: User ID performing action
        action: Action description
        details: Optional additional details

    Returns:
        dict: Audit log entry with metadata

    Raises:
        TypeError: If required parameters are None
        ValueError: If parameters are invalid
    """
    if not user_id:
        raise TypeError("user_id cannot be None")
    if not action:
        raise TypeError("action cannot be None")

    try:
        from app.models.audit_log import AuditLog

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        return {
            "id": log_entry.id,
            "user_id": log_entry.user_id,
            "action": log_entry.action,
            "details": log_entry.details,
            "timestamp": log_entry.timestamp.isoformat()
        }

    except Exception as e:
        db.rollback()
        raise
```

---

## Phase 5: Verification & Iteration - 2 hours

### Task 5.1: Run Tests by Category

```bash
# After each phase, verify progress
python3 -m pytest tests/ --tb=no -q | tee phase_X_results.txt

# Track progress
echo "Phase X: $(grep 'passed' phase_X_results.txt)"
```

### Task 5.2: Generate Coverage Report

```bash
python3 -m pytest tests/ --cov=app --cov-report=html --cov-report=term
open htmlcov/index.html
```

### Task 5.3: Final Validation

```bash
# Run full suite
python3 -m pytest tests/ -v --tb=short > final_test_report.txt

# Verify success criteria
python3 << 'EOF'
import re

with open("final_test_report.txt") as f:
    content = f.read()

match = re.search(r'(\d+) failed, (\d+) passed', content)
if match:
    failed = int(match.group(1))
    passed = int(match.group(2))
    total = failed + passed
    pass_rate = (passed / total) * 100

    print(f"Pass Rate: {pass_rate:.1f}%")
    print(f"Passed: {passed}/{total}")

    if pass_rate >= 95:
        print("✅ SUCCESS: Ready for deployment")
    else:
        print(f"❌ FAIL: Need {int((0.95 * total) - passed)} more passing tests")
EOF
```

---

## Success Criteria

- [ ] Pass rate ≥ 95% (2400+ passing tests)
- [ ] Zero collection errors
- [ ] Zero TypeErrors in core services
- [ ] All critical paths tested (auth, payment, verification)
- [ ] Test suite completes in <10 minutes
- [ ] Coverage ≥ 82% (maintain current level)

---

## Rollback Plan

If any phase breaks existing tests:

```bash
# Revert changes
git checkout -- .

# Run tests to verify
python3 -m pytest tests/ --tb=no -q

# Identify breaking change
git diff HEAD~1
```

---

**Timeline**: 18-20 hours
**Approach**: Systematic, institutional-grade
**Result**: Production-ready test suite
