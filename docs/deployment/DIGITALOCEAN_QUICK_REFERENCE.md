# DigitalOcean Quick Reference - Namaskah

## 🎯 RECOMMENDED SETUP

```
Droplet:         $24/month (2 vCPU, 4GB RAM, 80GB SSD)
PostgreSQL:      $15/month (1GB, managed)
Redis:           $15/month (1GB, managed)
Total:           $54/month
Supports:        1,000-5,000 users
```

## 📋 DEPLOYMENT CHECKLIST

```bash
# 1. Create droplet (Ubuntu 22.04, 2 vCPU, 4GB)
# 2. Create managed PostgreSQL
# 3. Create managed Redis
# 4. SSH and setup user
ssh root@IP
adduser namaskah
usermod -aG sudo namaskah

# 5. Install dependencies
sudo apt update && sudo apt install -y python3.11 python3.11-venv \
    postgresql-client nginx git build-essential libpq-dev

# 6. Clone and setup
cd /home/namaskah
git clone REPO namaskah-sms
cd namaskah-sms
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 7. Configure environment
# Create .env.production with DB credentials

# 8. Run migrations
alembic upgrade head

# 9. Setup systemd service
# Copy service file to /etc/systemd/system/namaskah.service
sudo systemctl enable namaskah
sudo systemctl start namaskah

# 10. Setup Nginx + SSL
# Configure Nginx, install certbot, get SSL
sudo certbot --nginx -d yourdomain.com

# 11. Enable firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# 12. Verify
curl https://yourdomain.com/health
```

## 🔧 COMMON COMMANDS

```bash
# Service management
sudo systemctl status namaskah
sudo systemctl restart namaskah
sudo systemctl reload namaskah

# View logs
sudo journalctl -u namaskah -f
sudo tail -f /var/log/nginx/error.log

# Update application
cd /home/namaskah/namaskah-sms
git pull
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl reload namaskah

# Monitor resources
htop
df -h
free -h
```

## 📊 SCALING TRIGGERS

```
Upgrade when:
- CPU > 70% sustained
- RAM > 80% sustained
- Response time > 1 second
- Users > 5,000

Next tier: $48/month (4 vCPU, 8GB RAM)
```

## 🆘 QUICK FIXES

```bash
# Service won't start
sudo systemctl status namaskah
sudo journalctl -u namaskah -n 50

# Database connection failed
# Add droplet IP to trusted sources in DO console

# High CPU
# Reduce workers in /etc/systemd/system/namaskah.service

# SSL expired
sudo certbot renew

# Out of disk space
df -h
sudo journalctl --vacuum-time=7d
find /var/log -name "*.gz" -delete
```

## 💰 COST OPTIMIZATION

```
Current:  $54/month (recommended)
Minimum:  $27/month (1 vCPU, 2GB, no Redis)
Maximum:  $206/month (8 vCPU, 16GB, multi-region)

Break-even: ~4 paying users
```

---

**Full Guide**: docs/deployment/DIGITALOCEAN_DEPLOYMENT_GUIDE.md
