#!/usr/bin/env python3
"""
Comprehensive indentation fix for all Python files.
This script fixes common indentation patterns that break CI/CD.
"""

import os
import re
from pathlib import Path


def fix_indentation_in_file(file_path):
    """Fix common indentation issues in a Python file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.splitlines()
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                fixed_lines.append(line)
                continue
            
            # Fix method definitions that got unindented
            if re.match(r'^def \w+\(', line.strip()) and not line.startswith('    def ') and not line.startswith('def '):
                # Check if this should be a class method
                if i > 0 and ('class ' in lines[i-1] or '@' in lines[i-1] or 'def ' in lines[i-1]):
                    fixed_lines.append('    ' + line.strip())
                else:
                    fixed_lines.append(line)
            
            # Fix if statements that got unindented
            elif re.match(r'^if ', line.strip()) and not line.startswith('    if ') and not line.startswith('if '):
                # Check if this should be inside a function/method
                if i > 0 and ('def ' in lines[i-1] or ':' in lines[i-1]):
                    fixed_lines.append('        ' + line.strip())
                else:
                    fixed_lines.append(line)
            
            # Fix try/except blocks
            elif re.match(r'^(try|except|finally):', line.strip()) and not line.startswith('    '):
                if i > 0 and ('def ' in lines[i-1] or ':' in lines[i-1]):
                    fixed_lines.append('    ' + line.strip())
                else:
                    fixed_lines.append(line)
            
            # Fix return statements
            elif line.strip().startswith('return ') and not line.startswith('    return ') and not line.startswith('return '):
                if i > 0 and ('def ' in lines[i-1] or 'if ' in lines[i-1] or 'else:' in lines[i-1]):
                    fixed_lines.append('        ' + line.strip())
                else:
                    fixed_lines.append(line)
            
            else:
                fixed_lines.append(line)
        
        # Write back the fixed content
        with open(file_path, 'w') as f:
            f.write('\n'.join(fixed_lines))
            if fixed_lines:  # Add final newline if file is not empty
                f.write('\n')
        
        print(f"✅ Fixed indentation in {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def main():
    """Fix indentation in critical Python files."""
    critical_files = [
        "app/schemas/auth.py",
        "app/models/base.py",
        "app/models/commission.py", 
        "app/models/reseller.py",
        "app/models/__init__.py",
        "app/core/database.py",
        "app/core/dependencies.py",
        "app/core/tier_helpers.py",
        "app/schemas/__init__.py",
        "app/utils/path_security.py",
        "tests/conftest.py",
        "app/core/config.py",
        "app/core/secrets.py",
        "app/core/pydantic_compat.py"
    ]
    
    print("🔧 COMPREHENSIVE INDENTATION FIX")
    print("=" * 50)
    
    fixed_count = 0
    for file_path in critical_files:
        if os.path.exists(file_path):
            if fix_indentation_in_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n✅ Fixed indentation in {fixed_count} files")
    return fixed_count > 0


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
