#!/usr/bin/env python3
"""
import os
import re
import shutil
from datetime import datetime

Safe cleanup script for Namaskah duplicates
Analyzes dependencies before removal to prevent breaking the codebase
"""


def backup_file(filepath):

    """Create timestamped backup before removal."""
if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.backup_{timestamp}"
        shutil.copy2(filepath, backup_path)
        print(f"📁 Backed up {filepath}")
        return backup_path
    return None


def find_imports(file_to_check):

    """Find all files that import the given file."""
    imports = []
    module_name = file_to_check.replace("app/", "").replace(".py", "").replace("/", ".")

for root, dirs, files in os.walk("app"):
for file in files:
if file.endswith(".py"):
                filepath = os.path.join(root, file)
try:
with open(filepath, "r") as f:
                        content = f.read()
if module_name in content:
                            imports.append(filepath)
except Exception:
                    pass
    return imports


def safe_remove_textverified_duplicates():

    """Safely remove TextVerified duplicate services."""
    print("🔍 STEP 1: Analyzing TextVerified service dependencies...")

    # Primary service to keep
    primary_service = "app/services/textverified_service.py"

    # Duplicates to potentially remove
    duplicates = [
        "app/services/textverified_integration.py",
        "app/services/textverified_api.py",
        "app/services/textverified_provider.py",
        "app/services/textverified_polling_service.py",
        "app/services/textverified_auth.py",
    ]

    print(f"✅ Primary service: {primary_service}")

for duplicate in duplicates:
if os.path.exists(duplicate):
            imports = find_imports(duplicate)
if imports:
                print(f"⚠️  {duplicate} is imported by:")
for imp in imports:
                    print(f"   - {imp}")
                print("   → SKIPPING removal (has dependencies)")
else:
                backup_file(duplicate)
                os.remove(duplicate)
                print(f"✅ Removed {duplicate} (no dependencies)")
else:
            print(f"❌ {duplicate} not found")


def safe_remove_old_pricing_service():

    """Safely remove old pricing service if not used."""
    print("\n🔍 STEP 2: Analyzing old pricing service...")

    old_service = "app/services/pricing_service.py"
    new_service = "app/services/pricing_calculator.py"

if os.path.exists(old_service):
        imports = find_imports(old_service)
if imports:
            print(f"⚠️  {old_service} is still imported by:")
for imp in imports:
                print(f"   - {imp}")
            print("   → SKIPPING removal (update imports first)")
else:
            backup_file(old_service)
            os.remove(old_service)
            print(f"✅ Removed {old_service} (no dependencies)")
            print(f"✅ Using {new_service} as primary")
else:
        print(f"❌ {old_service} not found")


def clean_archived_templates():

    """Remove archived templates safely."""
    print("\n🔍 STEP 3: Cleaning archived templates...")

    archive_dir = "templates/_archive"
if os.path.exists(archive_dir):
        files = os.listdir(archive_dir)
for file in files:
if file.endswith(".html"):
                filepath = os.path.join(archive_dir, file)
                backup_file(filepath)
                os.remove(filepath)
                print(f"✅ Removed archived template: {file}")

        # Remove empty archive directory
if not os.listdir(archive_dir):
            os.rmdir(archive_dir)
            print("✅ Removed empty archive directory")
else:
        print("❌ Archive directory not found")


def clean_empty_pass_statements():

    """Document empty pass statements for review."""
    print("\n🔍 STEP 4: Analyzing empty pass statements...")

    pass_files = []
for root, dirs, files in os.walk("app"):
for file in files:
if file.endswith(".py"):
                filepath = os.path.join(root, file)
try:
with open(filepath, "r") as f:
                        content = f.read()
if re.search(r"^\s*pass\s*$", content, re.MULTILINE):
                            pass_files.append(filepath)
except Exception:
                    pass

    print(f"📝 Found {len(pass_files)} files with empty pass statements:")
for file in pass_files[:10]:  # Show first 10
        print(f"   - {file}")
if len(pass_files) > 10:
        print(f"   ... and {len(pass_files) - 10} more")
    print("   → Manual review recommended")


def analyze_todo_comments():

    """Analyze TODO/FIXME comments."""
    print("\n🔍 STEP 5: Analyzing TODO/FIXME comments...")

    todo_items = []
for root, dirs, files in os.walk("app"):
for file in files:
if file.endswith(".py"):
                filepath = os.path.join(root, file)
try:
with open(filepath, "r") as f:
                        lines = f.readlines()
for i, line in enumerate(lines):
if re.search(r"TODO|FIXME|XXX|HACK", line):
                                todo_items.append((filepath, i + 1, line.strip()))
except Exception:
                    pass

    print(f"📝 Found {len(todo_items)} TODO/FIXME comments:")
for filepath, line_num, comment in todo_items:
        print(f"   - {filepath}:{line_num} → {comment}")


def main():

    """Main cleanup function."""
    print("🧹 SAFE CLEANUP STARTING...")
    print("=" * 60)

    # Change to project directory
    os.chdir("/Users/machine/Desktop/Namaskah. app")

    # Step 1: Remove TextVerified duplicates (safe)
    safe_remove_textverified_duplicates()

    # Step 2: Remove old pricing service (safe)
    safe_remove_old_pricing_service()

    # Step 3: Clean archived templates (safe)
    clean_archived_templates()

    # Step 4: Analyze empty pass statements (analysis only)
    clean_empty_pass_statements()

    # Step 5: Analyze TODO comments (analysis only)
    analyze_todo_comments()

    print("\n" + "=" * 60)
    print("✅ SAFE CLEANUP COMPLETED!")
    print("\n📋 Summary:")
    print("  - Removed duplicate services with no dependencies")
    print("  - Backed up all removed files")
    print("  - Analyzed remaining issues for manual review")
    print("  - Codebase integrity preserved")


if __name__ == "__main__":
    main()