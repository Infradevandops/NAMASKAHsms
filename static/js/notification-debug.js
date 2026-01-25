/**
 * Emergency fix for notification bell not being clickable
 * Add this script to your page to debug and fix notification issues
 */

(function() {
    'use strict';
    
    console.log('🔔 Notification Debug Script Loaded');
    
    function debugNotifications() {
        // Check if notification bell exists
        const bell = document.getElementById('notification-bell');
        const bellButton = document.querySelector('.bell-button');
        const badge = document.getElementById('notification-badge');
        
        console.log('Bell element:', bell);
        console.log('Bell button:', bellButton);
        console.log('Badge element:', badge);
        
        // Check if token exists
        const token = localStorage.getItem('access_token');
        console.log('Token exists:', !!token);
        console.log('Token length:', token ? token.length : 0);
        
        // Test notification API
        if (token) {
            fetch('/api/notifications', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            .then(res => {
                console.log('Notification API status:', res.status);
                return res.json();
            })
            .then(data => {
                console.log('Notification data:', data);
                
                // Force update badge
                if (data.notifications) {
                    const unreadCount = data.notifications.filter(n => !n.is_read).length;
                    console.log('Unread count:', unreadCount);
                    
                    if (badge) {
                        if (unreadCount > 0) {
                            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                            badge.style.display = 'block';
                            console.log('✅ Badge updated');
                        } else {
                            badge.style.display = 'none';
                        }
                    }
                }
            })
            .catch(err => {
                console.error('❌ Notification API error:', err);
            });
        }
        
        // Fix click handler if missing
        if (bellButton && !bellButton.onclick) {
            console.log('🔧 Adding missing click handler');
            bellButton.onclick = function() {
                console.log('Bell clicked');
                toggleNotifications();
            };
        }
        
        // Check if toggleNotifications function exists
        if (typeof window.toggleNotifications === 'undefined') {
            console.log('🔧 Adding missing toggleNotifications function');
            window.toggleNotifications = function() {
                const dropdown = document.getElementById('notification-dropdown');
                if (dropdown) {
                    const isVisible = dropdown.style.display !== 'none';
                    dropdown.style.display = isVisible ? 'none' : 'block';
                    
                    if (!isVisible) {
                        // Load notifications when opening
                        loadNotifications();
                    }
                }
            };
        }
        
        // Check if loadNotifications function exists
        if (typeof window.loadNotifications === 'undefined') {
            console.log('🔧 Adding missing loadNotifications function');
            window.loadNotifications = async function() {
                const list = document.getElementById('notification-list');
                const token = localStorage.getItem('access_token');
                
                if (!list || !token) return;
                
                try {
                    const res = await fetch('/api/notifications', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (res.ok) {
                        const data = await res.json();
                        const notifications = data.notifications || [];
                        
                        if (notifications.length === 0) {
                            list.innerHTML = '<div class="empty-state">No notifications</div>';
                        } else {
                            list.innerHTML = notifications.map(n => `
                                <div class="notification-item ${n.is_read ? '' : 'unread'}">
                                    <div class="notification-title">${escapeHtml(n.title)}</div>
                                    <div class="notification-message">${escapeHtml(n.message || '')}</div>
                                    <div class="notification-time">${formatTime(n.created_at)}</div>
                                </div>
                            `).join('');
                        }
                    }
                } catch (error) {
                    console.error('Load notifications error:', error);
                    list.innerHTML = '<div class="empty-state">Failed to load notifications</div>';
                }
            };
        }
        
        // Helper functions
        if (typeof window.escapeHtml === 'undefined') {
            window.escapeHtml = function(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            };
        }
        
        if (typeof window.formatTime === 'undefined') {
            window.formatTime = function(timestamp) {
                if (!timestamp) return '';
                const date = new Date(timestamp);
                const now = new Date();
                const diff = Math.floor((now - date) / 1000);
                
                if (diff < 60) return 'Just now';
                if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
                if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
                if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
                return date.toLocaleDateString();
            };
        }
    }
    
    // Run debug when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', debugNotifications);
    } else {
        debugNotifications();
    }
    
    // Also run after a short delay to catch dynamically loaded content
    setTimeout(debugNotifications, 2000);
    
    console.log('🔔 Notification debug script initialized');
})();