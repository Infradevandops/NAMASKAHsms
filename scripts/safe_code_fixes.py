#!/usr/bin/env python3
"""Safe code quality fixes that won't break syntax."""
import re
from pathlib import Path


def fix_identity_equality_safe():
    """Safely fix identity vs equality issues."""
    fixes_applied = 0
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Only fix obvious cases that are definitely wrong
            # Fix 'is' with numeric literals
            content = re.sub(r'\bis\s+([0-9]+)(?!\w)', r'== \1', content)
            
            # Fix 'is not' with numeric literals  
            content = re.sub(r'\bis\s+not\s+([0-9]+)(?!\w)', r'!= \1', content)
            
            if content != original_content:
                with open(py_file, 'w') as f:
                    f.write(content)
                print(f"Fixed identity/equality in {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return fixes_applied


def fix_trailing_whitespace():
    """Remove trailing whitespace."""
    fixes_applied = 0
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                lines = f.readlines()
            
            fixed_lines = [line.rstrip() + '\n' for line in lines]
            
            if lines != fixed_lines:
                with open(py_file, 'w') as f:
                    f.writelines(fixed_lines)
                print(f"Fixed trailing whitespace in {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return fixes_applied


def fix_multiple_blank_lines():
    """Fix multiple consecutive blank lines."""
    fixes_applied = 0
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Replace 3+ consecutive newlines with 2
            fixed_content = re.sub(r'\n\n\n+', '\n\n', content)
            
            if content != fixed_content:
                with open(py_file, 'w') as f:
                    f.write(fixed_content)
                print(f"Fixed blank lines in {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return fixes_applied


def check_resource_leaks():
    """Check for potential resource leaks."""
    issues = []
    
    for py_file in Path("app").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Check for file operations without context managers
                if re.search(r'\w+\s*=\s*open\s*\(', line) and 'with' not in line:
                    issues.append(f"{py_file}:{i} - File opened without context manager")
                
                # Check for database connections without proper closing
                if re.search(r'\.connect\s*\(', line) and 'with' not in line:
                    issues.append(f"{py_file}:{i} - Connection without context manager")
                    
        except Exception as e:
            print(f"Error checking {py_file}: {e}")
    
    return issues


def main():
    """Run safe code quality fixes."""
    print("🔧 Running safe code quality fixes...")
    
    print("\n1. Fixing identity/equality issues...")
    identity_fixes = fix_identity_equality_safe()
    print(f"   Applied {identity_fixes} identity/equality fixes")
    
    print("\n2. Removing trailing whitespace...")
    whitespace_fixes = fix_trailing_whitespace()
    print(f"   Fixed {whitespace_fixes} files with trailing whitespace")
    
    print("\n3. Fixing multiple blank lines...")
    blank_line_fixes = fix_multiple_blank_lines()
    print(f"   Fixed {blank_line_fixes} files with multiple blank lines")
    
    print("\n4. Checking for resource leaks...")
    resource_issues = check_resource_leaks()
    if resource_issues:
        print("   Potential resource leaks found:")
        for issue in resource_issues[:10]:  # Show first 10
            print(f"     {issue}")
        if len(resource_issues) > 10:
            print(f"     ... and {len(resource_issues) - 10} more")
    else:
        print("   ✅ No obvious resource leaks found")
    
    total_fixes = identity_fixes + whitespace_fixes + blank_line_fixes
    print(f"\n✅ Safe code quality fixes complete! Applied {total_fixes} fixes.")
    
    return total_fixes


if __name__ == "__main__":
    main()