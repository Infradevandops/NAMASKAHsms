# Vrenum — Deployment Quick Reference

**Stack:** Mac → GitHub → rsync → VPS (Ubuntu 24.04) → Docker Compose  
**Server:** `root@169.255.57.146`  
**App dir:** `~/vrenum/`  
**Env file:** `~/vrenum/.env.production` (on VPS only, never in repo)  
**Last Updated:** October 26, 2026

---

## Deploy (standard)

```bash
# From Mac — rsync + Docker rebuild + health check
bash scripts/deploy.sh
```

That script:
1. rsyncs all files from Mac → `root@169.255.57.146:~/vrenum/`
2. Runs `docker compose build --no-cache && docker compose up -d` on the server
3. Waits 20s then hits `/health`

---

## Force restart (after .env.production change)

Plain `docker compose restart` does NOT re-read the env file. Always use:

```bash
ssh root@169.255.57.146 "cd ~/vrenum && docker compose up -d --force-recreate"
```

---

## Common commands

```bash
# Watch live logs
ssh root@169.255.57.146 "cd ~/vrenum && docker compose logs -f app --tail=100"

# Health check
curl -s https://vrenum.app/api/monitoring/health/detailed | python3 -m json.tool

# Confirm Redis is connected (not memory fallback)
curl -s https://vrenum.app/api/monitoring/health/detailed \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['checks']['cache']['backend'])"

# Verify an env var loaded into the container
ssh root@169.255.57.146 "cd ~/vrenum && docker compose exec app printenv ADMIN_NOTIFY_EMAIL"

# Container status
ssh root@169.255.57.146 "cd ~/vrenum && docker compose ps"

# Edit env vars
ssh root@169.255.57.146 "nano ~/vrenum/.env.production"
# Then force-recreate to reload
```

---

## Env file management

```bash
# Add a new key
ssh root@169.255.57.146 "echo 'KEY=value' >> ~/vrenum/.env.production"
ssh root@169.255.57.146 "cd ~/vrenum && docker compose up -d --force-recreate"

# View all key names (values masked)
ssh root@169.255.57.146 "cat ~/vrenum/.env.production | cut -d= -f1 | sort"

# View full file
ssh root@169.255.57.146 "cat ~/vrenum/.env.production"
```

---

## Containers

| Container | Role |
|-----------|------|
| `vrenum-app` | FastAPI app (uvicorn) |
| `vrenum-nginx` | Reverse proxy + SSL termination |
| `vrenum-certbot` | Let's Encrypt cert renewal |

```bash
# Restart a single container
ssh root@169.255.57.146 "cd ~/vrenum && docker compose restart app"

# Rebuild a single container
ssh root@169.255.57.146 "cd ~/vrenum && docker compose up -d --build app"
```

---

## Rollback

```bash
# On Mac — revert last commit and redeploy
git revert HEAD
bash scripts/deploy.sh
```

---

## Background services (all start automatically in lifespan.py)

| Service | Interval | Purpose |
|---------|----------|---------|
| SMS polling | Adaptive 5–10s | Deliver SMS codes |
| Refund policy enforcer | 5 min | Backup refund for timed-out verifications |
| Health audit loop | 4 hours | Provider health checks |
| Daily growth snapshot | 24 hours | Target tracking |
| Rental expiry monitor | 15 min | Mark expired rentals |
| Abandoned payment cleanup | 1 hour | Mark stale Paystack checkouts |
| Revenue-zero monitor | Daily 18:00 UTC | Alert admin if $0 revenue |
| Digest scheduler | Daily 08:00 UTC | Send daily/weekly notification digests |

---

## Server info

```
IP:       169.255.57.146
OS:       Ubuntu 24.04.5 LTS
Disk:     76.45GB (27% used)
Memory:   ~60% used
DB:       Neon PostgreSQL (remote)
Cache:    Upstash Redis (remote, rediss://)
```

**Last Updated:** October 26, 2026
