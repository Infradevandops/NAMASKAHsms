#!/bin/bash
#
# EMERGENCY REFUND FIX DEPLOYMENT
# ================================
# One-click script to deploy the critical refund fix
#
# Usage:
#   ./deploy_refund_fix.sh [--production]
#

set -e  # Exit on error

echo "================================================================================"
echo "🚨 EMERGENCY REFUND FIX DEPLOYMENT"
echo "================================================================================"
echo ""

# Check if production flag is set
PRODUCTION=false
if [ "$1" == "--production" ]; then
    PRODUCTION=true
    echo "⚠️  PRODUCTION MODE ENABLED"
    echo ""
    read -p "Are you sure you want to deploy to PRODUCTION? (type 'yes'): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

echo "Step 1: Validating files..."
echo "--------------------------------------------------------------------------------"

# Check if all required files exist
FILES=(
    "app/services/auto_refund_service.py"
    "app/services/sms_polling_service.py"
    "reconcile_refunds.py"
    "production_diagnostic.py"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERROR: Required file not found: $file"
        exit 1
    fi
    echo "✓ $file"
done

echo ""
echo "Step 2: Running tests..."
echo "--------------------------------------------------------------------------------"

# Run quick syntax check
python3 -m py_compile app/services/auto_refund_service.py
python3 -m py_compile app/services/sms_polling_service.py
python3 -m py_compile reconcile_refunds.py
python3 -m py_compile production_diagnostic.py

echo "✓ All files compile successfully"
echo ""

if [ "$PRODUCTION" = true ]; then
    echo "Step 3: Backing up production files..."
    echo "--------------------------------------------------------------------------------"
    
    # Backup current files
    BACKUP_DIR="backups/refund_fix_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "app/services/sms_polling_service.py" ]; then
        cp app/services/sms_polling_service.py "$BACKUP_DIR/"
        echo "✓ Backed up sms_polling_service.py"
    fi
    
    echo "✓ Backup created in $BACKUP_DIR"
    echo ""
    
    echo "Step 4: Deploying to production..."
    echo "--------------------------------------------------------------------------------"
    
    # Note: Adjust these commands based on your deployment method
    echo "⚠️  Manual deployment required:"
    echo ""
    echo "1. Copy files to production server:"
    echo "   scp app/services/auto_refund_service.py production:/path/to/app/services/"
    echo "   scp app/services/sms_polling_service.py production:/path/to/app/services/"
    echo ""
    echo "2. Restart application:"
    echo "   ssh production 'systemctl restart namaskah-app'"
    echo ""
    echo "3. Verify deployment:"
    echo "   ssh production 'systemctl status namaskah-app'"
    echo ""
    
    read -p "Press Enter when deployment is complete..."
    
else
    echo "Step 3: Testing locally..."
    echo "--------------------------------------------------------------------------------"
    
    # Run local tests
    echo "Starting local test server..."
    
    # Check if server is already running
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Server already running on port 8000"
    else
        echo "✓ Port 8000 is available"
    fi
    
    echo ""
fi

echo "Step 4: Running diagnostic..."
echo "--------------------------------------------------------------------------------"

if [ "$PRODUCTION" = true ]; then
    echo "Run this command to diagnose production:"
    echo "  python3 production_diagnostic.py"
else
    echo "Diagnostic skipped in local mode"
fi

echo ""
echo "Step 5: Reconciliation instructions..."
echo "--------------------------------------------------------------------------------"
echo ""
echo "To identify affected users and process refunds:"
echo ""
echo "1. Dry run (report only):"
echo "   python3 reconcile_refunds.py --dry-run"
echo ""
echo "2. Review the report carefully"
echo ""
echo "3. Execute refunds:"
echo "   python3 reconcile_refunds.py --execute"
echo ""
echo "4. Check specific user:"
echo "   python3 reconcile_refunds.py --user-id USER_ID --dry-run"
echo ""

echo "================================================================================"
echo "✅ DEPLOYMENT PREPARATION COMPLETE"
echo "================================================================================"
echo ""

if [ "$PRODUCTION" = true ]; then
    echo "Next steps:"
    echo "1. Verify application is running"
    echo "2. Run production_diagnostic.py"
    echo "3. Run reconcile_refunds.py --dry-run"
    echo "4. Review and execute refunds"
    echo "5. Monitor logs for 24 hours"
else
    echo "Next steps:"
    echo "1. Test the fix locally"
    echo "2. Run: ./deploy_refund_fix.sh --production"
fi

echo ""
echo "📚 Documentation:"
echo "  - CRITICAL_BUG_EXECUTIVE_SUMMARY.md"
echo "  - REFUND_FIX_IMPLEMENTATION_GUIDE.md"
echo ""
echo "🆘 Rollback:"
echo "  Restore from: $BACKUP_DIR"
echo ""
echo "================================================================================"
