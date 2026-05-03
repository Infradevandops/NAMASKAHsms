# Free Tier Backup Setup for Namaskah

## 🎯 Strategy: 100% Free Infrastructure

### Primary Database
✅ **Render PostgreSQL (Free Tier)**
- 1GB storage
- Full PostgreSQL features
- Auto-renews every 90 days
- **Cost: $0/month**

### Backup Storage (Multi-Cloud)
✅ **Google Drive** - 15GB free (Daily backups)
✅ **OneDrive** - 5GB free (Weekly backups)
✅ **MEGA** - 20GB free (Monthly archives)

**Total Free Storage: 40GB**
**Cost: $0/month**

---

## 🚀 Setup Instructions

### Step 1: Install Rclone

```bash
# macOS
brew install rclone

# Linux/Render.com
curl https://rclone.org/install.sh | sudo bash

# Verify
rclone version
```

### Step 2: Configure Google Drive (15GB Free)

```bash
rclone config

# Follow prompts:
n) New remote
name> gdrive
Storage> drive
client_id> [press Enter for default]
client_secret> [press Enter for default]
scope> 1  # Full access
root_folder_id> [press Enter]
service_account_file> [press Enter]
y) Yes, use auto config
[Browser opens for OAuth]
y) Yes this is OK
q) Quit config
```

**Test**:
```bash
rclone lsd gdrive:
rclone mkdir gdrive:Namaskah-Backups
```

### Step 3: Configure OneDrive (5GB Free)

```bash
rclone config

# Follow prompts:
n) New remote
name> onedrive
Storage> onedrive
client_id> [press Enter for default]
client_secret> [press Enter for default]
y) Yes, use auto config
[Browser opens for OAuth]
1) OneDrive Personal or Business
0) Microsoft Cloud Global
y) Yes this is OK
q) Quit config
```

**Test**:
```bash
rclone lsd onedrive:
rclone mkdir onedrive:Namaskah-Backups
```

### Step 4: Configure MEGA (20GB Free)

```bash
rclone config

# Follow prompts:
n) New remote
name> mega
Storage> mega
user> your-mega-email@example.com
y) Yes type in my own password
password> [your-mega-password]
y) Yes this is OK
q) Quit config
```

**Get MEGA account**: https://mega.nz/register (20GB free)

**Test**:
```bash
rclone lsd mega:
rclone mkdir mega:Namaskah-Backups
```

---

## 📅 Backup Schedule

### Daily (Google Drive)
```bash
# Add to crontab
crontab -e

# Run at 2 AM daily
0 2 * * * cd /path/to/namaskah && python3 scripts/backup_free_tier.py
```

**What happens**:
- ✅ Backup database to local
- ✅ Upload to Google Drive
- ✅ Keep last 30 backups in cloud
- ✅ Keep last 7 days locally

### Weekly (OneDrive)
Automatically runs on Sundays via same script

### Monthly (MEGA)
Automatically runs on 1st of month via same script

---

## 💾 Storage Management

### Google Drive (15GB)
- **Usage**: ~30 daily backups
- **Per backup**: ~50MB (compressed)
- **Total**: ~1.5GB
- **Remaining**: 13.5GB for other files

### OneDrive (5GB)
- **Usage**: ~4 weekly backups
- **Per backup**: ~50MB
- **Total**: ~200MB
- **Remaining**: 4.8GB

### MEGA (20GB)
- **Usage**: ~12 monthly backups
- **Per backup**: ~50MB
- **Total**: ~600MB
- **Remaining**: 19.4GB

**Total Backup Coverage**:
- Daily: Last 30 days
- Weekly: Last 4 weeks
- Monthly: Last 12 months

---

## 🔄 Usage Examples

### Backup Now
```bash
python3 scripts/backup_free_tier.py
```

### List All Backups
```bash
python3 scripts/backup_free_tier.py --list
```

### Restore from Google Drive
```bash
python3 scripts/backup_free_tier.py --restore gdrive:Namaskah-Backups/database/namaskah_backup_20260425_020000.sql.gz
```

### Restore from OneDrive
```bash
python3 scripts/backup_free_tier.py --restore onedrive:Namaskah-Backups/database/namaskah_backup_20260425_020000.sql.gz
```

### Restore from MEGA
```bash
python3 scripts/backup_free_tier.py --restore mega:Namaskah-Backups/database/namaskah_backup_20260425_020000.sql.gz
```

---

## 📊 Cost Comparison

### Your Original Idea (❌ Not Recommended)
```
Replace PostgreSQL with Google Drive as database
Cost: $0/month
Performance: 100x slower ❌
Reliability: Data corruption risk ❌
Scalability: No concurrent access ❌
```

### Recommended Setup (✅ Best)
```
PostgreSQL (Render Free) + Multi-Cloud Backups
Cost: $0/month
Performance: Fast ✅
Reliability: ACID transactions ✅
Scalability: Unlimited concurrent users ✅
Backups: 3 cloud providers ✅
```

---

## 🎯 Why This is Better

### Your Idea vs Recommended

| Aspect | Your Idea | Recommended |
|--------|-----------|-------------|
| **Database** | Files on Drive ❌ | PostgreSQL ✅ |
| **Performance** | 5000ms ❌ | 50ms ✅ |
| **Concurrent Users** | 1 ❌ | Unlimited ✅ |
| **Data Safety** | Corruption risk ❌ | ACID ✅ |
| **Backups** | None ❌ | 3 clouds ✅ |
| **Cost** | $0 ✅ | $0 ✅ |

**Winner**: Recommended (5 vs 2)

---

## 🔒 Security

### Encryption at Rest
All providers encrypt data:
- ✅ Google Drive: AES-256
- ✅ OneDrive: AES-256
- ✅ MEGA: End-to-end encryption

### Additional Encryption (Optional)
```bash
# Encrypt backups before upload
rclone config

name> gdrive-encrypted
Storage> crypt
remote> gdrive:Namaskah-Backups
filename_encryption> standard
password> [your-encryption-password]
```

---

## 🆘 Disaster Recovery

### Scenario 1: Render Database Deleted
```bash
# Restore from latest Google Drive backup
python3 scripts/backup_free_tier.py --restore gdrive:Namaskah-Backups/database/[latest-file]
```

**Recovery Time**: 5-10 minutes

### Scenario 2: Google Drive Account Compromised
```bash
# Restore from OneDrive or MEGA
python3 scripts/backup_free_tier.py --restore onedrive:Namaskah-Backups/database/[latest-file]
```

**Recovery Time**: 5-10 minutes

### Scenario 3: All Cloud Backups Lost
```bash
# Restore from local backup (last 7 days)
python3 scripts/backup_free_tier.py --restore backups/[latest-file]
```

**Recovery Time**: 2 minutes

---

## ✅ Verification Checklist

After setup:

- [ ] Rclone installed
- [ ] Google Drive configured and tested
- [ ] OneDrive configured and tested
- [ ] MEGA configured and tested
- [ ] Cron job added
- [ ] Test backup runs successfully
- [ ] Test restore works
- [ ] Verify backups appear in all 3 clouds

---

## 📞 Support

### Common Issues

**"Remote not found"**
```bash
rclone listremotes  # Check configured remotes
rclone config  # Reconfigure
```

**"Quota exceeded"**
```bash
# Check usage
rclone about gdrive:
rclone about onedrive:
rclone about mega:

# Cleanup old backups
python3 scripts/backup_free_tier.py  # Auto-cleanup runs
```

**"Backup failed"**
```bash
# Check logs
tail -f logs/backup.log

# Test connection
rclone lsd gdrive:
```

---

## 🎉 Summary

### What You Get (100% Free)

✅ **Production Database**: Render PostgreSQL (1GB free)
✅ **Daily Backups**: Google Drive (15GB free)
✅ **Weekly Backups**: OneDrive (5GB free)
✅ **Monthly Archives**: MEGA (20GB free)
✅ **Total Storage**: 40GB free
✅ **Backup Retention**: 30 days + 4 weeks + 12 months
✅ **Cost**: $0/month forever

### What You DON'T Do

❌ Replace PostgreSQL with file storage
❌ Use cloud storage as primary database
❌ Risk data corruption
❌ Sacrifice performance

---

**Status**: ✅ Ready to implement
**Cost**: $0/month
**Setup Time**: 30 minutes
**Maintenance**: Automatic (cron job)
