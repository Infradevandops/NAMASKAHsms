# VRENUM SMS - Linux VPS Deployment Guide

**Version**: 4.8.2
**Target**: Ubuntu 22.04 LTS with Docker
**Time**: ~30 minutes

---

## Prerequisites

- Ubuntu 22.04 LTS VPS (2GB+ RAM recommended)
- Domain pointing to your VPS IP
- SSH access to the server

---

## Quick Start

### 1. SSH into your server
```bash
ssh root@YOUR_SERVER_IP
```

### 2. Run the deployment script
```bash
curl -fsSL https://raw.githubusercontent.com/Infradevandops/NAMASKAHsms/main/deploy.sh | bash
```

Or manually:
```bash
git clone https://github.com/Infradevandops/NAMASKAHsms.git /home/vrenum/app
cd /home/vrenum/app
chmod +x deploy.sh
./deploy.sh
```

### 3. Configure environment
```bash
cd /home/vrenum/app
nano .env
```

Fill in your credentials (see `.env.production.example`).

### 4. Setup SSL
```bash
./scripts/setup-ssl.sh vrenum.app your@email.com
```

### 5. Start the application
```bash
docker compose up -d
```

---

## Manual Installation

### Step 1: Update System
```bash
apt update && apt upgrade -y
```

### Step 2: Install Docker
```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
apt install -y docker-compose-plugin
```

### Step 3: Create App User
```bash
useradd -m -s /bin/bash vrenum
usermod -aG docker vrenum
```

### Step 4: Configure Firewall
```bash
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Step 5: Clone Repository
```bash
su - vrenum
git clone https://github.com/Infradevandops/NAMASKAHsms.git ~/app
cd ~/app
```

### Step 6: Configure Environment
```bash
cp .env.production.example .env
nano .env
```

**Required variables:**
- `SECRET_KEY` - Generate with `openssl rand -hex 32`
- `JWT_SECRET_KEY` - Generate with `openssl rand -hex 32`
- `POSTGRES_PASSWORD` - Strong database password
- `TEXTVERIFIED_API_KEY` - From TextVerified dashboard
- `PAYSTACK_SECRET_KEY` - From Paystack dashboard

### Step 7: Start Services
```bash
docker compose up -d
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Internet                            │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 Nginx (Port 80/443)                      │
│              SSL Termination + Reverse Proxy             │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              VRENUM App (Port 8000)                      │
│           Gunicorn + Uvicorn Workers                     │
└──────────┬─────────────────────────────┬────────────────┘
           │                             │
           ▼                             ▼
┌──────────────────────┐    ┌──────────────────────┐
│   PostgreSQL 15      │    │      Redis 7         │
│   (Database)         │    │   (Cache/Sessions)   │
└──────────────────────┘    └──────────────────────┘
```

---

## Common Commands

### Service Management
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart application
docker compose restart app

# View logs
docker compose logs -f app
docker compose logs -f nginx

# Check status
docker compose ps
```

### Database
```bash
# Backup database
./scripts/backup-db.sh

# Access database shell
docker compose exec db psql -U vrenum

# Run migrations
docker compose exec app alembic upgrade head
```

### Maintenance
```bash
# Update application
cd /home/vrenum/app
git pull origin main
docker compose up -d --build

# Check disk space
df -h

# Check memory
free -h

# View container resources
docker stats
```

---

## SSL Certificate

### Initial Setup
```bash
./scripts/setup-ssl.sh vrenum.app admin@vrenum.app
```

### Manual Renewal
```bash
docker compose run --rm certbot renew
docker compose restart nginx
```

Certificates auto-renew via the certbot container.

---

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Application Logs
```bash
# Real-time logs
docker compose logs -f app

# Last 100 lines
docker compose logs --tail=100 app
```

### Resource Usage
```bash
docker stats --no-stream
```

---

## Backup & Restore

### Automated Backups
Add to crontab (`crontab -e`):
```bash
# Daily backup at 2 AM
0 2 * * * /home/vrenum/app/scripts/backup-db.sh
```

### Manual Backup
```bash
./scripts/backup-db.sh
```

### Restore from Backup
```bash
gunzip -c backups/db/vrenum_backup_YYYYMMDD.sql.gz | \
  docker compose exec -T db psql -U vrenum
```

---

## Troubleshooting

### App won't start
```bash
# Check logs
docker compose logs app

# Check if database is ready
docker compose exec db pg_isready -U vrenum

# Check environment
docker compose exec app env | grep -E "DATABASE|REDIS"
```

### Database connection issues
```bash
# Restart database
docker compose restart db

# Check database logs
docker compose logs db
```

### SSL issues
```bash
# Check certificate
openssl s_client -connect vrenum.app:443 -servername vrenum.app

# Renew certificate
docker compose run --rm certbot renew --force-renewal
docker compose restart nginx
```

### Out of memory
```bash
# Check memory usage
free -h
docker stats --no-stream

# Reduce workers in .env
WORKERS=1
docker compose up -d
```

---

## Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Enable UFW firewall
- [ ] Setup SSH key authentication
- [ ] Disable root SSH login
- [ ] Enable automatic security updates
- [ ] Setup fail2ban (optional)
- [ ] Configure backup rotation

---

## Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB |
| Storage | 40 GB | 80 GB |
| Bandwidth | 1 TB | Unlimited |

---

## Support

- **Documentation**: https://vrenum.app/docs
- **Issues**: https://github.com/Infradevandops/NAMASKAHsms/issues
- **Email**: support@vrenum.app
