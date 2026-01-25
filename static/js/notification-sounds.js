/**
 * Notification Sound Integration
 * Automatically plays sounds when notifications arrive
 */

(function() {
    'use strict';
    
    // Wait for soundManager to be available
    function initNotificationSounds() {
        if (typeof window.soundManager === 'undefined') {
            console.log('⚠️ Sound manager not loaded');
            return;
        }
        
        console.log('✅ Notification sounds initialized');
        
        // Sound mapping for notification types
        const soundMap = {
            'credit_deducted': 'deduction',
            'verification_initiated': 'verification_created',
            'verification_complete': 'sms_received',
            'sms_received': 'sms_received',
            'instant_refund': 'refund',
            'refund_issued': 'refund',
            'credit_added': 'refund',
            'verification_failed': 'deduction',
            'balance_low': 'warning'
        };
        
        // Listen for custom notification events
        window.addEventListener('notification:new', (event) => {
            if (event.detail && event.detail.type) {
                const soundType = soundMap[event.detail.type] || event.detail.type;
                console.log(`🔊 Playing sound: ${soundType}`);
                window.soundManager.play(soundType);
            }
        });
        
        // Hook into notification loading
        const originalLoadNotifications = window.refreshNotifications;
        if (originalLoadNotifications) {
            window.refreshNotifications = async function() {
                const result = await originalLoadNotifications.call(this);
                
                // Check for new unread notifications and play sound
                try {
                    const token = localStorage.getItem('access_token');
                    if (token) {
                        const res = await fetch('/api/notifications?unread_only=true', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        if (res.ok) {
                            const data = await res.json();
                            const notifications = data.notifications || [];
                            if (notifications.length > 0) {
                                const newest = notifications[0];
                                const soundType = soundMap[newest.type] || newest.type;
                                console.log(`🔊 Playing sound for: ${newest.type}`);
                                window.soundManager.play(soundType);
                                
                                // Show toast
                                if (window.toast) {
                                    window.toast.show(newest.title, 'info', 3000);
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.error('Error checking for new notifications:', e);
                }
                
                return result;
            };
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNotificationSounds);
    } else {
        initNotificationSounds();
    }
})();
