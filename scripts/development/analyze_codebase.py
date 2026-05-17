#!/usr/bin/env python3
"""
import os
import re
from collections import defaultdict

Comprehensive analysis of duplicates and abandoned code in Vrenum app
"""


def analyze_duplicates_and_abandoned():

    """Analyze the codebase for duplicates and abandoned code."""

    print("🔍 COMPREHENSIVE CODEBASE ANALYSIS")
    print("=" * 60)

    # 1. TextVerified Service Duplicates
    print("\n📊 TEXTVERIFIED SERVICE ANALYSIS:")
    textverified_services = [
        "textverified_api.py",
        "textverified_auth.py",
        "textverified_integration.py",
        "textverified_polling_service.py",
        "textverified_provider.py",
        "textverified_service.py",
    ]

for service in textverified_services:
        path = f"app/services/{service}"
if os.path.exists(path):
with open(path, "r") as f:
                lines = len(f.readlines())
            print(f"  📁 {service}: {lines} lines")
else:
            print(f"  ❌ {service}: NOT FOUND")

    # 2. Pricing System Duplicates
    print("\n💰 PRICING SYSTEM ANALYSIS:")
    pricing_files = [
        "app/services/pricing_calculator.py",  # NEW
        "app/services/pricing_service.py",  # OLD
        "app/services/pricing_template_service.py",
        "app/api/billing/pricing_endpoints.py",
        "app/api/billing/tier_endpoints.py",
        "app/api/verification/pricing.py",
    ]

for file_path in pricing_files:
if os.path.exists(file_path):
with open(file_path, "r") as f:
                lines = len(f.readlines())
            status = "🆕 NEW" if "calculator" in file_path else "📁 EXISTS"
            print(f"  {status} {file_path}: {lines} lines")

    # 3. Router Import Analysis
    print("\n🛣️  ROUTER ANALYSIS:")
if os.path.exists("main.py"):
with open("main.py", "r") as f:
            content = f.read()

        router_imports = len(re.findall(r"from.*import.*router", content))
        router_includes = len(re.findall(r"include_router", content))

        print(f"  📥 Router imports: {router_imports}")
        print(f"  🔗 Router includes: {router_includes}")
        print(f"  ⚠️  Unused imports: {router_imports - router_includes}")

    # 4. Abandoned Code Analysis
    print("\n🏚️  ABANDONED CODE ANALYSIS:")

    # Count TODO/FIXME
    todo_count = 0
    pass_count = 0

for root, dirs, files in os.walk("app"):
for file in files:
if file.endswith(".py"):
                filepath = os.path.join(root, file)
try:
with open(filepath, "r") as f:
                        content = f.read()
                        todo_count += len(re.findall(r"TODO|FIXME|XXX|HACK", content))
                        pass_count += len(
                            re.findall(r"^\s*pass\s*$", content, re.MULTILINE)
                        )
except Exception:
                    pass

    print(f"  📝 TODO/FIXME comments: {todo_count}")
    print(f"  🚫 Empty pass statements: {pass_count}")

    # 5. Large Files Analysis
    print("\n📏 LARGE FILES (potential bloat):")
    large_files = []

for root, dirs, files in os.walk("app"):
for file in files:
if file.endswith(".py"):
                filepath = os.path.join(root, file)
try:
with open(filepath, "r") as f:
                        lines = len(f.readlines())
if lines > 300:
                            large_files.append((filepath, lines))
except Exception:
                    pass

    large_files.sort(key=lambda x: x[1], reverse=True)
for filepath, lines in large_files[:5]:
        print(f"  📄 {filepath}: {lines} lines")

    # 6. Service Duplication Analysis
    print("\n🔄 SERVICE DUPLICATION ANALYSIS:")
    service_patterns = defaultdict(list)

for root, dirs, files in os.walk("app/services"):
for file in files:
if file.endswith(".py") and "service" in file:
                # Group by service type
                service_type = file.replace("_service.py", "").replace("service.py", "")
                service_patterns[service_type].append(file)

for service_type, files in service_patterns.items():
if len(files) > 1:
            print(f"  🔄 {service_type}: {files}")


if __name__ == "__main__":
    os.chdir("/Users/machine/Desktop/Namaskah. app")
    analyze_duplicates_and_abandoned()
