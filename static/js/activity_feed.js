/**
 * Activity Feed JavaScript
 * Handles activity feed UI, filtering, pagination, and export
 */

class ActivityFeed {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalActivities = 0;
        this.activities = [];
        this.filters = {
            activity_type: null,
            resource_type: null,
            status: null,
            date_from: null,
            date_to: null,
        };

        this.initializeEventListeners();
        this.loadActivities();
        this.loadSummary();
    }

    initializeEventListeners() {
        // Filter buttons
        document.getElementById('apply-filters').addEventListener('click', () => this.applyFilters());
        document.getElementById('reset-filters').addEventListener('click', () => this.resetFilters());
        document.getElementById('export-btn').addEventListener('click', () => this.showExportModal());

        // Pagination
        document.getElementById('prev-page').addEventListener('click', () => this.previousPage());
        document.getElementById('next-page').addEventListener('click', () => this.nextPage());

        // Modal
        document.getElementById('close-modal').addEventListener('click', () => this.closeModal());
        document.getElementById('close-export-modal').addEventListener('click', () => this.closeExportModal());

        // Export options
        document.getElementById('export-json').addEventListener('click', () => this.exportActivities('json'));
        document.getElementById('export-csv').addEventListener('click', () => this.exportActivities('csv'));

        // Close modal on outside click
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('activity-modal');
            if (event.target === modal) {
                this.closeModal();
            }
            const exportModal = document.getElementById('export-modal');
            if (event.target === exportModal) {
                this.closeExportModal();
            }
        });
    }

    async loadActivities() {
        try {
            this.showLoading(true);

            const params = new URLSearchParams({
                skip: (this.currentPage - 1) * this.pageSize,
                limit: this.pageSize,
            });

            // Add filters
            if (this.filters.activity_type) {
                params.append('activity_type', this.filters.activity_type);
            }
            if (this.filters.resource_type) {
                params.append('resource_type', this.filters.resource_type);
            }
            if (this.filters.status) {
                params.append('status', this.filters.status);
            }
            if (this.filters.date_from) {
                params.append('date_from', this.filters.date_from);
            }
            if (this.filters.date_to) {
                params.append('date_to', this.filters.date_to);
            }

            const response = await fetch(`/api/activities?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.activities = data.activities;
            this.totalActivities = data.total;

            this.renderActivities();
            this.updatePagination();
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading activities:', error);
            this.showError('Failed to load activities');
            this.showLoading(false);
        }
    }

    async loadSummary() {
        try {
            const response = await fetch('/api/activities/summary/overview');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Update summary cards
            document.getElementById('total-activities').textContent = data.total_activities;
            document.getElementById('completed-count').textContent = data.by_status.completed || 0;
            document.getElementById('pending-count').textContent = data.by_status.pending || 0;
            document.getElementById('failed-count').textContent = data.by_status.failed || 0;
        } catch (error) {
            console.error('Error loading summary:', error);
        }
    }

    renderActivities() {
        const container = document.getElementById('activities-container');
        const emptyState = document.getElementById('empty-state');

        if (this.activities.length === 0) {
            container.innerHTML = '';
            emptyState.style.display = 'flex';
            return;
        }

        emptyState.style.display = 'none';

        container.innerHTML = this.activities
            .map((activity) => this.createActivityElement(activity))
            .join('');

        // Add click listeners to activity items
        document.querySelectorAll('.activity-item').forEach((item) => {
            item.addEventListener('click', () => {
                const activityId = item.dataset.activityId;
                this.showActivityDetails(activityId);
            });
        });
    }

    createActivityElement(activity) {
        const statusClass = `status-${activity.status}`;
        const typeIcon = this.getActivityIcon(activity.activity_type);
        const date = new Date(activity.created_at).toLocaleString();

        return `
            <div class="activity-item" data-activity-id="${activity.id}">
                <div class="activity-icon">${typeIcon}</div>
                <div class="activity-content">
                    <div class="activity-title">${this.escapeHtml(activity.title)}</div>
                    <div class="activity-meta">
                        <span class="activity-type">${activity.activity_type}</span>
                        <span class="activity-resource">${activity.resource_type}</span>
                        <span class="activity-action">${activity.action}</span>
                    </div>
                    <div class="activity-description">${this.escapeHtml(activity.description || '')}</div>
                </div>
                <div class="activity-status">
                    <span class="status-badge ${statusClass}">${activity.status}</span>
                    <div class="activity-date">${date}</div>
                </div>
            </div>
        `;
    }

    getActivityIcon(type) {
        const icons = {
            verification: '✓',
            payment: '💳',
            login: '🔐',
            settings: '⚙️',
            api_key: '🔑',
        };
        return icons[type] || '📋';
    }

    async showActivityDetails(activityId) {
        try {
            const response = await fetch(`/api/activities/${activityId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const activity = await response.json();

            // Populate modal
            document.getElementById('modal-title').textContent = activity.title;
            document.getElementById('modal-activity-type').textContent = activity.activity_type;
            document.getElementById('modal-resource').textContent = `${activity.resource_type} (${activity.resource_id || 'N/A'})`;
            document.getElementById('modal-action').textContent = activity.action;
            document.getElementById('modal-status').textContent = activity.status;
            document.getElementById('modal-description').textContent = activity.description || 'N/A';
            document.getElementById('modal-date').textContent = new Date(activity.created_at).toLocaleString();

            // Show metadata if available
            if (activity.metadata) {
                document.getElementById('metadata-section').style.display = 'block';
                document.getElementById('modal-metadata').textContent = JSON.stringify(activity.metadata, null, 2);
            } else {
                document.getElementById('metadata-section').style.display = 'none';
            }

            // Show modal
            document.getElementById('activity-modal').style.display = 'block';
        } catch (error) {
            console.error('Error loading activity details:', error);
            this.showError('Failed to load activity details');
        }
    }

    closeModal() {
        document.getElementById('activity-modal').style.display = 'none';
    }

    applyFilters() {
        this.filters.activity_type = document.getElementById('activity-type').value || null;
        this.filters.resource_type = document.getElementById('resource-type').value || null;
        this.filters.status = document.getElementById('status-filter').value || null;
        this.filters.date_from = document.getElementById('date-from').value || null;
        this.filters.date_to = document.getElementById('date-to').value || null;

        this.currentPage = 1;
        this.loadActivities();
    }

    resetFilters() {
        document.getElementById('activity-type').value = '';
        document.getElementById('resource-type').value = '';
        document.getElementById('status-filter').value = '';
        document.getElementById('date-from').value = '';
        document.getElementById('date-to').value = '';

        this.filters = {
            activity_type: null,
            resource_type: null,
            status: null,
            date_from: null,
            date_to: null,
        };

        this.currentPage = 1;
        this.loadActivities();
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadActivities();
        }
    }

    nextPage() {
        const maxPage = Math.ceil(this.totalActivities / this.pageSize);
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.loadActivities();
        }
    }

    updatePagination() {
        const maxPage = Math.ceil(this.totalActivities / this.pageSize);
        document.getElementById('page-info').textContent = `Page ${this.currentPage} of ${maxPage}`;
        document.getElementById('prev-page').disabled = this.currentPage === 1;
        document.getElementById('next-page').disabled = this.currentPage >= maxPage;
    }

    showExportModal() {
        document.getElementById('export-modal').style.display = 'block';
    }

    closeExportModal() {
        document.getElementById('export-modal').style.display = 'none';
    }

    async exportActivities(format) {
        try {
            const params = new URLSearchParams({ format });

            // Add filters
            if (this.filters.activity_type) {
                params.append('activity_type', this.filters.activity_type);
            }
            if (this.filters.resource_type) {
                params.append('resource_type', this.filters.resource_type);
            }
            if (this.filters.status) {
                params.append('status', this.filters.status);
            }
            if (this.filters.date_from) {
                params.append('date_from', this.filters.date_from);
            }
            if (this.filters.date_to) {
                params.append('date_to', this.filters.date_to);
            }

            const response = await fetch(`/api/activities/export?${params}`, { method: 'POST' });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (format === 'json') {
                this.downloadJSON(data.data, 'activities.json');
            } else if (format === 'csv') {
                this.downloadCSV(data.data, 'activities.csv');
            }

            this.closeExportModal();
            this.showSuccess(`Activities exported as ${format.toUpperCase()}`);
        } catch (error) {
            console.error('Error exporting activities:', error);
            this.showError('Failed to export activities');
        }
    }

    downloadJSON(data, filename) {
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        this.downloadBlob(blob, filename);
    }

    downloadCSV(data, filename) {
        const blob = new Blob([data], { type: 'text/csv' });
        this.downloadBlob(blob, filename);
    }

    downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    showLoading(show) {
        document.getElementById('loading-indicator').style.display = show ? 'flex' : 'none';
    }

    showError(message) {
        // Use toast notification if available
        if (window.toast) {
            window.toast.show(message, 'error');
        } else {
            alert(message);
        }
    }

    showSuccess(message) {
        // Use toast notification if available
        if (window.toast) {
            window.toast.show(message, 'success');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize activity feed when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ActivityFeed();
});
