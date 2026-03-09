#!/bin/bash

GITLAB_REPO="/Users/machine/My Drive/Github Projects/NAMASKAHsms-gitlab"

echo "📥 Pulling latest changes from GitLab..."
echo ""

cd "$GITLAB_REPO"

# Check if we're in a git repo
if [ ! -d .git ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Get current commit before pull
BEFORE_COMMIT=$(git rev-parse --short HEAD)

# Pull latest
echo "Fetching and pulling from origin/main..."
git pull origin main

# Get commit after pull
AFTER_COMMIT=$(git rev-parse --short HEAD)

echo ""

# Check if anything changed
if [ "$BEFORE_COMMIT" = "$AFTER_COMMIT" ]; then
    echo "✅ Already up to date!"
    echo "   Current commit: $AFTER_COMMIT"
else
    echo "🆕 Updated from $BEFORE_COMMIT to $AFTER_COMMIT"
    echo ""
    echo "📝 Recent changes:"
    git log $BEFORE_COMMIT..$AFTER_COMMIT --oneline --stat
fi

echo ""
echo "---"
echo "Current version:"
grep -A 1 "Version" README.md 2>/dev/null | head -2 || echo "Version info not found in README"

echo ""
echo "Last 5 commits:"
git log -5 --oneline

echo ""
echo "Updated: $(date)"
