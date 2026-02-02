#!/usr/bin/env python3
"""
SURGICAL CI/CD PIPELINE FIX
Targets only the critical files causing pipeline failures.
"""

import os
import subprocess
import sys
from pathlib import Path


def fix_critical_indentation_errors():
    """Fix only the critical indentation errors blocking CI."""
    critical_files = [
        "tests/conftest.py",
        "app/core/config.py", 
        "app/core/secrets.py",
        "app/core/pydantic_compat.py"
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"🔧 Fixing critical indentation in {file_path}")
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Fix common indentation patterns that break imports
                lines = content.splitlines()
                fixed_lines = []
                
                for i, line in enumerate(lines):
                    # Fix function definitions that got unindented
                    if line.strip().startswith('def ') and not line.startswith('    def ') and not line.startswith('def '):
                        if i > 0 and (lines[i-1].strip().startswith('class ') or 
                                    lines[i-1].strip().startswith('@') or
                                    'def ' in lines[i-1]):
                            fixed_lines.append('    ' + line.strip())
                        else:
                            fixed_lines.append(line)
                    # Fix if statements that got unindented  
                    elif line.strip().startswith('if ') and not line.startswith('    if ') and not line.startswith('if '):
                        if i > 0 and ('def ' in lines[i-1] or lines[i-1].strip().endswith(':')):
                            fixed_lines.append('        ' + line.strip())
                        else:
                            fixed_lines.append(line)
                    else:
                        fixed_lines.append(line)
                
                # Ensure file ends with newline
                if fixed_lines and not content.endswith('\n'):
                    fixed_lines.append('')
                
                with open(file_path, 'w') as f:
                    f.write('\n'.join(fixed_lines))
                
                print(f"✅ Fixed {file_path}")
                
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")


def run_targeted_linting():
    """Run linting only on critical files."""
    print("🔍 Running targeted linting fixes...")
    
    try:
        # Install autopep8 if not available
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'autopep8'], 
                      capture_output=True, check=False)
        
        # Fix only critical files with autopep8
        critical_files = [
            "tests/conftest.py",
            "app/core/config.py",
            "app/core/secrets.py", 
            "app/core/pydantic_compat.py"
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                result = subprocess.run([
                    sys.executable, '-m', 'autopep8',
                    '--in-place',
                    '--aggressive',
                    '--aggressive',
                    '--max-line-length=100',
                    file_path
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Linted {file_path}")
                else:
                    print(f"⚠️  Linting warning for {file_path}: {result.stderr}")
    
    except Exception as e:
        print(f"⚠️  Linting setup issue: {e}")


def validate_python_syntax():
    """Validate Python syntax of critical files."""
    print("🔍 Validating Python syntax...")
    
    critical_files = [
        "tests/conftest.py",
        "app/core/config.py",
        "app/core/secrets.py",
        "app/core/pydantic_compat.py"
    ]
    
    all_valid = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"✅ {file_path} - Valid syntax")
            except SyntaxError as e:
                print(f"❌ {file_path} - Syntax error: {e}")
                all_valid = False
            except IndentationError as e:
                print(f"❌ {file_path} - Indentation error: {e}")
                all_valid = False
    
    return all_valid


def run_critical_tests():
    """Run only the critical tests that were failing."""
    print("🧪 Running critical tests...")
    
    try:
        # Test analytics endpoint specifically
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_analytics_enhanced.py::test_analytics_summary_success',
            '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Critical analytics test passed")
            return True
        else:
            print(f"❌ Critical test failed:\n{result.stdout}\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Test timeout - may indicate import issues")
        return False
    except Exception as e:
        print(f"❌ Test execution error: {e}")
        return False


def main():
    """Execute surgical CI/CD fixes."""
    print("🚀 SURGICAL CI/CD PIPELINE FIX")
    print("=" * 50)
    
    # Step 1: Fix critical indentation
    print("\n📋 Step 1: Fixing critical indentation errors...")
    fix_critical_indentation_errors()
    
    # Step 2: Run targeted linting
    print("\n📋 Step 2: Running targeted linting...")
    run_targeted_linting()
    
    # Step 3: Validate syntax
    print("\n📋 Step 3: Validating Python syntax...")
    syntax_valid = validate_python_syntax()
    
    if not syntax_valid:
        print("❌ Syntax validation failed. Manual intervention required.")
        return False
    
    # Step 4: Run critical tests
    print("\n📋 Step 4: Running critical tests...")
    tests_pass = run_critical_tests()
    
    if tests_pass:
        print("\n🎉 SURGICAL FIX COMPLETE - Ready for CI/CD!")
        print("✅ All critical issues resolved")
        return True
    else:
        print("\n⚠️  Tests still failing - check output above")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)