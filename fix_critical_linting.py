#!/usr/bin/env python3
"""
Fix critical linting issues that are blocking CI/CD.
"""

import os
import re
from pathlib import Path


def fix_import_order(file_path):
    """Fix module level import not at top of file issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        
        # Find first non-import, non-comment, non-docstring line
        imports = []
        other_lines = []
        in_docstring = False
        docstring_quotes = None
        found_first_code = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Handle docstrings
            if not found_first_code and ('"""' in line or "'''" in line):
                if not in_docstring:
                    in_docstring = True
                    docstring_quotes = '"""' if '"""' in line else "'''"
                    other_lines.append(lines[i])
                    if line.count(docstring_quotes) >= 2:
                        in_docstring = False
                elif docstring_quotes in line:
                    in_docstring = False
                    other_lines.append(lines[i])
                else:
                    other_lines.append(lines[i])
                i += 1
                continue
            
            if in_docstring:
                other_lines.append(lines[i])
                i += 1
                continue
            
            # Skip comments and empty lines at the top
            if not found_first_code and (line.startswith('#') or line == ''):
                other_lines.append(lines[i])
                i += 1
                continue
            
            # Check if it's an import
            if line.startswith(('import ', 'from ')) and not found_first_code:
                imports.append(lines[i])
            elif line.startswith(('import ', 'from ')) and found_first_code:
                # This is a misplaced import - move it to top
                imports.append(lines[i])
            else:
                if line and not line.startswith('#'):
                    found_first_code = True
                other_lines.append(lines[i])
            
            i += 1
        
        # Reconstruct file with imports at top
        if imports:
            # Find where to insert imports (after initial comments/docstrings)
            insert_pos = 0
            for i, line in enumerate(other_lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not ('"""' in stripped or "'''" in stripped):
                    insert_pos = i
                    break
            
            # Insert imports
            new_content = other_lines[:insert_pos] + imports + [''] + other_lines[insert_pos:]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_content))
            
            print(f"✓ Fixed import order in {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing imports in {file_path}: {e}")


def fix_blank_lines(file_path):
    """Fix blank line issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Fix too many blank lines (E303)
            if line.strip() == '':
                blank_count = 1
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    blank_count += 1
                    j += 1
                
                # Limit to max 2 blank lines
                if blank_count > 2:
                    fixed_lines.extend([''] * 2)
                else:
                    fixed_lines.extend([''] * blank_count)
                
                i = j
                continue
            
            # Check for function/class definitions that need 2 blank lines before
            if (line.strip().startswith(('def ', 'class ')) and 
                fixed_lines and 
                fixed_lines[-1].strip() != '' and
                not fixed_lines[-1].strip().startswith('@')):
                
                # Add blank line if needed
                if len(fixed_lines) >= 2 and fixed_lines[-2].strip() != '':
                    fixed_lines.append('')
                elif len(fixed_lines) < 2:
                    fixed_lines.append('')
            
            fixed_lines.append(line)
            i += 1
        
        # Ensure file ends with newline
        if fixed_lines and not content.endswith('\n'):
            fixed_lines.append('')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"✓ Fixed blank lines in {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing blank lines in {file_path}: {e}")


def fix_bare_except(file_path):
    """Fix bare except clauses."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace bare except with except Exception
        content = re.sub(r'\bexcept\s*:', 'except Exception:', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Fixed bare except in {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing bare except in {file_path}: {e}")


def fix_comparison_issues(file_path):
    """Fix comparison to True/False issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix == True comparisons
        content = re.sub(r'(\w+)\s*==\s*True\b', r'\1', content)
        # Fix == False comparisons  
        content = re.sub(r'(\w+)\s*==\s*False\b', r'not \1', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Fixed comparisons in {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing comparisons in {file_path}: {e}")


def main():
    """Fix critical linting issues."""
    print("🔧 Fixing critical linting issues...")
    
    # Get Python files with issues
    python_files = []
    for directory in ['scripts', 'tests', '.']:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                # Skip certain directories
                if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'htmlcov', '.venv']):
                    continue
                    
                for file in files:
                    if file.endswith('.py') and not file.startswith('fix_'):
                        file_path = os.path.join(root, file)
                        # Only process files in our project, not in .venv
                        if '.venv' not in file_path:
                            python_files.append(file_path)
    
    print(f"Processing {len(python_files)} Python files...")
    
    for file_path in python_files:
        print(f"\n📁 Processing {file_path}")
        
        # Apply fixes
        fix_import_order(file_path)
        fix_blank_lines(file_path)
        fix_bare_except(file_path)
        fix_comparison_issues(file_path)
    
    print("\n✅ Critical linting fixes completed!")


if __name__ == '__main__':
    main()
