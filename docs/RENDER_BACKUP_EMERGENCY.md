# Emergency Backup Guide - Render PostgreSQL Data Extraction

## 🚨 Situation

Your Render PostgreSQL database is expiring/expired. You need to extract ALL data immediately before it's deleted.

---

## ⚡ Quick Start (5 Minutes)

### Option 1: Python Script (Recommended)
```bash
# Run emergency backup
python3 scripts/backup_render_emergency.py
```

### Option 2: Bash Script
```bash
# Run emergency backup
./scripts/backup_render_emergency.sh
```

### Option 3: Manual Backup
```bash
# Quick manual backup
pg_dump "postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a/namaskahdb_qg9v" > render_backup_$(date +%Y%m%d).sql
```

---

## 📦 What Gets Backed Up

### 1. Full Database Backup
- **full_backup.sql** - Complete SQL dump (use for migration)
- **full_backup.sql.gz** - Compressed version (smaller, faster upload)

### 2. Schema Only
- **schema_only.sql** - Database structure without data

### 3. Individual Tables (CSV)
- **csv_exports/** - Each table as CSV file
  - users.csv
  - transactions.csv
  - verifications.csv
  - subscription_tiers.csv
  - etc.

### 4. Critical Data (JSON)
- **json_exports/** - Important tables as JSON
  - users.json
  - transactions.json
  - verifications.json
  - subscription_tiers.json

### 5. Metadata
- **table_statistics.txt** - Row counts per table
- **database_size.txt** - Total database size
- **BACKUP_MANIFEST.txt** - Complete backup documentation
- **CHECKSUMS.md5** - File integrity verification

---

## 🎯 Step-by-Step Backup Process

### Step 1: Run Backup Script (5 min)

```bash
# Using Python (cross-platform)
python3 scripts/backup_render_emergency.py

# Or using Bash (Linux/Mac)
./scripts/backup_render_emergency.sh
```

**What it does**:
1. ✅ Tests database connection
2. ✅ Gets database statistics
3. ✅ Backs up schema
4. ✅ Backs up full database
5. ✅ Compresses backup
6. ✅ Exports tables as CSV
7. ✅ Exports critical data as JSON
8. ✅ Creates manifest and checksums

**Output**: `render_backup_YYYYMMDD_HHMMSS/` directory

### Step 2: Verify Backup (2 min)

```bash
# Check backup directory
ls -lh render_backup_*/

# View manifest
cat render_backup_*/BACKUP_MANIFEST.txt

# Verify checksums
cd render_backup_*/
md5sum -c CHECKSUMS.md5
```

**Expected files**:
- ✅ full_backup.sql (10-100 MB)
- ✅ full_backup.sql.gz (1-10 MB)
- ✅ schema_only.sql (100-500 KB)
- ✅ csv_exports/ (multiple CSV files)
- ✅ json_exports/ (multiple JSON files)

### Step 3: Upload to Cloud (5 min)

```bash
# To Google Drive (15GB free)
rclone copy render_backup_*/ gdrive:Namaskah-Backups/render_final/

# To OneDrive (5GB free)
rclone copy render_backup_*/ onedrive:Namaskah-Backups/render_final/

# To MEGA (20GB free)
rclone copy render_backup_*/ mega:Namaskah-Backups/render_final/
```

**Or manually**:
1. Compress backup: `tar -czf render_backup.tar.gz render_backup_*/`
2. Upload to Google Drive via web interface
3. Keep local copy until migration complete

### Step 4: Test Restore (Optional but Recommended)

```bash
# Create test database
createdb namaskah_test

# Restore backup
psql namaskah_test < render_backup_*/full_backup.sql

# Verify tables
psql namaskah_test -c "\dt"

# Check row counts
psql namaskah_test -c "SELECT COUNT(*) FROM users;"

# Drop test database
dropdb namaskah_test
```

---

## 🔍 Backup Verification Checklist

### File Integrity
- [ ] full_backup.sql exists and is > 1MB
- [ ] full_backup.sql.gz exists and is > 100KB
- [ ] schema_only.sql exists
- [ ] csv_exports/ has multiple CSV files
- [ ] json_exports/ has JSON files
- [ ] BACKUP_MANIFEST.txt exists

### Content Verification
- [ ] Can open full_backup.sql in text editor
- [ ] First line starts with `--` or `SET`
- [ ] Contains `CREATE TABLE` statements
- [ ] Contains `INSERT INTO` or `COPY` statements
- [ ] CSV files have headers and data
- [ ] JSON files are valid JSON

### Size Verification
```bash
# Check sizes
du -sh render_backup_*/

# Expected sizes (approximate):
# - Full backup: 10-100 MB
# - Compressed: 1-10 MB
# - CSV exports: 5-50 MB
# - JSON exports: 1-20 MB
```

---

## 🆘 Troubleshooting

### "Cannot connect to database"

**Problem**: Database already deleted or inaccessible

**Solution**:
1. Check if you have existing backups:
   ```bash
   find . -name "*backup*.sql*" -o -name "render_backup_*"
   ```

2. Check Render dashboard for manual backups:
   - Render Dashboard → Database → Backups → Download

3. If no backups exist:
   - Contact Render support immediately
   - Check if database can be temporarily restored

### "pg_dump: command not found"

**Problem**: PostgreSQL client tools not installed

**Solution**:
```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt-get install postgresql-client

# Windows
# Download from: https://www.postgresql.org/download/windows/
```

### "Permission denied"

**Problem**: Script not executable

**Solution**:
```bash
chmod +x scripts/backup_render_emergency.sh
chmod +x scripts/backup_render_emergency.py
```

### "Backup file is empty"

**Problem**: Database connection failed or database is empty

**Solution**:
1. Test connection manually:
   ```bash
   psql "postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a/namaskahdb_qg9v" -c "SELECT COUNT(*) FROM users;"
   ```

2. Check database status in Render dashboard

3. Try alternative backup method:
   ```bash
   pg_dump --verbose "postgresql://..." > backup.sql 2> backup.log
   cat backup.log  # Check for errors
   ```

---

## 📊 Your Current Database

Based on your `.env.production`:

**Connection String**:
```
postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a/namaskahdb_qg9v
```

**Expected Tables**:
- users
- transactions
- verifications
- subscription_tiers
- api_keys
- notifications
- webhooks
- referrals
- blacklist
- forwarding_rules
- etc.

**Estimated Size**: 50-200 MB (based on typical usage)

---

## 🔐 Security Considerations

### Sensitive Data in Backup

Your backup contains:
- ⚠️ User passwords (hashed)
- ⚠️ Email addresses
- ⚠️ Phone numbers
- ⚠️ Transaction history
- ⚠️ API keys
- ⚠️ Payment information

### Security Best Practices

1. **Encrypt before uploading**:
   ```bash
   # Encrypt backup
   gpg -c render_backup_*/full_backup.sql.gz

   # Upload encrypted file
   rclone copy full_backup.sql.gz.gpg gdrive:Namaskah-Backups/
   ```

2. **Use private cloud storage**:
   - Don't upload to public folders
   - Enable 2FA on cloud accounts
   - Use strong passwords

3. **Delete after migration**:
   - Keep backup for 30 days after successful migration
   - Securely delete local copies
   - Remove from cloud after verification

---

## 📋 Post-Backup Checklist

### Immediate (Today)
- [ ] Backup completed successfully
- [ ] Verified backup files exist
- [ ] Uploaded to at least 1 cloud provider
- [ ] Kept local copy

### Before Migration (This Week)
- [ ] Tested restore to local database
- [ ] Verified all tables present
- [ ] Checked row counts match
- [ ] Uploaded to 2+ cloud providers

### After Migration (Next Week)
- [ ] Successfully migrated to new provider
- [ ] Verified data in new database
- [ ] Tested application with new database
- [ ] Kept backup for 30 days

### Cleanup (After 30 Days)
- [ ] Confirmed new database stable
- [ ] No data loss detected
- [ ] Securely delete local backups
- [ ] Archive cloud backups

---

## 🚀 Next Steps After Backup

### 1. Choose New Provider
**Recommended**: Supabase (500MB free, PostgreSQL)

See: `docs/DATABASE_PROVIDER_DECISION.md`

### 2. Migrate Data
```bash
# Using migration script
./scripts/migrate_database.sh supabase "NEW_DATABASE_URL"

# Or manually
psql "NEW_DATABASE_URL" < render_backup_*/full_backup.sql
```

See: `docs/DATABASE_MIGRATION_GUIDE.md`

### 3. Update Application
```bash
# Update .env
DATABASE_URL=postgresql://new-provider-url

# Test locally
./start.sh

# Deploy to production
git push origin main
```

### 4. Verify Migration
```bash
# Check tables
psql "NEW_DATABASE_URL" -c "\dt"

# Check row counts
psql "NEW_DATABASE_URL" -c "SELECT COUNT(*) FROM users;"

# Test application
curl https://your-app.com/api/health
```

---

## 📞 Emergency Contacts

### If Database Already Deleted

1. **Check Render Dashboard**:
   - Render → Database → Backups
   - Download any available backups

2. **Contact Render Support**:
   - Email: support@render.com
   - Request temporary database restoration

3. **Check Local Backups**:
   ```bash
   find . -name "*backup*.sql*"
   ls -lh backups/
   ```

4. **Check Cloud Backups**:
   ```bash
   rclone ls gdrive:Namaskah-Backups/
   rclone ls onedrive:Namaskah-Backups/
   ```

---

## ✅ Summary

### What to Do RIGHT NOW

```bash
# 1. Backup immediately (5 min)
python3 scripts/backup_render_emergency.py

# 2. Verify backup (2 min)
ls -lh render_backup_*/
cat render_backup_*/BACKUP_MANIFEST.txt

# 3. Upload to cloud (5 min)
rclone copy render_backup_*/ gdrive:Namaskah-Backups/render_final/

# 4. Keep local copy
# Don't delete until migration complete!
```

### Total Time: 12 minutes

**Your data will be safe!** ✅

---

**Status**: 🚨 URGENT - Backup immediately
**Priority**: P0 - Critical
**Time Required**: 12 minutes
**Risk**: High if not done today
