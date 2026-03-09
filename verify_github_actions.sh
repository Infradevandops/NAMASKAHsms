#!/bin/bash

echo "🔍 Verifying GitHub Actions Setup..."
echo ""

# Check if workflows exist
echo "1. Checking workflow files..."
if [ -f ".github/workflows/ci.yml" ]; then
    echo "   ✅ CI workflow exists"
else
    echo "   ❌ CI workflow missing"
fi

if [ -f ".github/workflows/sync-to-gitlab.yml" ]; then
    echo "   ✅ GitLab sync workflow exists"
else
    echo "   ❌ GitLab sync workflow missing"
fi

if [ -f ".github/workflows/deploy.yml" ]; then
    echo "   ✅ Deploy workflow exists"
else
    echo "   ❌ Deploy workflow missing"
fi

echo ""
echo "2. Checking git status..."
git status --short .github/

echo ""
echo "3. Next steps:"
echo "   1. Add GITLAB_TOKEN to GitHub secrets"
echo "   2. git add .github/"
echo "   3. git commit -m 'ci: Add GitHub Actions workflows'"
echo "   4. git push origin main"
echo ""
echo "4. After pushing, check:"
echo "   - GitHub Actions tab: https://github.com/YOUR-USERNAME/YOUR-REPO/actions"
echo "   - GitLab repo: https://gitlab.com/oghenesuvwe-group/NAMASKAHsms"
echo ""
echo "📚 Full guide: GITHUB_ACTIONS_SETUP.md"
