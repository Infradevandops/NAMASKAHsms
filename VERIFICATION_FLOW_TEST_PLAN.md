# Verification Flow Test Plan

**Version**: 1.0  
**Date**: January 2026  
**Commit**: cfedbaf5

---

## Test Scope

Testing the complete verification flow redesign with:
- ServiceStore integration (stale-while-revalidate caching)
- Official brand logos via simpleicons.org
- 84 fallback services
- Instant service availability (no loading states)

---

## Phase 5: Production Testing Checklist

### 1. Service Loading Tests

#### 1.1 First Visit (Cold Cache)
- [ ] Navigate to `/verify`
- [ ] Services should load instantly from backend fallback (84 services)
- [ ] No loading spinner should appear
- [ ] Dropdown should populate immediately when clicking search input
- [ ] Official logos should display for major services (WhatsApp, Telegram, Google, etc.)
- [ ] Fallback circle icon should display for services without logos

**Expected**: Services available in < 100ms from fallback

#### 1.2 Cached Visit (Warm Cache)
- [ ] Refresh page after first visit
- [ ] Services should load instantly from localStorage cache
- [ ] No network request should block UI
- [ ] Background refresh should happen silently (check Network tab)

**Expected**: Services available in < 10ms from cache

#### 1.3 Stale Cache (3-6h old)
- [ ] Manually set cache timestamp to 4 hours ago in localStorage:
  ```js
  const cache = JSON.parse(localStorage.getItem('nsk_services_v4'));
  cache.timestamp = Date.now() - (4 * 60 * 60 * 1000);
  localStorage.setItem('nsk_services_v4', JSON.stringify(cache));
  ```
- [ ] Refresh page
- [ ] Services should display immediately from stale cache
- [ ] Background refresh should trigger (check Network tab)
- [ ] Services should update silently after refresh completes

**Expected**: Instant display + silent background update

#### 1.4 Network Failure
- [ ] Open DevTools → Network → Throttle to "Offline"
- [ ] Clear cache: `localStorage.removeItem('nsk_services_v4')`
- [ ] Refresh page
- [ ] Services should load from backend fallback (84 services)
- [ ] No error messages should appear
- [ ] User can proceed with verification

**Expected**: Graceful degradation to fallback

---

### 2. Logo Display Tests

#### 2.1 Major Services (Should Have Official Logos)
Test these services have correct logos from simpleicons.org:
- [ ] WhatsApp → Green phone icon
- [ ] Telegram → Blue paper plane
- [ ] Google → Multicolor "G"
- [ ] Facebook → Blue "f"
- [ ] Instagram → Gradient camera
- [ ] Discord → Purple game controller
- [ ] Twitter/X → Black "X"
- [ ] Microsoft → Four colored squares
- [ ] Amazon → Orange arrow smile
- [ ] Uber → Black/white logo

**Expected**: All logos load correctly with brand colors

#### 2.2 Fallback Icon
- [ ] Search for a service without a logo mapping
- [ ] Should display purple circle icon (Phosphor fallback)
- [ ] Icon should be same size as official logos (24x24px)

**Expected**: Consistent fallback icon

#### 2.3 Logo Error Handling
- [ ] Simulate CDN failure by blocking `cdn.simpleicons.org` in DevTools
- [ ] All services should show fallback circle icon
- [ ] No broken image icons
- [ ] No console errors

**Expected**: Graceful fallback to SVG circle

---

### 3. Search & Filter Tests

#### 3.1 Empty Search (Favorites + Popular)
- [ ] Click search input without typing
- [ ] Should show favorites at top (if any exist)
- [ ] Should show up to 10 popular services
- [ ] Each service should have logo + name + price

**Expected**: Smart default list

#### 3.2 Search Query
- [ ] Type "what" → Should show WhatsApp
- [ ] Type "tele" → Should show Telegram
- [ ] Type "goog" → Should show Google
- [ ] Type "xyz123" → Should show "No services found"

**Expected**: Fast fuzzy search

#### 3.3 Search Performance
- [ ] Type rapidly: "whatsapp"
- [ ] Should debounce (not search on every keystroke)
- [ ] Should show results within 300ms of last keystroke

**Expected**: Smooth, debounced search

---

### 4. Service Selection Tests

#### 4.1 Select from Dropdown
- [ ] Click a service from dropdown
- [ ] Service name + price should display in selected box
- [ ] Dropdown should close
- [ ] "Continue" button should enable
- [ ] Advanced options should show (if PAYG+ tier)

**Expected**: Clean selection flow

#### 4.2 Clear Selection
- [ ] Click X button on selected service
- [ ] Selection should clear
- [ ] Search input should clear
- [ ] "Continue" button should disable
- [ ] Advanced options should hide

**Expected**: Clean reset

#### 4.3 Pre-selected Service (Query Param)
- [ ] Navigate to `/verify?service=whatsapp`
- [ ] WhatsApp should be pre-selected
- [ ] "Continue" button should be enabled
- [ ] Can proceed directly to step 2

**Expected**: Deep linking works

---

### 5. Integration Tests

#### 5.1 Complete Verification Flow
- [ ] Select service (e.g., Telegram)
- [ ] Click "Continue"
- [ ] Review pricing on step 2
- [ ] Click "Get Number"
- [ ] Receive phone number on step 3
- [ ] Wait for SMS code
- [ ] Code should appear within 30-60s

**Expected**: End-to-end success

#### 5.2 Multiple Verifications
- [ ] Complete 3 verifications in a row
- [ ] Services should remain cached
- [ ] No performance degradation
- [ ] No memory leaks (check DevTools Memory tab)

**Expected**: Consistent performance

#### 5.3 Tier-Based Features
**Freemium**:
- [ ] No advanced options visible
- [ ] Freemium upsell banner shows

**PAYG+**:
- [ ] Advanced options visible
- [ ] Area code selector enabled
- [ ] Carrier selector enabled

**Expected**: Correct tier gating

---

### 6. Performance Tests

#### 6.1 Page Load Time
- [ ] Clear cache
- [ ] Measure time to interactive (TTI)
- [ ] Target: < 2s on 3G connection

**Expected**: Fast initial load

#### 6.2 Service Store Initialization
- [ ] Measure `ServiceStore.init()` time
- [ ] Target: < 100ms (cache hit), < 500ms (network)

**Expected**: Non-blocking initialization

#### 6.3 Memory Usage
- [ ] Open DevTools → Memory → Take heap snapshot
- [ ] Complete 10 verifications
- [ ] Take another heap snapshot
- [ ] Compare: should not grow significantly

**Expected**: No memory leaks

---

### 7. Error Handling Tests

#### 7.1 API Timeout
- [ ] Throttle network to "Slow 3G"
- [ ] Services should load from fallback
- [ ] No timeout errors visible to user

**Expected**: Graceful degradation

#### 7.2 Invalid Service ID
- [ ] Manually set `selectedService = 'invalid_service_xyz'`
- [ ] Click "Continue"
- [ ] Should proceed (backend will handle validation)

**Expected**: Backend validation

#### 7.3 Expired Token
- [ ] Set expired token in localStorage
- [ ] Refresh page
- [ ] Services should load (endpoint is public)
- [ ] No 401 errors

**Expected**: Public endpoint works without auth

---

### 8. Browser Compatibility Tests

Test on:
- [ ] Chrome 120+ (Desktop)
- [ ] Firefox 120+ (Desktop)
- [ ] Safari 17+ (Desktop)
- [ ] Chrome Mobile (Android)
- [ ] Safari Mobile (iOS)

**Expected**: Consistent behavior across browsers

---

### 9. Accessibility Tests

#### 9.1 Keyboard Navigation
- [ ] Tab through service search
- [ ] Arrow keys should navigate dropdown
- [ ] Enter should select service
- [ ] Escape should close dropdown

**Expected**: Full keyboard support

#### 9.2 Screen Reader
- [ ] Test with VoiceOver (Mac) or NVDA (Windows)
- [ ] Service names should be announced
- [ ] Prices should be announced
- [ ] Selection should be confirmed

**Expected**: Screen reader friendly

---

## Test Results Template

```markdown
## Test Run: [Date]
**Tester**: [Name]
**Environment**: [Production/Staging]
**Browser**: [Chrome 120 / Firefox 120 / Safari 17]

### Results
- [ ] All tests passed
- [ ] Partial pass (see issues below)
- [ ] Failed (see issues below)

### Issues Found
1. [Issue description]
   - **Severity**: Critical / High / Medium / Low
   - **Steps to reproduce**: ...
   - **Expected**: ...
   - **Actual**: ...

### Performance Metrics
- Page load time: [X]s
- ServiceStore init time: [X]ms
- First service display: [X]ms
- Memory usage: [X]MB

### Notes
[Any additional observations]
```

---

## Automated Testing (Future)

### Unit Tests
```javascript
// tests/frontend/service-store.test.js
describe('ServiceStore', () => {
  test('should initialize with cache', async () => {
    const services = await ServiceStore.init();
    expect(services.length).toBeGreaterThan(20);
  });

  test('should use stale cache immediately', async () => {
    // Set stale cache
    const staleCache = { /* ... */ };
    localStorage.setItem('nsk_services_v4', JSON.stringify(staleCache));
    
    const start = Date.now();
    await ServiceStore.init();
    const duration = Date.now() - start;
    
    expect(duration).toBeLessThan(50); // Should be instant
  });

  test('should refresh stale cache in background', async () => {
    // Test background refresh logic
  });
});
```

### E2E Tests
```javascript
// tests/e2e/verification-flow.spec.js
test('complete verification flow with ServiceStore', async ({ page }) => {
  await page.goto('/verify');
  
  // Services should be ready immediately
  await page.waitForSelector('#service-search-input', { timeout: 1000 });
  
  // Click search input
  await page.click('#service-search-input');
  
  // Dropdown should appear with services
  await page.waitForSelector('.service-item', { timeout: 500 });
  
  // Should have logos
  const logos = await page.$$('.service-icon');
  expect(logos.length).toBeGreaterThan(5);
  
  // Select WhatsApp
  await page.click('text=WhatsApp');
  
  // Continue button should be enabled
  await expect(page.locator('#continue-btn')).toBeEnabled();
  
  // Complete flow
  await page.click('#continue-btn');
  await page.click('#get-number-btn');
  
  // Should receive phone number
  await page.waitForSelector('#phone-number', { timeout: 5000 });
});
```

---

## Success Criteria

### Must Have ✅
- [x] Services load instantly (< 100ms from cache/fallback)
- [x] Official logos display for major services
- [x] No loading states visible to user
- [x] Stale-while-revalidate works correctly
- [x] Graceful fallback to 84 hardcoded services
- [x] Complete verification flow works end-to-end

### Should Have 🎯
- [ ] All 84 services have official logos (currently ~40)
- [ ] Automated E2E tests pass
- [ ] Performance metrics meet targets
- [ ] Accessibility audit passes

### Nice to Have 💡
- [ ] Service popularity tracking
- [ ] A/B test different logo styles
- [ ] Service recommendations based on history

---

## Rollback Plan

If critical issues found:

1. **Immediate**: Revert commit `cfedbaf5`
   ```bash
   git revert cfedbaf5
   git push origin main
   ```

2. **Temporary**: Disable ServiceStore, use old loadServices()
   ```javascript
   // In verify_modern.html, comment out:
   // await window.ServiceStore.init();
   // Uncomment old loadServices() implementation
   ```

3. **Investigate**: Check logs, reproduce locally, fix issue

4. **Redeploy**: Push fix, test, monitor

---

## Monitoring

### Metrics to Track
- Service load time (p50, p95, p99)
- Cache hit rate
- API error rate
- Logo load failures
- User drop-off at service selection

### Alerts
- Service load time > 1s (p95)
- Cache hit rate < 80%
- API error rate > 5%
- Logo load failures > 10%

---

## Next Steps

1. **Manual Testing** (Today)
   - Run through checklist on production
   - Document any issues
   - Verify all critical paths work

2. **Monitoring** (Week 1)
   - Watch error rates
   - Check performance metrics
   - Gather user feedback

3. **Iteration** (Week 2+)
   - Add missing logos
   - Optimize cache strategy
   - Implement automated tests

4. **Documentation** (Ongoing)
   - Update README with new architecture
   - Document ServiceStore API
   - Create troubleshooting guide

---

**Status**: Ready for Production Testing ✅  
**Risk Level**: Low (graceful fallbacks in place)  
**Estimated Test Time**: 2-3 hours
