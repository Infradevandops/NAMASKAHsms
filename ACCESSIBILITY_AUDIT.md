# ♿ Accessibility Audit & Fixes

**Target**: WCAG 2.1 Level AA Compliance  
**Goal**: Lighthouse Score > 90

---

## 🔍 Common Issues to Check

### 1. ARIA Labels
```html
<!-- ❌ Bad -->
<button onclick="submit()">Submit</button>

<!-- ✅ Good -->
<button onclick="submit()" aria-label="Submit form">Submit</button>
```

### 2. Form Labels
```html
<!-- ❌ Bad -->
<input type="email" placeholder="Email">

<!-- ✅ Good -->
<label for="email">Email</label>
<input type="email" id="email" name="email">
```

### 3. Alt Text
```html
<!-- ❌ Bad -->
<img src="logo.png">

<!-- ✅ Good -->
<img src="logo.png" alt="Namaskah Logo">
```

### 4. Color Contrast
- Text: 4.5:1 minimum
- Large text: 3:1 minimum
- Use tools: https://webaim.org/resources/contrastchecker/

### 5. Keyboard Navigation
- All interactive elements must be keyboard accessible
- Tab order should be logical
- Focus indicators must be visible

---

## 📋 Quick Fixes Checklist

### Dashboard Pages
- [ ] Add aria-label to all icon buttons
- [ ] Ensure all forms have proper labels
- [ ] Add alt text to all images
- [ ] Check color contrast ratios
- [ ] Test keyboard navigation
- [ ] Add skip navigation link
- [ ] Ensure focus indicators visible

### Specific Pages

**Analytics**:
- [ ] Chart canvas needs aria-label
- [ ] Export button needs aria-label
- [ ] Date pickers need labels

**Wallet**:
- [ ] Payment buttons need aria-labels
- [ ] Transaction table needs proper headers
- [ ] Amount inputs need labels

**History**:
- [ ] Filter dropdowns need labels
- [ ] Table needs proper th scope
- [ ] Status badges need aria-labels

**Notifications**:
- [ ] Mark as read buttons need aria-labels
- [ ] Notification items need role="listitem"
- [ ] Filter tabs need aria-selected

**Settings**:
- [ ] Tab navigation needs aria-selected
- [ ] Toggle switches need labels
- [ ] Form inputs need labels

---

## 🛠️ Run Audit

```bash
# Install dependencies
npm install -g lighthouse chrome-launcher

# Run audit
node scripts/lighthouse_audit.js

# View report
cat accessibility_report.json
```

---

## 🎯 Target Scores

| Page | Current | Target | Status |
|------|---------|--------|--------|
| Dashboard | ? | 90+ | ⏳ |
| Analytics | ? | 90+ | ⏳ |
| Wallet | ? | 90+ | ⏳ |
| History | ? | 90+ | ⏳ |
| Notifications | ? | 90+ | ⏳ |
| Verify | ? | 90+ | ⏳ |
| Settings | ? | 90+ | ⏳ |
| Webhooks | ? | 90+ | ⏳ |
| Referrals | ? | 90+ | ⏳ |

---

## 📝 Notes

Run audit first, then fix issues based on report.
