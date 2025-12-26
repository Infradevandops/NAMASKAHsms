# 📋 Task Breakdown - Implementation & Testing Guide

**Created:** 2025-12-26  
**Purpose:** Step-by-step implementation guide for all priority tasks

---

# 🔴 TASK 1: CRITICAL - Security & Duplicates

## Task 1.1: Security Cleanup
**Time:** 30 minutes  
**Risk:** HIGH - Prevents secrets exposure

### Step 1.1.1: Update .gitignore
```bash
# Add these lines to .gitignore
cat >> .gitignore << 'EOF'

# Database files
*.db
*.sqlite
*.sqlite3

# Environment files (if not already present)
.env
.env.*
!.env.example

# Certificate files
certs/*.key
certs/*.crt
certs/*.pem

# IDE and OS
.idea/
*.swp
.DS_Store
EOF
```

**Verify:**
```bash
cat .gitignore | grep -E "(\.db|\.env|certs)"
```

### Step 1.1.2: Remove Files from Git Tracking
```bash
# Remove database files (keeps local copies)
git rm --cached namaskah.db 2>/dev/null || echo "namaskah.db not tracked"
git rm --cached namaskah_dev.db 2>/dev/null || echo "namaskah_dev.db not tracked"
git rm --cached test.db 2>/dev/null || echo "test.db not tracked"

# Remove env files
git rm --cached .env 2>/dev/null || echo ".env not tracked"
git rm --cached .env.local 2>/dev/null || echo ".env.local not tracked"
git rm --cached .env.development 2>/dev/null || echo ".env.development not tracked"
git rm --cached .env.production 2>/dev/null || echo ".env.production not tracked"
git rm --cached .env.docker 2>/dev/null || echo ".env.docker not tracked"

# Remove cert files
git rm --cached certs/server.key 2>/dev/null || echo "server.key not tracked"
git rm --cached certs/server.crt 2>/dev/null || echo "server.crt not tracked"
```

### Step 1.1.3: Verify Cleanup
```bash
# Check what's still tracked
git ls-files | grep -E "\.(db|env|key|crt)$"

# Should return empty - if not, remove those files
```

### Step 1.1.4: Test Application Still Works
```bash
# Run tests
python3 -m pytest tests/test_critical_admin.py -v --tb=short

# Expected: 26 passed
```

### Checklist:
- [ ] .gitignore updated with db, env, cert patterns
- [ ] Database files removed from tracking
- [ ] Env files removed from tracking  
- [ ] Cert files removed from tracking
- [ ] `git ls-files` shows no sensitive files
- [ ] Tests still pass (26/26)

---

## Task 1.2: Duplicate Router Removal ✅ COMPLETED
**Status:** Done on 2025-12-26

- [x] Removed duplicate `verification_history_router`
- [x] Removed duplicate `dashboard_router`
- [x] Tests passing

---

# 🟠 TASK 2: HIGH PRIORITY - Code Quality

## Task 2.1: Split main.py
**Time:** 3-4 hours  
**Current:** ~1600 lines → **Target:** <200 lines

### Step 2.1.1: Create Pages Router Module

**Create file:** `app/api/pages/__init__.py`
```python
"""Page routes package."""
from .routes import router

__all__ = ["router"]
```

**Create file:** `app/api/pages/routes.py`
```python
"""HTML page routes - extracted from main.py."""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user_id, get_optional_user_id
from app.models.user import User

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory=str(Path("templates").resolve()))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
    """Home page."""
    # Move home route logic here
    pass


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: Optional[str] = Depends(get_optional_user_id), db: Session = Depends(get_db)):
    """Dashboard page."""
    # Move dashboard route logic here
    pass


# Add all other HTML page routes...
```

### Step 2.1.2: Create User API Module

**Create file:** `app/api/core/user.py`
```python
"""User-related API endpoints - extracted from main.py."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["User"])


@router.get("/user/balance")
async def user_balance(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get user balance."""
    # Move balance endpoint logic here
    pass


@router.post("/auth/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Refresh access token."""
    # Move refresh endpoint logic here
    pass


@router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Logout user."""
    # Move logout endpoint logic here
    pass
```

### Step 2.1.3: Create Lifespan Module

**Create file:** `app/core/lifespan.py`
```python
"""Application lifespan management - extracted from main.py."""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.logging import get_logger, setup_logging
from app.core.startup import run_startup_initialization
from app.core.unified_cache import cache
from app.core.database import engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    setup_logging()
    logger.info("Application startup - Phase 1")
    
    try:
        # Connect cache
        logger.info("Connecting to cache...")
        await cache.connect()
        logger.info("Cache connected successfully")
        
        # Initialize database
        logger.info("Initializing database...")
        run_startup_initialization()
        logger.info("Database initialized")
        
        # Start background services
        from app.services.sms_polling_service import sms_polling_service
        from app.services.voice_polling_service import voice_polling_service
        await sms_polling_service.start()
        await voice_polling_service.start()
        
        logger.info("Application startup completed successfully")
        
        yield  # Application runs here
        
    finally:
        # Shutdown
        logger.info("Starting graceful shutdown")
        
        # Stop polling services
        from app.services.sms_polling_service import sms_polling_service
        from app.services.voice_polling_service import voice_polling_service
        await sms_polling_service.stop()
        await voice_polling_service.stop()
        logger.info("Polling services stopped")
        
        # Disconnect cache
        await cache.disconnect()
        logger.info("Cache disconnected")
        
        # Dispose database connections
        engine.dispose()
        logger.info("Database connections disposed")
        
        logger.info("Graceful shutdown completed")
```

### Step 2.1.4: Update main.py

**New main.py structure (~150 lines):**
```python
"""Namaskah SMS - Application Factory."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from pathlib import Path

from app.core.lifespan import lifespan
from app.core.config import get_settings
from app.middleware.csrf_middleware import CSRFMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.xss_protection import XSSProtectionMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.core.unified_error_handling import setup_unified_middleware

# Import routers
from app.api.pages.routes import router as pages_router
from app.api.core.user import router as user_router
from app.api.core.auth import router as auth_router
# ... other router imports

STATIC_DIR = Path("static").resolve()


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    
    app = FastAPI(
        title="Namaskah SMS API",
        version="2.5.0",
        lifespan=lifespan,
    )
    
    # Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    setup_unified_middleware(app)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(XSSProtectionMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)))
    
    # Register routers
    app.include_router(pages_router)
    app.include_router(user_router)
    app.include_router(auth_router, prefix="/api")
    # ... other routers
    
    return app


app = create_app()
```

### Step 2.1.5: Test After Split
```bash
# Run all tests
python3 -m pytest tests/ -v

# Test specific endpoints
curl http://localhost:8000/api/user/balance -H "Authorization: Bearer <token>"
curl http://localhost:8000/dashboard

# Verify no import errors
python3 -c "from main import app; print('OK')"
```

### Checklist:
- [ ] Created `app/api/pages/__init__.py`
- [ ] Created `app/api/pages/routes.py` with HTML routes
- [ ] Created `app/api/core/user.py` with user endpoints
- [ ] Created `app/core/lifespan.py` with lifecycle handlers
- [ ] Updated main.py to use new modules
- [ ] main.py is under 200 lines
- [ ] All tests pass
- [ ] Manual endpoint testing works

---

## Task 2.2: Standardize API URLs ✅ COMPLETED
**Status:** Done on 2025-12-26

- [x] All admin endpoints use `/api/admin/` prefix
- [x] Tests updated and passing

---

## Task 2.3: Pydantic v2 Migration
**Time:** 2-3 hours

### Step 2.3.1: Update validators.py

**File:** `app/schemas/validators.py`

```python
# BEFORE
from pydantic import validator

@validator("phone_number", pre=True, allow_reuse=True)
def validate_phone(cls, v):
    return v

# AFTER
from pydantic import field_validator

@field_validator("phone_number", mode="before")
@classmethod
def validate_phone(cls, v):
    return v
```

**Test after:**
```bash
python3 -m pytest tests/test_critical_admin.py -v
```

### Step 2.3.2: Update auth.py

**File:** `app/schemas/auth.py`

```python
# BEFORE
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    email: str
    password: str
    
    @validator("email", pre=True)
    def validate_email(cls, v):
        return v.lower().strip()
    
    class Config:
        orm_mode = True

# AFTER
from pydantic import BaseModel, field_validator, ConfigDict

class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    email: str
    password: str
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        return v.lower().strip()
```

**Test after:**
```bash
python3 -m pytest tests/test_critical_admin.py -v
```

### Step 2.3.3: Update payment.py

**File:** `app/schemas/payment.py`

Same pattern - replace `@validator` with `@field_validator`

**Test after:**
```bash
python3 -m pytest tests/test_critical_admin.py -v
```

### Step 2.3.4: Update verification.py

**File:** `app/schemas/verification.py`

Same pattern

**Test after:**
```bash
python3 -m pytest tests/test_critical_admin.py -v
```

### Step 2.3.5: Update payment_endpoints.py

**File:** `app/api/billing/payment_endpoints.py`

Same pattern

### Step 2.3.6: Final Verification
```bash
# Run all tests
python3 -m pytest tests/ -v

# Check for remaining deprecation warnings
python3 -m pytest tests/ -v 2>&1 | grep -i "pydantic.*deprecated"

# Should return empty
```

### Checklist:
- [ ] Updated `app/schemas/validators.py`
- [ ] Updated `app/schemas/auth.py`
- [ ] Updated `app/schemas/payment.py`
- [ ] Updated `app/schemas/verification.py`
- [ ] Updated `app/api/billing/payment_endpoints.py`
- [ ] All `class Config` replaced with `model_config = ConfigDict(...)`
- [ ] No Pydantic deprecation warnings
- [ ] All tests pass

---

# 🟡 TASK 3: MEDIUM PRIORITY - Quality & Cleanup

## Task 3.1: Increase Test Coverage
**Time:** 4-6 hours  
**Current:** 34% → **Target:** 70%

### Step 3.1.1: Create Auth Tests

**Create file:** `tests/test_auth.py`
```python
"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient

class TestAuthentication:
    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "email": "newuser@test.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
    
    def test_register_duplicate_email(self, client, regular_user):
        response = client.post("/api/auth/register", json={
            "email": "user@test.com",  # Already exists
            "password": "SecurePass123!"
        })
        assert response.status_code == 400
    
    def test_login_success(self, client, regular_user):
        response = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_wrong_password(self, client, regular_user):
        response = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_token_refresh(self, client, regular_user):
        # First login
        login = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "password123"
        })
        refresh_token = login.json()["refresh_token"]
        
        # Then refresh
        response = client.post("/api/auth/refresh", 
            headers={"Authorization": f"Bearer {refresh_token}"})
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### Step 3.1.2: Create Verification Tests

**Create file:** `tests/test_verification.py`
```python
"""Tests for verification endpoints."""
import pytest
from fastapi.testclient import TestClient

class TestVerification:
    def test_purchase_verification(self, client, admin_token):
        response = client.post("/api/verification/purchase", 
            json={"service": "telegram", "country": "US"},
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code in [200, 201, 402]  # Success or insufficient funds
    
    def test_get_verification_status(self, client, admin_token, verification_data):
        verify_id = verification_data[0].id
        response = client.get(f"/api/verification/{verify_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
    
    def test_cancel_verification(self, client, admin_token, verification_data):
        verify_id = verification_data[0].id
        response = client.post(f"/api/verification/{verify_id}/cancel",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code in [200, 400]  # Success or already completed
```

### Step 3.1.3: Create Billing Tests

**Create file:** `tests/test_billing.py`
```python
"""Tests for billing endpoints."""
import pytest
from fastapi.testclient import TestClient

class TestBilling:
    def test_get_pricing(self, client):
        response = client.get("/api/pricing")
        assert response.status_code == 200
    
    def test_add_credits(self, client, admin_token):
        response = client.post("/api/credits/add",
            json={"amount": 10.00},
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code in [200, 201]
    
    def test_get_payment_history(self, client, admin_token):
        response = client.get("/api/payments/history",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
```

### Step 3.1.4: Run Coverage Report
```bash
# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Open HTML report
open htmlcov/index.html

# Check coverage meets threshold
python3 -m pytest tests/ --cov=app --cov-fail-under=70
```

### Checklist:
- [x] Created `tests/test_auth.py`
- [x] Created `tests/test_verification.py`
- [x] Created `tests/test_billing.py`
- [x] Coverage report generated
- [x] Coverage >= 70%

---

## Task 3.2: Clean Up Project Structure
**Time:** 1 hour

### Step 3.2.1: Remove Duplicate Virtual Env
```bash
# Check which venv is active
which python3

# Remove duplicate (keep .venv)
rm -rf venv/

# Verify .venv still works
source .venv/bin/activate
python3 -c "import fastapi; print('OK')"
```

### Step 3.2.2: Archive Old Documentation
```bash
# Create archive directory
mkdir -p docs/_archive

# Move old status docs
mv ADMIN_DASHBOARD_COMPLETE.md docs/_archive/
mv ADMIN_DASHBOARD_V2_COMPLETE.md docs/_archive/
mv ADMIN_NAVIGATION_COMPLETE.md docs/_archive/
mv ADMIN_NAV_QUICK_REF.md docs/_archive/
mv ADMIN_QUICK_START.md docs/_archive/
mv ADMIN_V2_QUICK_REF.md docs/_archive/
mv CRITICAL_IMPLEMENTATION_COMPLETE.md docs/_archive/
mv CRITICAL_TASKS.md docs/_archive/
mv DELIVERY_SUMMARY.md docs/_archive/
mv IMPLEMENTATION_CHECKLIST.md docs/_archive/
mv IMPLEMENTATION_COMPLETE.md docs/_archive/
mv IMPLEMENTATION_SUMMARY.txt docs/_archive/
mv QUICK_START_CRITICAL.md docs/_archive/
mv SEARCH_FUNCTIONALITY_COMPLETE.md docs/_archive/
mv BACKEND_IMPLEMENTATION_STATUS.md docs/_archive/
mv CLEANUP_SESSION_SUMMARY.md docs/_archive/
mv SMS_VERIFICATION_ANALYSIS.md docs/_archive/
mv SMS_VERIFICATION_STATUS.md docs/_archive/
mv TIER_MANAGEMENT_IMPLEMENTATION.md docs/_archive/
mv TIER_MANAGEMENT_QUICK_REFERENCE.md docs/_archive/
mv HOW_TO_ACCESS_TIER_MANAGEMENT.md docs/_archive/
mv INDEX.md docs/_archive/

# Keep only essential docs in root
# README.md
# CODEBASE_CLEANUP_ROADMAP.md
# PRIORITY_TASKS.md
# TASK_BREAKDOWN.md
```

### Step 3.2.3: Verify node_modules Ignored
```bash
# Check if tracked
git ls-files | grep node_modules

# If tracked, remove
git rm -r --cached node_modules/

# Verify in .gitignore
grep "node_modules" .gitignore || echo "node_modules/" >> .gitignore
```

### Checklist:
- [ ] Removed `venv/` directory
- [ ] Archived old documentation to `docs/_archive/`
- [ ] `node_modules/` not tracked in git
- [ ] Root directory clean with only essential files

---

## Task 3.3: Model-API Alignment Audit
**Time:** 2 hours

### Step 3.3.1: Create Audit Script

**Create file:** `scripts/audit_api_models.py`
```python
"""Audit API responses against model fields."""
import ast
import os

def get_model_fields(model_file):
    """Extract Column fields from SQLAlchemy model."""
    with open(model_file) as f:
        tree = ast.parse(f.read())
    
    fields = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    fields.append(target.id)
    return fields

def get_api_response_fields(api_file):
    """Extract response dict keys from API file."""
    with open(api_file) as f:
        content = f.read()
    
    # Simple regex to find dict keys in return statements
    import re
    keys = re.findall(r'"(\w+)":', content)
    return list(set(keys))

def audit():
    """Run audit."""
    models = {
        "User": "app/models/user.py",
        "Verification": "app/models/verification.py",
        "AuditLog": "app/models/audit_log.py",
    }
    
    apis = [
        "app/api/admin/verification_history.py",
        "app/api/admin/user_management.py",
        "app/api/admin/audit_compliance.py",
    ]
    
    print("=== Model-API Alignment Audit ===\n")
    
    for api_file in apis:
        print(f"\n📄 {api_file}")
        api_fields = get_api_response_fields(api_file)
        print(f"   Response fields: {api_fields[:10]}...")

if __name__ == "__main__":
    audit()
```

### Step 3.3.2: Run Audit
```bash
python3 scripts/audit_api_models.py
```

### Step 3.3.3: Create Response Schemas

**Create file:** `app/schemas/admin_responses.py`
```python
"""Response schemas for admin endpoints."""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class VerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    country: str
    service: str
    status: str
    phone_number: Optional[str]
    created_at: Optional[datetime]
    completed_at: Optional[datetime]
    cost_usd: float

class VerificationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    verifications: List[VerificationResponse]

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: str
    tier: str
    is_suspended: bool
    is_banned: bool
    credits: float
    created_at: Optional[datetime]
    last_login: Optional[datetime]

class UserSearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    query: str
    users: List[UserResponse]
```

- [x] All tests pass

---

# 🟢 TASK 4: UI & Admin Features ✅ COMPLETED

## Task 4.1: Phase 5 - Template Migration
**Status:** ✅ DONE (2025-12-27)

- [x] Settings Page (Account, Security, Notifications, API Keys)
- [x] Profile Page (Avatar, Details)
- [x] Auth Pages (Login, Register)
- [x] Error Pages (404, 500)
- [x] Global Components (Modal, Toast, Spinner)
- [x] Template Archive & Cleanup

## Task 4.2: Phase 6 - Critical Admin APIs
**Status:** ✅ DONE (2025-12-27)

- [x] implemented `verification_history.py` endpoints
- [x] implemented `user_management.py` endpoints
- [x] implemented `analytics` endpoints
- [x] Data Export to CSV
- [x] TextVerified Service enhancements
- [x] 39 Tests Passing


---

# 📊 Final Verification Checklist

Before pushing to remote:

```bash
# 1. Security check
git ls-files | grep -E "\.(db|env|key|crt)$"
# Expected: empty

# 2. Run all tests
python3 -m pytest tests/ -v
# Expected: All pass

# 3. Check coverage
python3 -m pytest tests/ --cov=app --cov-fail-under=70
# Expected: >= 70%

# 4. Check for deprecation warnings
python3 -m pytest tests/ 2>&1 | grep -c "DeprecationWarning"
# Expected: 0 (or minimal)

# 5. Verify main.py size
wc -l main.py
# Expected: < 200 lines

# 6. Check git status
git status
# Expected: Clean working directory
```

---

**Total Estimated Time:** 12-16 hours  
**Recommended:** Complete over 2-3 days
