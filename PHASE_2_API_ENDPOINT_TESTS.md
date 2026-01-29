# Phase 2: API Endpoint Tests (140+ Tests)

## Objective
Create comprehensive endpoint tests to increase coverage from 40-42% to 55-60%

## Timeline
8-10 hours

## Test Files to Create

### 1. Verification Endpoints (50+ tests)
**File:** `tests/unit/test_verification_endpoints_comprehensive.py`

**Endpoints to Test:**
- `POST /api/verification/purchase` - Purchase verification
- `GET /api/verification/status/{id}` - Check status
- `POST /api/verification/cancel` - Cancel verification
- `GET /api/verification/pricing` - Get pricing
- `GET /api/verification/carriers` - List carriers
- `GET /api/verification/area-codes` - List area codes

**Test Template:**
```python
class TestVerificationEndpoints:
    """Test verification endpoints."""
    
    def test_purchase_verification_success(self, client, regular_user):
        """Test successful verification purchase."""
        response = client.post(
            "/api/verification/purchase",
            json={
                "service_name": "telegram",
                "country": "US",
                "capability": "sms"
            },
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 200
        assert "verification_id" in response.json()
    
    def test_purchase_verification_insufficient_balance(self, client, regular_user):
        """Test purchase with insufficient balance."""
        regular_user.credits = 0.0
        db.commit()
        
        response = client.post(
            "/api/verification/purchase",
            json={"service_name": "telegram", "country": "US"},
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 402  # Payment Required
    
    def test_get_verification_status(self, client, regular_user):
        """Test getting verification status."""
        # Create verification
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            status="pending"
        )
        db.add(verification)
        db.commit()
        
        response = client.get(
            f"/api/verification/status/{verification.id}",
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"
    
    def test_cancel_verification(self, client, regular_user):
        """Test canceling verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            status="pending"
        )
        db.add(verification)
        db.commit()
        
        response = client.post(
            f"/api/verification/cancel/{verification.id}",
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    def test_get_pricing(self, client):
        """Test getting pricing."""
        response = client.get("/api/verification/pricing")
        assert response.status_code == 200
        assert "pricing" in response.json()
    
    def test_get_carriers(self, client):
        """Test getting carriers."""
        response = client.get("/api/verification/carriers?country=US")
        assert response.status_code == 200
        assert "carriers" in response.json()
    
    def test_get_area_codes(self, client):
        """Test getting area codes."""
        response = client.get("/api/verification/area-codes?country=US")
        assert response.status_code == 200
        assert "area_codes" in response.json()
```

---

### 2. Auth Endpoints (30+ tests)
**File:** `tests/unit/test_auth_endpoints_comprehensive.py`

**Endpoints to Test:**
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout
- `POST /api/auth/reset-password` - Reset password
- `GET /api/auth/me` - Get current user

**Test Template:**
```python
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!"
            }
        )
        assert response.status_code == 201
        assert "user_id" in response.json()
    
    def test_register_duplicate_email(self, client, regular_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": regular_user.email,
                "password": "SecurePassword123!"
            }
        )
        assert response.status_code == 409  # Conflict
    
    def test_login_success(self, client, regular_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": regular_user.email,
                "password": "password123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_invalid_credentials(self, client, regular_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": regular_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client, regular_user):
        """Test getting current user."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == regular_user.email
```

---

### 3. Wallet Endpoints (20+ tests)
**File:** `tests/unit/test_wallet_endpoints_comprehensive.py`

**Endpoints to Test:**
- `GET /api/wallet/balance` - Get balance
- `POST /api/wallet/add-credits` - Add credits
- `GET /api/wallet/transactions` - Get transactions
- `POST /api/wallet/transfer` - Transfer credits

**Test Template:**
```python
class TestWalletEndpoints:
    """Test wallet endpoints."""
    
    def test_get_balance(self, client, regular_user):
        """Test getting balance."""
        response = client.get(
            "/api/wallet/balance",
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 200
        assert response.json()["balance"] == regular_user.credits
    
    def test_add_credits(self, client, regular_user):
        """Test adding credits."""
        response = client.post(
            "/api/wallet/add-credits",
            json={"amount": 10.0},
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 200
        assert response.json()["new_balance"] == regular_user.credits + 10.0
    
    def test_get_transactions(self, client, regular_user):
        """Test getting transactions."""
        response = client.get(
            "/api/wallet/transactions",
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 200
        assert "transactions" in response.json()
```

---

### 4. Admin Endpoints (40+ tests)
**File:** `tests/unit/test_admin_endpoints_comprehensive.py`

**Endpoints to Test:**
- `GET /api/admin/users` - List users
- `POST /api/admin/users/{id}/suspend` - Suspend user
- `GET /api/admin/tiers` - List tiers
- `POST /api/admin/tiers` - Create tier
- `GET /api/admin/analytics` - Get analytics

**Test Template:**
```python
class TestAdminEndpoints:
    """Test admin endpoints."""
    
    def test_list_users(self, client, admin_user):
        """Test listing users."""
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_user.id}"}
        )
        assert response.status_code == 200
        assert "users" in response.json()
    
    def test_suspend_user(self, client, admin_user, regular_user):
        """Test suspending user."""
        response = client.post(
            f"/api/admin/users/{regular_user.id}/suspend",
            json={"reason": "Suspicious activity"},
            headers={"Authorization": f"Bearer {admin_user.id}"}
        )
        assert response.status_code == 200
        assert response.json()["suspended"] is True
    
    def test_non_admin_cannot_suspend(self, client, regular_user):
        """Test non-admin cannot suspend users."""
        response = client.post(
            f"/api/admin/users/other-user/suspend",
            json={"reason": "Test"},
            headers={"Authorization": f"Bearer {regular_user.id}"}
        )
        assert response.status_code == 403  # Forbidden
```

---

## Execution Plan

### Step 1: Verification Endpoints (2-3 hours)
1. Create `tests/unit/test_verification_endpoints_comprehensive.py`
2. Write 50+ tests covering all endpoints
3. Test success and error paths
4. Verify all tests pass

### Step 2: Auth Endpoints (1-2 hours)
1. Create `tests/unit/test_auth_endpoints_comprehensive.py`
2. Write 30+ tests covering all endpoints
3. Test token handling
4. Verify all tests pass

### Step 3: Wallet Endpoints (1-2 hours)
1. Create `tests/unit/test_wallet_endpoints_comprehensive.py`
2. Write 20+ tests covering all endpoints
3. Test balance operations
4. Verify all tests pass

### Step 4: Admin Endpoints (2-3 hours)
1. Create `tests/unit/test_admin_endpoints_comprehensive.py`
2. Write 40+ tests covering all endpoints
3. Test authorization
4. Verify all tests pass

---

## Test Patterns

### Success Path
```python
def test_[endpoint]_success(self, client, [user_fixture]):
    response = client.[method]("[endpoint]", ...)
    assert response.status_code == 200
    assert [expected_field] in response.json()
```

### Error Path
```python
def test_[endpoint]_error(self, client, [user_fixture]):
    response = client.[method]("[endpoint]", ...)
    assert response.status_code == [error_code]
    assert "error" in response.json()
```

### Authorization
```python
def test_[endpoint]_unauthorized(self, client):
    response = client.[method]("[endpoint]")
    assert response.status_code == 401
```

---

## Verification

```bash
# Run all endpoint tests
python3 -m pytest tests/unit/test_*_endpoints_comprehensive.py -v

# Check coverage
python3 -m pytest tests/unit/ --cov=app/api --cov-report=term-missing:skip-covered
```

---

## Success Criteria

- [ ] 140+ new tests created
- [ ] All endpoint tests passing
- [ ] Coverage increased to 55-60%
- [ ] All success paths tested
- [ ] All error paths tested
- [ ] Authorization tested
