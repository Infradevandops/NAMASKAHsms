#!/usr/bin/env python3
"""
Automated script to fix common linting issues across the codebase.
Focuses on critical violations that are causing CI/CD failures.
"""

import os
import re
import subprocess


def remove_unused_imports(file_path):
    """Remove unused imports from a Python file."""
    try:
        # Use autoflake to remove unused imports
        result = subprocess.run([
            'python3', '-m', 'autoflake',
            '--remove-all-unused-imports',
            '--remove-unused-variables',
            '--in-place',
            str(file_path)
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Fixed unused imports in {file_path}")
        else:
            print(f"✗ Failed to fix imports in {file_path}: {result.stderr}")
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")


def fix_whitespace_issues(file_path):
    """Fix trailing whitespace and blank line issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove trailing whitespace
        lines = content.splitlines()
        fixed_lines = [line.rstrip() for line in lines]

        # Ensure file ends with newline
        if fixed_lines and not content.endswith('\n'):
            fixed_lines.append('')

        # Remove blank lines with whitespace
        final_lines = []
        for line in fixed_lines:
            if line.strip() == '':
                final_lines.append('')
            else:
                final_lines.append(line)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_lines))

        print(f"✓ Fixed whitespace issues in {file_path}")

    except Exception as e:
        print(f"✗ Error fixing whitespace in {file_path}: {e}")


def fix_f_string_placeholders(file_path):
    """Fix f-strings missing placeholders."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find f-strings without placeholders and convert to regular strings
        # Pattern: f"text without {}" or f'text without {}'
        pattern = r'f(["\'])([^"\']*?)\1'

def replace_f_string(match):
            quote = match.group(1)
            text = match.group(2)
            # If no {} placeholders, convert to regular string
            if '{' not in text:
                return f'{quote}{text}{quote}'
            return match.group(0)

        fixed_content = re.sub(pattern, replace_f_string, content)

        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✓ Fixed f-string placeholders in {file_path}")

    except Exception as e:
        print(f"✗ Error fixing f-strings in {file_path}: {e}")


def fix_comparison_issues(file_path):
    """Fix comparison to True/False issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix comparisons
        content = re.sub(r'(\w+)\s*==\s*True\b', r'\1', content)
        # not Fix comparisons
        content = re.sub(r'(\w+)\s*==\s*False\b', r'not \1', content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Fixed comparison issues in {file_path}")

    except Exception as e:
        print(f"✗ Error fixing comparisons in {file_path}: {e}")


def get_python_files():
    """Get all Python files that need linting fixes."""
    python_files = []

    # Get files from scripts/ and tests/ directories
    for directory in ['scripts', 'tests', '.']:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                # Skip certain directories
                if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'htmlcov']):
                    continue

                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))

    return python_files


def main():
    """Main function to fix linting issues."""
    print("🔧 Starting automated linting fixes...")

    # Check if autoflake is available
    try:
        subprocess.run(['python3', '-m', 'autoflake', '--version'],
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing autoflake...")
        subprocess.run(['pip3', 'install', 'autoflake'], check=True)

    python_files = get_python_files()
    print(f"Found {len(python_files)} Python files to process")

    for file_path in python_files:
        print(f"\n📁 Processing {file_path}")

        # Apply fixes in order
        remove_unused_imports(file_path)
        fix_whitespace_issues(file_path)
        fix_f_string_placeholders(file_path)
        fix_comparison_issues(file_path)

    print("\n✅ Automated linting fixes completed!")
    print("Run 'python3 -m flake8 --statistics --count' to check remaining issues")


if __name__ == '__main__':
    main()