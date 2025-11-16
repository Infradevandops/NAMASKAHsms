/**
 * Receipt and Notification Management
 * Handles verification receipts and in-app notifications
 */

class ReceiptManager {
    constructor() {
        this.receipts = [];
        this.notifications = [];
        this.unreadCount = 0;
        this.init();
    }

    init() {
        this.loadReceipts();
        this.loadNotifications();
        this.setupEventListeners();
        this.startNotificationPolling();
    }

    setupEventListeners() {
        // Receipt modal events
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-receipt-id]')) {
                this.showReceiptDetails(e.target.dataset.receiptId);
            }
            
            if (e.target.matches('.notification-item')) {
                this.markNotificationRead(e.target.dataset.notificationId);
            }
            
            if (e.target.matches('#mark-all-read')) {
                this.markAllNotificationsRead();
            }
        });

        // Settings modal events
        document.addEventListener('change', (e) => {
            if (e.target.matches('[data-notification-setting]')) {
                this.updateNotificationSettings();
            }
        });
    }

    async loadReceipts() {
        try {
            const response = await fetch('/receipts/history', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.receipts = data.receipts;
                this.displayReceipts();
            }
        } catch (error) {
            console.error('Failed to load receipts:', error);
        }
    }

    async loadNotifications() {
        try {
            const response = await fetch('/notifications/list', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.notifications = data.notifications;
                this.unreadCount = data.unread_count;
                this.displayNotifications();
                this.updateNotificationBadge();
            }
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }

    displayReceipts() {
        const container = document.getElementById('receipts-list');
        if (!container) return;

        if (this.receipts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📧</div>
                    <h3>No Receipts Yet</h3>
                    <p>Your verification receipts will appear here after successful verifications.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.receipts.map(receipt => `
            <div class="receipt-item" data-receipt-id="${receipt.id}">
                <div class="receipt-header">
                    <div class="receipt-service">
                        <span class="service-icon">${this.getServiceIcon(receipt.service_name)}</span>
                        <span class="service-name">${receipt.service_name}</span>
                    </div>
                    <div class="receipt-amount">N${receipt.amount_spent.toFixed(2)}</div>
                </div>
                <div class="receipt-details">
                    <div class="receipt-number">Receipt #${receipt.receipt_number}</div>
                    <div class="receipt-phone">${receipt.phone_number}</div>
                    <div class="receipt-date">${this.formatDate(receipt.success_timestamp)}</div>
                </div>
                <div class="receipt-actions">
                    <button class="btn-secondary" data-receipt-id="${receipt.id}">View Details</button>
                </div>
            </div>
        `).join('');
    }

    displayNotifications() {
        const container = document.getElementById('notifications-list');
        if (!container) return;

        if (this.notifications.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔔</div>
                    <h3>No Notifications</h3>
                    <p>Your notifications will appear here.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.notifications.map(notification => `
            <div class="notification-item ${notification.is_read ? 'read' : 'unread'}" 
                 data-notification-id="${notification.id}">
                <div class="notification-icon">${this.getNotificationIcon(notification.type)}</div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${this.formatDate(notification.created_at)}</div>
                </div>
                ${!notification.is_read ? '<div class="unread-indicator"></div>' : ''}
            </div>
        `).join('');
    }

    updateNotificationBadge() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    async showReceiptDetails(receiptId) {
        try {
            const response = await fetch(`/receipts/${receiptId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (response.ok) {
                const receipt = await response.json();
                this.displayReceiptModal(receipt);
            }
        } catch (error) {
            console.error('Failed to load receipt details:', error);
            showNotification('Failed to load receipt details', 'error');
        }
    }

    displayReceiptModal(receipt) {
        const modal = document.createElement('div');
        modal.className = 'modal receipt-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>📧 Verification Receipt</h2>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="receipt-details-card">
                        <div class="receipt-header-info">
                            <div class="receipt-number-large">Receipt #${receipt.receipt_number}</div>
                            <div class="receipt-status">✅ Completed Successfully</div>
                        </div>
                        
                        <div class="receipt-info-grid">
                            <div class="info-item">
                                <label>Service Used</label>
                                <value>${receipt.service_name}</value>
                            </div>
                            <div class="info-item">
                                <label>Phone Number</label>
                                <value>${receipt.phone_number}</value>
                            </div>
                            <div class="info-item">
                                <label>ISP/Carrier</label>
                                <value>${receipt.isp_carrier || 'Unknown'}</value>
                            </div>
                            <div class="info-item">
                                <label>Area Code</label>
                                <value>${receipt.area_code || 'Unknown'}</value>
                            </div>
                            <div class="info-item">
                                <label>Amount Charged</label>
                                <value>N${receipt.amount_spent.toFixed(2)} ($${receipt.amount_usd.toFixed(2)} USD)</value>
                            </div>
                            <div class="info-item">
                                <label>Completed At</label>
                                <value>${this.formatFullDate(receipt.success_timestamp)}</value>
                            </div>
                        </div>
                        
                        <div class="receipt-actions">
                            <button class="btn-primary" onclick="window.print()">🖨️ Print Receipt</button>
                            <button class="btn-secondary" onclick="receiptManager.downloadReceipt('${receipt.id}')">📥 Download</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'flex';

        // Close modal events
        modal.querySelector('.close-modal').onclick = () => {
            document.body.removeChild(modal);
        };
        
        modal.onclick = (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        };
    }

    async markNotificationRead(notificationId) {
        try {
            const response = await fetch(`/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (response.ok) {
                // Update local state
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification && !notification.is_read) {
                    notification.is_read = true;
                    this.unreadCount--;
                    this.updateNotificationBadge();
                    this.displayNotifications();
                }
            }
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }

    async markAllNotificationsRead() {
        try {
            const response = await fetch('/notifications/mark-all-read', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (response.ok) {
                this.notifications.forEach(n => n.is_read = true);
                this.unreadCount = 0;
                this.updateNotificationBadge();
                this.displayNotifications();
                showNotification('All notifications marked as read', 'success');
            }
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    }

    async loadNotificationSettings() {
        try {
            const response = await fetch('/notifications/settings', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (response.ok) {
                const settings = await response.json();
                this.displayNotificationSettings(settings);
            }
        } catch (error) {
            console.error('Failed to load notification settings:', error);
        }
    }

    displayNotificationSettings(settings) {
        const container = document.getElementById('notification-settings');
        if (!container) return;

        container.innerHTML = `
            <div class="settings-section">
                <h3>📱 In-App Notifications</h3>
                <div class="setting-item">
                    <label class="switch">
                        <input type="checkbox" data-notification-setting="in_app_notifications" 
                               ${settings.in_app_notifications ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                    <div class="setting-info">
                        <div class="setting-title">Enable In-App Notifications</div>
                        <div class="setting-description">Show notifications within the app</div>
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h3>📧 Email Notifications</h3>
                <div class="setting-item">
                    <label class="switch">
                        <input type="checkbox" data-notification-setting="email_notifications" 
                               ${settings.email_notifications ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                    <div class="setting-info">
                        <div class="setting-title">Enable Email Notifications</div>
                        <div class="setting-description">Send notifications to your email</div>
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h3>🧾 Receipt Notifications</h3>
                <div class="setting-item">
                    <label class="switch">
                        <input type="checkbox" data-notification-setting="receipt_notifications" 
                               ${settings.receipt_notifications ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                    <div class="setting-info">
                        <div class="setting-title">Send Verification Receipts</div>
                        <div class="setting-description">Receive receipts for successful verifications</div>
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h3>⚙️ Legacy Settings</h3>
                <div class="setting-item">
                    <label class="switch">
                        <input type="checkbox" data-notification-setting="email_on_sms" 
                               ${settings.email_on_sms ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                    <div class="setting-info">
                        <div class="setting-title">Email on SMS Received</div>
                        <div class="setting-description">Legacy SMS notification setting</div>
                    </div>
                </div>
                
                <div class="setting-item">
                    <label class="switch">
                        <input type="checkbox" data-notification-setting="email_on_low_balance" 
                               ${settings.email_on_low_balance ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                    <div class="setting-info">
                        <div class="setting-title">Low Balance Alerts</div>
                        <div class="setting-description">Email when balance is low</div>
                    </div>
                </div>
            </div>
        `;
    }

    async updateNotificationSettings() {
        const settings = {};
        
        document.querySelectorAll('[data-notification-setting]').forEach(input => {
            settings[input.dataset.notificationSetting] = input.checked;
        });

        try {
            const response = await fetch('/notifications/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                showNotification('Notification settings updated', 'success');
            }
        } catch (error) {
            console.error('Failed to update notification settings:', error);
            showNotification('Failed to update settings', 'error');
        }
    }

    startNotificationPolling() {
        // Poll for new notifications every 30 seconds
        setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }

    downloadReceipt(receiptId) {
        // Generate and download receipt as PDF/text
        const receipt = this.receipts.find(r => r.id === receiptId);
        if (!receipt) return;

        const content = `
NAMASKAH SMS - VERIFICATION RECEIPT
==================================

Receipt Number: ${receipt.receipt_number}
Service Used: ${receipt.service_name}
Phone Number: ${receipt.phone_number}
ISP/Carrier: ${receipt.isp_carrier || 'Unknown'}
Area Code: ${receipt.area_code || 'Unknown'}
Amount Charged: N${receipt.amount_spent.toFixed(2)} ($${receipt.amount_usd.toFixed(2)} USD)
Completed At: ${this.formatFullDate(receipt.success_timestamp)}

Transaction Type: SMS Verification
Status: Completed Successfully

Thank you for using Namaskah SMS!
Support: support@namaskah.app
        `;

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `receipt-${receipt.receipt_number}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    getServiceIcon(serviceName) {
        const icons = {
            'whatsapp': '💬',
            'telegram': '✈️',
            'discord': '🎮',
            'google': '🔍',
            'facebook': '📘',
            'instagram': '📷',
            'twitter': '🐦',
            'tiktok': '🎵',
            'paypal': '💳',
            'default': '📱'
        };
        return icons[serviceName.toLowerCase()] || icons.default;
    }

    getNotificationIcon(type) {
        const icons = {
            'receipt': '🧾',
            'success': '✅',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        };
        return icons[type] || icons.info;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    formatFullDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    }
}

// Initialize receipt manager
let receiptManager;
document.addEventListener('DOMContentLoaded', () => {
    receiptManager = new ReceiptManager();
});

// Export for global access
window.receiptManager = receiptManager;