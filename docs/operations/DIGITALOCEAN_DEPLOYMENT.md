# DigitalOcean + Cloudflare Deployment Guide

**For**: Namaskah v4.7.2+
**When to use**: When Render cold starts become a problem, or at 100+ active users
**Time to complete**: ~2 hours first time, ~30 min after that
**Monthly cost**: ~$18-24/month total

---

## Architecture

```
User
 ↓
Cloudflare (DNS + SSL + DDoS + CDN)
 ↓
DigitalOcean Droplet (Nginx + Gunicorn + Uvicorn)
 ↓                    ↓
Neon PostgreSQL    Upstash Redis
(keep as-is)       (keep as-is)
```

---

## Part 1 — Create the Droplet

### 1.1 Log into DigitalOcean
Go to https://cloud.digitalocean.com → Create → Droplets

### 1.2 Choose Region
Pick the region closest to your users:
- **West Africa / Europe**: Frankfurt (`fra1`) or Amsterdam (`ams3`)
- **US users**: New York (`nyc3`)
- **Asia**: Singapore (`sgp1`)

### 1.3 Choose Image
- **OS**: Ubuntu 22.04 LTS (x64)
- Do NOT use Docker image — we'll install manually for full control

### 1.4 Choose Size
| Users | Plan | RAM | CPU | Cost |
|-------|------|-----|-----|------|
| <100 | Basic Regular | 1GB | 1 vCPU | $6/mo |
| 100-500 | Basic Regular | 2GB | 1 vCPU | $12/mo ← **recommended start** |
| 500-2000 | Basic Regular | 4GB | 2 vCPU | $24/mo |
| 2000+ | CPU-Optimized | 8GB | 4 vCPU | $48/mo |

**Select**: 2GB / 1 vCPU / $12/mo

### 1.5 Authentication
- Select **SSH Key** (not password)
- Add your SSH public key (`~/.ssh/id_rsa.pub`)
- If you don't have one: `ssh-keygen -t rsa -b 4096`

### 1.6 Hostname
Set to: `namaskah-prod`

### 1.7 Enable Backups
- Check **Enable Backups** (+$2.40/mo) — worth it

### 1.8 Create Droplet
Click **Create Droplet**. Note the IP address shown.

---

## Part 2 — Initial Server Setup

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

### 2.1 Update system
```bash
apt update && apt upgrade -y
```

### 2.2 Create app user (never run as root)
```bash
adduser namaskah
usermod -aG sudo namaskah
# Copy SSH keys to new user
rsync --archive --chown=namaskah:namaskah ~/.ssh /home/namaskah
```

### 2.3 Configure firewall
```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
ufw status
```

### 2.4 Switch to app user
```bash
su - namaskah
```

---

## Part 3 — Install Dependencies

### 3.1 Install Python 3.11
```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
python3.11 --version  # should show 3.11.x
```

### 3.2 Install system packages
```bash
sudo apt install -y \
  nginx \
  git \
  curl \
  build-essential \
  libpq-dev \
  supervisor
```

### 3.3 Install pip
```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
```

---

## Part 4 — Deploy the Application

### 4.1 Clone the repo
```bash
cd /home/namaskah
git clone https://github.com/Infradevandops/NAMASKAHsms.git app
cd app
```

### 4.2 Create virtual environment
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Create production environment file
```bash
nano /home/namaskah/app/.env
```

Paste all values from `.env.production` — every key/value pair. Save with `Ctrl+X → Y → Enter`.

```bash
# Verify it loaded
grep ENVIRONMENT /home/namaskah/app/.env
# Should show: ENVIRONMENT=production
```

### 4.4 Run database migrations
```bash
cd /home/namaskah/app
source .venv/bin/activate
alembic upgrade head
```

---

## Part 5 — Configure Gunicorn with Supervisor

Supervisor keeps Gunicorn running and auto-restarts on crash.

### 5.1 Create supervisor config
```bash
sudo nano /etc/supervisor/conf.d/namaskah.conf
```

Paste:
```ini
[program:namaskah]
command=/home/namaskah/app/.venv/bin/gunicorn main:app
    --workers 3
    --worker-class uvicorn.workers.UvicornWorker
    --bind 127.0.0.1:8000
    --timeout 120
    --graceful-timeout 30
    --keep-alive 5
    --access-logfile /var/log/namaskah/access.log
    --error-logfile /var/log/namaskah/error.log
    --log-level info
directory=/home/namaskah/app
user=namaskah
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
environment=
    HOME="/home/namaskah",
    PATH="/home/namaskah/app/.venv/bin"
stdout_logfile=/var/log/namaskah/supervisor.log
stderr_logfile=/var/log/namaskah/supervisor_err.log
```

### 5.2 Create log directory
```bash
sudo mkdir -p /var/log/namaskah
sudo chown namaskah:namaskah /var/log/namaskah
```

### 5.3 Start supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start namaskah
sudo supervisorctl status namaskah
# Should show: namaskah    RUNNING   pid XXXXX, uptime 0:00:XX
```

### 5.4 Verify app is running
```bash
curl http://127.0.0.1:8000/health
# Should return: {"status": "healthy", "service": "namaskah-sms"}
```

---

## Part 6 — Configure Nginx

Nginx sits in front of Gunicorn, handles SSL termination (via Cloudflare) and static files.

### 6.1 Create Nginx config
```bash
sudo nano /etc/nginx/sites-available/namaskah
```

Paste:
```nginx
server {
    listen 80;
    server_name namaskah.app www.namaskah.app;

    # Static files served directly by Nginx (faster)
    location /static/ {
        alias /home/namaskah/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy everything else to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Cloudflare real IP restoration
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 131.0.72.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    real_ip_header CF-Connecting-IP;
}
```

### 6.2 Enable the site
```bash
sudo ln -s /etc/nginx/sites-available/namaskah /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t  # must say: syntax is ok
sudo systemctl reload nginx
```

---

## Part 7 — Configure Cloudflare

### 7.1 Add domain to Cloudflare
1. Go to https://dash.cloudflare.com → Add Site → enter `namaskah.app`
2. Select **Free plan**
3. Cloudflare will scan your DNS records

### 7.2 Add DNS records
In Cloudflare DNS dashboard, add:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `YOUR_DROPLET_IP` | ✅ Proxied |
| A | `www` | `YOUR_DROPLET_IP` | ✅ Proxied |

**Proxied = orange cloud** — this routes traffic through Cloudflare (DDoS protection, CDN, SSL).

### 7.3 SSL/TLS settings
Cloudflare Dashboard → SSL/TLS → Overview:
- Set mode to **Full** (not Full Strict — Nginx doesn't have a cert, Cloudflare handles it)

### 7.4 Recommended Cloudflare settings
**Speed → Optimization**:
- Auto Minify: ✅ JavaScript, CSS, HTML
- Brotli: ✅ On

**Security → Settings**:
- Security Level: Medium
- Bot Fight Mode: ✅ On

**Caching → Configuration**:
- Caching Level: Standard
- Browser Cache TTL: 4 hours

**Rules → Page Rules** (add these):
```
namaskah.app/static/*  →  Cache Level: Cache Everything, Edge TTL: 1 month
namaskah.app/api/*     →  Cache Level: Bypass
```

### 7.5 Update nameservers
Cloudflare will give you 2 nameservers (e.g. `aria.ns.cloudflare.com`).
Go to your domain registrar → update nameservers to Cloudflare's.
Propagation takes 5-30 minutes.

---

## Part 8 — Update App Config for Droplet

### 8.1 Update CORS in .env
```bash
nano /home/namaskah/app/.env
```
Change:
```
CORS_ORIGINS=https://namaskah.app,https://www.namaskah.app
BASE_URL=https://namaskah.app
```

### 8.2 Update workers based on droplet size
Edit `/etc/supervisor/conf.d/namaskah.conf`:
```
# 1GB droplet:  --workers 2
# 2GB droplet:  --workers 3  ← default
# 4GB droplet:  --workers 5
# Formula: (2 × CPU cores) + 1
```

### 8.3 Restart app
```bash
sudo supervisorctl restart namaskah
```

---

## Part 9 — Verify Everything Works

```bash
# App health
curl https://namaskah.app/health

# Check Cloudflare is proxying (should see CF-Ray header)
curl -I https://namaskah.app | grep -i "cf-ray\|server"

# Check logs
sudo tail -f /var/log/namaskah/access.log
sudo tail -f /var/log/namaskah/error.log

# Check supervisor status
sudo supervisorctl status
```

---

## Part 10 — Auto-Deploy on Git Push (Optional)

Set up a deploy script so `git push` auto-deploys:

### 10.1 Create deploy script
```bash
nano /home/namaskah/deploy.sh
```

```bash
#!/bin/bash
set -e
echo "🚀 Deploying Namaskah..."

cd /home/namaskah/app
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt --quiet
alembic upgrade head
sudo supervisorctl restart namaskah

echo "✅ Deploy complete"
curl -s http://127.0.0.1:8000/health
```

```bash
chmod +x /home/namaskah/deploy.sh
```

### 10.2 Run deploy
```bash
/home/namaskah/deploy.sh
```

---

## Maintenance Commands

```bash
# Restart app
sudo supervisorctl restart namaskah

# View live logs
sudo tail -f /var/log/namaskah/error.log

# Check app status
sudo supervisorctl status namaskah

# Deploy new code
/home/namaskah/deploy.sh

# Check Nginx
sudo nginx -t && sudo systemctl reload nginx

# Check disk space
df -h

# Check memory
free -h

# Check CPU
htop
```

---

## Migrating from Render

When ready to cut over from Render:

1. Run deploy on droplet, verify everything works at the IP
2. In Cloudflare DNS, point `A` records to droplet IP (already done in Part 7)
3. Update `BASE_URL` and `CORS_ORIGINS` in droplet `.env`
4. Test: `curl https://namaskah.app/health`
5. Keep Render running for 24h as fallback
6. Once confirmed stable, disable Render auto-deploy

**Keep Neon and Upstash** — both work from any server, no migration needed.

---

## Cost Summary

| Service | Plan | Cost |
|---------|------|------|
| DigitalOcean Droplet | 2GB Basic | $12/mo |
| DigitalOcean Backups | 20% of droplet | $2.40/mo |
| Cloudflare | Free | $0/mo |
| Neon PostgreSQL | Free tier | $0/mo |
| Upstash Redis | Free tier | $0/mo |
| **Total** | | **~$14.40/mo** |

vs Render paid plan (~$25/mo) with less control.

---

*Last updated: May 15, 2026 — Namaskah v4.7.2*
