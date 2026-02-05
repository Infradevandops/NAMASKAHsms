# Tier Feature Matrix

| Feature | Freemium | PAYG | Pro | Custom |
|---------|----------|------|-----|--------|
| SMS Verification | ✅ | ✅ | ✅ | ✅ |
| SMS Rate | $2.22 | $2.50 | $0.30 overage | $0.20 overage |
| Monthly Quota | None | None | $15 | $25 |
| API Keys | ❌ | ❌ | ✅ (10 max) | ✅ (unlimited) |
| Location Filters | ❌ | ✅ (+$0.25) | ✅ | ✅ |
| ISP Filters | ❌ | ✅ (+$0.50) | ✅ | ✅ |
| Affiliate Program | ❌ | ❌ | ✅ | ✅ |
| Priority Support | ❌ | ❌ | ✅ | ✅ |
| Bulk Purchase | ❌ | ❌ | ✅ | ✅ |

## Tier-Gated Endpoints

### Requires: payg+
- `GET /api/verification/area-codes/{country}`
- `GET /api/verification/carriers/{country}`

### Requires: pro+
- `GET /api/keys`
- `POST /api/keys/generate`
- `DELETE /api/keys/{id}`
- `GET /api/affiliate/stats`
