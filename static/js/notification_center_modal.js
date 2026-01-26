/**
 * Notification Center Modal
 * Displays notifications in a modal/panel within the dashboard
 */

class NotificationCenterModal {
    constructor() {
        this.notifications = [];
        this.currentPage = 0;
        this.totalNotifications = 0;
        this.filters = {};
        this.selectedNotifications = new Set();
        this.isOpen = false;
        this.init();
    }

    async init() {
        this.createModal();
        this.setupEventListeners();
        await this.loadCategories();
    }

    createModal() {
        const modal = document.createElement('div');
        modal.id = 'notification-center-modal';
        modal.innerHTML = `
            <div class="notification-modal-overlay"></div>
            <div class="notification-modal-panel">
                <div class="notification-modal-header">
                    <h2>Notifications</h2>
                    <button class="notification-modal-close" aria-label="Close notifications">✕</button>
                </div>

                <div class="notification-modal-content">
                    <!-- Sidebar -->
                    <div class="notification-modal-sidebar">
                        <div class="notification-filters">
                            <h3>Filters</h3>
                            
                            <div class="filter-group">
                                <label>Category</label>
                                <select id="modal-category-filter">
                                    <option value="">All Categories</option>
                                    <option value="verification_initiated">Verification Started</option>
                                    <option value="sms_received">SMS Received</option>
                                    <option value="verification_complete">Verification Complete</option>
                                    <option value="verification_failed">Verification Failed</option>
                                    <option value="credit_deducted">Credit Deducted</option>
                                    <option value="refund_issued">Refund Issued</option>
                                    <option value="balance_low">Balance Low</option>
                                </select>
                            </div>

                            <div class="filter-group">
                                <label>Status</label>
                                <select id="modal-status-filter">
                                    <option value="">All</option>
                                    <option value="unread">Unread</option>
                                    <option value="read">Read</option>
                                </select>
                            </div>
                        </div>

                        <div class="notification-categories">
                            <h3>Categories</h3>
                            <div id="modal-categories-list">
                                <!-- Categories loaded here -->
                            </div>
                        </div>
                    </div>

                    <!-- Main Content -->
                    <div class="notification-modal-main">
                        <div class="notification-modal-toolbar">
                            <input type="text" id="modal-search-input" placeholder="Search notifications..." class="notification-search">
                            <div class="notification-toolbar-actions">
                                <button id="modal-mark-all-read" title="Mark all as read">✓ Read</button>
                                <button id="modal-delete-all" title="Delete selected">🗑 Delete</button>
                            </div>
                        </div>

                        <div class="notification-modal-list" id="modal-notification-list">
                            <div class="loading">Loading notifications...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.modal = modal;
    }

    setupEventListeners() {
        // Close button
        this.modal.querySelector('.notification-modal-close').addEventListener('click', () => this.close());
        
        // Overlay click
        this.modal.querySelector('.notification-modal-overlay').addEventListener('click', () => this.close());

        // Filters
        document.getElementById('modal-category-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('modal-status-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('modal-search-input').addEventListener('input', (e) => this.search(e.target.value));

        // Actions
        document.getElementById('modal-mark-all-read').addEventListener('click', () => this.markAllRead());
        document.getElementById('modal-delete-all').addEventListener('click', () => this.deleteAll());

        // Keyboard shortcut (Escape to close)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/notifications/categories');
            const data = await response.json();
            this.renderCategories(data.categories);
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    renderCategories(categories) {
        const list = document.getElementById('modal-categories-list');
        list.innerHTML = categories.map(cat => `
            <div class="category-item" onclick="notificationCenterModal.filterByCategory('${cat.type}')">
                <span class="category-name">${this.formatCategoryName(cat.type)}</span>
                <span class="category-count">${cat.unread}/${cat.total}</span>
            </div>
        `).join('');
    }

    formatCategoryName(type) {
        return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    async loadNotifications() {
        try {
            const params = new URLSearchParams({
                skip: this.currentPage * 10,
                limit: 10,
                ...this.filters
            });

            const response = await fetch(`/api/notifications/center?${params}`);
            const data = await response.json();

            this.notifications = data.notifications;
            this.totalNotifications = data.total;
            this.renderNotifications();
        } catch (error) {
            console.error('Failed to load notifications:', error);
            document.getElementById('modal-notification-list').innerHTML = '<div class="empty-state">Failed to load notifications</div>';
        }
    }

    renderNotifications() {
        const list = document.getElementById('modal-notification-list');

        if (this.notifications.length === 0) {
            list.innerHTML = '<div class="empty-state">📭 No notifications</div>';
            return;
        }

        list.innerHTML = this.notifications.map(n => `
            <div class="notification-modal-item ${n.is_read ? '' : 'unread'}">
                <input type="checkbox" class="notification-checkbox" value="${n.id}" onchange="notificationCenterModal.toggleSelection(this)">
                <div class="notification-modal-item-content">
                    <div class="notification-modal-item-title">${this.escapeHtml(n.title)}</div>
                    <div class="notification-modal-item-message">${this.escapeHtml(n.message)}</div>
                    <div class="notification-modal-item-meta">
                        <span class="notification-type">${this.formatCategoryName(n.type)}</span>
                        <span>${new Date(n.created_at).toLocaleString()}</span>
                    </div>
                </div>
                <div class="notification-modal-item-actions">
                    ${!n.is_read ? `<button onclick="notificationCenterModal.markAsRead('${n.id}')" title="Mark as read">✓</button>` : ''}
                    <button onclick="notificationCenterModal.deleteNotification('${n.id}')" title="Delete">✕</button>
                </div>
            </div>
        `).join('');
    }

    async applyFilters() {
        this.filters = {
            category: document.getElementById('modal-category-filter').value || undefined,
            is_read: document.getElementById('modal-status-filter').value === 'unread' ? false : document.getElementById('modal-status-filter').value === 'read' ? true : undefined,
        };

        Object.keys(this.filters).forEach(key => this.filters[key] === undefined && delete this.filters[key]);

        this.currentPage = 0;
        await this.loadNotifications();
    }

    async search(query) {
        if (query.length < 2) {
            await this.loadNotifications();
            return;
        }

        try {
            const response = await fetch(`/api/notifications/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.notifications = data.notifications;
            this.totalNotifications = data.total;
            this.renderNotifications();
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    toggleSelection(checkbox) {
        if (checkbox.checked) {
            this.selectedNotifications.add(checkbox.value);
        } else {
            this.selectedNotifications.delete(checkbox.value);
        }
    }

    async markAsRead(notificationId) {
        try {
            await fetch(`/api/notifications/bulk-read?notification_ids=${notificationId}`, { method: 'POST' });
            await this.loadNotifications();
        } catch (error) {
            console.error('Failed to mark as read:', error);
        }
    }

    async markAllRead() {
        if (this.selectedNotifications.size === 0) {
            alert('Please select notifications to mark as read');
            return;
        }

        try {
            const ids = Array.from(this.selectedNotifications).join('&notification_ids=');
            await fetch(`/api/notifications/bulk-read?notification_ids=${ids}`, { method: 'POST' });
            this.selectedNotifications.clear();
            await this.loadNotifications();
        } catch (error) {
            console.error('Failed to mark as read:', error);
        }
    }

    async deleteNotification(notificationId) {
        if (confirm('Delete this notification?')) {
            try {
                await fetch(`/api/notifications/bulk-delete?notification_ids=${notificationId}`, { method: 'POST' });
                await this.loadNotifications();
            } catch (error) {
                console.error('Failed to delete:', error);
            }
        }
    }

    async deleteAll() {
        if (this.selectedNotifications.size === 0) {
            alert('Please select notifications to delete');
            return;
        }

        if (!confirm('Delete selected notifications?')) return;

        try {
            const ids = Array.from(this.selectedNotifications).join('&notification_ids=');
            await fetch(`/api/notifications/bulk-delete?notification_ids=${ids}`, { method: 'POST' });
            this.selectedNotifications.clear();
            await this.loadNotifications();
        } catch (error) {
            console.error('Failed to delete:', error);
        }
    }

    filterByCategory(category) {
        document.getElementById('modal-category-filter').value = category;
        this.applyFilters();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    open() {
        this.isOpen = true;
        this.modal.classList.add('open');
        document.body.style.overflow = 'hidden';
        this.loadNotifications();
    }

    close() {
        this.isOpen = false;
        this.modal.classList.remove('open');
        document.body.style.overflow = '';
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationCenterModal = new NotificationCenterModal();
});
