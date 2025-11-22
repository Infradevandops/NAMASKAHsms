#!/usr/bin/env python3
"""Script to fix timezone issues across the codebase."""
import re
from pathlib import Path

def fix_timezone_issues():
    """Fix timezone issues in Python files."""
    app_dir = Path("app")
    if not app_dir.exists():
        print("Error: app directory not found")
        return False
    
    fixes_applied = 0
    
    # Patterns to fix
    patterns = [
        # datetime.now() -> utc_now()
        (r'datetime\.now\(\)', 'utc_now()'),
        # datetime.strptime without timezone -> parse_date_string
        (r'datetime\.strptime\(([^,]+),\s*([^)]+)\)', r'parse_date_string(\1, \2)'),
        # filename with datetime.now() -> get_timestamp_filename()
        (r'datetime\.now\(\)\.strftime\([\'"]%Y%m%d_%H%M%S[\'"]\)', 'get_timestamp_filename()'),
    ]
    
    for py_file in app_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            needs_import = False
            
            # Apply fixes
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    needs_import = True
            
            # Add import if needed and not already present
            if needs_import and 'from app.utils.timezone_utils import' not in content:
                # Find existing imports
                import_match = re.search(r'(from datetime import[^\n]*\n)', content)
                if import_match:
                    import_line = import_match.group(1)
                    new_import = import_line + 'from app.utils.timezone_utils import utc_now, parse_date_string, get_timestamp_filename\n'
                    content = content.replace(import_line, new_import)
                else:
                    # Add at top after docstring
                    lines = content.split('\n')
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('"""') or line.strip().startswith("'''"):
                            # Find end of docstring
                            quote = '"""' if '"""' in line else "'''"
                            if line.count(quote) == 2:  # Single line docstring
                                insert_idx = i + 1
                                break
                            else:  # Multi-line docstring
                                for j in range(i + 1, len(lines)):
                                    if quote in lines[j]:
                                        insert_idx = j + 1
                                        break
                                break
                    
                    lines.insert(insert_idx, 'from app.utils.timezone_utils import utc_now, parse_date_string, get_timestamp_filename')
                    content = '\n'.join(lines)
            
            # Write back if changed
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed timezone issues in {py_file}")
                fixes_applied += 1
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    print(f"Applied timezone fixes to {fixes_applied} files")
    return True

if __name__ == "__main__":
    fix_timezone_issues()