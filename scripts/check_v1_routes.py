
# Add parent dir to path

import os
import sys
from main import app

sys.path.append(os.path.abspath("."))


print("🔍 Inspecting Application Routes:")
for route in app.routes:
if hasattr(route, "path"):
if "/api/v1" in route.path:
            # We are looking for things like /api/v1/api/... which is bad
if "/api/v1/api/" in route.path:
                print(f"  ❌ Double Prefix: {route.path}")
else:
                print(f"  ✅ V1 Clean: {route.path}")
elif "/api/admin" in route.path:
            # Just checking legacy admin paths
            pass
