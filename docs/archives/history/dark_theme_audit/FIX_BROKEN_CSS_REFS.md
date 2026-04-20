# 🔧 Quick Fix: Broken CSS References

**Time**: 1.25 hours  
**Pages to Fix**: 5  
**Issue**: Malformed Jinja2 syntax in CSS/JS references

---

## 🎯 The Problem

These 5 pages have broken asset references:

```html
<!-- WRONG -->
<link rel="stylesheet" href="/static/css/design-tokens.css') }}">
                                                          ^^^^
                                                    Malformed syntax
```

This causes:
- CSS files don't load
- Pages appear unstyled
- Broken user experience

---

## ✅ The Solution

Replace with correct Jinja2 syntax:

```html
<!-- CORRECT -->
<link rel="stylesheet" href="{{ url_for('static', path='css/design-tokens.css') }}">
```

---

## 📋 Pages to Fix

1. templates/cookies.html
2. templates/services.html
3. templates/reviews.html
4. templates/affiliate_program.html
5. templates/api_docs.html

---

## 🚀 Step-by-Step Fix

### For Each Page:

1. **Open the file**
2. **Find all instances** of malformed syntax
3. **Replace** with correct syntax
4. **Test** the page loads

---

## 🔍 Find & Replace Patterns

### Pattern 1: CSS Files

**Find**:
```
/static/css/design-tokens.css') }}
```

**Replace**:
```
{{ url_for('static', path='css/design-tokens.css') }}
```

---

### Pattern 2: Components CSS

**Find**:
```
/static/css/components.css') }}
```

**Replace**:
```
{{ url_for('static', path='css/components.css') }}
```

---

### Pattern 3: JavaScript Files

**Find**:
```
/static/js/design-system.js') }}
```

**Replace**:
```
{{ url_for('static', path='js/design-system.js') }}
```

---

## 💻 Automated Fix Script

Save this as `fix_css_refs.py`:

```python
#!/usr/bin/env python3
"""Fix broken CSS references in HTML templates."""

import re
from pathlib import Path

# Files to fix
FILES = [
    'templates/cookies.html',
    'templates/services.html',
    'templates/reviews.html',
    'templates/affiliate_program.html',
    'templates/api_docs.html',
]

# Patterns to fix
PATTERNS = [
    # CSS files
    (r'/static/css/([^\']+)\.css\'\) }}', r"{{ url_for('static', path='css/\1.css') }}"),
    # JS files
    (r'/static/js/([^\']+)\.js\'\) }}', r"{{ url_for('static', path='js/\1.js') }}"),
]

def fix_file(filepath):
    """Fix CSS/JS references in a file."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    # Read file
    content = path.read_text()
    original = content
    
    # Apply all patterns
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content)
    
    # Check if changes were made
    if content == original:
        print(f"✅ {filepath} - No changes needed")
        return True
    
    # Backup original
    backup_path = path.with_suffix('.html.backup')
    backup_path.write_text(original)
    print(f"📦 Created backup: {backup_path}")
    
    # Write fixed content
    path.write_text(content)
    print(f"✅ Fixed: {filepath}")
    
    return True

def main():
    """Fix all files."""
    print("🔧 Fixing broken CSS/JS references...\n")
    
    success_count = 0
    for filepath in FILES:
        if fix_file(filepath):
            success_count += 1
        print()
    
    print(f"\n✅ Fixed {success_count}/{len(FILES)} files")
    print("\n🧪 Next steps:")
    print("1. Test each page loads correctly")
    print("2. Verify styles are applied")
    print("3. Check browser console for errors")
    print("4. If all good, delete .backup files")

if __name__ == '__main__':
    main()
```

**Usage**:
```bash
python fix_css_refs.py
```

---

## 🧪 Testing

After fixing each page:

```bash
# Start server
./start.sh

# Test each page
open http://localhost:8000/cookies
open http://localhost:8000/services
open http://localhost:8000/reviews
open http://localhost:8000/affiliate-program
open http://localhost:8000/api-docs
```

**Check**:
- [ ] Page loads without errors
- [ ] Styles are applied correctly
- [ ] No console errors
- [ ] All content visible
- [ ] Links work

---

## 📊 Expected Results

### Before Fix
```
Browser Console:
❌ Failed to load resource: /static/css/design-tokens.css') }}
❌ Failed to load resource: /static/css/components.css') }}
❌ Failed to load resource: /static/js/design-system.js') }}

Page Appearance:
- Unstyled content
- Broken layout
- Missing fonts
- No colors
```

### After Fix
```
Browser Console:
✅ No errors

Page Appearance:
- Properly styled
- Correct layout
- Fonts loaded
- Colors applied
```

---

## 🔄 Manual Fix (If Script Fails)

### 1. cookies.html

Open `templates/cookies.html` and replace:

```html
<!-- Line ~7-9 -->
<link rel="stylesheet" href="{{ url_for('static', path='css/design-tokens.css') }}">
<link rel="stylesheet" href="{{ url_for('static', path='css/components.css') }}">

<!-- Line ~300+ -->
<script src="{{ url_for('static', path='js/design-system.js') }}"></script>
```

### 2. services.html

Same replacements as cookies.html

### 3. reviews.html

Same replacements as cookies.html

### 4. affiliate_program.html

Same replacements as cookies.html

### 5. api_docs.html

Same replacements as cookies.html

---

## ✅ Verification Checklist

After fixing all 5 pages:

- [ ] All pages load without errors
- [ ] CSS files load correctly (check Network tab)
- [ ] JavaScript works (if applicable)
- [ ] No console errors
- [ ] Responsive on mobile
- [ ] All content visible and styled
- [ ] Navigation works
- [ ] Forms work (if applicable)

---

## 🚀 Deployment

```bash
# 1. Test locally
./start.sh
# Visit each page and verify

# 2. Commit changes
git add templates/
git commit -m "fix: correct CSS/JS asset references in 5 pages"

# 3. Push and deploy
git push origin main
```

---

## 🆘 Troubleshooting

### Issue: Page still unstyled after fix

**Solution**: Clear browser cache
```bash
# Chrome/Firefox
Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

### Issue: Script doesn't find files

**Solution**: Run from project root
```bash
cd /path/to/Namaskah.app
python fix_css_refs.py
```

### Issue: Permission denied

**Solution**: Make script executable
```bash
chmod +x fix_css_refs.py
./fix_css_refs.py
```

---

## 📊 Time Estimate

- cookies.html: 15 minutes
- services.html: 15 minutes
- reviews.html: 15 minutes
- affiliate_program.html: 15 minutes
- api_docs.html: 15 minutes

**Total**: 1.25 hours (or 5 minutes with script)

---

## ✅ Success Criteria

All 5 pages:
- ✅ Load without errors
- ✅ Styles applied correctly
- ✅ No console errors
- ✅ Responsive design works
- ✅ Professional appearance

---

**Ready to fix? Run the script or do manual fixes!** 🚀
