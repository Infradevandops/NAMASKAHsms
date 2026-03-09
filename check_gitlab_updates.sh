#!/bin/bash

# GitLab repo location
GITLAB_REPO="/Users/machine/My Drive/Github Projects/NAMASKAHsms-gitlab"
GITHUB_REPO="/Users/machine/My Drive/Github Projects/Namaskah. app"

echo "🔍 Checking GitLab repo for updates..."
echo ""

# Navigate to GitLab repo
cd "$GITLAB_REPO"

# Get current commit
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_SHORT=$(git rev-parse --short HEAD)

# Fetch latest
echo "📡 Fetching latest changes..."
git fetch origin --quiet

# Get latest commit on remote
LATEST_COMMIT=$(git rev-parse origin/main)
LATEST_SHORT=$(git rev-parse --short origin/main)

echo ""
echo "📊 Status:"
echo "  Current: $CURRENT_SHORT"
echo "  Latest:  $LATEST_SHORT"
echo ""

# Check if updates available
if [ "$CURRENT_COMMIT" = "$LATEST_COMMIT" ]; then
    echo "✅ GitLab repo is up to date!"
    echo ""
    echo "Last commit:"
    git log -1 --pretty=format:"  %h - %s (%cr) <%an>" HEAD
    echo ""
else
    echo "🆕 NEW UPDATES AVAILABLE!"
    echo ""
    echo "New commits:"
    git log HEAD..origin/main --pretty=format:"  %h - %s (%cr) <%an>"
    echo ""
    echo ""
    echo "📝 Summary of changes:"
    git diff HEAD..origin/main --stat | head -20
    echo ""
    echo "💡 To see full changes: cd '$GITLAB_REPO' && git diff HEAD..origin/main"
    echo "💡 To pull updates: cd '$GITLAB_REPO' && git pull origin main"
    echo ""
    echo "⚠️  DECISION NEEDED: Review changes before integrating into GitHub repo"
fi

echo ""
echo "---"
echo "Last checked: $(date)"
