# 🔍 VRENUM SMS - Log Audit & Debug Guide

## Quick Commands

### 1. **Live Logs** (Most Common)
```bash
./logs_audit.sh live
# OR directly via SSH:
ssh root@169.255.57.57 "journalctl -u vrenum -f"
```

### 2. **Error Logs Only**
```bash
./logs_audit.sh errors
# OR:
ssh root@169.255.57.57 "journalctl -u vrenum -p err -n 100"
```

### 3. **Search Logs**
```bash
./logs_audit.sh search "payment"
./logs_audit.sh search "500"
./logs_audit.sh search "database"
./logs_audit.sh search "error"
```

### 4. **Today's Logs**
```bash
./logs_audit.sh today
```

### 5. **Service Status**
```bash
./logs_audit.sh status
```

---

## Direct SSH Commands

### View Last 100 Lines
```bash
ssh root@169.255.57.57 "journalctl -u vrenum -n 100 --no-pager"
```

### View Logs Since Specific Time
```bash
# Last hour
ssh root@169.255.57.57 "journalctl -u vrenum --since '1 hour ago'"

# Last 30 minutes
ssh root@169.255.57.57 "journalctl -u vrenum --since '30 minutes ago'"

# Specific date/time
ssh root@169.255.57.57 "journalctl -u vrenum --since '2026-05-18 10:00:00'"
```

### Filter by Priority
```bash
# Errors only
ssh root@169.255.57.57 "journalctl -u vrenum -p err"

# Warnings and above
ssh root@169.255.57.57 "journalctl -u vrenum -p warning"

# Critical only
ssh root@169.255.57.57 "journalctl -u vrenum -p crit"
```

### Export Logs to File
```bash
# Export last 1000 lines
ssh root@169.255.57.57 "journalctl -u vrenum -n 1000 --no-pager" > vrenum_logs_$(date +%Y%m%d_%H%M%S).txt

# Export today's logs
ssh root@169.255.57.57 "journalctl -u vrenum --since today --no-pager" > vrenum_today_$(date +%Y%m%d).txt
```

---

## Common Debug Scenarios

### 🔴 App Not Starting
```bash
# Check service status
ssh root@169.255.57.57 "systemctl status vrenum"

# Check last 50 lines
ssh root@169.255.57.57 "journalctl -u vrenum -n 50"

# Check for Python errors
ssh root@169.255.57.57 "journalctl -u vrenum | grep -i 'traceback\|error\|exception'"
```

### 🔴 Database Connection Issues
```bash
./logs_audit.sh search "database"
./logs_audit.sh search "postgresql"
./logs_audit.sh search "connection"
```

### 🔴 Payment Failures
```bash
./logs_audit.sh search "paystack"
./logs_audit.sh search "payment"
./logs_audit.sh search "webhook"
```

### 🔴 SMS Verification Issues
```bash
./logs_audit.sh search "textverified"
./logs_audit.sh search "verification"
./logs_audit.sh search "sms"
```

### 🔴 High Memory/CPU
```bash
# Check resource usage
ssh root@169.255.57.57 "top -bn1 | head -20"

# Check memory
ssh root@169.255.57.57 "free -h"

# Check disk
ssh root@169.255.57.57 "df -h"
```

### 🔴 API Errors (500, 404, etc.)
```bash
./logs_audit.sh search "500"
./logs_audit.sh search "404"
./logs_audit.sh search "error"
```

---

## Log Rotation & Cleanup

### Check Log Size
```bash
ssh root@169.255.57.57 "journalctl --disk-usage"
```

### Clean Old Logs
```bash
# Keep only last 7 days
ssh root@169.255.57.57 "journalctl --vacuum-time=7d"

# Keep only 500MB
ssh root@169.255.57.57 "journalctl --vacuum-size=500M"
```

---

## Application-Level Logging

### Check App Log File (if configured)
```bash
ssh root@169.255.57.57 "tail -f /root/NAMASKAHsms/app.log"
```

### Check Uvicorn Access Logs
```bash
# If configured in systemd service
ssh root@169.255.57.57 "tail -f /root/NAMASKAHsms/access.log"
```

---

## Monitoring Integration

### Sentry Dashboard
- **URL**: https://dev-vp.sentry.io/issues/
- **Use for**: Real-time error tracking, stack traces, user context

### Better Stack Uptime
- **URL**: https://uptime.betterstack.com/team/t545038/monitors/4422808
- **Use for**: Uptime monitoring, response times, incident alerts

---

## Advanced Debugging

### Follow Specific Request
```bash
# Get request ID from logs, then filter
ssh root@169.255.57.57 "journalctl -u vrenum | grep 'request_id_here'"
```

### Monitor in Real-Time with Filters
```bash
# Only show errors in real-time
ssh root@169.255.57.57 "journalctl -u vrenum -f -p err"

# Only show specific keyword
ssh root@169.255.57.57 "journalctl -u vrenum -f | grep --line-buffered 'payment'"
```

### Check Environment Variables
```bash
ssh root@169.255.57.57 "systemctl show vrenum --property=Environment"
```

### Restart Service with Log Monitoring
```bash
# Terminal 1: Watch logs
./logs_audit.sh live

# Terminal 2: Restart service
ssh root@169.255.57.57 "systemctl restart vrenum"
```

---

## Quick Troubleshooting Checklist

1. ✅ **Service Running?**
   ```bash
   ssh root@169.255.57.57 "systemctl is-active vrenum"
   ```

2. ✅ **Recent Errors?**
   ```bash
   ./logs_audit.sh errors
   ```

3. ✅ **Database Connected?**
   ```bash
   ./logs_audit.sh search "database"
   ```

4. ✅ **Port Listening?**
   ```bash
   ssh root@169.255.57.57 "netstat -tlnp | grep 8000"
   ```

5. ✅ **Health Check?**
   ```bash
   curl -I https://vrenum.app/health
   ```

---

## Tips

- **Use `live` mode** for real-time debugging during deployments
- **Use `errors` mode** for quick issue identification
- **Use `search` mode** for specific feature debugging
- **Export logs** before making major changes
- **Check Sentry** for detailed error context and stack traces
- **Monitor Better Stack** for uptime and performance trends

---

**Need Help?**
- Check [DEPLOY_NOW.md](./DEPLOY_NOW.md) for deployment issues
- Check [README.md](./README.md) for architecture overview
- Contact: support@vrenum.app
