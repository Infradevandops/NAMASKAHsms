# Credential Security - CWE-798, CWE-259 Fix

**Issue**: Hardcoded JWT tokens in `token.json`  
**Severity**: CRITICAL  
**Status**: ✅ FIXED

---

## What Was Fixed

### Before (Vulnerable)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {"id": "...", "email": "admin@namaskah.app"}
}
```
**Risk**: Token exposed in version control, can be used to impersonate users

### After (Secure)
```json
{
  "access_token": "USE_ENVIRONMENT_VARIABLE",
  "token_type": "bearer",
  "user": null,
  "note": "DO NOT COMMIT REAL TOKENS"
}
```

---

## Secure Credential Management

### 1. Environment Variables (.env)
```bash
# .env (NEVER commit this file)
JWT_TOKEN=your-actual-token-here
ADMIN_EMAIL=admin@namaskah.app
```

### 2. Load Credentials in Code
```python
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('JWT_TOKEN')
if not token:
    raise ValueError("JWT_TOKEN not set in environment")
```

### 3. For Testing Only
```python
# tests/conftest.py
import pytest
import os

@pytest.fixture
def test_token():
    """Use test token only in tests, never in production"""
    return "test-token-only-for-testing"
```

---

## Best Practices

✅ **DO**:
- Store tokens in environment variables
- Use `.env` files (add to `.gitignore`)
- Use AWS Secrets Manager for production
- Rotate tokens regularly
- Use short-lived tokens (JWT exp)
- Log token usage (without exposing token)

❌ **DON'T**:
- Commit tokens to git
- Hardcode credentials in code
- Share tokens in chat/email
- Use long-lived tokens
- Log full token values
- Store in plain text files

---

## Implementation

### Step 1: Create .env.example
```bash
# .env.example (safe to commit)
JWT_TOKEN=your-token-here
ADMIN_EMAIL=admin@example.com
DATABASE_URL=postgresql://user:pass@host/db
```

### Step 2: Update .env (never commit)
```bash
# .env (in .gitignore)
JWT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ADMIN_EMAIL=admin@namaskah.app
```

### Step 3: Load in Application
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    jwt_token: str = ""
    admin_email: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Verification

```bash
# Check token.json is in .gitignore
grep "token.json" .gitignore

# Verify no real tokens in git
git log -p --all -- token.json | grep -i "eyJ"

# Scan for exposed credentials
detect-secrets scan --all-files
```

---

## CWE References

- **CWE-798**: Use of Hard-Coded Credentials
- **CWE-259**: Use of Hard-Coded Password
- **CWE-798 Mitigation**: Use environment variables, secure vaults

---

## Status

✅ Hardcoded token removed  
✅ Placeholder added  
✅ .gitignore configured  
✅ Documentation created  

**Next**: Implement environment variable loading in application startup
