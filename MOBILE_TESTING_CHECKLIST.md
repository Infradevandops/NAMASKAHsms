# 📱 Mobile Testing Checklist

**Devices**: iPhone, Android, iPad  
**Browsers**: Safari, Chrome  
**Viewports**: 375px, 768px, 1024px

---

## 🧪 Test Scenarios

### 1. Dashboard Page
- [ ] Balance displays correctly
- [ ] Cards stack properly on mobile
- [ ] Sidebar collapses to hamburger menu
- [ ] Touch targets ≥44x44px
- [ ] No horizontal scrolling

### 2. Analytics Page
- [ ] Charts render on mobile
- [ ] Date picker works on touch
- [ ] Stats cards stack vertically
- [ ] Export button accessible
- [ ] Tables scroll horizontally

### 3. Wallet Page
- [ ] Payment buttons work
- [ ] Amount input keyboard shows numbers
- [ ] Transaction table scrolls
- [ ] Crypto QR code displays
- [ ] Modal fits screen

### 4. History Page
- [ ] Table scrolls horizontally
- [ ] Filters work on mobile
- [ ] Date picker accessible
- [ ] Export works
- [ ] Status badges visible

### 5. Notifications Page
- [ ] List scrolls smoothly
- [ ] Mark as read works
- [ ] Filter tabs accessible
- [ ] Swipe actions (optional)
- [ ] Pull to refresh (optional)

### 6. Verify Page
- [ ] Service search works
- [ ] Dropdown accessible
- [ ] Purchase button visible
- [ ] Phone number displays
- [ ] Copy button works

### 7. Settings Page
- [ ] Tabs work on mobile
- [ ] Forms usable
- [ ] Toggle switches work
- [ ] Save button accessible
- [ ] Modals fit screen

### 8. Webhooks Page
- [ ] Cards stack properly
- [ ] Create button accessible
- [ ] Forms work
- [ ] Test button works
- [ ] Delete confirmation

### 9. Referrals Page
- [ ] Referral link displays
- [ ] Copy button works
- [ ] Stats cards stack
- [ ] Table scrolls
- [ ] Share button (optional)

---

## 🔧 Testing Tools

### Browser DevTools
```javascript
// Test different viewports
// iPhone SE: 375x667
// iPhone 12: 390x844
// iPad: 768x1024
// Android: 360x640
```

### Manual Testing
1. Use real devices if available
2. Test in portrait and landscape
3. Test with different font sizes
4. Test with slow network (3G)

---

## ✅ Pass Criteria

- [ ] All pages load on mobile
- [ ] No horizontal scrolling
- [ ] Touch targets ≥44x44px
- [ ] Text readable (≥16px)
- [ ] Forms usable
- [ ] Buttons accessible
- [ ] Modals fit screen
- [ ] Tables scroll properly
- [ ] Images scale correctly
- [ ] Performance acceptable (<3s load)

---

## 📊 Results Template

| Page | iPhone | Android | iPad | Issues |
|------|--------|---------|------|--------|
| Dashboard | ⏳ | ⏳ | ⏳ | - |
| Analytics | ⏳ | ⏳ | ⏳ | - |
| Wallet | ⏳ | ⏳ | ⏳ | - |
| History | ⏳ | ⏳ | ⏳ | - |
| Notifications | ⏳ | ⏳ | ⏳ | - |
| Verify | ⏳ | ⏳ | ⏳ | - |
| Settings | ⏳ | ⏳ | ⏳ | - |
| Webhooks | ⏳ | ⏳ | ⏳ | - |
| Referrals | ⏳ | ⏳ | ⏳ | - |

---

## 🐛 Common Issues

1. **Horizontal scroll**: Check max-width, overflow
2. **Small touch targets**: Increase button size
3. **Tiny text**: Use min 16px font size
4. **Broken layout**: Test flexbox/grid
5. **Modal overflow**: Add max-height, scroll
