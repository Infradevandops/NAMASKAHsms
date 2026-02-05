#!/bin/bash
# Fix: Connect to correct Namaskah database

echo "🔧 Fixing Database Connection"
echo "================================"

# Current (WRONG) database
CURRENT_DB=$(psql "$DATABASE_URL" -t -c "SELECT current_database();")
echo "❌ Currently connected to: $CURRENT_DB"

# Extract connection details
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

# Correct database name
CORRECT_DB="namaskah"

# Build correct DATABASE_URL
CORRECT_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${CORRECT_DB}"

echo "✅ Should connect to: $CORRECT_DB"
echo ""

# Test connection to correct database
echo "Testing connection to $CORRECT_DB..."
if psql "$CORRECT_URL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Connection successful!"
    
    # Verify it has correct schema
    echo ""
    echo "Verifying schema..."
    HAS_CREDITS=$(psql "$CORRECT_URL" -t -c "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='credits';" | tr -d ' ')
    HAS_ADMIN=$(psql "$CORRECT_URL" -t -c "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='is_admin';" | tr -d ' ')
    
    if [ "$HAS_CREDITS" = "credits" ] && [ "$HAS_ADMIN" = "is_admin" ]; then
        echo "✅ Correct schema found (has credits, is_admin)"
        echo ""
        echo "🎯 To fix permanently, run:"
        echo "   export DATABASE_URL=\"$CORRECT_URL\""
        echo ""
        echo "Or add to .env file:"
        echo "   echo 'DATABASE_URL=$CORRECT_URL' > .env"
        echo ""
        
        # Test login
        echo "Testing login..."
        export DATABASE_URL="$CORRECT_URL"
        python3 scripts/test_login.py "admin@namaskah.app" "Namaskah@Admin2024"
    else
        echo "❌ Wrong schema (missing credits or is_admin)"
    fi
else
    echo "❌ Connection failed"
fi
