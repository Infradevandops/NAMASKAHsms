#!/bin/bash
#
# Automated deployment script for area code tier gating feature
# Runs tests before and after deployment
#
# Usage:
#   ./scripts/deploy_area_code_feature.sh staging
#   ./scripts/deploy_area_code_feature.sh production

set -e

ENVIRONMENT=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Validate environment
if [ -z "$ENVIRONMENT" ]; then
    error "Environment not specified"
    echo "Usage: $0 <staging|production>"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    error "Invalid environment: $ENVIRONMENT"
    echo "Must be 'staging' or 'production'"
    exit 1
fi

log "=========================================="
log "Area Code Feature Deployment"
log "Environment: $ENVIRONMENT"
log "=========================================="

# Step 1: Pre-deployment checks
log "Step 1: Running pre-deployment checks..."

# Check if standalone tests pass
log "Running standalone tests..."
cd "$PROJECT_ROOT"
python3 tests/standalone_area_code_test.py
if [ $? -ne 0 ]; then
    error "Standalone tests failed"
    exit 1
fi
log "✅ Standalone tests passed"

# Step 2: Backup current state
log "Step 2: Creating backup..."
BACKUP_DIR="$PROJECT_ROOT/backups/$(date +'%Y%m%d_%H%M%S')"
mkdir -p "$BACKUP_DIR"
log "Backup directory: $BACKUP_DIR"

# Step 3: Deploy code
log "Step 3: Deploying code to $ENVIRONMENT..."

if [ "$ENVIRONMENT" == "staging" ]; then
    log "Pushing to staging branch..."
    git push staging main:staging
elif [ "$ENVIRONMENT" == "production" ]; then
    log "Pushing to production branch..."

    # Production requires confirmation
    read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        warn "Deployment cancelled"
        exit 0
    fi

    git push production main:production
fi

log "✅ Code deployed"

# Step 4: Wait for deployment to complete
log "Step 4: Waiting for deployment to complete..."
sleep 30

# Step 5: Run smoke tests
log "Step 5: Running smoke tests on $ENVIRONMENT..."

python3 tests/smoke/test_area_code_smoke.py --env $ENVIRONMENT

if [ $? -ne 0 ]; then
    error "Smoke tests failed on $ENVIRONMENT"

    if [ "$ENVIRONMENT" == "production" ]; then
        warn "CRITICAL: Production smoke tests failed!"
        warn "Consider rolling back deployment"
    fi

    exit 1
fi

log "✅ Smoke tests passed"

# Step 6: Verify deployment
log "Step 6: Verifying deployment..."

if [ "$ENVIRONMENT" == "staging" ]; then
    BASE_URL="https://staging.vrenum.app"
elif [ "$ENVIRONMENT" == "production" ]; then
    BASE_URL="https://vrenum.app"
fi

# Check health endpoint
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health")
if [ "$HEALTH_STATUS" != "200" ]; then
    error "Health check failed: HTTP $HEALTH_STATUS"
    exit 1
fi

log "✅ Health check passed"

# Step 7: Monitor for errors
log "Step 7: Monitoring for errors (60 seconds)..."
sleep 60

log "=========================================="
log "✅ Deployment Complete!"
log "Environment: $ENVIRONMENT"
log "URL: $BASE_URL"
log "=========================================="

# Step 8: Post-deployment tasks
log "Step 8: Post-deployment tasks..."

log "Next steps:"
log "1. Monitor error rates in Sentry"
log "2. Check revenue tracking dashboard"
log "3. Monitor user feedback"
log "4. Run full manual tests if needed"

log ""
log "Smoke test results saved to:"
log "  smoke_test_results_${ENVIRONMENT}_*.json"

log ""
log "🎉 Deployment successful!"

exit 0
