#!/usr/bin/env python3
"""
Version Sync Validator
Ensures version consistency across all project files.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Files to check for version strings
VERSION_FILES = {
    "app/core/config.py": r'version:\s*str\s*=\s*"([^"]+)"',
    "README.md": r"\*\*Version\*\*:\s*([0-9.]+)",
    "GAP_ANALYSIS_REPORT.md": r"to \*\*v([0-9.]+)\*\*",
    "CHANGELOG.md": r"##\s*\[([0-9.]+)\]",  # Gets latest version
}


def extract_version(file_path: str, pattern: str) -> str:
    """Extract version from file using regex pattern."""
    try:
        content = Path(file_path).read_text()
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        return "NOT_FOUND"
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {str(e)}"


def validate_versions() -> Tuple[bool, Dict[str, str]]:
    """Validate all versions match."""
    versions = {}

    for file_path, pattern in VERSION_FILES.items():
        version = extract_version(file_path, pattern)
        versions[file_path] = version

    # Get canonical version from config.py
    canonical = versions.get("app/core/config.py", "UNKNOWN")

    # Check if all versions match
    all_match = all(
        v == canonical
        for v in versions.values()
        if v not in ["NOT_FOUND", "FILE_NOT_FOUND"] and not v.startswith("ERROR")
    )

    return all_match, versions


def main():
    """Main validation function."""
    print("🔍 Version Sync Validator")
    print("=" * 50)

    all_match, versions = validate_versions()

    # Get canonical version
    canonical = versions.get("app/core/config.py", "UNKNOWN")
    print(f"\n📌 Canonical Version (config.py): {canonical}")
    print("\n📋 Version Check Results:")
    print("-" * 50)

    for file_path, version in versions.items():
        if file_path == "app/core/config.py":
            continue

        status = "✅" if version == canonical else "❌"
        print(f"{status} {file_path}: {version}")

    print("-" * 50)

    if all_match:
        print("\n✅ SUCCESS: All versions are synchronized!")
        print(f"   Current version: {canonical}")
        return 0
    else:
        print("\n❌ FAILURE: Version mismatch detected!")
        print(f"   Expected: {canonical}")
        print("\n🔧 Action Required:")
        print("   1. Update all files to match config.py version")
        print("   2. Run this script again to verify")
        return 1


if __name__ == "__main__":
    sys.exit(main())
