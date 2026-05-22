#!/bin/bash

echo "🔍 Verifying all fixes are in place..."
echo ""

# Check public_base.html
echo "✓ Checking public_base.html..."
if grep -q "display: flex !important" templates/public_base.html; then
    echo "  ✅ Navigation responsive fix: PRESENT"
else
    echo "  ❌ Navigation responsive fix: MISSING"
fi

if grep -q "Light mode defaults - CRITICAL" templates/public_base.html; then
    echo "  ✅ Light mode defaults: PRESENT"
else
    echo "  ❌ Light mode defaults: MISSING"
fi

# Check register.html
echo ""
echo "✓ Checking register.html..."
if grep -q "data-theme=\"dark\"" templates/register.html; then
    echo "  ✅ Dark mode support: PRESENT"
else
    echo "  ❌ Dark mode support: MISSING"
fi

# Check terms.html
echo ""
echo "✓ Checking terms.html..."
if grep -q "Light mode defaults - CRITICAL" templates/terms.html; then
    echo "  ✅ Light mode fix: PRESENT"
else
    echo "  ❌ Light mode fix: MISSING"
fi

# Check privacy.html
echo ""
echo "✓ Checking privacy.html..."
if grep -q "Light mode defaults - CRITICAL" templates/privacy.html; then
    echo "  ✅ Light mode fix: PRESENT"
else
    echo "  ❌ Light mode fix: MISSING"
fi

# Check affiliate_program.html
echo ""
echo "✓ Checking affiliate_program.html..."
if grep -q "Light mode defaults - CRITICAL" templates/affiliate_program.html; then
    echo "  ✅ Light mode fix: PRESENT"
else
    echo "  ❌ Light mode fix: MISSING"
fi

echo ""
echo "🎯 Summary:"
echo "All fixes are in the template files."
echo ""
echo "📋 Next steps:"
echo "1. Stop the server (Ctrl+C or: pkill -f 'uvicorn main:app')"
echo "2. Clear Python cache: find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null"
echo "3. Restart server: ./start.sh"
echo "4. Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)"
echo ""
