# Blocking Issues

Issues that prevent clean startup / deployment.

---

## 🔴 CRITICAL — Startup Blockers

### 1. `hash_password` missing from `app/utils/security.py`
- **File**: `app/api/core/user_settings.py:9`
- **Error**: `ImportError: cannot import name 'hash_password' from 'app.utils.security'`
- **Root cause**: `security.py` exports `get_password_hash`, not `hash_password`. `user_settings.py` imports the wrong name.
- **Fix**: Change line 9 of `user_settings.py`:
  ```python
  # Before
  from app.utils.security import hash_password, verify_password
  # After
  from app.utils.security import get_password_hash as hash_password, verify_password
  ```
- **Also affected**: `app/api/core/setup.py:6` imports `hash_password` from `app.core.auth_security` — that file has no such function either. Same alias fix needed.

---

### 2. `settings.smtp_host` attribute missing
- **File**: `app/services/email_service.py:23`
- **Error**: `AttributeError: 'Settings' object has no attribute 'smtp_host'`
- **Root cause**: `config.py` defines `smtp_server`, but `email_service.py` reads `settings.smtp_host`.
- **Blocks**: `app/api/core/forwarding.py` (imported at startup via `main.py`)
- **Fix**: Change `email_service.py:23`:
  ```python
  # Before
  self.smtp_host = settings.smtp_host
  # After
  self.smtp_host = settings.smtp_server
  ```

---

## 🟡 HIGH — Will Fail Under Load / On Fresh Deploy

### 3. Migration chain not stamped on fresh DB
- **Files**: `alembic/versions/`
- **Risk**: On a brand-new database, `alembic upgrade head` must run all 7 migrations in order. If the DB `alembic_version` row is missing or points to a stale revision, migrations silently skip.
- **Action**: After next deploy, run on production:
  ```bash
  alembic current
  alembic heads
  ```
  Both should return `003_payment_idempotency`. If not, run `alembic stamp head` then `alembic upgrade head`.

### 4. `app/api/core/setup.py` imports `hash_password` from `app.core.auth_security`
- **File**: `app/api/core/setup.py:6`
- **Error**: `ImportError: cannot import name 'hash_password' from 'app.core.auth_security'`
- **Root cause**: `auth_security.py` has no `hash_password` function.
- **Fix**:
  ```python
  # Before
  from app.core.auth_security import hash_password
  # After
  from app.utils.security import get_password_hash as hash_password
  ```

---

## 🟢 LOW — Non-blocking but should be cleaned up

### 5. `app/core/startup.py` alias is correct but fragile
- **File**: `app/core/startup.py:10`
- `from app.utils.security import get_password_hash as hash_password` — this works, but is inconsistent with the broken imports in items 1 and 4 above. No fix needed, just awareness.

---

## ✅ Already Fixed (this session)

- `GET /api/verification/textverified/balance` → 404 (URL corrected in `balance.html`)
- `TextVerifiedService` re-initializing on every request (singleton in `textverified_balance.py`)
- Migration `001`, `002`, `003` crashing with `DuplicateColumn` on redeploy (idempotency guards added)
- `websocket_router` registered twice in `main.py`
- `str | None` Pydantic crash on Python 3.9 (`Optional[X]` in `user_settings_endpoints.py`)
