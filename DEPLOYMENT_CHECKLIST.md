# ✅ Deployment Checklist

## Pre-Deployment

### Code Review
- [ ] All error handling implemented
- [ ] Rate limiting configured
- [ ] Webhooks tested
- [ ] Analytics working
- [ ] Frontend error alerts working
- [ ] Cancel button functional
- [ ] No hardcoded credentials
- [ ] All imports correct
- [ ] No syntax errors

### Testing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Error handling tested
- [ ] Rate limiting tested
- [ ] Webhooks tested
- [ ] Analytics tested
- [ ] Frontend tested on mobile
- [ ] Cancel functionality tested
- [ ] Timeout handling tested

### Security
- [ ] SSL certificates ready
- [ ] Environment variables configured
- [ ] Database password strong (20+ chars)
- [ ] SECRET_KEY randomly generated
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] Error handling active
- [ ] No debug mode in production
- [ ] Firewall rules configured

### Infrastructure
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] PostgreSQL 15+ available
- [ ] Redis 7+ available
- [ ] Nginx configured
- [ ] Domain name ready
- [ ] SSL certificates obtained
- [ ] Backup storage configured

---

## Deployment Steps

### 1. Environment Setup
- [ ] Create `.env.production` file
- [ ] Set `TEXTVERIFIED_API_KEY`
- [ ] Set `TEXTVERIFIED_EMAIL`
- [ ] Set `DATABASE_URL`
- [ ] Generate `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `LOG_LEVEL=INFO`
- [ ] Configure CORS origins

### 2. SSL Certificates
- [ ] Obtain SSL certificates (Let's Encrypt)
- [ ] Copy fullchain.pem to `./certs/`
- [ ] Copy privkey.pem to `./certs/`
- [ ] Verify certificate validity
- [ ] Set up auto-renewal

### 3. Database Setup
- [ ] Create PostgreSQL database
- [ ] Create database user
- [ ] Set strong password
- [ ] Configure backups
- [ ] Test connection

### 4. Build & Deploy
- [ ] Build Docker image: `docker build -t namaskah:latest .`
- [ ] Start services: `docker-compose -f docker-compose.production.yml up -d`
- [ ] Run migrations: `docker-compose exec app alembic upgrade head`
- [ ] Create admin user: `docker-compose exec app python create_production_admin.py`
- [ ] Verify all services running: `docker-compose ps`

### 5. Health Checks
- [ ] App health: `curl https://yourdomain.com/health`
- [ ] Database connection: `docker-compose exec db psql -U user -d db -c "SELECT 1"`
- [ ] Redis connection: `docker-compose exec redis redis-cli ping`
- [ ] Nginx running: `curl -I https://yourdomain.com`

### 6. Verification
- [ ] Frontend loads: `https://yourdomain.com/verify`
- [ ] Login works
- [ ] Create verification works
- [ ] Cancel verification works
- [ ] Analytics loads
- [ ] Error handling works
- [ ] Rate limiting works

---

## Post-Deployment

### Monitoring
- [ ] Set up error logging
- [ ] Set up performance monitoring
- [ ] Set up uptime monitoring
- [ ] Configure alerts
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Monitor database performance

### Backups
- [ ] Schedule daily database backups
- [ ] Test backup restoration
- [ ] Store backups securely
- [ ] Document backup procedure
- [ ] Set up backup alerts

### Maintenance
- [ ] Document deployment procedure
- [ ] Document rollback procedure
- [ ] Set up log rotation
- [ ] Plan security updates
- [ ] Plan feature updates
- [ ] Monitor costs

### Documentation
- [ ] Document deployment steps
- [ ] Document configuration
- [ ] Document troubleshooting
- [ ] Document support contacts
- [ ] Create runbooks

---

## Troubleshooting

### App Won't Start
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs app

# Check environment variables
docker-compose -f docker-compose.production.yml config

# Restart
docker-compose -f docker-compose.production.yml restart app
```

### Database Connection Error
```bash
# Test connection
docker-compose -f docker-compose.production.yml exec db psql -U user -d db -c "SELECT 1"

# Check DATABASE_URL
echo $DATABASE_URL

# Restart database
docker-compose -f docker-compose.production.yml restart db
```

### High Memory Usage
```bash
# Check container stats
docker stats namaskah-app

# Check logs for errors
docker-compose -f docker-compose.production.yml logs app

# Restart if needed
docker-compose -f docker-compose.production.yml restart app
```

### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ./certs/fullchain.pem -text -noout

# Renew certificate
certbot renew

# Restart nginx
docker-compose -f docker-compose.production.yml restart nginx
```

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop current deployment
docker-compose -f docker-compose.production.yml down

# 2. Restore previous database backup
psql -U user -d db < backup_YYYYMMDD_HHMMSS.sql

# 3. Checkout previous code version
git checkout previous-tag

# 4. Rebuild and restart
docker-compose -f docker-compose.production.yml up -d

# 5. Verify
curl https://yourdomain.com/health
```

---

## Performance Optimization

### Database
- [ ] Enable connection pooling
- [ ] Create indexes on frequently queried columns
- [ ] Archive old data
- [ ] Optimize queries

### Caching
- [ ] Enable Redis caching
- [ ] Cache API responses
- [ ] Cache static files
- [ ] Set appropriate TTLs

### Load Balancing
- [ ] Scale app to multiple instances
- [ ] Configure load balancer
- [ ] Monitor instance health
- [ ] Auto-scale based on metrics

---

## Security Hardening

### Network
- [ ] Configure firewall rules
- [ ] Enable DDoS protection (Cloudflare)
- [ ] Restrict SSH access
- [ ] Enable VPN for admin access

### Application
- [ ] Enable rate limiting
- [ ] Enable error handling
- [ ] Enable CORS restrictions
- [ ] Enable CSRF protection
- [ ] Enable XSS protection

### Data
- [ ] Encrypt sensitive data
- [ ] Secure password hashing
- [ ] Secure API keys
- [ ] Secure database credentials

---

## Monitoring Setup

### Prometheus
- [ ] Install Prometheus
- [ ] Configure scrape targets
- [ ] Set up retention policy
- [ ] Configure alerts

### Grafana
- [ ] Install Grafana
- [ ] Add Prometheus data source
- [ ] Import dashboards
- [ ] Configure alerts

### Logging
- [ ] Set up centralized logging
- [ ] Configure log retention
- [ ] Set up log alerts
- [ ] Monitor error rates

---

## Support Contacts

- **Technical Support:** support@namaskah.app
- **Emergency:** emergency@namaskah.app
- **Billing:** billing@namaskah.app

---

## Sign-Off

- [ ] Project Manager: _________________ Date: _______
- [ ] DevOps Engineer: _________________ Date: _______
- [ ] Security Officer: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Version:** 2.5.0  
**Status:** ✅ READY FOR PRODUCTION
