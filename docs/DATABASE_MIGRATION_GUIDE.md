# Database Migration Guide - Render PostgreSQL Alternatives

## 🚨 Situation: Render Free PostgreSQL Ended

Render's free PostgreSQL tier has expired/ended. You need to migrate to a new provider.

---

## 🏆 Recommended Provider: **Supabase**

### Why Supabase?

✅ **Best for Namaskah**:
- 500MB database (enough for your needs)
- PostgreSQL 15 (same as Render)
- No credit card required
- Free forever
- Built-in features (auth, storage, realtime)
- Automatic backups
- Great dashboard

✅ **Perfect Match**:
- Your current DB size: ~50-100MB
- Supabase limit: 500MB
- Room to grow: 5-10x

---

## 🚀 Migration Steps (30 Minutes)

### Step 1: Create Supabase Account (5 min)

1. Go to https://supabase.com
2. Sign up with GitHub/Google
3. Click "New Project"
4. Fill in:
   - **Name**: namaskah-production
   - **Database Password**: [generate strong password]
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free
5. Click "Create new project" (takes 2-3 minutes)

### Step 2: Get Connection String (2 min)

1. In Supabase dashboard → Settings → Database
2. Scroll to "Connection string"
3. Select "URI" tab
4. Copy the connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual password

### Step 3: Backup Current Database (5 min)

```bash
# If Render DB still accessible
pg_dump $DATABASE_URL > render_backup_$(date +%Y%m%d).sql

# Or use your backup script
python3 scripts/backup_database.py

# Or download from Render dashboard
# Render Dashboard → Database → Backups → Download
```

### Step 4: Run Migration Script (10 min)

```bash
# Make script executable (if not already)
chmod +x scripts/migrate_database.sh

# Run migration
./scripts/migrate_database.sh supabase "postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres"
```

**What it does**:
1. ✅ Backs up current database
2. ✅ Tests new connection
3. ✅ Restores data to Supabase
4. ✅ Verifies migration
5. ✅ Updates .env files
6. ✅ Creates backup of old configs

### Step 5: Test Locally (5 min)

```bash
# Test database connection
python3 -c "from app.core.database import test_database_connection; print(test_database_connection())"

# Run migrations
alembic upgrade head

# Start app
./start.sh

# Test in browser
open http://localhost:8000
```

### Step 6: Update Production (3 min)

**If using Render for hosting**:
1. Render Dashboard → Your Service → Environment
2. Update `DATABASE_URL` with new Supabase URL
3. Save (auto-deploys)

**If using other hosting**:
1. Update environment variable in your hosting dashboard
2. Redeploy application

---

## 📊 Provider Comparison (Quick Reference)

| Feature | Supabase | Neon | Railway | PlanetScale |
|---------|----------|------|---------|-------------|
| **Storage** | 500MB | 3GB | ~500hrs | 5GB |
| **Type** | PostgreSQL | PostgreSQL | PostgreSQL | MySQL |
| **Credit Card** | No | No | Yes | No |
| **Backups** | Auto | Manual | Auto | Auto |
| **Dashboard** | Excellent | Good | Good | Excellent |
| **Migration** | Easy | Easy | Easy | Hard (MySQL) |
| **Best For** | ✅ **Namaskah** | Large DB | Render users | High traffic |

---

## 🎯 Detailed Provider Guides

### Option 1: Supabase (Recommended) ⭐

**Setup**:
```bash
# 1. Sign up: https://supabase.com
# 2. New Project → namaskah-production
# 3. Copy connection string from Settings → Database

# 4. Migrate
./scripts/migrate_database.sh supabase "postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres"

# 5. Update production
# Render/Hosting Dashboard → Environment → DATABASE_URL
```

**Connection String Format**:
```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Free Tier Limits**:
- 500MB database
- 2GB bandwidth/month
- 50MB file storage
- Unlimited API requests

**Pros**:
- ✅ No credit card
- ✅ Best dashboard
- ✅ Built-in auth/storage
- ✅ Auto backups

**Cons**:
- ⚠️ 500MB limit (but enough for you)

---

### Option 2: Neon (More Storage)

**Setup**:
```bash
# 1. Sign up: https://neon.tech
# 2. Create project → Choose region
# 3. Copy connection string

# 4. Migrate
./scripts/migrate_database.sh neon "postgresql://[USER]:[PASSWORD]@[ENDPOINT].neon.tech/[DBNAME]?sslmode=require"

# 5. Update production
```

**Connection String Format**:
```
postgresql://[user]:[password]@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Free Tier Limits**:
- 3GB storage
- 191.9 compute hours/month
- 1 project

**Pros**:
- ✅ More storage (3GB)
- ✅ Serverless (auto-scales)
- ✅ Instant branching

**Cons**:
- ⚠️ Compute hour limits

---

### Option 3: Railway (Render Alternative)

**Setup**:
```bash
# 1. Sign up: https://railway.app
# 2. New Project → PostgreSQL
# 3. Copy connection string from Variables tab

# 4. Migrate
./scripts/migrate_database.sh railway "postgresql://postgres:[PASSWORD]@[HOST].railway.app:5432/railway"

# 5. Update production
```

**Connection String Format**:
```
postgresql://postgres:[PASSWORD]@containers-us-west-xxx.railway.app:5432/railway
```

**Free Tier**:
- $5 credit/month
- ~500 hours compute
- Credit card required (not charged)

**Pros**:
- ✅ Similar to Render
- ✅ Easy migration
- ✅ Redis included

**Cons**:
- ⚠️ Credit card required
- ⚠️ Limited free credit

---

## 🔄 Migration Checklist

### Pre-Migration
- [ ] Backup current database
- [ ] Test backup restore locally
- [ ] Choose new provider
- [ ] Create account on new provider
- [ ] Get connection string

### Migration
- [ ] Run migration script
- [ ] Verify data transferred
- [ ] Test application locally
- [ ] Check all tables exist
- [ ] Verify user data intact

### Post-Migration
- [ ] Update production environment
- [ ] Deploy application
- [ ] Test production app
- [ ] Monitor for errors
- [ ] Update documentation

### Cleanup (After 1 Week)
- [ ] Verify everything works
- [ ] Delete Render database (if accessible)
- [ ] Update team documentation
- [ ] Archive old backups

---

## 🆘 Troubleshooting

### "Cannot connect to database"
```bash
# Test connection manually
psql "postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres"

# Check SSL requirement
# Add ?sslmode=require to connection string
```

### "Migration failed"
```bash
# Check backup file
ls -lh *.sql

# Restore manually
psql "NEW_DATABASE_URL" < backup.sql

# Check for errors
tail -100 migration.log
```

### "Tables missing after migration"
```bash
# List tables in new database
psql "NEW_DATABASE_URL" -c "\dt"

# Re-run migration
./scripts/migrate_database.sh [provider] [url]

# Or restore from backup
psql "NEW_DATABASE_URL" < backup.sql
```

### "Application won't start"
```bash
# Check DATABASE_URL is set
echo $DATABASE_URL

# Test connection
python3 -c "from app.core.database import test_database_connection; print(test_database_connection())"

# Check logs
tail -f logs/app.log
```

---

## 💰 Cost Comparison

### Current (Render - Expired)
```
Cost: $0/month (but no longer available)
```

### Supabase (Recommended)
```
Free Tier: 500MB database
Cost: $0/month forever
Upgrade: $25/month for 8GB (if needed later)
```

### Neon
```
Free Tier: 3GB database
Cost: $0/month forever
Upgrade: $19/month for 10GB (if needed later)
```

### Railway
```
Free Tier: $5 credit/month (~500 hours)
Cost: $0/month (with credit)
After credit: ~$5-10/month
```

---

## 🎯 Recommendation

### For Namaskah: **Use Supabase**

**Why**:
1. ✅ Your DB is ~50-100MB (well under 500MB limit)
2. ✅ No credit card required
3. ✅ Best dashboard and features
4. ✅ Free forever
5. ✅ Room to grow 5-10x

**Timeline**:
- Setup: 5 minutes
- Migration: 10 minutes
- Testing: 5 minutes
- Production: 5 minutes
- **Total: 25 minutes**

**Risk**: Low (easy rollback with backups)

---

## 🚀 Quick Start Command

```bash
# One-command migration to Supabase
./scripts/migrate_database.sh supabase "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
```

Replace:
- `[YOUR-PASSWORD]` - Your Supabase database password
- `[PROJECT-REF]` - Your Supabase project reference (from dashboard)

---

## 📞 Support

### Supabase
- Docs: https://supabase.com/docs
- Discord: https://discord.supabase.com
- Status: https://status.supabase.com

### Neon
- Docs: https://neon.tech/docs
- Discord: https://discord.gg/neon
- Status: https://neonstatus.com

### Railway
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

---

**Status**: ✅ Ready to Migrate  
**Recommended**: Supabase  
**Time**: 25 minutes  
**Cost**: $0/month  
**Risk**: Low
