# Production Database Migration Guide

**Date**: April 18, 2026  
**Migration**: Add Credit Hold & Reconciliation Fields to Users Table  
**Status**: ⚠️ REQUIRED - Login is currently broken without this migration

---

## 🚨 Critical Issue

The production database is missing required columns in the `users` table:
- `credit_hold_amount`
- `credit_hold_reason`
- `credit_hold_until`
- `last_reconciliation_at`

**Impact**: Login is failing with error:
```
column users.credit_hold_amount does not exist
```

---

## 📋 Migration Details

**Migration File**: `c5d8e9f1a2b3_add_credit_hold_and_reconciliation_fields.py`

**Changes**:
1. Adds `credit_hold_amount` (Numeric) - For tracking held credits
2. Adds `credit_hold_reason` (String) - Reason for credit hold
3. Adds `credit_hold_until` (DateTime) - Hold expiration date
4. Adds `last_reconciliation_at` (DateTime) - Last balance reconciliation timestamp
5. Creates performance indices on datetime fields

---

## 🚀 How to Run Migration

### Option 1: Via Render Dashboard (Recommended)

1. Go to your Render dashboard: https://dashboard.render.com
2. Select your Namaskah service
3. Go to **Shell** tab
4. Run the following commands:

```bash
# Navigate to app directory
cd /opt/render/project/src

# Run migration
alembic upgrade head
```

5. Restart the service from the dashboard

### Option 2: Via Local Script (If you have DB access)

```bash
# Set your production database URL
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# Run migration script
./scripts/deployment/run_production_migration.sh
```

### Option 3: Manual SQL (Emergency fallback)

If Alembic fails, you can run this SQL directly on your production database:

```sql
-- Add credit hold fields
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS credit_hold_amount NUMERIC(10, 4) NOT NULL DEFAULT 0.0;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS credit_hold_reason VARCHAR;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS credit_hold_until TIMESTAMP;

-- Add reconciliation tracking
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_reconciliation_at TIMESTAMP;

-- Create indices for performance
CREATE INDEX IF NOT EXISTS ix_users_credit_hold_until 
ON users(credit_hold_until);

CREATE INDEX IF NOT EXISTS ix_users_last_reconciliation_at 
ON users(last_reconciliation_at);
```

---

## ✅ Verification Steps

After running the migration:

1. **Check migration status**:
   ```bash
   alembic current
   # Should show: c5d8e9f1a2b3 (head)
   ```

2. **Verify columns exist**:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'users' 
   AND column_name IN (
     'credit_hold_amount', 
     'credit_hold_reason', 
     'credit_hold_until', 
     'last_reconciliation_at'
   );
   ```

3. **Test login**:
   - Go to https://namaskahsms.onrender.com/login
   - Try logging in with admin credentials
   - Should succeed without "Invalid credentials" error

---

## 🔄 Rollback (If needed)

If something goes wrong:

```bash
# Rollback to previous migration
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade b1279f965154
```

---

## 📊 Expected Results

**Before Migration**:
- ❌ Login fails with database error
- ❌ 500 Internal Server Error on login attempts
- ❌ Logs show: "column users.credit_hold_amount does not exist"

**After Migration**:
- ✅ Login works successfully
- ✅ All user operations function normally
- ✅ Credit hold features available
- ✅ Reconciliation tracking enabled

---

## 🆘 Troubleshooting

### Issue: "relation 'users' does not exist"
**Solution**: Your database might not be initialized. Run:
```bash
alembic upgrade head
```

### Issue: "column already exists"
**Solution**: Migration is idempotent and checks for existing columns. Safe to re-run.

### Issue: Permission denied
**Solution**: Ensure your database user has ALTER TABLE permissions.

### Issue: Alembic not found
**Solution**: Install dependencies first:
```bash
pip install -r requirements.txt
```

---

## 📝 Post-Migration Tasks

1. ✅ Verify login functionality
2. ✅ Test user registration
3. ✅ Check admin dashboard access
4. ✅ Monitor application logs for errors
5. ✅ Update deployment documentation

---

## 🔗 Related Files

- Migration: `alembic/versions/c5d8e9f1a2b3_add_credit_hold_and_reconciliation_fields.py`
- User Model: `app/models/user.py` (lines 68-71)
- Migration Script: `scripts/deployment/run_production_migration.sh`

---

**Status**: Ready to deploy ✅  
**Priority**: CRITICAL 🚨  
**Estimated Time**: 2-5 minutes
