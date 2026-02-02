#!/usr/bin/env python3
"""
Ultimate indentation fix script - Comprehensive solution for all Python files
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_indentation_issues(file_path: str) -> bool:
    """Fix common indentation issues in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                fixed_lines.append(line)
                i += 1
                continue
            
            # Fix common patterns
            
            # Pattern 1: Method/function definitions with wrong indentation
            if re.match(r'^(\s*)@\w+', line):  # Decorator
                # Next line should be function/method definition
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.match(r'^\s*(def|async def|class)', next_line):
                        # Ensure decorator and function have same indentation
                        indent = len(line) - len(line.lstrip())
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent != indent:
                            next_line = ' ' * indent + next_line.lstrip()
                            lines[i + 1] = next_line
            
            # Pattern 2: Function definitions that should be methods (inside class)
            elif re.match(r'^(def|async def)\s+\w+', line.strip()):
                # Check if we're inside a class by looking backwards
                in_class = False
                class_indent = 0
                for j in range(i - 1, -1, -1):
                    prev_line = lines[j].strip()
                    if prev_line.startswith('class '):
                        in_class = True
                        class_indent = len(lines[j]) - len(lines[j].lstrip())
                        break
                    elif prev_line and not prev_line.startswith('#') and not prev_line.startswith('@'):
                        if len(lines[j]) - len(lines[j].lstrip()) <= class_indent:
                            break
                
                if in_class:
                    # This should be indented as a method
                    current_indent = len(line) - len(line.lstrip())
                    expected_indent = class_indent + 4
                    if current_indent != expected_indent:
                        line = ' ' * expected_indent + line.lstrip()
            
            # Pattern 3: Statements that should be inside functions/methods
            elif line.strip() and not line.strip().startswith('#'):
                # Check if this line should be indented more
                if re.match(r'^(if|for|while|try|with|return|raise|yield)', line.strip()):
                    # Look for the function/method this belongs to
                    for j in range(i - 1, -1, -1):
                        prev_line = lines[j].strip()
                        if re.match(r'^(def|async def|class)', prev_line):
                            func_indent = len(lines[j]) - len(lines[j].lstrip())
                            current_indent = len(line) - len(line.lstrip())
                            expected_indent = func_indent + 4
                            if current_indent < expected_indent:
                                line = ' ' * expected_indent + line.lstrip()
                            break
                        elif prev_line and len(lines[j]) - len(lines[j].lstrip()) == 0:
                            break
            
            fixed_lines.append(line)
            i += 1
        
        # Join lines and validate syntax
        fixed_content = '\n'.join(fixed_lines)
        
        # Try to parse the fixed content
        try:
            ast.parse(fixed_content)
            # If parsing succeeds, write the fixed content
            if fixed_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                return True
        except SyntaxError as e:
            print(f"❌ Syntax error in {file_path} after fix: {e}")
            return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def validate_python_file(file_path: str) -> Tuple[bool, str]:
    """Validate if a Python file has correct syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        return True, "Valid"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main function to fix indentation issues."""
    print("🔧 ULTIMATE INDENTATION FIX")
    print("=" * 50)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv']):
            continue
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    # Critical files that must work
    critical_files = [
        'main.py',
        'app/core/config.py',
        'app/core/secrets.py',
        'app/core/pydantic_compat.py',
        'app/core/dependencies.py',
        'app/schemas/__init__.py',
        'app/schemas/payment.py',
        'app/schemas/validators.py',
        'app/schemas/auth.py',
        'app/services/base.py',
        'app/services/auth_service.py',
        'tests/conftest.py'
    ]
    
    # First, fix critical files
    print("\n🎯 Fixing critical files...")
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"🔧 Fixing {file_path}")
            fixed = fix_indentation_issues(file_path)
            valid, msg = validate_python_file(file_path)
            if valid:
                print(f"✅ {file_path} - Valid")
            else:
                print(f"❌ {file_path} - {msg}")
    
    # Test main import
    print("\n🧪 Testing main application import...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-c', 'from main import app; print("SUCCESS")'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Main application imports successfully!")
        else:
            print(f"❌ Main import failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
    
    print("\n🏁 Ultimate fix complete!")


if __name__ == "__main__":
    main()