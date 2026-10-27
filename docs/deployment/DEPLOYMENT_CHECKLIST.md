# Vrenum — Deployment Checklist

**Stack:** Mac → rsync → VPS (`root@169.255.57.146`) → Docker Compose  
**Last Updated:** October 26, 2026

---

## Pre-deploy (Mac)

- [ ] All changes committed and pushed to GitHub
- [ ] No credentials or `.env` files in git: `git ls-files | grep -i env`
- [ ] Tests passing locally: `pytest --cov=app -q`
- [ ] Version bumped in `app/core/config.py` and `CHANGELOG.md`

---

## Deploy

```bash
bash scripts/deploy.sh
```

Confirm output ends with:
- `✔ Container vrenum-app  Healthy`
- `✔ Container vrenum-nginx  Started`
- Health check returns `{"status": "healthy"}`

---

## Post-deploy verification

```bash
# 1. Full health check
curl -s https://vrenum.app/api/monitoring/health/detailed | python3 -m json.tool

# 2. Redis must say "redis" not "memory"
# Look for: "cache": { "backend": "redis" }

# 3. TextVerified balance must be above $10
# Look for: "textverified": { "balance": XX.XX }

# 4. Check Sentry for new errors
# https://dev-vp.sentry.io/issues/ → sort by "First Seen"

# 5. Check uptime monitor
# https://uptime.betterstack.com/team/t545038/monitors/4422808
```

---

## After changing .env.production on VPS

Plain restart does NOT reload env vars. Always force-recreate:

```bash
ssh root@169.255.57.146 "cd ~/vrenum && docker compose up -d --force-recreate"

# Verify the var loaded
ssh root@169.255.57.146 "cd ~/vrenum && docker compose exec app printenv <KEY_NAME>"
```

---

## Required env vars on VPS

All live in `~/vrenum/.env.production` on the server. Reference template: `.env.production.example` in repo root.

| Key | Purpose | Status |
|-----|---------|--------|
| `DATABASE_URL` | Neon PostgreSQL | ✅ |
| `REDIS_URL` | Upstash Redis | ✅ |
| `SECRET_KEY` | JWT signing | ✅ |
| `JWT_SECRET_KEY` | JWT signing | ✅ |
| `TEXTVERIFIED_API_KEY` | SMS provider | ✅ |
| `TEXTVERIFIED_EMAIL` | SMS provider auth | ✅ |
| `PAYSTACK_SECRET_KEY` | Payments | ✅ |
| `PAYSTACK_PUBLIC_KEY` | Payments | ✅ |
| `RESEND_API_KEY` | Email sending | ✅ |
| `SENTRY_DSN` | Error tracking | ✅ |
| `TELEGRAM_BOT_TOKEN` | SMS forwarding bot | ✅ |
| `ADMIN_EMAIL` | Admin account | ✅ |
| `ADMIN_NOTIFY_EMAIL` | Revenue-zero alerts | ✅ `vrenum.proton.me` (confirmed Oct 26 2026) |
| `ONESIGNAL_APP_ID` | Push notifications | ✅ |
| `ONESIGNAL_API_KEY` | Push notifications | ✅ |
| `GOOGLE_CLIENT_ID` | OAuth | ✅ |
| `GOOGLE_CLIENT_SECRET` | OAuth | ✅ |

---

## Rollback

```bash
# Revert last commit on Mac and redeploy
git revert HEAD
bash scripts/deploy.sh
```

---

## Credential rotation schedule

| Credential | Rotate every |
|-----------|-------------|
| `JWT_SECRET_KEY`, `SECRET_KEY` | 90 days |
| `TEXTVERIFIED_API_KEY`, `PAYSTACK_SECRET_KEY` | 180 days |
| `RESEND_API_KEY` | 180 days |
| SSL cert | Auto-renewed by certbot container |

To rotate: edit `~/vrenum/.env.production` on VPS → force-recreate.

---

**Status:** ✅ Production Ready (v4.9.1)  
**Last Deploy:** October 26, 2026
