# Vrenum SMS - Production Deployment Best Practices

**Status:** ✅ Credentials NOT in git (only `.env.example` tracked)  
**Last Updated:** October 25, 2026

---

## 🔐 Security Audit Results

### Current State
- ✅ `.env.production` is in `.gitignore`
- ✅ Only `.env.example` and `.env.production.example` are tracked
- ✅ Actual credentials are NOT exposed in git history
- ✅ Production keys are safely stored locally

### Credentials to Rotate (Before Public Launch)
- TextVerified API Key
- Paystack Live Keys (pk_live_*, sk_live_*)
- Resend API Key
- Sentry DSN
- OneSignal API Key
- Google OAuth Secret
- Turnstile Secret Key

---

## 📋 Pre-Deployment Checklist

### 1. Secrets Management Setup

#### Option A: Environment Variables (Recommended for Linux)
```bash
# On your Linux server, set environment variables
export TEXTVERIFIED_API_KEY="your-key"
export PAYSTACK_SECRET_KEY="your-key"
export PAYSTACK_PUBLIC_KEY="your-key"
export RESEND_API_KEY="your-key"
export JWT_SECRET_KEY="your-key"
export SECRET_KEY="your-key"
# ... etc
```

#### Option B: Systemd Service File (Recommended)
Create `/etc/systemd/system/vrenum.service`:
```ini
[Unit]
Description=Vrenum SMS API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=vrenum
WorkingDirectory=/opt/vrenum
Environment="ENVIRONMENT=production"
Environment="DATABASE_URL=postgresql://user:pass@localhost/vrenum"
Environment="REDIS_URL=redis://localhost:6379/0"
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
```

#### Option C: Docker Secrets (For Docker/Kubernetes)
```bash
# Create secrets
docker secret create textverified_key -
docker secret create paystack_secret -
docker secret create jwt_secret -

# Reference in docker-compose.yml
services:
  app:
    secrets:
      - textverified_key
      - paystack_secret
      - jwt_secret
    environment:
      TEXTVERIFIED_API_KEY_FILE: /run/secrets/textverified_key
```

#### Option D: HashiCorp Vault (Enterprise)
```bash
# Store secrets in Vault
vault kv put secret/vrenum/prod \
  textverified_api_key="..." \
  paystack_secret_key="..." \
  jwt_secret_key="..."

# Application reads from Vault at startup
```

---

## 🚀 Linux Server Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
  python3.9 \
  python3.9-venv \
  python3-pip \
  postgresql \
  postgresql-contrib \
  redis-server \
  nginx \
  certbot \
  python3-certbot-nginx \
  supervisor \
  git

# Create application user
sudo useradd -m -s /bin/bash vrenum
sudo usermod -aG sudo vrenum
```

### 2. Clone Repository

```bash
sudo -u vrenum git clone https://github.com/Infradevandops/NAMASKAHsms.git /opt/vrenum
cd /opt/vrenum
```

### 3. Setup Python Environment

```bash
sudo -u vrenum python3.9 -m venv /opt/vrenum/.venv
sudo -u vrenum /opt/vrenum/.venv/bin/pip install --upgrade pip
sudo -u vrenum /opt/vrenum/.venv/bin/pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Create secure directory for secrets
sudo mkdir -p /etc/vrenum
sudo chown vrenum:vrenum /etc/vrenum
sudo chmod 700 /etc/vrenum

# Copy and edit production config
sudo -u vrenum cp .env.production.example /etc/vrenum/.env.production
sudo nano /etc/vrenum/.env.production

# Set restrictive permissions
sudo chmod 600 /etc/vrenum/.env.production
```

### 5. Setup PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE vrenum;
CREATE USER vrenum_user WITH PASSWORD 'secure_password_here';
ALTER ROLE vrenum_user SET client_encoding TO 'utf8';
ALTER ROLE vrenum_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE vrenum_user SET default_transaction_deferrable TO on;
ALTER ROLE vrenum_user SET default_transaction_level TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE vrenum TO vrenum_user;
EOF

# Update DATABASE_URL in /etc/vrenum/.env.production
DATABASE_URL=postgresql://vrenum_user:secure_password_here@localhost/vrenum
```

### 6. Setup Redis

```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping  # Should return PONG
```

### 7. Run Database Migrations

```bash
cd /opt/vrenum
sudo -u vrenum bash scripts/deployment/migrate.sh
```

### 8. Setup Nginx Reverse Proxy

Create `/etc/nginx/sites-available/vrenum`:
```nginx
upstream vrenum_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name vrenum.app www.vrenum.app;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name vrenum.app www.vrenum.app;

    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/vrenum.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vrenum.app/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://vrenum_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    location /ws {
        proxy_pass http://vrenum_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Static files caching
    location /static/ {
        alias /opt/vrenum/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/vrenum /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Setup SSL Certificate

```bash
sudo certbot certonly --nginx -d vrenum.app -d www.vrenum.app
sudo certbot renew --dry-run  # Test auto-renewal
```

### 10. Setup Systemd Service

```bash
sudo cp /opt/vrenum/deploy/systemd/vrenum.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vrenum
sudo systemctl start vrenum
sudo systemctl status vrenum
```

### 11. Setup Logging

```bash
# Create log directory
sudo mkdir -p /var/log/vrenum
sudo chown vrenum:vrenum /var/log/vrenum
sudo chmod 755 /var/log/vrenum

# Setup log rotation
sudo tee /etc/logrotate.d/vrenum > /dev/null << EOF
/var/log/vrenum/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 vrenum vrenum
    sharedscripts
    postrotate
        systemctl reload vrenum > /dev/null 2>&1 || true
    endscript
}
EOF
```

### 12. Setup Monitoring & Alerts

```bash
# Install monitoring agent (e.g., Datadog, New Relic, or Prometheus)
# Example: Prometheus node exporter
sudo apt install -y prometheus-node-exporter
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter
```

---

## 🔒 Security Hardening

### 1. Firewall Configuration

```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5432/tcp  # PostgreSQL (internal only)
sudo ufw allow 6379/tcp  # Redis (internal only)
```

### 2. SSH Hardening

```bash
# Edit /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config

# Changes:
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# X11Forwarding no

sudo systemctl restart ssh
```

### 3. Database Security

```bash
# PostgreSQL: Only allow local connections
sudo nano /etc/postgresql/*/main/postgresql.conf
# listen_addresses = 'localhost'

# Restrict pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
# local   all             all                                     trust
# host    all             all             127.0.0.1/32            md5
```

### 4. Application Security

```bash
# Set restrictive file permissions
sudo chown -R vrenum:vrenum /opt/vrenum
sudo chmod -R 755 /opt/vrenum
sudo chmod 600 /opt/vrenum/.env*

# Disable debug mode in production
# ENVIRONMENT=production
# DEBUG=false
```

---

## 📊 Monitoring & Observability

### 1. Application Logs

```bash
# View logs
sudo journalctl -u vrenum -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Health Checks

```bash
# Setup health check endpoint
curl https://vrenum.app/health

# Monitor with cron
*/5 * * * * curl -f https://vrenum.app/health || systemctl restart vrenum
```

### 3. Performance Monitoring

```bash
# Monitor system resources
top
htop
iotop

# Monitor database
sudo -u postgres psql -d vrenum -c "SELECT * FROM pg_stat_statements;"

# Monitor Redis
redis-cli INFO stats
```

---

## 🔄 Backup & Disaster Recovery

### 1. Database Backups

```bash
# Daily backup script
sudo tee /usr/local/bin/backup-vrenum.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/vrenum"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# PostgreSQL backup
sudo -u postgres pg_dump vrenum | gzip > $BACKUP_DIR/vrenum_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "vrenum_*.sql.gz" -mtime +30 -delete
EOF

sudo chmod +x /usr/local/bin/backup-vrenum.sh

# Schedule with cron
sudo crontab -e
# 0 2 * * * /usr/local/bin/backup-vrenum.sh
```

### 2. Automated Backups to S3

```bash
# Install AWS CLI
sudo apt install -y awscli

# Configure AWS credentials
aws configure

# Backup script with S3 upload
sudo tee /usr/local/bin/backup-to-s3.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/vrenum"
S3_BUCKET="s3://vrenum-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
sudo -u postgres pg_dump vrenum | gzip > $BACKUP_DIR/vrenum_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/vrenum_$DATE.sql.gz $S3_BUCKET/

# Cleanup old local backups
find $BACKUP_DIR -name "vrenum_*.sql.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-to-s3.sh
```

---

## 🚨 Incident Response

### 1. Application Crash

```bash
# Check status
sudo systemctl status vrenum

# View recent logs
sudo journalctl -u vrenum -n 50

# Restart
sudo systemctl restart vrenum

# Check if it stays up
sleep 5 && sudo systemctl status vrenum
```

### 2. Database Connection Issues

```bash
# Check PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"

# Check Redis
redis-cli ping

# Restart services
sudo systemctl restart postgresql
sudo systemctl restart redis-server
```

### 3. High CPU/Memory Usage

```bash
# Identify process
top -b -n 1 | head -20

# Check application logs for errors
sudo journalctl -u vrenum -f

# Restart if needed
sudo systemctl restart vrenum
```

---

## 📈 Scaling Considerations

### 1. Load Balancing

```bash
# Setup multiple app instances
# Use Nginx upstream with multiple servers
upstream vrenum_app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

### 2. Database Replication

```bash
# Setup PostgreSQL replication for high availability
# Primary-Replica setup with automatic failover
```

### 3. Caching Strategy

```bash
# Redis clustering for distributed caching
# Implement cache invalidation strategy
```

---

## ✅ Post-Deployment Verification

```bash
# 1. Check application is running
curl https://vrenum.app/health

# 2. Verify database connectivity
curl https://vrenum.app/api/auth/me -H "Authorization: Bearer $TOKEN"

# 3. Check SSL certificate
openssl s_client -connect vrenum.app:443

# 4. Verify all services
sudo systemctl status vrenum postgresql redis-server nginx

# 5. Check logs for errors
sudo journalctl -u vrenum -n 100 | grep -i error
```

---

## 🔐 Credential Rotation Schedule

| Credential | Rotation Frequency | Next Rotation |
|------------|-------------------|---------------|
| JWT_SECRET_KEY | Every 90 days | 2027-01-23 |
| DATABASE_PASSWORD | Every 90 days | 2027-01-23 |
| API Keys (TextVerified, Paystack) | Every 180 days | 2027-04-23 |
| SSL Certificates | Auto (Let's Encrypt) | Auto-renewed |
| OAuth Secrets | Every 180 days | 2027-04-23 |

---

## 📞 Support & Troubleshooting

- **Logs:** `/var/log/vrenum/`
- **Status:** `sudo systemctl status vrenum`
- **Restart:** `sudo systemctl restart vrenum`
- **Monitoring:** Check Sentry dashboard for errors
- **Database:** `sudo -u postgres psql -d vrenum`

---

**Last Updated:** October 25, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
