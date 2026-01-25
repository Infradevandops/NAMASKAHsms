# Phase 1 Testing Guide

**Objective**: Verify all notification fixes are working correctly  
**Time Required**: 15-20 minutes  
**Prerequisites**: Application running on localhost:9527

---

## Pre-Test Setup

1. **Start the application**:
   ```bash
   python3 main.py
   ```

2. **Open browser**:
   - Navigate to `http://localhost:9527`
   - Open DevTools: Press `F12`
   - Go to Console tab

3. **Login with admin credentials**:
   - Email: `admin@namaskah.app`
   - Password: `Namaskah@Admin2024`

---

## Test 1: Notification Bell Functionality

### Steps
1. Look at the top-right corner of the dashboard
2. Find the notification bell icon (🔔)
3. Click on it
4. Observe the dropdown menu

### Expected Results
- ✅ Dropdown appears below the bell
- ✅ Console shows: `✅ Notification bell initialized`
- ✅ Notifications list loads
- ✅ Badge shows unread count (if any)
- ✅ "Mark all read" button is visible

### If It Fails
- Check console for errors
- Verify `notification.html` was updated
- Check browser cache (Ctrl+Shift+Delete)
- Restart application

---

## Test 2: Toast Notifications

### Steps
1. Open DevTools Console
2. Type: `window.toast.success('Test notification')`
3. Press Enter
4. Observe top-right corner

### Expected Results
- ✅ Toast appears in top-right corner
- ✅ Shows "✅ Test notification"
- ✅ Disappears after 3 seconds
- ✅ No console errors

### Test Other Toast Types
```javascript
window.toast.error('Error message')
window.toast.warning('Warning message')
window.toast.info('Info message')
```

---

## Test 3: Sound Notifications

### Steps
1. Open DevTools Console
2. Type: `window.soundManager.play('sms_received')`
3. Press Enter
4. Listen for sound

### Expected Results
- ✅ Hear a notification sound
- ✅ No console errors
- ✅ Sound plays immediately

### Test Other Sounds
```javascript
window.soundManager.play('verification_created')
window.soundManager.play('deduction')
window.soundManager.play('refund')
```

---

## Test 4: Create Verification (Full Flow)

### Steps
1. Navigate to SMS Verification page
2. Select a service (e.g., WhatsApp)
3. Select area code (e.g., 479)
4. Select carrier (e.g., AT&T)
5. Click "Get Number"
6. Observe notifications

### Expected Results
- ✅ Toast appears: "🚀 Verification Started"
- ✅ Sound plays (verification_created tone)
- ✅ Toast appears: "💳 Credits Deducted"
- ✅ Sound plays (deduction tone)
- ✅ Phone number displays
- ✅ Notification bell badge updates
- ✅ No console errors

### Check Notification Bell
1. Click notification bell
2. Should see 2 new notifications:
   - "🚀 Verification Started"
   - "💳 Credits Deducted"

---

## Test 5: SMS Code Reception (Simulated)

### Steps
1. In DevTools Console, type:
   ```javascript
   window.dispatchEvent(new CustomEvent('notification:new', {
       detail: {
           type: 'sms_received',
           title: '✅ SMS Code Received!'
       }
   }));
   ```
2. Press Enter

### Expected Results
- ✅ Toast appears: "✅ SMS Code Received!"
- ✅ Sound plays (sms_received tone)
- ✅ No console errors

---

## Test 6: Notification Bell Dropdown

### Steps
1. Click notification bell
2. Observe dropdown
3. Click "Mark all read"
4. Observe badge disappears
5. Click bell again
6. Observe dropdown closes

### Expected Results
- ✅ Dropdown opens/closes on click
- ✅ Notifications display correctly
- ✅ "Mark all read" button works
- ✅ Badge updates correctly
- ✅ Outside click closes dropdown

---

## Test 7: Mobile Responsiveness

### Steps
1. Open DevTools
2. Click device toggle (Ctrl+Shift+M)
3. Select iPhone 12
4. Refresh page
5. Click notification bell
6. Try to interact with dropdown

### Expected Results
- ✅ Notification bell is visible
- ✅ Dropdown appears
- ✅ Dropdown is readable on mobile
- ✅ Touch interactions work
- ✅ No layout issues

---

## Test 8: Console Logging

### Steps
1. Open DevTools Console
2. Look for initialization messages
3. Create a verification
4. Look for notification dispatch messages

### Expected Results
- ✅ See: `✅ Notification bell initialized`
- ✅ See: `✅ Toast notification system loaded`
- ✅ See: `✅ Notification sounds initialized`
- ✅ See: `✅ Loaded X notifications`
- ✅ See: `🔊 Playing sound: ...`
- ✅ No error messages

---

## Test 9: Error Handling

### Steps
1. Open DevTools Console
2. Simulate network error:
   ```javascript
   // Temporarily break the API
   localStorage.removeItem('access_token');
   window.refreshNotifications();
   ```
3. Observe error handling

### Expected Results
- ✅ Console shows: `⚠️ No auth token`
- ✅ Notification list shows: "Please log in"
- ✅ No crash or unhandled errors
- ✅ Application remains functional

---

## Test 10: Notification Persistence

### Steps
1. Create a verification
2. Note the notifications
3. Refresh the page
4. Click notification bell
5. Verify notifications are still there

### Expected Results
- ✅ Notifications persist after refresh
- ✅ Unread count is correct
- ✅ Notification content is accurate
- ✅ No data loss

---

## Troubleshooting

### Issue: Notification bell doesn't respond
**Solution**:
1. Check console for errors
2. Verify `notification.html` was updated
3. Clear browser cache (Ctrl+Shift+Delete)
4. Restart application
5. Hard refresh (Ctrl+Shift+R)

### Issue: Toast doesn't appear
**Solution**:
1. Check console for errors
2. Verify `toast-notifications.js` is loaded
3. Check if `window.toast` exists in console
4. Verify CSS is not hidden

### Issue: Sound doesn't play
**Solution**:
1. Check browser volume
2. Check if sound is enabled in browser
3. Verify `soundManager` exists in console
4. Try different sound types

### Issue: Notifications don't load
**Solution**:
1. Check if user is logged in
2. Verify API endpoint is working
3. Check network tab in DevTools
4. Verify token is valid

---

## Performance Checks

### Check Notification Loading Time
1. Open DevTools Network tab
2. Click notification bell
3. Look for `/api/notifications` request
4. Check response time

**Expected**: < 500ms

### Check Toast Animation
1. Open DevTools Performance tab
2. Create a verification
3. Observe toast animation
4. Check for jank or stuttering

**Expected**: Smooth 60fps animation

### Check Sound Playback
1. Open DevTools Console
2. Play a sound
3. Check for any delays

**Expected**: Instant playback

---

## Sign-Off Checklist

After completing all tests, verify:

- [ ] Notification bell is clickable
- [ ] Dropdown shows notifications
- [ ] Toast notifications appear
- [ ] Sounds play correctly
- [ ] Verification creation triggers notifications
- [ ] SMS received triggers notifications
- [ ] Credit deduction triggers notifications
- [ ] Mobile experience is good
- [ ] No console errors
- [ ] Performance is acceptable
- [ ] All features work as expected

---

## Reporting Issues

If you find any issues:

1. **Document the issue**:
   - What were you doing?
   - What happened?
   - What should have happened?

2. **Collect evidence**:
   - Screenshot
   - Console errors
   - Network requests
   - Browser/OS info

3. **Report to development team**:
   - Include all documentation
   - Include evidence
   - Include steps to reproduce

---

## Next Steps

After successful testing:

1. ✅ Mark Phase 1 as complete
2. ✅ Proceed to Phase 2: UI Improvements
3. ✅ Implement progress indicators
4. ✅ Unify verification UI design

---

**Testing Date**: January 25, 2026  
**Estimated Time**: 15-20 minutes  
**Difficulty**: Easy  
**Status**: Ready to test
