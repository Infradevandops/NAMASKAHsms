/**
 * Notification Sound Integration
 * Automatically plays sounds when notifications arrive
 */

(function() {
    'use strict';
    
    // Wait for soundManager to be available
    function initNotificationSounds() {
        if (typeof window.soundManager === 'undefined') {
            console.log('Sound manager not loaded');
            return;
        }
        
        // Sound mapping for notification types
        const soundMap = {
            'credit_deducted': 'deduction',
            'verification_created': 'verification_created',
            'sms_received': 'sms_received',
            'instant_refund': 'refund',
            'credit_added': 'refund' // Use same sound as refund
        };
        
        // Hook into notification display
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            return originalFetch.apply(this, args).then(response => {
                // Check if this is a notification endpoint
                if (args[0] && args[0].includes('/api/notifications')) {
                    response.clone().json().then(data => {
                        if (Array.isArray(data) && data.length > 0) {
                            // Play sound for newest unread notification
                            const newest = data.find(n => !n.is_read);
                            if (newest && soundMap[newest.type]) {
                                window.soundManager.play(soundMap[newest.type]);
                            }
                        }
                    }).catch(() => {});
                }
                return response;
            });
        };
        
        // Listen for custom notification events
        window.addEventListener('notification:new', (event) => {
            if (event.detail && event.detail.type) {
                const soundType = soundMap[event.detail.type] || event.detail.type;
                window.soundManager.play(soundType);
            }
        });
        
        console.log('Notification sounds initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNotificationSounds);
    } else {
        initNotificationSounds();
    }
})();
