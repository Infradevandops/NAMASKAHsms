# Monitoring Guide

**Version**: 1.0  
**Status**: Production Ready  
**Last Updated**: March 15, 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Monitoring Stack](#monitoring-stack)
3. [Sentry Setup](#sentry-setup)
4. [Prometheus Setup](#prometheus-setup)
5. [Grafana Setup](#grafana-setup)
6. [Metrics Reference](#metrics-reference)
7. [Alert Rules](#alert-rules)
8. [Dashboards](#dashboards)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The monitoring stack provides comprehensive visibility into system health, performance, and errors.

### Components

- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **AlertManager**: Alert routing and notification

### Architecture

```
Application
    ↓
Sentry (Error Tracking)
Prometheus (Metrics)
    ↓
Grafana (Visualization)
    ↓
AlertManager (Notifications)
    ↓
Slack/Email (Alerts)
```

---

## Monitoring Stack

### Sentry

**Purpose**: Error tracking and performance monitoring

**Features**:
- Real-time error tracking
- Performance monitoring
- Release tracking
- User feedback
- Source maps

**Configuration**:
```python
# app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    environment=os.getenv('ENVIRONMENT'),
)
```

### Prometheus

**Purpose**: Metrics collection and storage

**Features**:
- Time-series database
- Flexible query language (PromQL)
- Alerting rules
- Data retention

**Configuration**:
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'namaskah-app'
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana

**Purpose**: Metrics visualization

**Features**:
- Interactive dashboards
- Multiple data sources
- Alerting integration
- User management

**Configuration**:
```yaml
# grafana.ini
[security]
admin_user = admin
admin_password = ${GF_SECURITY_ADMIN_PASSWORD}

[datasources]
url = http://prometheus:9090
```

---

## Sentry Setup

### 1. Create Sentry Account

```bash
# Go to https://sentry.io
# Create account
# Create organization
# Create project (Python)
```

### 2. Get DSN

```bash
# Copy DSN from project settings
# Format: https://<key>@<host>/projects/<org>/<project>
```

### 3. Configure Environment

```bash
# Add to .env
SENTRY_DSN=https://<key>@<host>/projects/<org>/<project>
```

### 4. Verify Integration

```bash
# Check Sentry logs
curl https://sentry.io/api/0/organizations/<org>/events/

# Expected: Recent events from your application
```

### 5. Configure Alerts

```bash
# Go to Sentry project settings
# Alerts → Create Alert Rule
# Condition: Error rate > 1%
# Action: Send to Slack
```

---

## Prometheus Setup

### 1. Start Prometheus

```bash
# Using Docker
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Using Docker Compose
docker-compose -f monitoring/docker-compose.yml up prometheus
```

### 2. Configure Scrape Targets

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'namaskah-app'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 3. Verify Metrics Collection

```bash
# Access Prometheus UI
# http://localhost:9090

# Query metrics
# http://localhost:9090/api/v1/query?query=up

# Expected: Metrics from your application
```

### 4. Configure Retention

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'namaskah-monitor'

# Storage retention
storage:
  tsdb:
    retention:
      time: 30d
      size: 50GB
```

---

## Grafana Setup

### 1. Start Grafana

```bash
# Using Docker
docker run -d \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

# Using Docker Compose
docker-compose -f monitoring/docker-compose.yml up grafana
```

### 2. Add Prometheus Data Source

```bash
# Access Grafana
# http://localhost:3000
# Login: admin / admin

# Configuration → Data Sources → Add
# Name: Prometheus
# URL: http://prometheus:9090
# Save & Test
```

### 3. Import Dashboard

```bash
# Dashboards → Import
# Upload: grafana-dashboard.json
# Select Prometheus data source
# Import
```

### 4. Create Custom Dashboard

```bash
# Dashboards → New
# Add panels
# Configure queries
# Save
```

---

## Metrics Reference

### Tier Identification Metrics

```
tier_identification_latency_ms{quantile="0.95"}
tier_identification_latency_ms{quantile="0.99"}
tier_identification_errors_total
tier_identification_cache_hits_total
tier_identification_cache_misses_total
```

### Cache Metrics

```
cache_hit_rate
cache_miss_rate
cache_size_bytes
cache_eviction_rate
cache_operation_latency_ms
```

### API Metrics

```
http_requests_total{method="GET",status="200"}
http_requests_total{method="POST",status="201"}
http_request_duration_seconds{quantile="0.95"}
http_request_duration_seconds{quantile="0.99"}
http_requests_in_flight
```

### Database Metrics

```
db_query_duration_ms{quantile="0.95"}
db_query_duration_ms{quantile="0.99"}
db_connection_pool_size
db_connection_pool_available
db_slow_queries_total
```

### Feature Access Metrics

```
feature_access_total{feature="api_access",tier="pro"}
feature_access_denied_total{feature="api_access"}
feature_access_latency_ms
```

### Tier Change Metrics

```
tier_changes_total{old_tier="freemium",new_tier="pro"}
tier_upgrade_total
tier_downgrade_total
```

### System Metrics

```
process_resident_memory_bytes
process_cpu_seconds_total
process_open_fds
process_max_fds
```

---

## Alert Rules

### Critical Alerts

**Tier Identification Latency High**
```yaml
alert: TierIdentificationLatencyHigh
expr: tier_identification_latency_ms{quantile="0.95"} > 200
for: 5m
annotations:
  summary: "Tier identification latency high"
  description: "P95 latency: {{ $value }}ms"
```

**API Error Rate High**
```yaml
alert: APIErrorRateHigh
expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
for: 5m
annotations:
  summary: "API error rate high"
  description: "Error rate: {{ $value }}"
```

**Cache Hit Rate Low**
```yaml
alert: CacheHitRateLow
expr: cache_hit_rate < 0.7
for: 10m
annotations:
  summary: "Cache hit rate low"
  description: "Hit rate: {{ $value }}"
```

### Warning Alerts

**API Latency High**
```yaml
alert: APILatencyHigh
expr: http_request_duration_seconds{quantile="0.95"} > 0.5
for: 5m
annotations:
  summary: "API latency high"
  description: "P95 latency: {{ $value }}s"
```

**Memory Usage High**
```yaml
alert: MemoryUsageHigh
expr: process_resident_memory_bytes / 1024 / 1024 > 800
for: 10m
annotations:
  summary: "Memory usage high"
  description: "Memory: {{ $value }}MB"
```

---

## Dashboards

### Main Dashboard

**Panels**:
1. Tier Identification Latency (p95)
2. Cache Hit Rate (gauge)
3. API Request/Error Rates (graph)
4. Feature Access Distribution (pie chart)
5. Tier Changes (counter)
6. Active Requests (gauge)
7. Cache Size (gauge)
8. Unauthorized Access (counter)
9. Tier Errors (counter)
10. System Health (status)

### Performance Dashboard

**Panels**:
1. API Response Time (p50, p95, p99)
2. Database Query Time (p50, p95, p99)
3. Cache Operation Latency
4. Request Queue Depth
5. Active Connections
6. Memory Usage
7. CPU Usage
8. Disk I/O

### Error Dashboard

**Panels**:
1. Error Rate by Endpoint
2. Error Rate by Status Code
3. Top Errors (table)
4. Error Trend (graph)
5. Error Distribution (pie chart)
6. Sentry Integration Status

### Business Dashboard

**Panels**:
1. Tier Distribution (pie chart)
2. Tier Changes (graph)
3. Feature Usage (bar chart)
4. User Growth (graph)
5. Revenue Trend (graph)
6. Verification Success Rate

---

## Troubleshooting

### Metrics Not Appearing

**Problem**: Prometheus shows no data

**Solution**:
```bash
# 1. Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# 2. Check application metrics endpoint
curl http://localhost:8000/metrics

# 3. Check Prometheus logs
docker logs prometheus

# 4. Verify scrape config
cat prometheus.yml
```

### Alerts Not Firing

**Problem**: Alerts not triggering

**Solution**:
```bash
# 1. Check AlertManager status
curl http://localhost:9093/api/v1/status

# 2. Check alert rules
curl http://localhost:9090/api/v1/rules

# 3. Check Slack integration
# Go to AlertManager config
# Verify Slack webhook URL

# 4. Test alert manually
# Trigger condition in Prometheus
```

### High Memory Usage

**Problem**: Prometheus using too much memory

**Solution**:
```bash
# 1. Reduce retention period
# prometheus.yml
storage:
  tsdb:
    retention:
      time: 7d  # Reduce from 30d

# 2. Reduce scrape frequency
global:
  scrape_interval: 30s  # Increase from 15s

# 3. Restart Prometheus
docker restart prometheus
```

### Grafana Dashboard Not Loading

**Problem**: Dashboard shows no data

**Solution**:
```bash
# 1. Check data source
# Configuration → Data Sources
# Test connection

# 2. Check queries
# Edit panel
# Verify PromQL query

# 3. Check time range
# Select appropriate time range
# Ensure data exists for that period

# 4. Check Prometheus
# Verify metrics are being collected
```

---

## Best Practices

### Monitoring

1. **Set appropriate thresholds**
   - Based on historical data
   - Account for normal variations
   - Avoid alert fatigue

2. **Monitor key metrics**
   - Tier identification latency
   - Cache hit rate
   - Error rate
   - API response time

3. **Review alerts regularly**
   - Daily alert review
   - Adjust thresholds as needed
   - Document alert patterns

4. **Maintain dashboards**
   - Keep dashboards up to date
   - Remove unused panels
   - Add new metrics as needed

### Performance

1. **Optimize metric collection**
   - Use appropriate scrape intervals
   - Avoid high-cardinality metrics
   - Aggregate metrics when possible

2. **Manage data retention**
   - Balance retention vs. storage
   - Archive old data
   - Clean up unused metrics

3. **Scale monitoring**
   - Use multiple Prometheus instances
   - Implement federation
   - Use remote storage

---

## Related Documentation

- [PRODUCTION_DEPLOYMENT_RUNBOOK.md](./PRODUCTION_DEPLOYMENT_RUNBOOK.md)
- [PERFORMANCE_TUNING_GUIDE.md](./PERFORMANCE_TUNING_GUIDE.md)
- [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)

---

**Last Updated**: March 15, 2026  
**Status**: Production Ready ✅
