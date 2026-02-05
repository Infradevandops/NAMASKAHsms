# Tier System Architecture

## Data Model

**Single Source of Truth**: `users.subscription_tier`

```sql
subscription_tier VARCHAR(50) NOT NULL DEFAULT 'freemium'
CHECK (subscription_tier IN ('freemium', 'payg', 'pro', 'custom'))
INDEX idx_users_subscription_tier
```

## Hierarchy

```
custom (3) > pro (2) > payg (1) > freemium (0)
```

## Access Control Flow

1. Request → JWT decode → user_id
2. Fetch tier from DB (cached 60s)
3. Check: `has_tier_access(user_tier, required_tier)`
4. If fail: 402 with `TierAccessDenied`
5. If pass: proceed

## Performance

- Tier check: < 1ms (cached)
- DB query: < 10ms (indexed)
- Cache TTL: 60s
