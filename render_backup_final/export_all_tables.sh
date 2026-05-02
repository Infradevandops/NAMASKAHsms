#!/bin/bash
# Export all critical tables from Render PostgreSQL

DB_URL="postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a.frankfurt-postgres.render.com/namaskahdb_qg9v"
BACKUP_DIR="render_backup_final"

echo "🚀 Exporting critical tables from Render PostgreSQL..."
echo ""

# Critical tables with data
TABLES=(
    "users"
    "sms_transactions"
    "verifications"
    "payment_logs"
    "subscription_tiers"
    "tiers"
    "tier_pricing"
    "pricing_templates"
    "notifications"
    "notification_settings"
    "activity_logs"
    "monthly_quota_usage"
)

for TABLE in "${TABLES[@]}"; do
    echo "📦 Exporting $TABLE..."
    psql "$DB_URL" -c "\COPY $TABLE TO '$BACKUP_DIR/${TABLE}.csv' WITH CSV HEADER;" 2>&1 | grep -v "^$"
done

echo ""
echo "✅ Export complete!"
echo ""
echo "📊 Exported files:"
ls -lh "$BACKUP_DIR"/*.csv
echo ""
echo "📋 Next steps:"
echo "  1. Download backup from Render Dashboard (recommended)"
echo "  2. OR use these CSV files for migration"
echo "  3. Sign up for Supabase: https://supabase.com"
echo "  4. Migrate data to Supabase"
