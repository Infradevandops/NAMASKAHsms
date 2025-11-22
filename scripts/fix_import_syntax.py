#!/usr/bin/env python3
"""Fix trailing comma syntax errors in import statements."""

import re
from pathlib import Path

def fix_import_syntax(file_path):
    """Fix trailing comma syntax errors in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match import statements with trailing commas
        # This matches: from module import item1, item2,\n    item3
        pattern = r'(from\s+[\w.]+\s+import\s+[^,\n]+),(\s*\n\s*[^,\n]+)'
        
        # Fix trailing commas in import statements
        while True:
            match = re.search(pattern, content)
            if not match:
                break
            
            # Remove the trailing comma
            fixed_line = match.group(1) + match.group(2)
            content = content[:match.start()] + fixed_line + content[match.end():]
        
        # Also fix cases where there's a trailing comma at the end of import line
        pattern2 = r'(from\s+[\w.]+\s+import\s+[^,\n]+),(\s*\n)'
        content = re.sub(pattern2, r'\1\2', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def main():
    """Fix all Python files in the project."""
    project_root = Path(__file__).parent.parent
    python_files = list(project_root.rglob("*.py"))
    
    fixed_count = 0
    
    for file_path in python_files:
        # Skip test files and virtual environments
        if any(skip in str(file_path) for skip in ['venv', '__pycache__', '.git']):
            continue
            
        if fix_import_syntax(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files with import syntax errors.")

if __name__ == "__main__":
    main()