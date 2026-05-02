#!/bin/bash
# Database Migration Script - Render to Alternative Provider
# Usage: ./migrate_database.sh [provider] [new_database_url]

set -e

PROVIDER=$1
NEW_DATABASE_URL=$2
BACKUP_FILE="migration_backup_$(date +%Y%m%d_%H%M%S).sql"

if [ -z "$PROVIDER" ] || [ -z "$NEW_DATABASE_URL" ]; then
    echo "Usage: ./migrate_database.sh [supabase|neon|railway|fly] [new_database_url]"
    echo ""
    echo "Example:"
    echo "  ./migrate_database.sh supabase 'postgresql://postgres:password@db.xxx.supabase.co:5432/postgres'"
    exit 1
fi

echo "🚀 Starting database migration to $PROVIDER..."
echo ""

# Step 1: Backup current database
echo "📦 Step 1: Backing up current database..."
if [ -n "$DATABASE_URL" ]; then
    pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
    echo "✅ Backup saved to: $BACKUP_FILE"
else
    echo "⚠️  DATABASE_URL not set. Using existing backup..."
    BACKUP_FILE=$(ls -t migration_backup_*.sql backup_*.sql namaskah_backup_*.sql 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        echo "❌ No backup found! Please create a backup first."
        exit 1
    fi
    echo "✅ Using backup: $BACKUP_FILE"
fi
echo ""

# Step 2: Test new database connection
echo "🔌 Step 2: Testing new database connection..."
if psql "$NEW_DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Connection successful!"
else
    echo "❌ Cannot connect to new database. Check your connection string."
    exit 1
fi
echo ""

# Step 3: Restore to new database
echo "📥 Step 3: Restoring data to new database..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql "$NEW_DATABASE_URL"
else
    psql "$NEW_DATABASE_URL" < "$BACKUP_FILE"
fi
echo "✅ Data restored successfully!"
echo ""

# Step 4: Verify migration
echo "🔍 Step 4: Verifying migration..."
TABLE_COUNT=$(psql "$NEW_DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo "✅ Found $TABLE_COUNT tables in new database"
echo ""

# Step 5: Update environment files
echo "📝 Step 5: Updating environment configuration..."

# Update .env
if [ -f .env ]; then
    # Backup current .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update DATABASE_URL
    if grep -q "^DATABASE_URL=" .env; then
        sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=$NEW_DATABASE_URL|" .env
        rm .env.bak
    else
        echo "DATABASE_URL=$NEW_DATABASE_URL" >> .env
    fi
    echo "✅ Updated .env"
fi

# Update .env.production
if [ -f .env.production ]; then
    cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)
    
    if grep -q "^DATABASE_URL=" .env.production; then
        sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=$NEW_DATABASE_URL|" .env.production
        rm .env.production.bak
    else
        echo "DATABASE_URL=$NEW_DATABASE_URL" >> .env.production
    fi
    echo "✅ Updated .env.production"
fi
echo ""

# Step 6: Provider-specific setup
echo "⚙️  Step 6: Provider-specific configuration..."

case $PROVIDER in
    supabase)
        echo "📌 Supabase Setup:"
        echo "   1. Enable Row Level Security (RLS) if needed"
        echo "   2. Configure Auth in Supabase dashboard"
        echo "   3. Set up Storage buckets if using file uploads"
        echo "   4. Dashboard: https://app.supabase.com"
        ;;
    neon)
        echo "📌 Neon Setup:"
        echo "   1. Enable connection pooling for better performance"
        echo "   2. Create branches for dev/staging if needed"
        echo "   3. Dashboard: https://console.neon.tech"
        ;;
    railway)
        echo "📌 Railway Setup:"
        echo "   1. Add Redis if needed: railway add redis"
        echo "   2. Configure environment variables in dashboard"
        echo "   3. Dashboard: https://railway.app/dashboard"
        ;;
    fly)
        echo "📌 Fly.io Setup:"
        echo "   1. Scale Postgres: fly scale vm shared-cpu-1x --app [db-app]"
        echo "   2. Configure backups: fly postgres backup"
        echo "   3. Dashboard: https://fly.io/dashboard"
        ;;
esac
echo ""

# Step 7: Test application
echo "🧪 Step 7: Testing application..."
echo "Run these commands to verify:"
echo ""
echo "  # Test database connection"
echo "  python3 -c 'from app.core.database import test_database_connection; print(test_database_connection())'"
echo ""
echo "  # Run migrations"
echo "  alembic upgrade head"
echo ""
echo "  # Start application"
echo "  ./start.sh"
echo ""

# Summary
echo "✅ Migration Complete!"
echo ""
echo "📋 Summary:"
echo "   Provider: $PROVIDER"
echo "   Backup: $BACKUP_FILE"
echo "   Tables: $TABLE_COUNT"
echo ""
echo "🔄 Next Steps:"
echo "   1. Test application locally"
echo "   2. Update production environment variables"
echo "   3. Deploy to production"
echo "   4. Monitor for issues"
echo ""
echo "💾 Backup files saved:"
echo "   - Database: $BACKUP_FILE"
echo "   - .env: .env.backup.*"
echo "   - .env.production: .env.production.backup.*"
echo ""
echo "🆘 Rollback (if needed):"
echo "   mv .env.backup.[timestamp] .env"
echo "   psql \$OLD_DATABASE_URL < $BACKUP_FILE"
