#!/usr/bin/env python3
"""
Fix final linting issues - indentation errors and missing newlines.
"""

import os
import re
from pathlib import Path


def fix_indentation_errors(file_path):
    """Fix indentation errors by removing extra indentation."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        fixed_lines = []
        
        for line in lines:
            # Remove leading spaces that cause indentation errors
            if line.strip() and line.startswith('    ') and not line.strip().startswith('#'):
                # Check if this is likely an import that got indented
                stripped = line.strip()
                if (stripped.startswith(('import ', 'from ')) or 
                    stripped.startswith(('def ', 'class ', 'if ', 'else:', 'elif ', 'try:', 'except', 'finally:', 'with ', 'for ', 'while '))):
                    fixed_lines.append(stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Ensure file ends with newline
        if fixed_lines and not content.endswith('\n'):
            fixed_lines.append('')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"✓ Fixed indentation in {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing indentation in {file_path}: {e}")


def fix_missing_newlines(file_path):
    """Fix missing newlines at end of file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content and not content.endswith('\n'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content + '\n')
            print(f"✓ Added newline to {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing newlines in {file_path}: {e}")


def fix_blank_line_issues(file_path):
    """Fix blank line issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Fix E302: expected 2 blank lines, found 1
            if (line.strip().startswith(('def ', 'class ')) and 
                i > 0 and 
                fixed_lines and 
                fixed_lines[-1].strip() != '' and
                not fixed_lines[-1].strip().startswith('@')):
                
                # Count existing blank lines
                blank_count = 0
                j = len(fixed_lines) - 1
                while j >= 0 and fixed_lines[j].strip() == '':
                    blank_count += 1
                    j -= 1
                
                # Add blank line if needed
                if blank_count < 2:
                    fixed_lines.append('')
            
            # Fix E305: expected 2 blank lines after class or function definition
            if (i < len(lines) - 1 and 
                line.strip().startswith(('def ', 'class ')) and
                lines[i + 1].strip() != '' and
                not lines[i + 1].strip().startswith(('def ', 'class ', '@', '#'))):
                
                fixed_lines.append(line)
                fixed_lines.append('')
                i += 1
                continue
            
            # Fix E303: too many blank lines
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
            
            # Fix E304: blank lines found after function decorator
            if line.strip().startswith('@') and i < len(lines) - 1:
                fixed_lines.append(line)
                # Skip any blank lines after decorator
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    j += 1
                i = j
                continue
            
            fixed_lines.append(line)
            i += 1
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"✓ Fixed blank lines in {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing blank lines in {file_path}: {e}")


def fix_f_string_issues(file_path):
    """Fix f-string missing placeholders."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find f-strings without placeholders and convert to regular strings
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
            print(f"✓ Fixed f-strings in {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing f-strings in {file_path}: {e}")


def main():
    """Fix final linting issues."""
    print("🔧 Fixing final linting issues...")
    
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
        fix_indentation_errors(file_path)
        fix_missing_newlines(file_path)
        fix_blank_line_issues(file_path)
        fix_f_string_issues(file_path)
    
    print("\n✅ Final linting fixes completed!")


if __name__ == '__main__':
    main()
