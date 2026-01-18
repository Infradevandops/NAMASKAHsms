
## Common Issues

### High 402 Rate
**Symptom**: > 5% requests return 402
**Fix**: Check tier distribution, verify upgrades

### NULL Tiers
**Symptom**: Users see errors
**Fix**: `UPDATE users SET subscription_tier = 'freemium' WHERE subscription_tier IS NULL`

### Slow Queries
**Symptom**: Requests > 100ms
**Fix**: Verify index exists on subscription_tier
