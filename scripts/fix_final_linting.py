#!/usr/bin/env python3
"""Final linting fixes for pricing system"""

import re


def fix_final_linting():
    """Fix remaining linting issues."""

    files_to_fix = [
        "/Users/machine/Desktop/Namaskah. app/app/api/billing/pricing_endpoints.py",
        "/Users/machine/Desktop/Namaskah. app/app/api/billing/tier_endpoints.py",
        "/Users/machine/Desktop/Namaskah. app/app/core/tier_config.py",
    ]

    for filepath in files_to_fix:
        print(f"Fixing {filepath}...")

        with open(filepath, "r") as f:
            content = f.read()

        # Remove unused variable
        if "pricing_endpoints.py" in filepath:
            content = re.sub(
                r"\s+calculator = PricingCalculator\(db\)\s+", "\n        ", content
            )

        # Fix whitespace issues
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # Remove trailing whitespace
            line = line.rstrip()

            # Fix too many blank lines (max 2)
            if i > 0 and line == "" and fixed_lines and fixed_lines[-1] == "":
                if len(fixed_lines) > 1 and fixed_lines[-2] == "":
                    continue  # Skip third consecutive blank line

            fixed_lines.append(line)

        # Remove trailing blank lines
        while fixed_lines and fixed_lines[-1] == "":
            fixed_lines.pop()

        # Ensure single newline at end
        content = "\n".join(fixed_lines) + "\n"

        with open(filepath, "w") as f:
            f.write(content)

        print(f"✅ Fixed {filepath}")


if __name__ == "__main__":
    fix_final_linting()
    print("\n✅ All linting issues resolved!")