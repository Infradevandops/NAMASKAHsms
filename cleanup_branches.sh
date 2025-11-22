#!/bin/bash
set -e

echo "🧹 Cleaning up non-useful branches..."

# Delete DeepSource automation branches
echo "Deleting DeepSource transform branches..."
git branch -r | grep 'deepsource-transform' | sed 's/origin\///' | xargs -I {} git push origin --delete {} 2>/dev/null || true

# Delete old PR branches (keep main merged)
echo "Deleting PR branches..."
git branch -r | grep 'pr/' | sed 's/origin\///' | xargs -I {} git push origin --delete {} 2>/dev/null || true

# Delete phase branches (development roadmap, not needed)
echo "Deleting phase branches..."
for phase in phase-1-mvp phase-2-core-features phase-3-ui-enhancement phase-4-security-hardening phase-5-analytics-monitoring phase-6-production-ready; do
  git push origin --delete "$phase" 2>/dev/null || true
done

# Delete CI/CD setup branches
echo "Deleting CI/CD branches..."
git push origin --delete circleci-project-setup 2>/dev/null || true
git push origin --delete snyk-fix-aae2d89fabada020c638fc150c1e994d 2>/dev/null || true

# Delete old snapshot branches
echo "Deleting snapshot branches..."
git push origin --delete 2025-03-09 2>/dev/null || true
git push origin --delete production-fix 2>/dev/null || true

# Prune local tracking branches
echo "Pruning local tracking branches..."
git fetch --prune

echo "✅ Cleanup complete!"
echo ""
echo "Remaining branches:"
git branch -a | grep -E '(main|production-ready|fix/login)' || echo "Main branches preserved"
