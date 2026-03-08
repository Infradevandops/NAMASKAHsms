#!/bin/bash
# i18n Fix Verification Script
# Verifies that all i18n fixes are properly implemented

echo "🔍 Verifying i18n Fix Implementation..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Check if files exist
echo "📁 Checking file existence..."

FILES=(
    "static/js/i18n.js"
    "static/js/i18n-helpers.js"
    "static/js/global-balance.js"
    "static/js/tier-card.js"
    "templates/dashboard.html"
    "templates/dashboard_base.html"
    "docs/I18N_IMPLEMENTATION_GUIDE.md"
    "docs/I18N_QUICK_REFERENCE.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}✗${NC} $file missing"
        ((ERRORS++))
    fi
done

echo ""

# Check for key patterns in files
echo "🔎 Checking for key patterns..."

# Check i18n.js has new methods
if grep -q "observeDOM()" static/js/i18n.js; then
    echo -e "${GREEN}✓${NC} i18n.js has observeDOM() method"
else
    echo -e "${RED}✗${NC} i18n.js missing observeDOM() method"
    ((ERRORS++))
fi

if grep -q "setContent(" static/js/i18n.js; then
    echo -e "${GREEN}✓${NC} i18n.js has setContent() method"
else
    echo -e "${RED}✗${NC} i18n.js missing setContent() method"
    ((ERRORS++))
fi

if grep -q "window.i18n = i18n" static/js/i18n.js; then
    echo -e "${GREEN}✓${NC} i18n.js exposes window.i18n"
else
    echo -e "${RED}✗${NC} i18n.js doesn't expose window.i18n"
    ((ERRORS++))
fi

# Check dashboard.html has i18nReady
if grep -q "window.i18nReady" templates/dashboard.html; then
    echo -e "${GREEN}✓${NC} dashboard.html waits for i18nReady"
else
    echo -e "${RED}✗${NC} dashboard.html doesn't wait for i18nReady"
    ((ERRORS++))
fi

# Check dashboard.html removes data-i18n
if grep -q "removeAttribute('data-i18n')" templates/dashboard.html; then
    echo -e "${GREEN}✓${NC} dashboard.html removes data-i18n attributes"
else
    echo -e "${RED}✗${NC} dashboard.html doesn't remove data-i18n"
    ((ERRORS++))
fi

# Check dashboard_base.html has updated cache version
if grep -q "i18n.js?v=20260308e" templates/dashboard_base.html; then
    echo -e "${GREEN}✓${NC} dashboard_base.html has updated cache version"
else
    echo -e "${YELLOW}⚠${NC} dashboard_base.html cache version not updated"
fi

# Check global-balance.js removes data-i18n
if grep -q "removeAttribute('data-i18n')" static/js/global-balance.js; then
    echo -e "${GREEN}✓${NC} global-balance.js removes data-i18n attributes"
else
    echo -e "${RED}✗${NC} global-balance.js doesn't remove data-i18n"
    ((ERRORS++))
fi

# Check tier-card.js removes data-i18n
if grep -q "removeAttribute('data-i18n')" static/js/tier-card.js; then
    echo -e "${GREEN}✓${NC} tier-card.js removes data-i18n attributes"
else
    echo -e "${RED}✗${NC} tier-card.js doesn't remove data-i18n"
    ((ERRORS++))
fi

# Check i18n-helpers.js has key exports
if grep -q "export function setI18nContent" static/js/i18n-helpers.js; then
    echo -e "${GREEN}✓${NC} i18n-helpers.js exports setI18nContent"
else
    echo -e "${RED}✗${NC} i18n-helpers.js missing setI18nContent export"
    ((ERRORS++))
fi

echo ""

# Check JavaScript syntax
echo "🔧 Checking JavaScript syntax..."

JS_FILES=(
    "static/js/i18n.js"
    "static/js/i18n-helpers.js"
    "static/js/tier-card.js"
)

for file in "${JS_FILES[@]}"; do
    if command -v node &> /dev/null; then
        if node -c "$file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $file syntax OK"
        else
            echo -e "${RED}✗${NC} $file has syntax errors"
            ((ERRORS++))
        fi
    else
        echo -e "${YELLOW}⚠${NC} Node.js not found, skipping syntax check for $file"
    fi
done

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test in browser: Load dashboard and verify translations"
    echo "2. Check console: No errors related to i18n"
    echo "3. Test language switch: Change language and verify updates"
    echo "4. Wait 1 second: Verify translations don't revert to keys"
    echo ""
    echo "Debug commands:"
    echo "  window.i18n.loaded"
    echo "  window.i18nHelpers.debugI18nElements()"
    echo "  window.i18n.translatePage()"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) found${NC}"
    echo ""
    echo "Please review the errors above and fix them."
    echo "See docs/I18N_IMPLEMENTATION_GUIDE.md for details."
    exit 1
fi
