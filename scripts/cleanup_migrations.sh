#!/bin/bash
# Migration cleanup script - removes old fragmented migrations

set -e

MIGRATIONS_DIR="alembic/versions"

echo "🔧 Cleaning up fragmented migrations..."

# Backup old migrations
mkdir -p "$MIGRATIONS_DIR/backup"
echo "📦 Backing up old migrations to $MIGRATIONS_DIR/backup/"

# Move old migrations to backup
for file in \
    "001_initial_schema.py" \
    "002_add_system_tables.py" \
    "003_add_country_to_verification.py" \
    "004_add_rentals_table.py" \
    "005_add_5sim_fields.py" \
    "006_add_google_oauth.py" \
    "007_add_kyc_system.py" \
    "008_add_enterprise_features.py" \
    "009_add_waitlist_table.py" \
    "010_add_whitelabel_table.py" \
    "011_add_enterprise_tables.py" \
    "012_add_affiliate_system.py" \
    "013_add_5sim_fields.py" \
    "0320b211ff27_add_rental_system.py" \
    "83868cab20af_merge_google_oauth_with_existing_.py"
do
    if [ -f "$MIGRATIONS_DIR/$file" ]; then
        mv "$MIGRATIONS_DIR/$file" "$MIGRATIONS_DIR/backup/$file"
        echo "  ✓ Moved $file"
    fi
done

echo ""
echo "✅ Migration cleanup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Review the new consolidated migration: $MIGRATIONS_DIR/001_consolidated_initial_schema.py"
echo "  2. Test migration: alembic upgrade head"
echo "  3. Verify schema: alembic current"
echo ""
echo "⚠️  Old migrations backed up in: $MIGRATIONS_DIR/backup/"
