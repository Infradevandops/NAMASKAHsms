# Rclone Configuration for Namaskah

## Quick Setup

### 1. Install Rclone

```bash
# macOS
brew install rclone

# Linux/Render.com
curl https://rclone.org/install.sh | sudo bash

# Verify
rclone version
```

### 2. Configure Remote

```bash
rclone config
```

Follow prompts:
```
n) New remote
name> namaskah-backup
Storage> [choose provider]
[follow provider-specific prompts]
y) Yes this is OK
q) Quit config
```

### 3. Test Connection

```bash
# List buckets
rclone lsd namaskah-backup:

# Test upload
echo "test" > test.txt
rclone copy test.txt namaskah-backup:namaskah-backups/test/
rclone ls namaskah-backup:namaskah-backups/test/
```

---

## Recommended Providers

### Option 1: Backblaze B2 (Recommended)
**Why**: Cheapest, reliable, S3-compatible

**Pricing**:
- Storage: $0.005/GB/month ($5 for 1TB)
- Download: $0.01/GB (first 3x storage free)
- No API fees

**Setup**:
```bash
rclone config
# Storage> backblaze
# account> [your_account_id]
# key> [your_application_key]
```

**Get credentials**: https://www.backblaze.com/b2/cloud-storage.html

### Option 2: AWS S3 (Current)
**Why**: Already using, familiar

**Pricing**:
- Storage: $0.023/GB/month ($23 for 1TB)
- Download: $0.09/GB
- API fees apply

**Setup**:
```bash
rclone config
# Storage> s3
# provider> AWS
# access_key_id> [your_key]
# secret_access_key> [your_secret]
# region> us-east-1
```

### Option 3: Google Drive (Free Tier)
**Why**: 15GB free, easy

**Pricing**:
- Free: 15GB
- Paid: $1.99/month for 100GB

**Setup**:
```bash
rclone config
# Storage> drive
# [follow OAuth flow]
```

### Option 4: Wasabi (Fast)
**Why**: Fast, no egress fees

**Pricing**:
- Storage: $0.0059/GB/month
- No download fees
- Minimum $5.99/month

**Setup**:
```bash
rclone config
# Storage> s3
# provider> Wasabi
# access_key_id> [your_key]
# secret_access_key> [your_secret]
# region> us-east-1
```

---

## Environment Variables

Add to `.env`:

```bash
# Rclone Configuration
RCLONE_REMOTE=namaskah-backup
BACKUP_BUCKET=namaskah-backups
BACKUP_LOCAL_DIR=backups
BACKUP_KEEP_DAYS=30

# Optional: Encryption
RCLONE_ENCRYPT=true
RCLONE_PASSWORD=your-encryption-password

# Optional: Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## Usage Examples

### Daily Automated Backup

```bash
# Add to crontab
crontab -e

# Run at 2 AM daily
0 2 * * * /path/to/namaskah/scripts/deployment/backup_rclone.sh
```

### Manual Backup

```bash
# Full backup
python3 scripts/backup_rclone.py

# Database only
python3 scripts/backup_rclone.py --db-only

# List backups
python3 scripts/backup_rclone.py --list
```

### Restore

```bash
# From cloud
python3 scripts/backup_rclone.py --restore namaskah-backup:namaskah-backups/database/namaskah_backup_20260425_020000.sql.gz

# From local
python3 scripts/backup_rclone.py --restore backups/namaskah_backup_20260425_020000.sql.gz
```

### Sync User Uploads

```bash
# One-time sync
rclone sync uploads/kyc/ namaskah-backup:namaskah-backups/uploads/ --progress

# Continuous sync (every 5 minutes)
watch -n 300 'rclone sync uploads/kyc/ namaskah-backup:namaskah-backups/uploads/'
```

### Archive Logs

```bash
# Archive logs older than 30 days
rclone move logs/ namaskah-backup:namaskah-backups/logs-archive/ --min-age 30d
```

---

## Advanced Features

### 1. Encryption

```bash
# Configure encrypted remote
rclone config
# name> namaskah-backup-encrypted
# Storage> crypt
# remote> namaskah-backup:namaskah-backups
# filename_encryption> standard
# directory_name_encryption> true
# password> [your-password]
```

### 2. Bandwidth Limiting

```bash
# Limit to 10MB/s
rclone sync uploads/ remote:backups/ --bwlimit 10M
```

### 3. Exclude Patterns

```bash
# Exclude sensitive files
rclone sync . remote:full-backup/ \
  --exclude ".env" \
  --exclude "*.log" \
  --exclude "__pycache__/**" \
  --exclude "node_modules/**"
```

### 4. Dry Run (Test)

```bash
# See what would be synced without actually doing it
rclone sync uploads/ remote:backups/ --dry-run
```

### 5. Mount Cloud Storage

```bash
# Mount as local filesystem
mkdir ~/namaskah-backups
rclone mount namaskah-backup:namaskah-backups ~/namaskah-backups --daemon

# Access like local folder
ls ~/namaskah-backups/database/
```

---

## Monitoring

### Check Backup Status

```bash
# List recent backups
rclone ls namaskah-backup:namaskah-backups/database/ | tail -5

# Check backup size
rclone size namaskah-backup:namaskah-backups/

# Verify specific backup
rclone check backups/ namaskah-backup:namaskah-backups/database/
```

### Logs

```bash
# View backup logs
tail -f logs/backup.log

# Search for errors
grep ERROR logs/backup.log
```

---

## Troubleshooting

### "Remote not found"
```bash
# List configured remotes
rclone listremotes

# Reconfigure
rclone config
```

### "Permission denied"
```bash
# Check credentials
rclone lsd namaskah-backup: -vv

# Reconfigure with correct credentials
rclone config update namaskah-backup
```

### "Slow uploads"
```bash
# Increase transfers
rclone sync uploads/ remote:backups/ --transfers 8 --checkers 16

# Use multiple connections
rclone sync uploads/ remote:backups/ --multi-thread-streams 4
```

---

## Cost Comparison

For 100GB backup + 10GB monthly uploads:

| Provider | Storage | Transfer | Total/Month |
|----------|---------|----------|-------------|
| Backblaze B2 | $0.50 | $0.10 | **$0.60** |
| AWS S3 | $2.30 | $0.90 | **$3.20** |
| Google Drive | $1.99 | Free | **$1.99** |
| Wasabi | $5.99 | Free | **$5.99** |

**Recommendation**: Backblaze B2 for production

---

## Security Best Practices

1. ✅ Use encryption for sensitive data
2. ✅ Store credentials in environment variables
3. ✅ Enable versioning on cloud storage
4. ✅ Test restores monthly
5. ✅ Monitor backup logs
6. ✅ Use separate credentials for backups
7. ✅ Enable MFA on cloud account

---

## Next Steps

1. Choose provider (recommend Backblaze B2)
2. Run `rclone config`
3. Test with `python3 scripts/backup_rclone.py --db-only`
4. Set up cron job for daily backups
5. Test restore procedure
6. Monitor for 1 week
7. Document for team

---

**Status**: Ready to implement
**Estimated Setup Time**: 30 minutes
**Monthly Cost**: $0.60 - $6.00 depending on provider
