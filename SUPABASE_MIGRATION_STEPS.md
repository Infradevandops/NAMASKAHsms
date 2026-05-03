# 🚀 Switch to Supabase - Quick Steps

## ✅ Your Supabase is Ready

**Status**: Healthy ✅
**Region**: Central EU (Frankfurt) 
**Connection**: `postgresql://postgres:rgW&X7}azUC@db.glhhmjqewgptmzqojtwx.supabase.co:5432/postgres`

---

## ⚡ Update Render Environment (2 Minutes)

### Step 1: Go to Render Dashboard
1. Open: https://dashboard.render.com
2. Click your service: **vrenum**
3. Click: **Environment** (left sidebar)

### Step 2: Update DATABASE_URL
1. Find: `DATABASE_URL`
2. Click: **Edit** (pencil icon)
3. **Replace with**:
```
postgresql://postgres:rgW&X7}azUC@db.glhhmjqewgptmzqojtwx.supabase.co:5432/postgres
```
4. Click: **Save**

### Step 3: Migrate Data First (Optional but Recommended)

Before the auto-redeploy happens, let's migrate your data:

**Option A: From Render Dashboard**
1. Go to your Render PostgreSQL database
2. Click: **Backups** tab  
3. Download latest backup
4. Restore to Supabase (I'll help with this)

**Option B: Use Our CSV Backups**
We already have all your data in `render_backup_final/` - we can import those CSVs to Supabase.

---

## 🎯 What Happens Next

1. ✅ You save the new DATABASE_URL
2. ⏳ Render auto-redeploys (3-5 minutes)
3. ✅ App connects to Supabase
4. ✅ App starts successfully!

---

## ⚠️ Important: Migrate Data First

Your Supabase database is **empty** right now. We need to:

1. **Create tables** (run migrations)
2. **Import data** (465 rows from Render)

**Do you want to**:
- **A**: Migrate data now (10 minutes, safer)
- **B**: Update Render first, migrate after (5 minutes, riskier)

I recommend **Option A** - migrate data first, then update Render.

---

## 📋 Data Migration Commands

If you choose Option A, run these:

```bash
# 1. Create tables in Supabase
export SUPABASE_URL="postgresql://postgres:rgW&X7}azUC@db.glhhmjqewgptmzqojtwx.supabase.co:5432/postgres"

# 2. Run migrations
DATABASE_URL=$SUPABASE_URL alembic upgrade head

# 3. Import CSV data
cd render_backup_final
for file in *.csv; do
    table=$(basename $file .csv)
    psql "$SUPABASE_URL" -c "\COPY $table FROM '$file' WITH CSV HEADER;"
done
```

**Which option do you prefer: A or B?**
