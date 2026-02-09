# 🔒 Security Hardening Plan

**Version**: 1.0  
**Created**: January 2026  
**Goal**: Zero critical vulnerabilities  
**Timeline**: 1 week (concurrent with testing)  
**Priority**: CRITICAL

---

## 🎯 Current Security Status

### Known Issues
- ⚠️ Payment race conditions (partially fixed)
- ⚠️ Missing rate limiting on some endpoints
- ⚠️ CSRF protection not implemented
- ⚠️ Input validation gaps
- ⚠️ Security headers incomplete

### Compliance Status
- ✅ OWASP A02: Bcrypt password hashing
- ✅ OWASP A03: SQLAlchemy ORM (prevents SQL injection)
- ⚠️ OWASP A01: Access control needs review
- ⚠️ OWASP A07: Rate limiting incomplete
- ⚠️ OWASP A05: Security headers missing

---

## 🛡️ Security Improvements

### 1. Payment Security (CRITICAL)

#### Race Condition Prevention
**Priority**: P0  
**Time**: 1 day

```python
# app/services/payment_service.py

from sqlalchemy import select
from sqlalchemy.orm import Session

class PaymentService:
    async def process_payment(self, user_id: int, amount: float, idempotency_key: str):
        """Process payment with race condition protection"""
        
        async with self.db.begin():  # Transaction
            # 1. Check idempotency
            existing = await self.db.execute(
                select(Transaction).where(
                    Transaction.idempotency_key == idempotency_key
                ).with_for_update()  # Row-level lock
            )
            
            if existing.scalar_one_or_none():
                raise DuplicatePaymentError()
            
            # 2. Update balance with lock
            user = await self.db.execute(
                select(User).where(User.id == user_id).with_for_update()
            )
            user = user.scalar_one()
            
            # 3. Create transaction record
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                idempotency_key=idempotency_key,
                status="completed"
            )
            
            # 4. Update balance
            user.balance += amount
            
            self.db.add(transaction)
            await self.db.commit()
```

#### Webhook Security
```python
# app/api/billing/webhook.py

import hmac
import hashlib

def verify_paystack_signature(payload: bytes, signature: str) -> bool:
    """Verify Paystack webhook signature"""
    secret = settings.PAYSTACK_SECRET_KEY
    computed = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    return hmac.compare_digest(computed, signature)

@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(...)
):
    # Verify signature
    body = await request.body()
    if not verify_paystack_signature(body, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    ...
```

---

### 2. Rate Limiting (HIGH)

#### Global Rate Limits
**Priority**: P1  
**Time**: 0.5 days

```python
# app/middleware/rate_limiting.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Apply to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

#### Endpoint-Specific Limits
```python
# app/api/core/auth.py

@router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, credentials: LoginRequest):
    ...

@router.post("/register")
@limiter.limit("3/hour")  # 3 registrations per hour
async def register(request: Request, user_data: RegisterRequest):
    ...

# app/api/core/verification.py

@router.post("/create")
@limiter.limit("10/minute")  # 10 verifications per minute
async def create_verification(request: Request):
    ...

# app/api/billing/wallet.py

@router.post("/paystack/initialize")
@limiter.limit("5/minute")  # 5 payment attempts per minute
async def initialize_payment(request: Request):
    ...
```

---

### 3. CSRF Protection (HIGH)

#### Implementation
**Priority**: P1  
**Time**: 0.5 days

```python
# app/middleware/csrf.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import secrets

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate CSRF token for GET requests
        if request.method == "GET":
            token = secrets.token_urlsafe(32)
            request.state.csrf_token = token
            response = await call_next(request)
            response.set_cookie(
                "csrf_token",
                token,
                httponly=True,
                secure=True,
                samesite="strict"
            )
            return response
        
        # Validate CSRF token for state-changing requests
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            cookie_token = request.cookies.get("csrf_token")
            header_token = request.headers.get("X-CSRF-Token")
            
            if not cookie_token or cookie_token != header_token:
                return Response("CSRF token invalid", status_code=403)
        
        return await call_next(request)

# Add to app
app.add_middleware(CSRFMiddleware)
```

#### Frontend Integration
```javascript
// static/js/api.js

async function apiRequest(url, options = {}) {
    // Get CSRF token from cookie
    const csrfToken = getCookie('csrf_token');
    
    // Add to headers
    options.headers = {
        ...options.headers,
        'X-CSRF-Token': csrfToken
    };
    
    return fetch(url, options);
}
```

---

### 4. Input Validation (MEDIUM)

#### Pydantic Models
**Priority**: P2  
**Time**: 1 day

```python
# app/schemas/validation.py

from pydantic import BaseModel, validator, Field
import re

class PaymentRequest(BaseModel):
    amount: float = Field(gt=0, le=10000)  # $0-$10,000
    currency: str = Field(regex="^(USD|NGN)$")
    
    @validator('amount')
    def validate_amount(cls, v):
        # Must be multiple of 0.01
        if round(v, 2) != v:
            raise ValueError('Amount must have max 2 decimal places')
        return v

class VerificationRequest(BaseModel):
    country_code: str = Field(regex="^[A-Z]{2}$")
    service_id: int = Field(gt=0)
    
    @validator('country_code')
    def validate_country(cls, v):
        # Check against allowed countries
        if v not in ALLOWED_COUNTRIES:
            raise ValueError(f'Country {v} not supported')
        return v

class RegisterRequest(BaseModel):
    email: str = Field(regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        # Must contain uppercase, lowercase, digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        return v
```

---

### 5. Security Headers (MEDIUM)

#### Implementation
**Priority**: P2  
**Time**: 0.5 days

```python
# app/middleware/security_headers.py

from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.paystack.co; "
            "frame-ancestors 'none';"
        )
        
        # Strict Transport Security
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response

# Add to app
app.add_middleware(SecurityHeadersMiddleware)
```

---

### 6. Authentication Hardening (MEDIUM)

#### JWT Security
**Priority**: P2  
**Time**: 0.5 days

```python
# app/core/security.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets

# Secure JWT configuration
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = secrets.token_urlsafe(32)  # Generate strong key
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check if token is revoked
        jti = payload.get("jti")
        if is_token_revoked(jti):
            raise JWTError("Token revoked")
        
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### Session Management
```python
# app/services/auth_service.py

class AuthService:
    async def logout(self, token: str):
        """Revoke token on logout"""
        payload = verify_token(token)
        jti = payload.get("jti")
        
        # Store revoked token in Redis
        await redis.setex(
            f"revoked:{jti}",
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "1"
        )
    
    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked"""
        return await redis.exists(f"revoked:{jti}")
```

---

## 🔍 Security Scanning

### Automated Scans
**Schedule**: Daily in CI/CD

```bash
# Python security
bandit -r app/ -f json -o bandit-report.json

# Dependency vulnerabilities
safety check --json > safety-report.json
pip-audit --format json > pip-audit-report.json

# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -J zap-report.json

# Secrets scanning
trufflehog filesystem . --json > trufflehog-report.json
```

### Manual Security Review
**Schedule**: Weekly

- [ ] Review authentication flows
- [ ] Check authorization logic
- [ ] Audit database queries
- [ ] Review API endpoints
- [ ] Check error messages (no info leakage)
- [ ] Verify logging (no sensitive data)

---

## 📋 Security Checklist

### Authentication & Authorization
- [x] Bcrypt password hashing (cost factor 12)
- [x] JWT tokens with expiration
- [ ] Token revocation on logout
- [ ] Refresh token rotation
- [ ] OAuth2 state parameter validation
- [ ] Account lockout after failed attempts

### Data Protection
- [x] HTTPS enforced
- [ ] Database encryption at rest
- [ ] Sensitive data not logged
- [ ] PII data minimization
- [ ] Secure cookie flags (httponly, secure, samesite)

### API Security
- [ ] Rate limiting on all endpoints
- [ ] CSRF protection
- [ ] Input validation
- [ ] Output encoding
- [ ] API key rotation
- [ ] Webhook signature verification

### Infrastructure
- [ ] Security headers
- [ ] CORS configuration
- [ ] Error handling (no stack traces)
- [ ] Dependency updates
- [ ] Security patches applied

---

## 🚨 Incident Response

### Security Incident Procedure

1. **Detect**: Monitoring alerts, user reports
2. **Contain**: Disable affected endpoints, revoke tokens
3. **Investigate**: Review logs, identify root cause
4. **Remediate**: Apply fixes, deploy patches
5. **Communicate**: Notify affected users
6. **Learn**: Post-mortem, update procedures

### Emergency Contacts
- Security Lead: [email]
- DevOps: [email]
- Legal: [email]

---

## 📊 Implementation Timeline

### Week 1: Critical Fixes
**Days 1-2**: Payment Security
- Race condition fixes
- Webhook signature verification
- Idempotency enforcement

**Days 3-4**: Rate Limiting & CSRF
- Global rate limiter
- Endpoint-specific limits
- CSRF middleware

**Day 5**: Security Headers
- CSP, HSTS, X-Frame-Options
- Security middleware

### Week 2: Hardening
**Days 1-2**: Input Validation
- Pydantic models
- Custom validators
- Error messages

**Days 3-4**: Auth Hardening
- Token revocation
- Session management
- Account lockout

**Day 5**: Security Scanning
- Automated scans
- Manual review
- Documentation

---

## ✅ Success Criteria

- ✅ Zero critical vulnerabilities
- ✅ All endpoints rate-limited
- ✅ CSRF protection enabled
- ✅ Security headers implemented
- ✅ Payment race conditions fixed
- ✅ Automated security scans passing
- ✅ Security documentation complete

---

**Next Steps**: Start with payment security (highest risk)
