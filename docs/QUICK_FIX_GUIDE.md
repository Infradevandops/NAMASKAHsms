# 🔧 Quick Implementation Guide: Dark Theme Fixes

**Estimated Time**: 1.75 hours  
**Difficulty**: Easy  
**Files to Modify**: 5

---

## 🎯 Goal

Fix critical dark theme inconsistencies in legal and support pages.

---

## 📋 Files to Fix

1. `templates/terms.html` (30 min)
2. `templates/privacy.html` (30 min)
3. `templates/faq.html` (35 min)
4. `templates/cookies.html` (20 min)
5. `templates/services.html` (20 min)

---

## 🚀 Step-by-Step Instructions

### 1. Fix terms.html (30 minutes)

**Current Issue**: Standalone page with hardcoded dark theme

**Steps**:

1. **Backup the file**:
```bash
cp templates/terms.html templates/terms.html.backup
```

2. **Replace entire file** with:

```html
{% extends "public_base.html" %}

{% block page_title %}Terms of Service{% endblock %}

{% block head_extra %}
{{ super() }}
<style>
    .terms-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 40px 20px;
    }
    
    .terms-header {
        background: linear-gradient(135deg, var(--primary) 0%, #4f46e5 100%);
        padding: 40px 20px;
        text-align: center;
        border-radius: 16px;
        margin-bottom: 40px;
        color: white;
    }
    
    .terms-header h1 {
        font-size: 36px;
        margin-bottom: 12px;
    }
    
    .terms-header p {
        opacity: 0.9;
        font-size: 14px;
    }
    
    .terms-section {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    .terms-section h2 {
        font-size: 24px;
        color: var(--primary);
        margin-bottom: 16px;
    }
    
    .terms-section h3 {
        font-size: 18px;
        color: var(--success);
        margin-top: 16px;
        margin-bottom: 12px;
    }
    
    .terms-section p {
        color: var(--text-secondary);
        margin-bottom: 12px;
        line-height: 1.6;
    }
    
    .terms-section ul {
        margin-left: 20px;
        margin-bottom: 12px;
    }
    
    .terms-section li {
        margin-bottom: 8px;
        color: var(--text-secondary);
    }
    
    .highlight {
        background: rgba(239, 68, 68, 0.1);
        padding: 16px;
        border-left: 4px solid var(--error);
        border-radius: 4px;
        margin: 16px 0;
    }
</style>
{% endblock %}

{% block public_content %}
<div class="terms-container">
    <div class="terms-header">
        <h1>Terms of Service</h1>
        <p>Last Updated: December 2024</p>
    </div>

    <div class="terms-section">
        <h2>1. Acceptance of Terms</h2>
        <p>By accessing and using Namaskah's SMS verification services, you accept and agree to be bound by the terms and provision of this agreement.</p>
    </div>

    <div class="terms-section">
        <h2>2. Use License</h2>
        <p>Permission is granted to temporarily download one copy of the materials on Namaskah's website for personal, non-commercial transitory viewing only.</p>
        <ul>
            <li>Modify or copy the materials</li>
            <li>Use the materials for any commercial purpose</li>
            <li>Attempt to decompile or reverse engineer any software</li>
            <li>Remove any copyright or proprietary notations</li>
            <li>Transfer the materials to another person</li>
            <li>Use the service for illegal purposes</li>
        </ul>
    </div>

    <!-- Add remaining sections following same pattern -->
    
    <div class="terms-section">
        <h2>15. Contact Information</h2>
        <p>If you have any questions about these Terms of Service, please contact us at:</p>
        <ul>
            <li>Email: legal@namaskah.com</li>
            <li>Website: www.namaskah.com</li>
        </ul>
    </div>
</div>
{% endblock %}
```

3. **Test**:
```bash
# Start server
./start.sh

# Visit http://localhost:8000/terms
# Toggle theme and verify it works
```

---

### 2. Fix privacy.html (30 minutes)

**Steps**: Same as terms.html

1. Backup: `cp templates/privacy.html templates/privacy.html.backup`
2. Replace with template extending `public_base.html`
3. Use same CSS variable pattern
4. Test theme toggle

---

### 3. Fix faq.html (35 minutes)

**Current Issue**: Standalone page + JavaScript needs CSP nonce

**Steps**:

1. **Backup**: `cp templates/faq.html templates/faq.html.backup`

2. **Replace with**:

```html
{% extends "public_base.html" %}

{% block page_title %}FAQ{% endblock %}

{% block head_extra %}
{{ super() }}
<style>
    .faq-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 40px 20px;
    }
    
    .faq-header {
        background: linear-gradient(135deg, var(--primary) 0%, #4f46e5 100%);
        padding: 40px 20px;
        text-align: center;
        border-radius: 16px;
        margin-bottom: 40px;
        color: white;
    }
    
    .faq-item {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        margin-bottom: 12px;
        overflow: hidden;
    }
    
    .faq-question {
        padding: 16px;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s;
    }
    
    .faq-question:hover {
        background: var(--bg-secondary);
    }
    
    .faq-question h3 {
        font-size: 16px;
        margin: 0;
        color: var(--text-primary);
    }
    
    .faq-toggle {
        font-size: 20px;
        transition: transform 0.3s;
        color: var(--text-secondary);
    }
    
    .faq-item.open .faq-toggle {
        transform: rotate(180deg);
    }
    
    .faq-answer {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
    }
    
    .faq-item.open .faq-answer {
        max-height: 500px;
    }
    
    .faq-answer-content {
        padding: 16px;
        border-top: 1px solid var(--border-color);
        color: var(--text-secondary);
    }
</style>
{% endblock %}

{% block public_content %}
<div class="faq-container">
    <div class="faq-header">
        <h1>Frequently Asked Questions</h1>
        <p>Find answers to common questions</p>
    </div>

    <div class="faq-section">
        <h2 style="margin-bottom: 20px; color: var(--text-primary);">Getting Started</h2>
        
        <div class="faq-item" onclick="toggleFAQ(this)">
            <div class="faq-question">
                <h3>How do I create an account?</h3>
                <span class="faq-toggle">▼</span>
            </div>
            <div class="faq-answer">
                <div class="faq-answer-content">
                    <p>Creating an account is simple and free. Click "Sign Up", enter your email, and verify.</p>
                </div>
            </div>
        </div>

        <!-- Add more FAQ items -->
    </div>
</div>

<script nonce="{{ request.state.csp_nonce }}">
    function toggleFAQ(element) {
        element.classList.toggle('open');
    }
</script>
{% endblock %}
```

3. **Test FAQ toggle functionality**

---

### 4. Fix cookies.html (20 minutes)

**Current Issue**: Broken CSS references

**Steps**:

1. **Find and replace** in `templates/cookies.html`:

**Find**:
```html
<link rel="stylesheet" href="/static/css/design-tokens.css') }}">
```

**Replace with**:
```html
<link rel="stylesheet" href="{{ url_for('static', path='css/design-tokens.css') }}">
```

2. **Fix all similar references**:
```html
<!-- Before -->
<link rel="stylesheet" href="/static/css/components.css') }}">
<script src="/static/js/design-system.js') }}"></script>

<!-- After -->
<link rel="stylesheet" href="{{ url_for('static', path='css/components.css') }}">
<script src="{{ url_for('static', path='js/design-system.js') }}"></script>
```

3. **Test page loads correctly**

---

### 5. Fix services.html (20 minutes)

**Steps**: Same as cookies.html

1. Find and replace broken CSS references
2. Test page loads correctly

---

## ✅ Testing Checklist

After each fix:

- [ ] Page loads without errors
- [ ] Theme toggle works (light ↔ dark)
- [ ] All content is visible
- [ ] Links work correctly
- [ ] Forms submit (if applicable)
- [ ] JavaScript works (if applicable)
- [ ] Responsive on mobile
- [ ] No console errors

---

## 🔍 Common Issues & Solutions

### Issue 1: Theme toggle not working
**Solution**: Ensure page extends correct base template

### Issue 2: Styles not applying
**Solution**: Check CSS variable names match design system

### Issue 3: JavaScript not working
**Solution**: Add CSP nonce: `nonce="{{ request.state.csp_nonce }}"`

### Issue 4: Content not visible
**Solution**: Use `var(--text-primary)` instead of hardcoded colors

---

## 🎨 CSS Variables Reference

```css
/* Backgrounds */
--bg-primary: /* white / dark */
--bg-secondary: /* light gray / darker */
--bg-card: /* white / dark card */

/* Text */
--text-primary: /* dark / light */
--text-secondary: /* gray / light gray */
--text-muted: /* light gray / dark gray */

/* Borders */
--border-color: /* light / dark */

/* Brand Colors (same in both themes) */
--primary: #6366f1
--success: #10b981
--warning: #f59e0b
--error: #ef4444
```

---

## 🚀 Deployment

```bash
# 1. Test locally
./start.sh

# 2. Commit changes
git add templates/
git commit -m "fix: dark theme consistency for legal pages"

# 3. Push to staging
git push origin fix/dark-theme-consistency

# 4. Create PR and deploy
```

---

## 📊 Success Criteria

✅ All 5 pages load without errors  
✅ Theme toggle works on all pages  
✅ No hardcoded colors (use CSS variables)  
✅ Consistent with brand design  
✅ Mobile responsive  
✅ No console errors  

---

## 🆘 Need Help?

- Check [FULL_PAGE_AUDIT_DARK_THEME.md](./FULL_PAGE_AUDIT_DARK_THEME.md) for details
- Review existing pages: `about.html`, `contact.html` for examples
- Test in both light and dark modes
- Use browser DevTools to debug CSS

---

**Ready to start? Begin with terms.html!** 🚀
