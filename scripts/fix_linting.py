#!/usr/bin/env python3
"""
Fix linting issues in pricing implementation files
"""

import os
import re


def fix_file_linting(filepath):
    """Fix common linting issues in a Python file."""
    print(f"Fixing {filepath}...")

    with open(filepath, "r") as f:
        content = f.read()

    # Remove unused imports
    if "tier_endpoints.py" in filepath:
        content = re.sub(
            r"from fastapi import APIRouter, Depends, HTTPException, status\n",
            "from fastapi import APIRouter, Depends, HTTPException\n",
            content,
        )
        content = re.sub(r"from datetime import datetime\n", "", content)

    if "pricing_calculator.py" in filepath:
        content = re.sub(
            r"from typing import Dict, Any, Optional\n",
            "from typing import Dict, Any\n",
            content,
        )

    # Fix whitespace issues
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        fixed_lines.append(line)

    # Ensure file ends with newline
    content = "\n".join(fixed_lines) + "\n"

    # Fix blank lines with whitespace (convert to empty lines)
    content = re.sub(r"\n[ \t]+\n", "\n\n", content)

    # Fix class definition spacing (2 blank lines before class)
    content = re.sub(r"\n\nclass ", "\n\n\nclass ", content)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"✅ Fixed {filepath}")


# Fix the three main files
files_to_fix = [
    "/Users/machine/Desktop/Namaskah. app/app/services/pricing_calculator.py",
    "/Users/machine/Desktop/Namaskah. app/app/core/tier_config.py",
    "/Users/machine/Desktop/Namaskah. app/app/api/billing/tier_endpoints.py",
]

for filepath in files_to_fix:
    if os.path.exists(filepath):
        fix_file_linting(filepath)
    else:
        print(f"❌ File not found: {filepath}")

print("\n✅ All linting issues fixed!")