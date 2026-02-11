# DevTools Automated Test Guide

**Quick guide to run automated dashboard tests in browser console**

---

## 🚀 Quick Start (30 seconds)

1. **Open any dashboard page** (e.g., https://namaskah.app/dashboard)
2. **Press F12** (or Cmd+Option+I on Mac)
3. **Click "Console" tab**
4. **Paste this command**:
```javascript
fetch('/static/js/dashboard-test-suite.js').then(r=>r.text()).then(eval)
```
5. **Press Enter**
6. **Read results** ✅ or ❌

---

## 📋 What Gets Tested

### ✅ Automatic Checks (50+)
- Sidebar items (17 links)
- Settings tabs (7 tabs)
- Wallet buttons (14 buttons)
- Verify page elements
- Global features (error handler, WebSocket, pagination)
- Tier-gated features visibility
- Mobile responsiveness
- Accessibility attributes

---

## 🎯 Step-by-Step Instructions

### Method 1: Load from Server (Recommended)
```javascript
// Copy and paste this into Console:
fetch('/static/js/dashboard-test-suite.js')
  .then(response => response.text())
  .then(code => eval(code));
```

### Method 2: Direct Paste
1. Open `/static/js/dashboard-test-suite.js` in your editor
2. Copy entire file contents
3. Paste into Console
4. Press Enter

---

## 📊 Reading Results

### Success Output
```
✅ SIDEBAR TESTS: 17/17 passed
✅ SETTINGS TESTS: 7/7 passed
✅ WALLET TESTS: 14/14 passed
✅ VERIFY TESTS: 8/8 passed
✅ GLOBAL TESTS: 5/5 passed

🎉 ALL TESTS PASSED: 51/51
```

### Failure Output
```
❌ SIDEBAR TESTS: 16/17 passed
  ❌ Dashboard link not found

✅ SETTINGS TESTS: 7/7 passed
❌ WALLET TESTS: 13/14 passed
  ❌ $10 button not found

⚠️ TESTS FAILED: 48/51
```

---

## 🔍 Testing Different Pages

### Dashboard Page
```javascript
// Navigate to /dashboard first, then run:
fetch('/static/js/dashboard-test-suite.js').then(r=>r.text()).then(eval)
```

### Settings Page
```javascript
// Navigate to /settings first, then run:
fetch('/static/js/dashboard-test-suite.js').then(r=>r.text()).then(eval)
```

### Wallet Page
```javascript
// Navigate to /wallet first, then run:
fetch('/static/js/dashboard-test-suite.js').then(r=>r.text()).then(eval)
```

### Verify Page
```javascript
// Navigate to /verify first, then run:
fetch('/static/js/dashboard-test-suite.js').then(r=>r.text()).then(eval)
```

---

## 🐛 Debugging Failed Tests

### Check Specific Element
```javascript
// Example: Check if button exists
document.querySelector('[data-amount="10"]')
// Should return: <button...> or null
```

### Check Function Exists
```javascript
// Example: Check if function is global
typeof window.switchTab
// Should return: "function" or "undefined"
```

### Check Event Listener
```javascript
// Example: Check onclick attribute
document.querySelector('#accountTab').onclick
// Should return: function or null
```

---

## 📱 Mobile Testing

### Enable Mobile View
1. Press F12 (DevTools)
2. Click device icon (Ctrl+Shift+M)
3. Select device (iPhone, iPad, etc.)
4. Run test suite
5. Check mobile-specific tests

### Mobile-Specific Checks
```javascript
// Check if mobile menu exists
document.querySelector('.mobile-menu-toggle')

// Check if tables convert to cards
window.innerWidth < 768 && document.querySelector('.card-view')
```

---

## ⚡ Quick Commands

### Run All Tests
```javascript
fetch('/static/js/dashboard-test-suite.js').then(r=>r.text()).then(eval)
```

### Check Sidebar Only
```javascript
console.log('Sidebar items:', document.querySelectorAll('.sidebar-item').length);
```

### Check Settings Tabs Only
```javascript
console.log('Settings tabs:', document.querySelectorAll('.settings-tab').length);
```

### Check Wallet Buttons Only
```javascript
console.log('Payment buttons:', document.querySelectorAll('[data-amount]').length);
```

---

## 🎨 Console Tips

### Clear Console
```javascript
clear()
```

### Filter Messages
- Click "Filter" icon
- Type "TESTS" to see only test results
- Type "❌" to see only failures

### Copy Results
- Right-click on output
- Select "Copy object"
- Paste into bug report

---

## 🔧 Troubleshooting

### Test File Not Loading
```javascript
// Check if file exists:
fetch('/static/js/dashboard-test-suite.js')
  .then(r => console.log('Status:', r.status))
// Should show: Status: 200
```

### CORS Error
- Must run on same domain (namaskah.app)
- Cannot run from file:// protocol
- Use local server for development

### Script Blocked
- Check Content Security Policy
- Ensure JavaScript enabled
- Disable ad blockers temporarily

---

## 📈 Best Practices

### Before Testing
1. ✅ Clear browser cache (Ctrl+Shift+Delete)
2. ✅ Disable browser extensions
3. ✅ Use incognito/private mode
4. ✅ Check internet connection

### During Testing
1. ✅ Test one page at a time
2. ✅ Wait for page to fully load
3. ✅ Don't interact while tests run
4. ✅ Take screenshots of failures

### After Testing
1. ✅ Document all failures
2. ✅ Test on different browsers
3. ✅ Test on mobile devices
4. ✅ Report issues with details

---

## 📝 Reporting Issues

### Include This Info
```
Browser: Chrome 120
OS: macOS 14
Page: /settings
Test: Settings tabs
Error: "switchTab is not defined"
Screenshot: [attach]
```

### Template
```markdown
**Page**: /wallet
**Test Failed**: $10 button not found
**Expected**: Button with data-amount="10"
**Actual**: Element not found
**Console Error**: None
**Screenshot**: [attach]
```

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `F12` | Open DevTools |
| `Ctrl+Shift+M` | Toggle mobile view |
| `Ctrl+L` | Clear console |
| `Ctrl+F` | Find in console |
| `↑` | Previous command |
| `Tab` | Autocomplete |

---

## ✅ Checklist

Before reporting "tests pass":
- [ ] Ran on /dashboard
- [ ] Ran on /settings
- [ ] Ran on /wallet
- [ ] Ran on /verify
- [ ] Tested on desktop
- [ ] Tested on mobile view
- [ ] Tested on Chrome
- [ ] Tested on Firefox
- [ ] All tests show ✅
- [ ] No console errors

---

**Time Required**: 5-10 minutes per page  
**Total Time**: 30-40 minutes for full test  
**Recommended**: Run after every deployment

