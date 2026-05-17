#!/bin/bash
# CI/CD Setup Script

echo "🚀 Setting up CI/CD for Vrenum"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Not a git repository. Run: git init"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Railway setup
echo "🚂 Railway Setup"
echo "1. Login to Railway:"
railway login

echo ""
echo "2. Link project (or create new):"
railway link

echo ""
echo "3. Generate token for GitHub Actions:"
echo "   Run: railway tokens create"
echo "   Add to GitHub Secrets as: RAILWAY_TOKEN"
echo ""

# GitHub setup
echo "📝 GitHub Secrets Required:"
echo ""
echo "Deployment:"
echo "  - RAILWAY_TOKEN (from above)"
echo "  - DOCKER_USERNAME"
echo "  - DOCKER_PASSWORD"
echo ""
echo "Database:"
echo "  - DATABASE_URL"
echo "  - AWS_ACCESS_KEY_ID"
echo "  - AWS_SECRET_ACCESS_KEY"
echo "  - S3_BACKUP_BUCKET"
echo ""
echo "APIs:"
echo "  - TEXTVERIFIED_API_KEY"
echo "  - PAYSTACK_SECRET_KEY"
echo "  - GOOGLE_CLIENT_ID"
echo "  - JWT_SECRET_KEY"
echo ""
echo "Monitoring:"
echo "  - SLACK_WEBHOOK (optional)"
echo ""

echo "📖 Full guide: CICD_SETUP.md"
echo ""
echo "✅ Setup complete! Push to main branch to trigger first deployment."
