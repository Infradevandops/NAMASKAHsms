# 🚀 Vrenum SMS - Quick Deployment Checklist

## Pre-Deployment (Local)

- [ ] Verify credentials are NOT in git: `git ls-files | grep .env`
- [ ] Rotate all production credentials (TextVerified, Paystack, etc.)
- [ ] Update `.env.production.example` with new placeholder values
- [ ] Test application locally: `python3 -m uvicorn main:app --reload`
- [ ] Run full test suite: `pytest --cov=app`
- [ ] Build Docker image (if using Docker): `docker build -t vrenum:latest .`

## Server Setup (Linux)

- [ ] Provision Linux server (Ubuntu 22.04 LTS recommended)
- [ ] Update system: `sudo apt update && sudo apt upgrade -y`
- [ ] Install dependencies: Python 3.9+, PostgreSQL, Redis, Nginx
- [ ] Create application user: `sudo useradd -m vrenum`
- [ ] Clone repository: `git clone ... /opt/vrenum`
- [ ] Setup Python venv: `python3.9 -m venv /opt/vrenum/.venv`
- [ ] Install requirements: `pip install -r requirements.txt`

## Secrets Management

- [ ] Create `/etc/vrenum/.env.production` with actual credentials
- [ ] Set permissions: `sudo chmod 600 /etc/vrenum/.env.production`
- [ ] Verify secrets are NOT readable by other users
- [ ] Setup systemd EnvironmentFile to load secrets
- [ ] Test that application can read all required env vars

## Database Setup

- [ ] Create PostgreSQL database: `createdb vrenum`
- [ ] Create database user with strong password
- [ ] Run migrations: `bash scripts/deployment/migrate.sh`
- [ ] Verify database connectivity: `psql -U vrenum_user -d vrenum`
- [ ] Setup database backups (daily to S3)
- [ ] Test backup restoration process

## Redis Setup

- [ ] Install and start Redis: `sudo systemctl start redis-server`
- [ ] Enable Redis on boot: `sudo systemctl enable redis-server`
- [ ] Verify Redis is running: `redis-cli ping`
- [ ] Configure Redis persistence (if needed)
- [ ] Setup Redis monitoring

## Application Deployment

- [ ] Create systemd service file: `/etc/systemd/system/vrenum.service`
- [ ] Enable service: `sudo systemctl enable vrenum`
- [ ] Start service: `sudo systemctl start vrenum`
- [ ] Verify service is running: `sudo systemctl status vrenum`
- [ ] Check application logs: `sudo journalctl -u vrenum -f`
- [ ] Test health endpoint: `curl http://localhost:8000/health`

## Nginx Configuration

- [ ] Create Nginx config: `/etc/nginx/sites-available/vrenum`
- [ ] Enable site: `sudo ln -s /etc/nginx/sites-available/vrenum /etc/nginx/sites-enabled/`
- [ ] Test Nginx config: `sudo nginx -t`
- [ ] Restart Nginx: `sudo systemctl restart nginx`
- [ ] Verify Nginx is running: `sudo systemctl status nginx`

## SSL/TLS Setup

- [ ] Install Certbot: `sudo apt install certbot python3-certbot-nginx`
- [ ] Generate certificate: `sudo certbot certonly --nginx -d vrenum.app`
- [ ] Verify certificate: `openssl s_client -connect vrenum.app:443`
- [ ] Setup auto-renewal: `sudo certbot renew --dry-run`
- [ ] Add security headers to Nginx config

## Security Hardening

- [ ] Enable UFW firewall: `sudo ufw enable`
- [ ] Allow SSH (22), HTTP (80), HTTPS (443)
- [ ] Disable root SSH login
- [ ] Setup SSH key-based authentication only
- [ ] Configure PostgreSQL to listen only on localhost
- [ ] Configure Redis to listen only on localhost
- [ ] Set restrictive file permissions on `/opt/vrenum`
- [ ] Disable debug mode: `DEBUG=false`

## Monitoring & Logging

- [ ] Setup application logging to `/var/log/vrenum/`
- [ ] Configure log rotation: `/etc/logrotate.d/vrenum`
- [ ] Setup Sentry error tracking (verify DSN is set)
- [ ] Setup uptime monitoring (Better Stack, Pingdom, etc.)
- [ ] Configure alerts for critical errors
- [ ] Setup performance monitoring (Prometheus, Datadog, etc.)

## Testing & Verification

- [ ] Test login endpoint: `curl -X POST http://localhost:8000/api/auth/login`
- [ ] Test health check: `curl https://vrenum.app/health`
- [ ] Verify HTTPS redirect: `curl -I http://vrenum.app`
- [ ] Test database connectivity
- [ ] Test Redis connectivity
- [ ] Verify all external API keys are working
- [ ] Test email notifications
- [ ] Test SMS verification flow (if TextVerified is configured)
- [ ] Test payment processing (if Paystack is configured)

## Performance Optimization

- [ ] Enable Gzip compression in Nginx
- [ ] Setup caching headers for static files
- [ ] Configure rate limiting in Nginx
- [ ] Optimize database queries (check slow query log)
- [ ] Setup connection pooling for database
- [ ] Monitor application performance metrics

## Backup & Disaster Recovery

- [ ] Setup automated database backups (daily)
- [ ] Test backup restoration process
- [ ] Upload backups to S3 or external storage
- [ ] Document disaster recovery procedure
- [ ] Setup automated failover (if applicable)

## Documentation

- [ ] Document server IP and access details
- [ ] Document database credentials (in secure location)
- [ ] Document API keys and secrets (in secure location)
- [ ] Create runbook for common operations
- [ ] Create incident response procedures
- [ ] Document scaling procedures

## Post-Deployment

- [ ] Verify application is accessible: `https://vrenum.app`
- [ ] Check all pages load correctly
- [ ] Verify admin dashboard works
- [ ] Test user registration and login
- [ ] Monitor logs for errors: `sudo journalctl -u vrenum -f`
- [ ] Monitor system resources: `top`, `htop`
- [ ] Verify backups are running
- [ ] Setup monitoring alerts
- [ ] Notify team of successful deployment

## Credential Rotation (Schedule)

- [ ] **Immediate:** Rotate all credentials used in development
- [ ] **Every 90 days:** JWT_SECRET_KEY, DATABASE_PASSWORD
- [ ] **Every 180 days:** API Keys (TextVerified, Paystack, etc.)
- [ ] **Auto-renewed:** SSL Certificates (Let's Encrypt)

## Ongoing Maintenance

- [ ] Monitor application logs daily
- [ ] Review error tracking (Sentry) weekly
- [ ] Check system resources weekly
- [ ] Verify backups are running daily
- [ ] Update dependencies monthly
- [ ] Review security logs monthly
- [ ] Rotate credentials on schedule
- [ ] Test disaster recovery quarterly

---

## Quick Commands Reference

```bash
# Check application status
sudo systemctl status vrenum

# View logs
sudo journalctl -u vrenum -f

# Restart application
sudo systemctl restart vrenum

# Check database
sudo -u postgres psql -d vrenum -c "SELECT COUNT(*) FROM users;"

# Check Redis
redis-cli ping

# Check Nginx
sudo nginx -t && sudo systemctl status nginx

# Monitor system
top
htop
iotop

# View SSL certificate
openssl s_client -connect vrenum.app:443

# Test API
curl https://vrenum.app/health
curl https://vrenum.app/api/auth/me -H "Authorization: Bearer $TOKEN"
```

---

**Status:** ✅ Ready for Production Deployment  
**Last Updated:** October 25, 2026  
**Version:** 1.0
