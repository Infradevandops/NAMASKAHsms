#!/usr/bin/env python3
"""
COMPREHENSIVE INDENTATION FIX
Fixes all Python files with indentation issues in the project.
"""

import os
import subprocess
import sys
from pathlib import Path


def fix_file_indentation(file_path):
    """Fix indentation issues in a Python file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.splitlines()
        fixed_lines = []
        in_class = False
        in_function = False
        class_indent = 0
        function_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue
            
            # Handle class definitions
            if stripped.startswith('class '):
                in_class = True
                class_indent = 0
                fixed_lines.append(line)
                continue
            
            # Handle function/method definitions
            if stripped.startswith('def ') or stripped.startswith('async def '):
                if in_class:
                    # Method inside class
                    if not line.startswith('    def ') and not line.startswith('    async def '):
                        fixed_lines.append('    ' + stripped)
                    else:
                        fixed_lines.append(line)
                    in_function = True
                    function_indent = 4
                else:
                    # Top-level function
                    if line.startswith('def ') or line.startswith('async def '):
                        fixed_lines.append(line)
                    else:
                        fixed_lines.append(stripped)
                    in_function = True
                    function_indent = 0
                continue
            
            # Handle docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_function and function_indent > 0:
                    if not line.startswith('        '):
                        fixed_lines.append('        ' + stripped)
                    else:
                        fixed_lines.append(line)
                elif in_class and not in_function:
                    if not line.startswith('    '):
                        fixed_lines.append('    ' + stripped)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                continue
            
            # Handle if statements
            if stripped.startswith('if '):
                if in_function and function_indent > 0:
                    if not line.startswith('        if '):
                        fixed_lines.append('        ' + stripped)
                    else:
                        fixed_lines.append(line)
                elif in_class and not in_function:
                    if not line.startswith('    if '):
                        fixed_lines.append('    ' + stripped)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                continue
            
            # Handle for/while loops
            if stripped.startswith('for ') or stripped.startswith('while '):
                if in_function and function_indent > 0:
                    if not line.startswith('        '):
                        fixed_lines.append('        ' + stripped)
                    else:
                        fixed_lines.append(line)
                elif in_class and not in_function:
                    if not line.startswith('    '):
                        fixed_lines.append('    ' + stripped)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                continue
            
            # Handle try/except blocks
            if stripped.startswith('try:') or stripped.startswith('except ') or stripped.startswith('finally:'):
                if in_function and function_indent > 0:
                    if not line.startswith('        '):
                        fixed_lines.append('        ' + stripped)
                    else:
                        fixed_lines.append(line)
                elif in_class and not in_function:
                    if not line.startswith('    '):
                        fixed_lines.append('    ' + stripped)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                continue
            
            # Handle return statements
            if stripped.startswith('return '):
                if in_function and function_indent > 0:
                    if not line.startswith('        return '):
                        fixed_lines.append('        ' + stripped)
                    else:
                        fixed_lines.append(line)
                elif in_class and not in_function:
                    if not line.startswith('    return '):
                        fixed_lines.append('    ' + stripped)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                continue
            
            # Handle other statements in functions/methods
            if in_function and function_indent > 0:
                if not line.startswith('        ') and not line.startswith('    def ') and not line.startswith('    async def '):
                    fixed_lines.append('        ' + stripped)
                else:
                    fixed_lines.append(line)
            elif in_class and not in_function:
                if not line.startswith('    ') and not stripped.startswith('def ') and not stripped.startswith('async def '):
                    fixed_lines.append('    ' + stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Write fixed content
        with open(file_path, 'w') as f:
            f.write('\n'.join(fixed_lines))
            if fixed_lines and not content.endswith('\n'):
                f.write('\n')
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def main():
    """Fix indentation in all Python files."""
    print("🔧 COMPREHENSIVE INDENTATION FIX")
    print("=" * 50)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', '.venv', 'htmlcov']):
            continue
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    fixed_count = 0
    for file_path in python_files:
        print(f"🔧 Fixing {file_path}")
        if fix_file_indentation(file_path):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count}/{len(python_files)} files")
    
    # Validate syntax of critical files
    critical_files = [
        'main.py',
        'app/services/auth_service.py',
        'app/services/base.py',
        'app/core/logging.py',
        'app/core/tier_config.py'
    ]
    
    print("\n🔍 Validating critical files...")
    all_valid = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                subprocess.run([sys.executable, '-m', 'py_compile', file_path], 
                             check=True, capture_output=True)
                print(f"✅ {file_path} - Valid syntax")
            except subprocess.CalledProcessError as e:
                print(f"❌ {file_path} - Syntax error")
                all_valid = False
    
    if all_valid:
        print("\n🎉 ALL CRITICAL FILES HAVE VALID SYNTAX!")
        return True
    else:
        print("\n⚠️  Some files still have syntax errors")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
