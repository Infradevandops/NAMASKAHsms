# Quick Fix: Run Production Migration Remotely

## 🚨 Problem
Login is broken with error: `column users.credit_hold_amount does not exist`

## ✅ Solution (5 minutes)

### Step 1: Get Your Database URL

1. Go to Render Dashboard: https://dashboard.render.com
2. Click on your **PostgreSQL** database (not the web service)
3. Copy the **External Database URL** (starts with `postgresql://`)

It looks like:
```
postgresql://username:password@dpg-xxxxx.oregon-postgres.render.com/dbname
```

### Step 2: Run Migration Script

Open your terminal and run:

```bash
# Navigate to project directory
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"

# Set database URL (replace with your actual URL)
export DATABASE_URL='postgresql://username:password@dpg-xxxxx.oregon-postgres.render.com/dbname'

# Run migration
python scripts/deployment/migrate_remote_db.py
```

**One-liner version:**
```bash
DATABASE_URL='your_database_url_here' python scripts/deployment/migrate_remote_db.py
```

### Step 3: Restart Render Service

1. Go back to Render Dashboard
2. Click on your **Web Service** (namaskahsms)
3. Click **Manual Deploy** → **Deploy latest commit**
4. Wait for deployment to complete (~2 minutes)

### Step 4: Test Login

Go to https://namaskahsms.onrender.com/login and try logging in.

✅ Should work now!

---

## 🔍 What This Does

The migration adds 4 missing columns to the `users` table:
- `credit_hold_amount` - For tracking held credits
- `credit_hold_reason` - Reason for hold
- `credit_hold_until` - Hold expiration
- `last_reconciliation_at` - Last balance check

---

## ⚠️ Troubleshooting

### "Connection refused" or "timeout"
- Your database might not allow external connections
- Check Render database settings for "External Connections"

### "Permission denied"
- Database user needs ALTER TABLE permission
- This should be automatic on Render

### "Alembic not installed"
```bash
pip install -r requirements.txt
```

### Still not working?
Run the SQL manually in Render's database console:

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS credit_hold_amount NUMERIC(10, 4) NOT NULL DEFAULT 0.0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS credit_hold_reason VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS credit_hold_until TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_reconciliation_at TIMESTAMP;
```

---

## 📞 Need Help?

Check the full guide: `docs/operations/PRODUCTION_MIGRATION_GUIDE.md`
