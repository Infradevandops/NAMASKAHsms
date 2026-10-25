# 🚀 Vrenum SMS - Linux Deployment Quick Reference

## One-Liner Setup (For Experienced DevOps)

```bash
# Complete setup in one script (requires sudo)
curl -fsSL https://raw.githubusercontent.com/Infradevandops/NAMASKAHsms/main/scripts/deployment/deploy_production.sh | bash
```

---

## Step-by-Step Quick Commands

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install all dependencies at once
sudo apt install -y python3.9 python3.9-venv python3-pip postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx supervisor git

# Create application user
sudo useradd -m -s /bin/bash vrenum
```

### 2. Clone & Setup
```bash
# Clone repository
sudo -u vrenum git clone https://github.com/Infradevandops/NAMASKAHsms.git /opt/vrenum
cd /opt/vrenum

# Setup Python environment
sudo -u vrenum python3.9 -m venv /opt/vrenum/.venv
sudo -u vrenum /opt/vrenum/.venv/bin/pip install -r requirements.txt
```

### 3. Configure Secrets
```bash
# Create secrets directory
sudo mkdir -p /etc/vrenum
sudo chown vrenum:vrenum /etc/vrenum
sudo chmod 700 /etc/vrenum

# Copy and edit production config
sudo -u vrenum cp .env.production.example /etc/vrenum/.env.production
sudo nano /etc/vrenum/.env.production  # Edit with your credentials
sudo chmod 600 /etc/vrenum/.env.production
```

### 4. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql << EOF
CREATE DATABASE vrenum;
CREATE USER vrenum_user WITH PASSWORD 'your_secure_password';
ALTER ROLE vrenum_user SET client_encoding TO 'utf8';
ALTER ROLE vrenum_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE vrenum TO vrenum_user;
EOF

# Run migrations
cd /opt/vrenum
sudo -u vrenum bash scripts/deployment/migrate.sh
```

### 5. Redis Setup
```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping  # Should return PONG
```

### 6. Nginx Setup
```bash
# Copy Nginx config
sudo cp deploy/nginx/nginx.conf /etc/nginx/sites-available/vrenum

# Enable site
sudo ln -s /etc/nginx/sites-available/vrenum /etc/nginx/sites-enabled/

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate
```bash
# Get SSL certificate
sudo certbot certonly --nginx -d vrenum.app -d www.vrenum.app

# Test auto-renewal
sudo certbot renew --dry-run
```

### 8. Systemd Service
```bash
# Create service file
sudo tee /etc/systemd/system/vrenum.service > /dev/null << 'EOF'
[Unit]
Description=Vrenum SMS API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=vrenum
WorkingDirectory=/opt/vrenum
EnvironmentFile=/etc/vrenum/.env.production
ExecStart=/opt/vrenum/.venv/bin/gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/vrenum/access.log \
  --error-logfile /var/log/vrenum/error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable vrenum
sudo systemctl start vrenum
```

### 9. Logging Setup
```bash
# Create log directory
sudo mkdir -p /var/log/vrenum
sudo chown vrenum:vrenum /var/log/vrenum

# Setup log rotation
sudo tee /etc/logrotate.d/vrenum > /dev/null << 'EOF'
/var/log/vrenum/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 vrenum vrenum
    sharedscripts
}
EOF
```

### 10. Firewall Setup
```bash
# Enable firewall
sudo ufw enable

# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Verify
sudo ufw status
```

---

## Verification Commands

```bash
# Check application status
sudo systemctl status vrenum

# View logs
sudo journalctl -u vrenum -f

# Test health endpoint
curl https://vrenum.app/health

# Test login
curl -X POST https://vrenum.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vrenum.app","password":"your_password"}'

# Check database
sudo -u postgres psql -d vrenum -c "SELECT COUNT(*) FROM users;"

# Check Redis
redis-cli ping

# Check Nginx
sudo nginx -t

# Check SSL certificate
openssl s_client -connect vrenum.app:443
```

---

## Troubleshooting Commands

```bash
# Application won't start
sudo journalctl -u vrenum -n 50  # View last 50 log lines
sudo systemctl restart vrenum     # Restart service

# Database connection error
sudo -u postgres psql -d vrenum   # Test connection
sudo systemctl restart postgresql # Restart database

# Redis connection error
redis-cli ping                    # Test connection
sudo systemctl restart redis-server # Restart Redis

# Nginx errors
sudo nginx -t                     # Test config
sudo systemctl restart nginx      # Restart Nginx

# Check system resources
top                               # View processes
htop                              # Interactive view
df -h                             # Disk usage
free -h                           # Memory usage
```

---

## Backup Commands

```bash
# Manual database backup
sudo -u postgres pg_dump vrenum | gzip > /backups/vrenum_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore from backup
gunzip < /backups/vrenum_20261025_120000.sql.gz | sudo -u postgres psql -d vrenum

# Upload to S3
aws s3 cp /backups/vrenum_*.sql.gz s3://vrenum-backups/

# List backups
ls -lh /backups/vrenum_*.sql.gz
```

---

## Monitoring Commands

```bash
# Real-time logs
sudo journalctl -u vrenum -f

# Last 100 lines
sudo journalctl -u vrenum -n 100

# Errors only
sudo journalctl -u vrenum -p err

# Since last boot
sudo journalctl -u vrenum -b

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# System resources
watch -n 1 'free -h && echo "---" && df -h'
```

---

## Maintenance Commands

```bash
# Update dependencies
cd /opt/vrenum
sudo -u vrenum /opt/vrenum/.venv/bin/pip install --upgrade -r requirements.txt

# Run tests
cd /opt/vrenum
sudo -u vrenum /opt/vrenum/.venv/bin/pytest

# Database maintenance
sudo -u postgres psql -d vrenum -c "VACUUM ANALYZE;"

# Restart all services
sudo systemctl restart vrenum postgresql redis-server nginx

# Check service status
sudo systemctl status vrenum postgresql redis-server nginx
```

---

## Emergency Commands

```bash
# Stop application
sudo systemctl stop vrenum

# Start application
sudo systemctl start vrenum

# Restart application
sudo systemctl restart vrenum

# Disable auto-start
sudo systemctl disable vrenum

# Enable auto-start
sudo systemctl enable vrenum

# View service logs
sudo journalctl -u vrenum -n 100

# Kill stuck process
sudo pkill -f "gunicorn main:app"

# Force restart
sudo systemctl kill -s 9 vrenum
sudo systemctl start vrenum
```

---

## Credential Rotation

```bash
# Update JWT secret
# 1. Edit /etc/vrenum/.env.production
# 2. Change JWT_SECRET_KEY to new value
# 3. Restart application
sudo systemctl restart vrenum

# Update database password
# 1. Change password in PostgreSQL
sudo -u postgres psql -c "ALTER USER vrenum_user WITH PASSWORD 'new_password';"
# 2. Update DATABASE_URL in /etc/vrenum/.env.production
# 3. Restart application
sudo systemctl restart vrenum

# Update API keys
# 1. Generate new keys in provider (TextVerified, Paystack, etc.)
# 2. Update in /etc/vrenum/.env.production
# 3. Restart application
sudo systemctl restart vrenum
```

---

## Performance Tuning

```bash
# Increase file descriptors
sudo sysctl -w fs.file-max=2097152

# Optimize TCP
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Make permanent
sudo tee -a /etc/sysctl.conf > /dev/null << EOF
fs.file-max=2097152
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
EOF

sudo sysctl -p
```

---

## Useful Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Vrenum aliases
alias vrenum-status='sudo systemctl status vrenum'
alias vrenum-logs='sudo journalctl -u vrenum -f'
alias vrenum-restart='sudo systemctl restart vrenum'
alias vrenum-stop='sudo systemctl stop vrenum'
alias vrenum-start='sudo systemctl start vrenum'
alias vrenum-test='curl https://vrenum.app/health'
alias vrenum-db='sudo -u postgres psql -d vrenum'
alias vrenum-redis='redis-cli'
```

---

## Quick Health Check Script

Save as `/usr/local/bin/vrenum-health-check.sh`:

```bash
#!/bin/bash

echo "🔍 Vrenum Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check application
echo "✓ Application:"
sudo systemctl is-active vrenum > /dev/null && echo "  ✅ Running" || echo "  ❌ Stopped"

# Check database
echo "✓ Database:"
sudo -u postgres psql -d vrenum -c "SELECT 1" > /dev/null 2>&1 && echo "  ✅ Connected" || echo "  ❌ Error"

# Check Redis
echo "✓ Redis:"
redis-cli ping > /dev/null 2>&1 && echo "  ✅ Connected" || echo "  ❌ Error"

# Check Nginx
echo "✓ Nginx:"
sudo systemctl is-active nginx > /dev/null && echo "  ✅ Running" || echo "  ❌ Stopped"

# Check API
echo "✓ API:"
curl -s https://vrenum.app/health > /dev/null && echo "  ✅ Responding" || echo "  ❌ Error"

# Check disk space
echo "✓ Disk Space:"
DISK_USAGE=$(df /opt/vrenum | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
  echo "  ✅ OK ($DISK_USAGE%)"
else
  echo "  ⚠️  Warning ($DISK_USAGE%)"
fi

# Check memory
echo "✓ Memory:"
MEM_USAGE=$(free | awk 'NR==2 {printf("%.0f", $3/$2 * 100)}')
if [ "$MEM_USAGE" -lt 80 ]; then
  echo "  ✅ OK ($MEM_USAGE%)"
else
  echo "  ⚠️  Warning ($MEM_USAGE%)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

Make executable:
```bash
sudo chmod +x /usr/local/bin/vrenum-health-check.sh
```

Run anytime:
```bash
vrenum-health-check.sh
```

---

## Cron Jobs for Maintenance

```bash
# Edit crontab
sudo crontab -e

# Add these lines:

# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-vrenum.sh

# Health check every 5 minutes
*/5 * * * * /usr/local/bin/vrenum-health-check.sh

# Weekly database maintenance
0 3 * * 0 sudo -u postgres psql -d vrenum -c "VACUUM ANALYZE;"

# Monthly log cleanup
0 4 1 * * find /var/log/vrenum -name "*.log.*" -mtime +30 -delete

# SSL certificate renewal (Let's Encrypt)
0 12 * * * certbot renew --quiet
```

---

## Documentation Files

- **DEPLOYMENT_BEST_PRACTICES.md** - Comprehensive guide
- **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist
- **SECURITY_AUDIT.md** - Security audit report
- **README.md** - Project overview

---

**Last Updated:** October 25, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
