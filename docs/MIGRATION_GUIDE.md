# 🔄 Security Migration Guide

**Version**: 2.4.0 Security Update  
**Migration Required**: Yes  
**Estimated Time**: 2-4 hours  

---

## 📋 Pre-Migration Checklist

### Environment Preparation
- [ ] Backup current database
- [ ] Review current environment variables
- [ ] Test in staging environment first
- [ ] Prepare rollback plan

### Dependencies
- [ ] Update Python packages: `pip install -r requirements.txt`
- [ ] Install new security packages: `pydantic-settings`, `prometheus_client`
- [ ] Verify Redis connection (for caching)

---

## 🔧 Configuration Updates

### Required Environment Variables
```bash
# New required variables
SECRET_KEY=your-32-char-secret-key
JWT_SECRET_KEY=your-32-char-jwt-secret

# Updated variables
DATABASE_URL=postgresql://user:pass@host:port/db  # SQLite deprecated for production
```

### Security Configuration
```bash
# Rate limiting (optional)
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# JWT settings (optional)
JWT_EXPIRE_MINUTES=480
```

---

## 🚀 Deployment Steps

### 1. Database Migration
```bash
# Run database migrations
alembic upgrade head

# Verify schema
python scripts/validate_migration.py
```

### 2. Environment Update
```bash
# Generate secure keys
python scripts/manage_secrets.py generate

# Validate configuration
python scripts/validate_config.py
```

### 3. Application Deployment
```bash
# Deploy with new configuration
./scripts/deploy_production.sh

# Run smoke tests
python scripts/smoke_checks.py
```

---

## 🔒 Security Improvements

### What's New
- **SQL Injection Protection** - All queries parameterized
- **XSS Prevention** - Input sanitization and output encoding
- **Authentication Required** - JWT tokens for all endpoints
- **Rate Limiting** - Multi-algorithm rate limiting
- **Secure Logging** - Log injection prevention
- **Data Masking** - Sensitive information protection

### Breaking Changes
- **Authentication Required** - All API endpoints now require JWT tokens
- **Input Validation** - Stricter input validation may reject previously accepted requests
- **Error Responses** - Standardized error format

---

## 🧪 Testing & Validation

### Post-Migration Tests
```bash
# Run security tests
python scripts/run_security_tests.py

# Validate all endpoints
python scripts/validate_deployment.py

# Performance testing
python scripts/load_test.py
```

### Validation Checklist
- [ ] All endpoints return expected responses
- [ ] Authentication works correctly
- [ ] Rate limiting functions properly
- [ ] No security vulnerabilities detected
- [ ] Performance within acceptable limits

---

## 🚨 Rollback Procedure

### If Issues Occur
1. **Stop Application** - `systemctl stop namaskah`
2. **Restore Database** - `./scripts/restore_backup.sh`
3. **Revert Code** - Deploy previous version
4. **Restart Services** - `systemctl start namaskah`
5. **Verify Functionality** - Run smoke tests

### Rollback Script
```bash
# Automated rollback
./scripts/rollback_deployment.sh --version=previous
```

---

## 📊 Monitoring & Alerts

### New Metrics
- **Security Events** - Failed authentication attempts
- **Rate Limit Events** - Rate limit violations
- **Error Rates** - Application error tracking
- **Performance Metrics** - Response times and throughput

### Alert Configuration
```yaml
# Example Prometheus alerts
- alert: HighErrorRate
  expr: error_rate > 0.05
  for: 5m
  
- alert: SecurityViolation
  expr: security_events > 10
  for: 1m
```

---

## 💡 Best Practices

### Security
- **Regular Updates** - Keep dependencies updated
- **Secret Rotation** - Rotate secrets regularly
- **Monitoring** - Monitor security events
- **Backup Strategy** - Regular automated backups

### Performance
- **Caching** - Utilize Redis caching effectively
- **Rate Limiting** - Configure appropriate limits
- **Database** - Use PostgreSQL for production
- **Monitoring** - Track performance metrics

---

## 📞 Support

### Migration Support
- **Documentation** - Complete migration documentation
- **Scripts** - Automated migration scripts provided
- **Testing** - Comprehensive test suite included

### Contact
- **Technical Issues** - support@namaskah.app
- **Security Concerns** - security@namaskah.app
- **Emergency** - Use rollback procedure immediately

---

**Migration Success Criteria**: All tests pass, no security vulnerabilities, performance within limits
