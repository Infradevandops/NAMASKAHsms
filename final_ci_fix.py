#!/usr/bin/env python3
"""
FINAL CI/CD PIPELINE FIX
This script performs the ultimate fix for all remaining syntax issues.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def fix_method_indentation(file_path):
    """Fix class method indentation issues in Python files."""
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
            
            # Fix @classmethod decorator indentation
            if line.strip() == '@classmethod' and not line.startswith('    @'):
                fixed_lines.append('    @classmethod')
                continue
            
            # Fix @field_validator decorator indentation  
            if line.strip().startswith('@field_validator') and not line.startswith('    @'):
                fixed_lines.append('    ' + line.strip())
                continue
            
            # Fix method definitions that should be class methods
            if re.match(r'^def \w+\(cls,', line.strip()) and not line.startswith('    def'):
                fixed_lines.append('    ' + line.strip())
                continue
            
            # Fix if statements inside methods
            if line.strip().startswith('if ') and not line.startswith('    if ') and not line.startswith('if '):
                # Check if previous line was a method definition or decorator
                if i > 0 and ('def ' in lines[i-1] or '@' in lines[i-1] or ':' in lines[i-1]):
                    fixed_lines.append('        ' + line.strip())
                else:
                    fixed_lines.append(line)
                continue
            
            # Fix return statements
            if line.strip().startswith('return ') and not line.startswith('    return ') and not line.startswith('return '):
                if i > 0 and ('def ' in lines[i-1] or 'if ' in lines[i-1] or 'else:' in lines[i-1]):
                    fixed_lines.append('        ' + line.strip())
                else:
                    fixed_lines.append(line)
                continue
            
            # Fix raise statements
            if line.strip().startswith('raise ') and not line.startswith('        raise'):
                fixed_lines.append('            ' + line.strip())
                continue
            
            fixed_lines.append(line)
        
        # Write back the fixed content
        with open(file_path, 'w') as f:
            f.write('\n'.join(fixed_lines))
            if fixed_lines:
                f.write('\n')
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def validate_python_syntax(file_path):
    """Validate Python syntax of a file."""
    try:
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        return True
    except (SyntaxError, IndentationError) as e:
        print(f"❌ {file_path} - {type(e).__name__}: {e}")
        return False


def main():
    """Execute final CI/CD fixes."""
    print("🚀 FINAL CI/CD PIPELINE FIX")
    print("=" * 50)
    
    # Critical files that need fixing
    critical_files = [
        "app/schemas/payment.py",
        "app/schemas/validators.py", 
        "app/schemas/auth.py",
        "app/schemas/verification.py",
        "app/schemas/analytics.py",
        "app/schemas/system.py"
    ]
    
    print("\n📋 Step 1: Fixing method indentation...")
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"🔧 Fixing {file_path}")
            fix_method_indentation(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n📋 Step 2: Running autopep8 on all files...")
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                subprocess.run([
                    sys.executable, '-m', 'autopep8',
                    '--in-place',
                    '--aggressive',
                    '--aggressive',
                    '--max-line-length=100',
                    file_path
                ], check=True, capture_output=True)
                print(f"✅ Linted {file_path}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Linting warning for {file_path}")
    
    print("\n📋 Step 3: Validating syntax...")
    all_valid = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            if validate_python_syntax(file_path):
                print(f"✅ {file_path} - Valid syntax")
            else:
                all_valid = False
    
    if all_valid:
        print("\n🎉 FINAL FIX COMPLETE - ALL SYNTAX VALID!")
        print("✅ Ready for CI/CD pipeline success")
        return True
    else:
        print("\n⚠️  Some files still have syntax issues")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
