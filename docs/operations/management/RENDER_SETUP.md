# Render Deployment Setup

## Database Connection Issue

If you see this error in Render logs:
```
could not translate host name "dpg-xxxxx-a" to address
```

**Fix:** Update the `DATABASE_URL` environment variable with the full hostname.

### Steps

1. **Get Database URL**
   - Render Dashboard → Databases → Your Database
   - Copy "Internal Database URL"

2. **Update Web Service**
   - Render Dashboard → Services → Your Service
   - Environment tab → Edit `DATABASE_URL`
   - Paste the full URL (should end with `.oregon-postgres.render.com` or similar)
   - Save Changes

3. **Verify**
   - Service will auto-redeploy
   - Check logs for successful startup
   - Test your endpoints

### Required Environment Variables

Ensure these are set in your Render web service:

```bash
DATABASE_URL=postgresql://user:pass@host.region-postgres.render.com/db
ADMIN_EMAIL=your-admin-email
ADMIN_PASSWORD=your-admin-password
SECRET_KEY=your-secret-key-32-chars-minimum
JWT_SECRET_KEY=your-jwt-secret-32-chars-minimum
ENVIRONMENT=production
```

### Database URL Format

**Correct format:**
```
postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com/dbname
```

**Common regions:**
- `oregon-postgres.render.com` (US West)
- `ohio-postgres.render.com` (US East)
- `frankfurt-postgres.render.com` (EU)
- `singapore-postgres.render.com` (Asia)

### Automatic Schema Updates

The application automatically:
- Creates missing database columns on startup
- Creates admin user from environment variables
- Verifies database schema integrity

No manual migrations needed.

---

For detailed setup instructions, see the Render documentation:
https://render.com/docs/databases
