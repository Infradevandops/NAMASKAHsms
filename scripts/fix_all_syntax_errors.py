#!/usr/bin/env python3
"""Fix all syntax errors in Python files."""

import re
from pathlib import Path

def fix_file_syntax(file_path):
    """Fix syntax errors in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix trailing commas in import statements
        # Pattern 1: from module import item1, item2,\n    item3
        pattern1 = r'(from\s+[\w.]+\s+import\s+[^,\n]+),(\s*\n\s*[^,\n]+)'
        while re.search(pattern1, content):
            content = re.sub(pattern1, r'\1\2', content)
        
        # Pattern 2: trailing comma at end of import line
        pattern2 = r'(from\s+[\w.]+\s+import\s+[^,\n]+),(\s*\n)'
        content = re.sub(pattern2, r'\1\2', content)
        
        # Pattern 3: Multi-line imports with trailing comma
        pattern3 = r'(from\s+[\w.]+\s+import\s+[^,\n]+(?:,\s*[^,\n]+)*),(\s*\n)'
        content = re.sub(pattern3, r'\1\2', content)
        
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
    """Fix all Python files in the models directory."""
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "app" / "models"
    
    if not models_dir.exists():
        print(f"Models directory not found: {models_dir}")
        return
    
    python_files = list(models_dir.glob("*.py"))
    fixed_count = 0
    
    for file_path in python_files:
        if fix_file_syntax(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files with syntax errors.")

if __name__ == "__main__":
    main()