# 🎯 Get Render Database Connection & Backup Data

## 🔍 Issue Found

Your `.env.production` has an **incomplete connection string**:
```
❌ postgresql://namaskahdb:...@dpg-d7geq9vlk1mc7386tjl0-a/namaskahdb_qg9v
```

It should be:
```
✅ postgresql://namaskahdb:...@dpg-d7geq9vlk1mc7386tjl0-a.oregon-postgres.render.com:5432/namaskahdb_qg9v
```

The hostname is missing the region suffix (`.oregon-postgres.render.com` or similar).

---

## ⚡ Step 1: Get Full Connection String (2 minutes)

### Option A: From Render Dashboard (Recommended)

1. **Go to**: https://dashboard.render.com
2. **Login** with your account
3. **Find your database**: Look for `namaskahdb` in your services
4. **Click on the database**
5. **Scroll down** to "Connections" section
6. **Copy** the connection string

You'll see two options:
- **Internal Database URL** (for apps on Render)
- **External Database URL** (for external access)

**Copy the External Database URL** - it looks like:
```
postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a.oregon-postgres.render.com:5432/namaskahdb_qg9v
```

### Option B: From Render CLI

```bash
# Install Render CLI
npm install -g @render/cli

# Login
render login

# List databases
render services list --type database

# Get connection info
render service info namaskahdb
```

---

## ⚡ Step 2: Test Connection (1 minute)

Once you have the full connection string:

```bash
# Test connection
psql "postgresql://namaskahdb:PASSWORD@dpg-xxx.REGION-postgres.render.com:5432/namaskahdb_qg9v" -c "SELECT version();"

# If successful, you'll see PostgreSQL version
# If failed, check:
# - Password is correct
# - Hostname is complete
# - Database still exists
```

---

## ⚡ Step 3: Backup Data (5 minutes)

### Method 1: Using Our Script (Recommended)

```bash
# Update the script with correct connection string
export RENDER_DB_URL="postgresql://namaskahdb:PASSWORD@dpg-xxx.REGION-postgres.render.com:5432/namaskahdb_qg9v"

# Run backup
python3 scripts/backup_render_emergency.py
```

### Method 2: Manual Backup

```bash
# Full backup
pg_dump "postgresql://namaskahdb:PASSWORD@dpg-xxx.REGION-postgres.render.com:5432/namaskahdb_qg9v" > render_backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump "postgresql://namaskahdb:PASSWORD@dpg-xxx.REGION-postgres.render.com:5432/namaskahdb_qg9v" | gzip > render_backup_$(date +%Y%m%d).sql.gz
```

### Method 3: From Render Dashboard

1. **Render Dashboard** → Your Database
2. **Backups** tab
3. **Download** latest backup
4. Save to `backups/` directory

---

## ⚡ Step 4: Inspect Database Contents (3 minutes)

Once connected, let's see what's in your database:

```bash
# Set connection string
export DB_URL="postgresql://namaskahdb:PASSWORD@dpg-xxx.REGION-postgres.render.com:5432/namaskahdb_qg9v"

# List all tables
psql "$DB_URL" -c "\dt"

# Get row counts for all tables
psql "$DB_URL" -c "
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"

# Check database size
psql "$DB_URL" -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Check specific tables
psql "$DB_URL" -c "SELECT COUNT(*) FROM users;"
psql "$DB_URL" -c "SELECT COUNT(*) FROM transactions;"
psql "$DB_URL" -c "SELECT COUNT(*) FROM verifications;"
```

---

## 📊 What to Look For

### Critical Tables (Should Exist)

| Table | Expected Rows | Importance |
|-------|---------------|------------|
| **users** | 10-1000+ | 🔴 Critical |
| **transactions** | 50-5000+ | 🔴 Critical |
| **verifications** | 100-10000+ | 🔴 Critical |
| **subscription_tiers** | 4-10 | 🟡 Important |
| **api_keys** | 0-100 | 🟡 Important |
| **notifications** | 0-1000+ | 🟢 Optional |
| **webhooks** | 0-50 | 🟢 Optional |

### Database Size

**Expected**: 50-500 MB depending on usage

**If smaller**: Might be a new/test database
**If larger**: Lots of data to backup

---

## 🎯 Quick Commands Reference

### Get Full Connection String
```bash
# From Render Dashboard
# Dashboard → Database → Connections → External Database URL
```

### Test Connection
```bash
psql "FULL_CONNECTION_STRING" -c "SELECT version();"
```

### Quick Backup
```bash
pg_dump "FULL_CONNECTION_STRING" | gzip > backup_$(date +%Y%m%d).sql.gz
```

### List Tables
```bash
psql "FULL_CONNECTION_STRING" -c "\dt"
```

### Count Rows
```bash
psql "FULL_CONNECTION_STRING" -c "SELECT COUNT(*) FROM users;"
```

### Database Size
```bash
psql "FULL_CONNECTION_STRING" -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
```

---

## 🔧 Interactive Backup Script

Let me create an interactive script that will prompt you for the connection string:

```bash
# Run this
python3 scripts/backup_render_interactive.py
```

This will:
1. Ask for your full connection string
2. Test the connection
3. Show database statistics
4. Backup all data
5. Verify backup integrity

---

## 📋 Checklist

### Before Proceeding
- [ ] Logged into Render Dashboard
- [ ] Found your database (namaskahdb)
- [ ] Copied FULL connection string (with .render.com suffix)
- [ ] Tested connection with psql
- [ ] Connection successful

### After Connection Works
- [ ] Listed all tables
- [ ] Checked row counts
- [ ] Verified database size
- [ ] Created full backup
- [ ] Verified backup file exists
- [ ] Uploaded backup to cloud

---

## 🆘 Troubleshooting

### "Could not translate host name"
**Problem**: Incomplete hostname
**Solution**: Get full connection string from Render Dashboard

### "Password authentication failed"
**Problem**: Wrong password
**Solution**: Copy password exactly from Render Dashboard (no spaces)

### "Database does not exist"
**Problem**: Database deleted or wrong name
**Solution**: Check Render Dashboard for correct database name

### "Connection timed out"
**Problem**: Network issue or database suspended
**Solution**:
1. Check Render status: https://status.render.com
2. Verify database is running in dashboard
3. Try from different network

---

## ✅ Next Steps

Once you have the full connection string and can connect:

1. **Backup immediately**:
   ```bash
   python3 scripts/backup_render_emergency.py
   ```

2. **Inspect data**:
   ```bash
   psql "$DB_URL" -c "\dt"
   psql "$DB_URL" -c "SELECT COUNT(*) FROM users;"
   ```

3. **Upload to cloud**:
   ```bash
   rclone copy render_backup_*/ gdrive:Namaskah-Backups/
   ```

4. **Migrate to Supabase**:
   ```bash
   ./scripts/migrate_database.sh supabase "NEW_URL"
   ```

---

## 📞 What to Share

Once you get the connection string, share:
- ✅ Can you connect? (yes/no)
- ✅ Number of tables
- ✅ Number of users
- ✅ Database size
- ✅ Any errors

Then we'll proceed with the backup and migration!

---

**Status**: ⏸️ Waiting for full connection string
**Action**: Get connection string from Render Dashboard
**Time**: 2 minutes
