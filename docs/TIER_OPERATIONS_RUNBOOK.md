# Tier System Operations Runbook

## Common Issues

### High 402 Rate

**Symptom**: > 5% requests return 402

**Diagnosis**:
```bash
python scripts/tier_metrics.py
grep "402" logs/app.log | tail -100
```

**Fix**: Check if users need tier upgrades

### NULL Tiers

**Symptom**: Users see errors

**Diagnosis**:
```sql
SELECT id, email FROM users WHERE subscription_tier IS NULL;
```

**Fix**:
```sql
UPDATE users SET subscription_tier = 'freemium' WHERE subscription_tier IS NULL;
```

### Slow Queries

**Symptom**: Requests > 100ms

**Diagnosis**:
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE subscription_tier = 'pro';
```

**Fix**: Verify index exists
```sql
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
```

## Monitoring

```bash
# Tier distribution
python scripts/tier_metrics.py

# Recent 402 errors
grep "Tier access denied" logs/app.log | tail -50

# Performance
grep "tier_check" logs/app.log | awk '{print $NF}' | sort -n | tail -10
```
