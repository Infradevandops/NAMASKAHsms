#!/usr/bin/env python3
"""
Fix remaining broken imports in main.py
"""

import re


def fix_main_py_imports():
    """Fix broken textverified_integration imports in main.py."""
    print("🔧 FIXING MAIN.PY IMPORTS...")

    with open("main.py", "r") as f:
        content = f.read()

    # Replace textverified_integration imports with textverified_service
    updated_content = re.sub(
        r"from app\.services\.textverified_integration import get_textverified_integration",
        "from app.services.textverified_service import TextVerifiedService",
        content,
    )

    # Replace get_textverified_integration() calls with TextVerifiedService()
    updated_content = re.sub(
        r"integration = get_textverified_integration\(\)",
        "integration = TextVerifiedService()",
        updated_content,
    )

    # Also replace any other references
    updated_content = re.sub(
        r"get_textverified_integration\(\)", "TextVerifiedService()", updated_content
    )

    if updated_content != content:
        # Create backup
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2("main.py", f"main.py.backup_{timestamp}")

        # Write updated content
        with open("main.py", "w") as f:
            f.write(updated_content)

        print("✅ Fixed main.py imports")
        print("📁 Backup created: main.py.backup_" + timestamp)
        return True
    else:
        print("ℹ️  No changes needed in main.py")
        return False


def verify_fix():
    """Verify the fix worked."""
    print("\n🔍 VERIFYING FIX...")

    try:
        # Test import
        import os
        import sys

        sys.path.append(os.getcwd())

        from app.services.textverified_service import TextVerifiedService

        TextVerifiedService()
        print("✅ TextVerifiedService imports and initializes correctly")

        # Check for remaining broken imports
        with open("main.py", "r") as f:
            content = f.read()

        if "textverified_integration" in content:
            print("❌ Still has textverified_integration references")
            return False
        else:
            print("✅ No more textverified_integration references")
            return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def main():
    """Main fix function."""
    import os

    os.chdir("/Users/machine/Desktop/Namaskah. app")

    print("🔧 FIXING REMAINING BROKEN IMPORTS")
    print("=" * 50)

    # Fix main.py imports
    fix_main_py_imports()

    # Verify the fix
    if verify_fix():
        print("\n✅ ALL IMPORTS FIXED SUCCESSFULLY!")
        print("🚀 Codebase is now clean and functional")
    else:
        print("\n❌ SOME ISSUES REMAIN")
        print("🔍 Manual review may be needed")


if __name__ == "__main__":
    main()