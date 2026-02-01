/**
 * ENHANCED NOTIFICATION SYSTEM
 * Industry-standard notification management with real-time alerts
 */

class NotificationSystem {
    constructor() {
        this.isInitialized = false;
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.toastQueue = [];
        this.activeToasts = new Set();
        this.maxToasts = 5;
        this.unreadCount = 0;
        
        this.init();
    }

    async init() {
        if (this.isInitialized) return;
        
        console.log('🔔 Initializing Enhanced Notification System...');
        
        // Create toast container
        this.createToastContainer();
        
        // Initialize header notification bell
        this.initializeHeaderBell();
        
        // Load initial notifications
        await this.loadNotifications();
        
        // Initialize WebSocket for real-time notifications
        this.initializeWebSocket();
        
        // Set up periodic refresh
        this.startPeriodicRefresh();
        
        this.isInitialized = true;
        console.log('✅ Enhanced Notification System initialized');
    }

    createToastContainer() {
        if (document.getElementById('toast-container')) return;
        
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-label', 'Notifications');
        document.body.appendChild(container);
    }

    initializeHeaderBell() {
        const bellBtn = document.querySelector('.notification-bell-btn');
        const dropdown = document.querySelector('.notification-dropdown');
        
        if (!bellBtn) {
            console.warn('⚠️ Notification bell button not found');
            return;
        }

        // Enhanced click handler
        bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleNotificationDropdown();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (dropdown && !bellBtn.contains(e.target) && !dropdown.contains(e.target)) {
                this.closeNotificationDropdown();
            }
        });

        // Keyboard navigation
        bellBtn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleNotificationDropdown();
            }
        });

        console.log('✅ Header notification bell initialized');
    }

    async loadNotifications() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.warn('⚠️ No auth token available');
                return;
            }

            // Fetch notifications and unread count in parallel
            const [notificationsResponse, countResponse] = await Promise.all([
                fetch('/api/notifications', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache'
                    }
                }),
                fetch('/api/notifications/unread-count', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Cache-Control': 'no-cache'
                    }
                })
            ]);

            if (!notificationsResponse.ok || !countResponse.ok) {
                throw new Error(`API error: ${notificationsResponse.status} / ${countResponse.status}`);
            }

            const notificationsData = await notificationsResponse.json();
            const countData = await countResponse.json();
            
            const notifications = notificationsData.notifications || [];
            
            // Use backend count as source of truth
            this.unreadCount = countData.count || 0;
            this.updateNotificationBadge();
            
            // Update dropdown content
            this.updateNotificationDropdown(notifications);
            
            console.log(`✅ Loaded ${notifications.length} notifications (${this.unreadCount} unread)`);
            
        } catch (error) {
            console.error('❌ Failed to load notifications:', error);
        }
    }

    updateNotificationBadge() {
        // Update header badge
        const headerBadge = document.getElementById('notification-bell-badge');
        if (headerBadge) {
            if (this.unreadCount > 0) {
                headerBadge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                headerBadge.classList.add('show');
            } else {
                headerBadge.classList.remove('show');
            }
        }

        // Update sidebar badge
        const sidebarBadge = document.getElementById('sidebar-notif-badge');
        if (sidebarBadge) {
            if (this.unreadCount > 0) {
                sidebarBadge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                sidebarBadge.classList.add('show');
            } else {
                sidebarBadge.classList.remove('show');
            }
        }

        // Add bell shake animation for new notifications
        const bellBtn = document.querySelector('.notification-bell-btn');
        if (bellBtn && this.unreadCount > 0) {
            bellBtn.classList.add('has-new');
            setTimeout(() => bellBtn.classList.remove('has-new'), 500);
        }
    }

    updateNotificationDropdown(notifications) {
        const list = document.getElementById('notification-list');
        if (!list) return;

        if (notifications.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔔</div>
                    <div class="empty-state-title">No notifications</div>
                    <div class="empty-state-message">You're all caught up!</div>
                </div>
            `;
            return;
        }

        list.innerHTML = notifications.map(notification => `
            <div class="notification-item ${notification.is_read ? '' : 'unread'}" 
                 onclick="notificationSystem.markAsRead('${notification.id}', '${notification.link || ''}')"
                 tabindex="0"
                 role="button"
                 aria-label="Notification: ${this.escapeHtml(notification.title)}">
                <div class="notification-item-icon">
                    ${this.getNotificationIcon(notification.type)}
                </div>
                <div class="notification-item-content">
                    <div class="notification-title">${this.escapeHtml(notification.title)}</div>
                    <div class="notification-message">${this.escapeHtml(notification.message || '')}</div>
                    <div class="notification-time">${this.formatTime(notification.created_at)}</div>
                </div>
            </div>
        `).join('');
    }

    getNotificationIcon(type) {
        const icons = {
            'verification_initiated': '🚀',
            'sms_received': '✅',
            'verification_complete': '✅',
            'verification_failed': '❌',
            'credit_deducted': '💳',
            'refund_issued': '💰',
            'balance_low': '⚠️',
            'verification_progress': '⏳',
            'payment_success': '💳',
            'payment_failed': '❌',
            'account_update': '👤',
            'system_alert': '🔔',
            'default': '📢'
        };
        return icons[type] || icons.default;
    }

    toggleNotificationDropdown() {
        const dropdown = document.querySelector('.notification-dropdown');
        if (!dropdown) return;

        const isVisible = dropdown.classList.contains('show');
        
        if (isVisible) {
            this.closeNotificationDropdown();
        } else {
            this.openNotificationDropdown();
        }
    }

    openNotificationDropdown() {
        const dropdown = document.querySelector('.notification-dropdown');
        if (!dropdown) return;

        dropdown.classList.add('show');
        
        // Load fresh notifications when opening
        this.loadNotifications();
        
        // Focus management
        const firstItem = dropdown.querySelector('.notification-item');
        if (firstItem) {
            firstItem.focus();
        }
    }

    closeNotificationDropdown() {
        const dropdown = document.querySelector('.notification-dropdown');
        if (!dropdown) return;

        dropdown.classList.remove('show');
    }

    async markAsRead(notificationId, link = '') {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            // Reload notifications to update UI
            await this.loadNotifications();

            // Navigate to link if provided
            if (link && link !== 'undefined' && link !== 'null') {
                window.location.href = link;
            }

        } catch (error) {
            console.error('❌ Failed to mark notification as read:', error);
        }
    }

    async markAllAsRead() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            await fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            // Reload notifications to update UI
            await this.loadNotifications();

        } catch (error) {
            console.error('❌ Failed to mark all notifications as read:', error);
        }
    }

    // ==================== TOAST NOTIFICATIONS ==================== //

    showToast(notification) {
        // Prevent duplicate toasts
        if (this.activeToasts.has(notification.id)) return;

        // Limit number of active toasts
        if (this.activeToasts.size >= this.maxToasts) {
            this.dismissOldestToast();
        }

        const toast = this.createToastElement(notification);
        const container = document.getElementById('toast-container');
        
        if (!container) return;

        container.appendChild(toast);
        this.activeToasts.add(notification.id);

        // Show toast with animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            this.dismissToast(toast, notification.id);
        }, 5000);

        // Play notification sound (optional)
        this.playNotificationSound();
    }

    createToastElement(notification) {
        const toast = document.createElement('div');
        toast.className = `toast-notification ${this.getToastType(notification.type)}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');

        toast.innerHTML = `
            <div class="toast-icon">${this.getNotificationIcon(notification.type)}</div>
            <div class="toast-content">
                <div class="toast-title">${this.escapeHtml(notification.title)}</div>
                <div class="toast-message">${this.escapeHtml(notification.message || '')}</div>
                <div class="toast-time">Just now</div>
            </div>
            <button class="toast-close" onclick="notificationSystem.dismissToast(this.parentElement, '${notification.id}')" 
                    aria-label="Close notification">
                ✕
            </button>
            <div class="toast-progress">
                <div class="toast-progress-bar"></div>
            </div>
        `;

        // Click to navigate
        if (notification.link) {
            toast.style.cursor = 'pointer';
            toast.addEventListener('click', (e) => {
                if (!e.target.classList.contains('toast-close')) {
                    window.location.href = notification.link;
                    this.dismissToast(toast, notification.id);
                }
            });
        }

        return toast;
    }

    getToastType(notificationType) {
        const typeMap = {
            'verification_complete': 'success',
            'sms_received': 'success',
            'refund_issued': 'success',
            'payment_success': 'success',
            'verification_failed': 'error',
            'payment_failed': 'error',
            'balance_low': 'warning',
            'verification_progress': 'info',
            'verification_initiated': 'info',
            'credit_deducted': 'info',
            'account_update': 'info',
            'system_alert': 'warning'
        };
        return typeMap[notificationType] || 'info';
    }

    dismissToast(toastElement, notificationId) {
        if (!toastElement || !toastElement.parentElement) return;

        toastElement.classList.add('hide');
        this.activeToasts.delete(notificationId);

        setTimeout(() => {
            if (toastElement.parentElement) {
                toastElement.parentElement.removeChild(toastElement);
            }
        }, 300);
    }

    dismissOldestToast() {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const oldestToast = container.firstElementChild;
        if (oldestToast) {
            const notificationId = Array.from(this.activeToasts)[0];
            this.dismissToast(oldestToast, notificationId);
        }
    }

    playNotificationSound() {
        // Optional: Play a subtle notification sound
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
            audio.volume = 0.1;
            audio.play().catch(() => {}); // Ignore errors if audio fails
        } catch (error) {
            // Ignore audio errors
        }
    }

    // ==================== WEBSOCKET INTEGRATION ==================== //

    initializeWebSocket() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.warn('⚠️ No auth token for WebSocket connection');
            return;
        }

        // Get user ID from token (simplified)
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const userId = payload.user_id;
            
            if (!userId) {
                console.warn('⚠️ No user ID in token');
                return;
            }

            this.connectWebSocket(userId);
        } catch (error) {
            console.error('❌ Failed to parse token for WebSocket:', error);
        }
    }

    connectWebSocket(userId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/${userId}`;

        try {
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('✅ WebSocket connected for real-time notifications');
                this.reconnectAttempts = 0;
                
                // Subscribe to notifications channel
                this.websocket.send(JSON.stringify({
                    type: 'subscribe',
                    channel: 'notifications'
                }));
            };

            this.websocket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('❌ Failed to parse WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.websocket = null;
                this.scheduleReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };

        } catch (error) {
            console.error('❌ Failed to create WebSocket connection:', error);
        }
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'notification':
                // New notification received
                this.handleNewNotification(message.data);
                break;
            case 'subscribed':
                console.log(`✅ Subscribed to ${message.channel} channel`);
                break;
            case 'pong':
                // Keep-alive response
                break;
            default:
                console.log('📨 WebSocket message:', message);
        }
    }

    handleNewNotification(notification) {
        console.log('🔔 New notification received:', notification);
        
        // Show toast notification
        this.showToast(notification);
        
        // Update unread count
        this.unreadCount++;
        this.updateNotificationBadge();
        
        // Reload notifications if dropdown is open
        const dropdown = document.querySelector('.notification-dropdown');
        if (dropdown && dropdown.classList.contains('show')) {
            this.loadNotifications();
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Max WebSocket reconnection attempts reached');
            return;
        }

        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        console.log(`🔄 Scheduling WebSocket reconnection in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
        
        setTimeout(() => {
            this.reconnectAttempts++;
            this.initializeWebSocket();
        }, delay);
    }

    // ==================== UTILITY METHODS ==================== //

    startPeriodicRefresh() {
        // Refresh notifications every 30 seconds
        setInterval(() => {
            if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                this.loadNotifications();
            }
        }, 30000);
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ==================== PUBLIC API ==================== //

    // Expose methods for global access
    refresh() {
        return this.loadNotifications();
    }

    showCustomToast(title, message, type = 'info', link = null) {
        const notification = {
            id: `custom_${Date.now()}`,
            title,
            message,
            type,
            link,
            created_at: new Date().toISOString()
        };
        this.showToast(notification);
    }

    getUnreadCount() {
        return this.unreadCount;
    }

    isConnected() {
        return this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }
}

// Initialize the notification system
let notificationSystem;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        notificationSystem = new NotificationSystem();
    });
} else {
    notificationSystem = new NotificationSystem();
}

// Expose globally for backward compatibility
window.notificationSystem = notificationSystem;
window.toggleNotifications = () => notificationSystem?.toggleNotificationDropdown();
window.markAsRead = (id, link) => notificationSystem?.markAsRead(id, link);
window.markAllRead = () => notificationSystem?.markAllAsRead();
window.refreshNotifications = () => notificationSystem?.refresh();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}