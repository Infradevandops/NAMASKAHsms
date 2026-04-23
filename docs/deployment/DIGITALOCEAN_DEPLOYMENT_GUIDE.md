# DigitalOcean Deployment Guide - Namaskah Platform

**Version**: 4.4.2  
**Date**: March 20, 2026  
**Deployment Time**: ~60 minutes

---

## 🎯 RECOMMENDED CONFIGURATION

### ⭐ Best Choice: $24/month Droplet

```
vCPU:            2 cores
RAM:             4 GB
Storage:         80 GB SSD
Bandwidth:       4 TB/month
Region:          NYC3 or SFO3
OS:              Ubuntu 22.04 LTS

Additional Services:
+ PostgreSQL:    $15/month (1GB, managed)
+ Redis:         $15/month (1GB, managed)
───────────────────────────────────────
Total:           $54/month
```

**Supports**: 1,000-5,000 users comfortably

---

## 🚀 QUICK DEPLOYMENT (10 Steps)

### 1. Create Droplet (5 min)

```bash
# Via DigitalOcean Console:
- Image: Ubuntu 22.04 LTS
- Plan: Basic $24/month (2 vCPU, 4GB)
- Region: NYC3
- Authentication: SSH Key
- Hostname: namaskah-prod
```

### 2. Initial Setup (10 min)

```bash
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Create user
adduser namaskah
usermod -aG sudo namaskah
rsync --archive --chown=namaskah:namaskah ~/.ssh /home/namaskah
su - namaskah

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql-client redis-tools nginx git \
    build-essential libpq-dev
```

### 3. Setup Databases (10 min)

```bash
# Create Managed PostgreSQL (via console):
- Type: PostgreSQL 15
- Plan: $15/month (1GB)
- Region: NYC3
- Name: namaskah-db

# Create Managed Redis (via console):
- Type: Redis 7
- Plan: $15/month (1GB)
- Region: NYC3
- Name: namaskah-redis

# Add droplet IP to trusted sources in both databases
```

### 4. Deploy Application (15 min)

```bash
cd /home/namaskah
git clone YOUR_REPO_URL namaskah-sms
cd namaskah-sms

# Setup virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env.production
cat > .env.production << 'EOF'
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://USER:PASS@HOST:PORT/namaskah_production?sslmode=require
REDIS_URL=redis://:PASS@HOST:PORT/0
SECRET_KEY=GENERATE_32_CHAR_KEY
JWT_SECRET_KEY=GENERATE_32_CHAR_KEY
BASE_URL=https://yourdomain.com
TEXTVERIFIED_API_KEY=your_key
PAYSTACK_SECRET_KEY=your_key
EOF

# Generate keys
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Run migrations
alembic upgrade head
```

### 5. Setup Systemd Service (5 min)

```bash
sudo nano /etc/systemd/system/namaskah.service
```

```ini
[Unit]
Description=Namaskah SMS Platform
After=network.target

[Service]
Type=notify
User=namaskah
WorkingDirectory=/home/namaskah/namaskah-sms
Environment="PATH=/home/namaskah/namaskah-sms/.venv/bin"
EnvironmentFile=/home/namaskah/namaskah-sms/.env.production
ExecStart=/home/namaskah/namaskah-sms/.venv/bin/gunicorn main:app \
    --workers 5 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/namaskah
sudo chown namaskah:namaskah /var/log/namaskah
sudo systemctl enable namaskah
sudo systemctl start namaskah
```

### 6. Setup Nginx (10 min)

```bash
sudo nano /etc/nginx/sites-available/namaskah
```

```nginx
upstream namaskah_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /home/namaskah/namaskah-sms/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://namaskah_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/namaskah /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Setup SSL (5 min)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo certbot renew --dry-run
```

### 8. Setup Firewall (2 min)

```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 9. Setup Backups (3 min)

```bash
cat > /home/namaskah/backup.sh << 'EOF'
#!/bin/bash
tar -czf /home/namaskah/backups/app_$(date +%Y%m%d).tar.gz \
    /home/namaskah/namaskah-sms \
    --exclude='.venv' --exclude='.git'
find /home/namaskah/backups -mtime +7 -delete
EOF

chmod +x /home/namaskah/backup.sh
mkdir -p /home/namaskah/backups

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /home/namaskah/backup.sh") | crontab -
```

### 10. Verify (5 min)

```bash
# Check services
sudo systemctl status namaskah
sudo systemctl status nginx

# Test endpoints
curl https://yourdomain.com/health
curl https://yourdomain.com/api/diagnostics

# Monitor
htop
```

---

## 📊 SCALING GUIDE

### When to Upgrade

```
CPU > 70%:       Upgrade to 4 vCPU ($48/month)
RAM > 80%:       Upgrade to 8 GB RAM
Response > 1s:   Add more workers or upgrade
Users > 5,000:   Upgrade to 4 vCPU, 8GB RAM
```

### Upgrade Path

```
Current:  2 vCPU, 4GB  ($24/month) → 1,000-5,000 users
Next:     4 vCPU, 8GB  ($48/month) → 5,000-20,000 users
Scale:    8 vCPU, 16GB ($96/month) → 20,000-50,000 users
```

---

## 🔧 MAINTENANCE

### Update Application

```bash
cd /home/namaskah/namaskah-sms
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl reload namaskah
```

### Monitor Logs

```bash
# Application logs
sudo journalctl -u namaskah -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Access logs
sudo tail -f /var/log/nginx/access.log
```

### Database Maintenance

```bash
# Backups are automatic (daily, 7-day retention)
# Access via DigitalOcean console

# Manual backup
pg_dump "postgresql://USER:PASS@HOST:PORT/namaskah_production" > backup.sql
```

---

## 💰 COST BREAKDOWN

```
Droplet (2 vCPU, 4GB):     $24/month
PostgreSQL (1GB):          $15/month
Redis (1GB):               $15/month
Domain:                    $12/year ($1/month)
SSL:                       $0 (Let's Encrypt)
Backups:                   $0 (included)
───────────────────────────────────────
Total:                     $55/month
```

**Per User Cost**: $0.011/month (at 5,000 users)

---

## 🆘 TROUBLESHOOTING

### Service Won't Start

```bash
sudo systemctl status namaskah
sudo journalctl -u namaskah -n 50
# Check DATABASE_URL and permissions
```

### High CPU

```bash
htop
# Reduce workers in systemd service
# Or upgrade droplet
```

### Database Connection Failed

```bash
# Check trusted sources in DO console
# Verify DATABASE_URL format
# Test: psql "DATABASE_URL"
```

### SSL Issues

```bash
sudo certbot renew
sudo certbot certificates
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] Application accessible via HTTPS
- [ ] Health endpoint returns 200
- [ ] User registration works
- [ ] SMS verification works
- [ ] Payment processing works
- [ ] Logs are clean
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Firewall enabled
- [ ] SSL auto-renewal tested

---

**Total Setup Time**: ~60 minutes  
**Difficulty**: Intermediate  
**Cost**: $55/month  
**Supports**: 1,000-5,000 users
