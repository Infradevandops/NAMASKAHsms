#!/bin/bash
# Local testing script - doesn't require full environment

echo "🔍 Local Validation (Quick Check)"
echo "=================================="
echo ""

# Check Python syntax
echo "✓ Python syntax..."
python3 -m py_compile main.py 2>/dev/null && echo "  ✅ main.py" || echo "  ❌ main.py"
python3 -m py_compile app/core/dependencies.py 2>/dev/null && echo "  ✅ app/core/dependencies.py" || echo "  ❌ app/core/dependencies.py"

echo ""
echo "✓ Files created..."
[ -f "scripts/validate_production.py" ] && echo "  ✅ validate_production.py" || echo "  ❌ validate_production.py"
[ -f "start_production.sh" ] && echo "  ✅ start_production.sh" || echo "  ❌ start_production.sh"
[ -f "static/js/auth-check.js" ] && echo "  ✅ auth-check.js" || echo "  ❌ auth-check.js"

echo ""
echo "✓ Key fixes applied..."
grep -q "settings.jwt_secret_key" app/core/dependencies.py && echo "  ✅ JWT secret key fix" || echo "  ❌ JWT secret key fix"
grep -q "settings.base_url" main.py && echo "  ✅ CORS dynamic config" || echo "  ❌ CORS dynamic config"
grep -q "text/css; charset=utf-8" main.py && echo "  ✅ MIME type fix" || echo "  ❌ MIME type fix"
grep -q "/api/diagnostics" main.py && echo "  ✅ Diagnostics endpoint" || echo "  ❌ Diagnostics endpoint"

echo ""
echo "✓ Documentation..."
[ -f "PRODUCTION_FIXES.md" ] && echo "  ✅ PRODUCTION_FIXES.md" || echo "  ❌ PRODUCTION_FIXES.md"
[ -f "DEPLOYMENT_GUIDE.md" ] && echo "  ✅ DEPLOYMENT_GUIDE.md" || echo "  ❌ DEPLOYMENT_GUIDE.md"
[ -f "QUICK_START.md" ] && echo "  ✅ QUICK_START.md" || echo "  ❌ QUICK_START.md"

echo ""
echo "=================================="
echo "✅ Local validation complete!"
echo ""
echo "Production Status:"
curl -s https://namaskah.onrender.com/api/system/health | python3 -m json.tool 2>/dev/null || echo "  (Unable to check - no internet)"
