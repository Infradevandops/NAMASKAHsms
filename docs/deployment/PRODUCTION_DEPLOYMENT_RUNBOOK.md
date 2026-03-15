# Production Deployment Runbook

**Version**: 1.0  
**Last Updated**: March 15, 2026  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Procedure](#deployment-procedure)
3. [Canary Deployment](#canary-deployment)
4. [Monitoring & Verification](#monitoring--verification)
5. [Rollback Procedure](#rollback-procedure)
6. [Troubleshooting](#troubleshooting)
7. [Post-Deployment](#post-deployment)

---

## Pre-Deployment Checklist

### 24 Hours Before Deployment

- [ ] Notify all stakeholders of deployment window
- [ ] Verify all tests passing (120+ tests, 98%+ coverage)
- [ ] Review all changes since last deployment
- [ ] Backup production database
- [ ] Verify staging deployment is stable
- [ ] Prepare rollback plan
- [ ] Ensure on-call team is available

### 1 Hour Before Deployment

- [ ] Verify all services are healthy
- [ ] Check database connectivity
- [ ] Verify Redis cache is working
- [ ] Confirm monitoring is active
- [ ] Verify Sentry is configured
- [ ] Check disk space (> 1GB free)
- [ ] Verify network connectivity

### 15 Minutes Before Deployment

- [ ] Final health check on all services
- [ ] Verify deployment scripts are executable
- [ ] Confirm team is ready
- [ ] Start monitoring dashboard
- [ ] Prepare communication channels

---

## Deployment Procedure

### Step 1: Pre-Deployment Checks

```bash
# Run pre-deployment verification
python scripts/deployment/pre_deploy_checks.py

# Expected output:
# ✓ All required environment variables present
# ✓ Database connection successful
# ✓ Redis connection successful
# ✓ Database migrations verified
# ✓ All required dependencies installed
# ✓ Disk space available: X.XXGB
# ✓ Memory available: X.XXGB
# ✓ Application configuration valid
# ✓ Monitoring setup verified
```

### Step 2: Deploy to Render

```bash
# Option A: Using Render Dashboard
# 1. Go to https://dashboard.render.com
# 2. Select namaskah-api-prod service
# 3. Click "Deploy" button
# 4. Monitor deployment progress

# Option B: Using Render CLI
render deploy --service namaskah-api-prod

# Expected: Deployment starts, shows progress
```

### Step 3: Monitor Deployment Progress

```bash
# Watch deployment logs
render logs --service namaskah-api-prod --follow

# Expected output:
# Building application...
# Installing dependencies...
# Running pre-deploy checks...
# Starting application...
# Application ready on port 8000
```

### Step 4: Post-Deployment Verification

```bash
# Run post-deployment verification
python scripts/deployment/post_deploy_verification.py

# Expected output:
# ✓ API health check passed
# ✓ Database health check passed
# ✓ Redis health check passed
# ✓ API response time acceptable: XXXms
# ✓ Error rate acceptable: X.XXX%
# ✓ Tier system healthy
# ✓ Prometheus metrics available
# ✓ Canary success rate: XX.XX%
# ✓ Database migrations verified
# ✓ SSL certificate valid
```

---

## Canary Deployment

### Canary Strategy

The deployment uses a 4-stage canary strategy:

1. **Stage 1**: 10% traffic (5 minutes)
2. **Stage 2**: 25% traffic (5 minutes)
3. **Stage 3**: 50% traffic (5 minutes)
4. **Stage 4**: 100% traffic (stable)

### Running Canary Deployment

```bash
# Start canary deployment
python scripts/deployment/canary_deployment.py

# Expected output:
# ============================================================
# STAGE 1: 10% Traffic
# ============================================================
# Shifting traffic to 10%...
# ✓ Traffic shifted to 10%
# Monitoring deployment for 300 seconds...
# ✓ Metrics healthy: Metrics within acceptable thresholds
# ✓ Stage 1 passed
#
# ============================================================
# STAGE 2: 25% Traffic
# ============================================================
# ... (repeat for stages 2-4)
#
# ✓ Canary deployment completed successfully
```

### Canary Metrics Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate | > 1% | Rollback |
| P95 Latency | > 500ms | Rollback |
| Success Rate | < 99% | Rollback |
| Health Check | Failed | Rollback |

---

## Monitoring & Verification

### Real-Time Monitoring

```bash
# Access Grafana dashboard
# URL: https://namaskah-grafana-prod.onrender.com
# Username: admin
# Password: (from environment)

# Key dashboards to monitor:
# 1. Tier Identification Latency (p95 < 100ms)
# 2. Cache Hit Rate (> 85%)
# 3. API Request/Error Rates (< 1% errors)
# 4. Feature Access Distribution
# 5. Tier Changes (should be minimal)
# 6. Active Requests (should be stable)
# 7. Cache Size (should be stable)
# 8. Unauthorized Access (should be 0)
# 9. Tier Errors (should be 0)
```

### Prometheus Metrics

```bash
# Access Prometheus
# URL: https://namaskah-prometheus-prod.onrender.com

# Key metrics to check:
# - tier_identification_latency_ms (p95)
# - cache_hit_rate
# - api_requests_total
# - api_errors_total
# - feature_access_total
# - tier_changes_total
# - http_requests_in_flight
```

### Alert Rules

The following alerts are configured:

1. **Tier Identification Latency High**
   - Threshold: p95 > 200ms
   - Action: Page on-call engineer

2. **Cache Hit Rate Low**
   - Threshold: < 70%
   - Action: Investigate cache configuration

3. **API Error Rate High**
   - Threshold: > 1%
   - Action: Page on-call engineer

4. **API Latency High**
   - Threshold: p95 > 500ms
   - Action: Investigate performance

5. **Feature Access Errors**
   - Threshold: > 0 errors
   - Action: Investigate tier system

6. **Unauthorized Access Attempts**
   - Threshold: > 10 in 5 minutes
   - Action: Investigate security

---

## Rollback Procedure

### Automatic Rollback

Rollback is triggered automatically if:
- Error rate exceeds 1%
- P95 latency exceeds 500ms
- Success rate drops below 99%
- Health checks fail 5 consecutive times

### Manual Rollback

```bash
# Step 1: Trigger rollback
python scripts/deployment/canary_deployment.py --rollback

# Step 2: Verify rollback
python scripts/deployment/post_deploy_verification.py

# Step 3: Confirm services are healthy
curl https://namaskah-api-prod.onrender.com/health

# Step 4: Notify stakeholders
# Send message to #deployments channel
```

### Rollback Verification

```bash
# Check if rollback was successful
curl https://namaskah-api-prod.onrender.com/api/deployment/status

# Expected response:
# {
#   "status": "rolled_back",
#   "previous_version": "v4.4.0",
#   "current_version": "v4.3.0",
#   "timestamp": "2026-03-15T10:30:00Z"
# }
```

---

## Troubleshooting

### Issue: Pre-Deployment Checks Fail

**Symptoms**: Pre-deployment checks fail with database/Redis errors

**Solution**:
```bash
# 1. Check database connectivity
psql $DATABASE_URL -c "SELECT 1"

# 2. Check Redis connectivity
redis-cli -u $REDIS_URL ping

# 3. Verify environment variables
env | grep -E "DATABASE_URL|REDIS_URL|SECRET_KEY"

# 4. Check service status
curl https://namaskah-api-prod.onrender.com/health
```

### Issue: Deployment Hangs

**Symptoms**: Deployment progress stops or takes > 30 minutes

**Solution**:
```bash
# 1. Check deployment logs
render logs --service namaskah-api-prod --follow

# 2. Check for stuck processes
ps aux | grep python

# 3. Restart deployment
render deploy --service namaskah-api-prod --force

# 4. If still stuck, rollback
python scripts/deployment/canary_deployment.py --rollback
```

### Issue: High Error Rate After Deployment

**Symptoms**: Error rate > 1% after deployment

**Solution**:
```bash
# 1. Check error logs
curl https://namaskah-api-prod.onrender.com/api/logs/errors?limit=100

# 2. Check Sentry for errors
# Go to https://sentry.io/organizations/namaskah/issues/

# 3. Identify error pattern
# Common issues:
# - Database migration failed
# - Cache connection lost
# - Configuration mismatch

# 4. If critical, rollback
python scripts/deployment/canary_deployment.py --rollback

# 5. Fix issue and redeploy
```

### Issue: Tier System Not Working

**Symptoms**: Tier identification fails or returns wrong tier

**Solution**:
```bash
# 1. Check tier system health
curl https://namaskah-api-prod.onrender.com/api/health/tiers

# 2. Check database tier data
psql $DATABASE_URL -c "SELECT * FROM subscription_tiers LIMIT 5"

# 3. Check cache
redis-cli -u $REDIS_URL GET "tier:user:123"

# 4. Verify tier configuration
curl https://namaskah-api-prod.onrender.com/api/tiers

# 5. If data is corrupted, restore from backup
python scripts/deployment/restore_backup.py
```

### Issue: Performance Degradation

**Symptoms**: API latency > 500ms or cache hit rate < 70%

**Solution**:
```bash
# 1. Check database performance
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM users LIMIT 1"

# 2. Check cache hit rate
curl https://namaskah-api-prod.onrender.com/api/metrics/cache

# 3. Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"

# 4. Optimize queries if needed
python scripts/deployment/optimize_queries.py

# 5. Increase cache TTL if needed
# Update app/core/cache_optimization.py
```

---

## Post-Deployment

### Immediate Actions (0-30 minutes)

- [ ] Verify all services are healthy
- [ ] Check error rates are normal
- [ ] Verify tier system is working
- [ ] Check cache hit rates
- [ ] Monitor API latency
- [ ] Verify monitoring is active
- [ ] Notify stakeholders of successful deployment

### Short-Term Actions (30 minutes - 2 hours)

- [ ] Monitor for any issues
- [ ] Check user feedback
- [ ] Verify all features are working
- [ ] Check performance metrics
- [ ] Review error logs
- [ ] Verify database integrity

### Long-Term Actions (2+ hours)

- [ ] Document any issues encountered
- [ ] Update deployment procedures if needed
- [ ] Archive deployment logs
- [ ] Schedule post-deployment review
- [ ] Update runbook with lessons learned

### Deployment Sign-Off

```bash
# Generate deployment report
python scripts/deployment/generate_deployment_report.py

# Expected output:
# Deployment Report
# ================
# Deployment Date: 2026-03-15
# Deployment Time: 15 minutes
# Stages Completed: 4/4
# Success Rate: 100%
# Errors: 0
# Warnings: 0
# Status: ✓ SUCCESSFUL
```

---

## Communication Template

### Pre-Deployment Notification

```
🚀 DEPLOYMENT NOTICE

We will be deploying Namaskah v4.4.0 to production on [DATE] at [TIME].

Expected Duration: 15-30 minutes
Impact: Minimal (canary deployment)
Rollback Plan: Automatic if issues detected

Services Affected:
- API (namaskah-api-prod)
- Database (namaskah-db-prod)
- Cache (namaskah-redis-prod)

We will monitor closely and notify you of any issues.
```

### Deployment Started

```
🔄 DEPLOYMENT IN PROGRESS

Deployment started at [TIME]
Current Stage: [STAGE]
Progress: [PERCENTAGE]%

Monitoring: Active
Status: Healthy
```

### Deployment Completed

```
✅ DEPLOYMENT SUCCESSFUL

Deployment completed at [TIME]
Duration: [DURATION]
Version: v4.4.0

All systems operational
No issues detected
```

### Deployment Failed (Rollback)

```
⚠️ DEPLOYMENT ROLLED BACK

Deployment rolled back at [TIME]
Reason: [REASON]
Previous Version: v4.3.0

All systems restored
Investigating issue
```

---

## Emergency Contacts

- **On-Call Engineer**: [Phone/Slack]
- **DevOps Lead**: [Phone/Slack]
- **Engineering Manager**: [Phone/Slack]
- **CTO**: [Phone/Slack]

---

## Related Documentation

- [SETUP.md](../SETUP.md) - Setup and installation guide
- [README.md](../README.md) - Project overview
- [PHASE4_ROADMAP.md](./PHASE4_ROADMAP.md) - Phase 4 roadmap
- [Monitoring Guide](./monitoring-guide.md) - Monitoring setup

---

**Last Updated**: March 15, 2026  
**Next Review**: March 22, 2026  
**Status**: Production Ready ✅
