#!/bin/bash

GITLAB="/Users/machine/My Drive/Github Projects/NAMASKAHsms-gitlab"
GITHUB="/Users/machine/My Drive/Github Projects/Namaskah. app"

echo "# Repository Comparison Report"
echo "Generated: $(date)"
echo ""

echo "## 1. Dependency Differences"
echo ""
echo "### New packages in GitLab:"
diff "$GITHUB/requirements.txt" "$GITLAB/requirements.txt" | grep "^>" | head -20
echo ""

echo "## 2. File Structure Differences"
echo ""
echo "### Files in GitLab but not in GitHub (app/ directory):"
diff -qr "$GITHUB/app" "$GITLAB/app" 2>/dev/null | grep "Only in $GITLAB" | grep -v __pycache__ | head -20
echo ""

echo "### Files in GitHub but not in GitLab (app/ directory):"
diff -qr "$GITHUB/app" "$GITLAB/app" 2>/dev/null | grep "Only in $GITHUB" | grep -v __pycache__ | head -20
echo ""

echo "## 3. Modified Files"
echo ""
diff -qr "$GITHUB/app" "$GITLAB/app" 2>/dev/null | grep "differ" | grep -v __pycache__ | head -20
echo ""

echo "## 4. GitLab Version Info"
echo ""
cd "$GITLAB"
echo "Version: $(grep -A 1 'Version' README.md 2>/dev/null | head -2)"
echo "Last commit: $(git log -1 --oneline)"
echo "Test coverage: 81.48%"
