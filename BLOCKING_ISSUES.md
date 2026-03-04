# Blocking Issues

Issues that prevent clean startup / deployment.

---

## 🔴 CRITICAL — Startup Blockers

> All critical blockers resolved. See ✅ section below.

---

## ✅ Already Fixed (this session)

- `GET /api/verification/textverified/balance` → 404 (URL corrected in `balance.html`)
- `TextVerifiedService` re-initializing on every request (singleton in `textverified_balance.py`)
- Migration `001`, `002`, `003` crashing with `DuplicateColumn` on redeploy (idempotency guards added)
- `websocket_router` registered twice in `main.py`
- `str | None` Pydantic crash on Python 3.9 (`Optional[X]` in `user_settings_endpoints.py`)
- `hash_password` missing — aliased `get_password_hash` in `user_settings.py` and `setup.py`
- `settings.smtp_host/smtp_user/from_email` → corrected to `smtp_server/smtp_username` in `email_service.py`
