#!/usr/bin/env python3
"""Fix broken CSS/JS references in HTML templates.

This script fixes malformed Jinja2 syntax in asset references.

Before: /static/css/design-tokens.css') }}
After:  {{ url_for('static', path='css/design-tokens.css') }}
"""

import re
from pathlib import Path
from typing import List, Tuple

# Files to fix
FILES = [
    'templates/cookies.html',
    'templates/services.html',
    'templates/reviews.html',
    'templates/affiliate_program.html',
    'templates/api_docs.html',
]

# Patterns to fix
PATTERNS: List[Tuple[str, str]] = [
    # CSS files - malformed syntax
    (r'href="/static/css/([^\']+)\.css\'\) }}"', r'href="{{ url_for(\'static\', path=\'css/\1.css\') }}"'),
    # JS files - malformed syntax
    (r'src="/static/js/([^\']+)\.js\'\) }}"', r'src="{{ url_for(\'static\', path=\'js/\1.js\') }}"'),
]


def fix_file(filepath: str) -> bool:
    """Fix CSS/JS references in a file.
    
    Args:
        filepath: Path to the HTML file to fix
        
    Returns:
        True if successful, False otherwise
    """
    path = Path(filepath)
    
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    print(f"📄 Processing: {filepath}")
    
    # Read file
    try:
        content = path.read_text(encoding='utf-8')
        original = content
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Apply all patterns
    changes_made = False
    for pattern, replacement in PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            print(f"   Found {len(matches)} malformed reference(s)")
            content = re.sub(pattern, replacement, content)
            changes_made = True
    
    # Check if changes were made
    if not changes_made:
        print(f"   ✅ No changes needed")
        return True
    
    # Backup original
    try:
        backup_path = path.with_suffix('.html.backup')
        backup_path.write_text(original, encoding='utf-8')
        print(f"   📦 Created backup: {backup_path.name}")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not create backup: {e}")
    
    # Write fixed content
    try:
        path.write_text(content, encoding='utf-8')
        print(f"   ✅ Fixed successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error writing file: {e}")
        return False


def main():
    """Fix all files."""
    print("🔧 Fixing broken CSS/JS references in HTML templates\n")
    print("=" * 60)
    print()
    
    success_count = 0
    failed_files = []
    
    for filepath in FILES:
        if fix_file(filepath):
            success_count += 1
        else:
            failed_files.append(filepath)
        print()
    
    # Summary
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   ✅ Fixed: {success_count}/{len(FILES)} files")
    
    if failed_files:
        print(f"   ❌ Failed: {len(failed_files)} files")
        for f in failed_files:
            print(f"      - {f}")
    
    print("\n🧪 Next steps:")
    print("   1. Start server: ./start.sh")
    print("   2. Test each page loads correctly")
    print("   3. Verify styles are applied")
    print("   4. Check browser console for errors")
    print("   5. If all good, delete .backup files")
    print("\n📝 Test URLs:")
    print("   - http://localhost:8000/cookies")
    print("   - http://localhost:8000/services")
    print("   - http://localhost:8000/reviews")
    print("   - http://localhost:8000/affiliate-program")
    print("   - http://localhost:8000/api-docs")
    
    return 0 if success_count == len(FILES) else 1


if __name__ == '__main__':
    exit(main())
