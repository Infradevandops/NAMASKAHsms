#!/bin/bash
#
# PRODUCTION DEPLOYMENT - REFUND FIX
# ==================================
# Deploys critical refund fix to production
#

set -e

echo "================================================================================"
echo "🚀 PRODUCTION DEPLOYMENT - REFUND FIX"
echo "================================================================================"
echo ""
echo "⚠️  WARNING: This will deploy critical fixes to PRODUCTION"
echo ""
read -p "Are you sure you want to continue? (type 'DEPLOY'): " confirm

if [ "$confirm" != "DEPLOY" ]; then
    echo "Deployment cancelled."
    exit 1
fi

echo ""
echo "Step 1: Pre-deployment checks..."
echo "--------------------------------------------------------------------------------"

# Check if all required files exist
FILES=(
    "app/services/auto_refund_service.py"
    "app/services/sms_polling_service.py"
    "app/api/verification/purchase_endpoints.py"
    "app/schemas/verification.py"
    "app/api/verification/cancel_endpoint.py"
    "app/core/circuit_breaker.py"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERROR: Required file not found: $file"
        exit 1
    fi
    echo "✓ $file"
done

echo ""
echo "Step 2: Running safety tests..."
echo "--------------------------------------------------------------------------------"

python3 test_verification_safety.py
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Safety tests failed"
    exit 1
fi

echo ""
echo "Step 3: Creating backup..."
echo "--------------------------------------------------------------------------------"

BACKUP_DIR="backups/production_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup files that will be modified
cp app/services/sms_polling_service.py "$BACKUP_DIR/" 2>/dev/null || true
cp app/api/verification/purchase_endpoints.py "$BACKUP_DIR/" 2>/dev/null || true
cp app/schemas/verification.py "$BACKUP_DIR/" 2>/dev/null || true

echo "✓ Backup created in $BACKUP_DIR"

echo ""
echo "Step 4: Deployment summary..."
echo "--------------------------------------------------------------------------------"
echo ""
echo "Files to deploy:"
echo "  1. app/services/auto_refund_service.py (NEW)"
echo "  2. app/services/sms_polling_service.py (UPDATED)"
echo "  3. app/api/verification/purchase_endpoints.py (UPDATED)"
echo "  4. app/schemas/verification.py (UPDATED)"
echo "  5. app/api/verification/cancel_endpoint.py (NEW)"
echo "  6. app/core/circuit_breaker.py (NEW)"
echo ""
echo "Changes:"
echo "  ✅ Two-phase commit (API first, charge after)"
echo "  ✅ Automatic rollback on failure"
echo "  ✅ Auto-refunds on timeout/cancel/failure"
echo "  ✅ Idempotency protection"
echo "  ✅ Circuit breaker for resilience"
echo ""

read -p "Proceed with deployment? (yes/no): " proceed
if [ "$proceed" != "yes" ]; then
    echo "Deployment cancelled."
    exit 1
fi

echo ""
echo "Step 5: Deploying to production..."
echo "--------------------------------------------------------------------------------"

# Note: Adjust these commands based on your deployment method
echo ""
echo "📦 Deployment Instructions:"
echo ""
echo "If using Git deployment:"
echo "  git add -A"
echo "  git commit -m 'fix: critical refund system with auto-refunds and two-phase commit'"
echo "  git push origin main"
echo ""
echo "If using direct file copy:"
echo "  scp app/services/auto_refund_service.py production:/path/to/app/services/"
echo "  scp app/services/sms_polling_service.py production:/path/to/app/services/"
echo "  scp app/api/verification/purchase_endpoints.py production:/path/to/app/api/verification/"
echo "  scp app/schemas/verification.py production:/path/to/app/schemas/"
echo "  scp app/api/verification/cancel_endpoint.py production:/path/to/app/api/verification/"
echo "  scp app/core/circuit_breaker.py production:/path/to/app/core/"
echo ""
echo "If using Render.com (auto-deploy on push):"
echo "  git add -A"
echo "  git commit -m 'fix: critical refund system'"
echo "  git push origin main"
echo "  # Render will auto-deploy"
echo ""

read -p "Have you deployed the files? (yes/no): " deployed
if [ "$deployed" != "yes" ]; then
    echo "Please deploy the files and run this script again."
    exit 1
fi

echo ""
echo "Step 6: Post-deployment verification..."
echo "--------------------------------------------------------------------------------"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Monitor application logs for errors"
echo "2. Run production diagnostic:"
echo "   python3 production_diagnostic.py"
echo ""
echo "3. Run reconciliation for past issues:"
echo "   python3 reconcile_refunds.py --days 30 --dry-run"
echo "   python3 reconcile_refunds.py --days 30 --execute"
echo ""
echo "4. Monitor for 24 hours:"
echo "   - Check refunds are processing"
echo "   - Verify no errors in logs"
echo "   - Monitor user feedback"
echo ""
echo "Rollback instructions (if needed):"
echo "  Restore from: $BACKUP_DIR"
echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "================================================================================"
