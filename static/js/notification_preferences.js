/**
 * Notification Preferences Manager
 * Handles user notification preference customization
 */

class NotificationPreferencesManager {
    constructor() {
        this.preferences = {};
        this.defaults = {};
        this.init();
    }

    async init() {
        await this.loadPreferences();
        this.setupEventListeners();
        this.renderPreferences();
    }

    async loadPreferences() {
        try {
            const response = await fetch('/api/notifications/preferences');
            const data = await response.json();
            this.preferences = {};
            this.defaults = {};

            // Index preferences by type
            data.preferences.forEach((pref) => {
                this.preferences[pref.notification_type] = pref;
            });

            // Index defaults by type
            data.defaults.forEach((def) => {
                this.defaults[def.notification_type] = def;
            });

            console.log('Preferences loaded:', this.preferences);
        } catch (error) {
            console.error('Failed to load preferences:', error);
            this.showError('Failed to load preferences');
        }
    }

    setupEventListeners() {
        // Save button
        const saveBtn = document.getElementById('save-preferences-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePreferences());
        }

        // Reset button
        const resetBtn = document.getElementById('reset-preferences-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetPreferences());
        }

        // Quiet hours toggle
        const quietHoursCheckbox = document.getElementById('enable-quiet-hours');
        if (quietHoursCheckbox) {
            quietHoursCheckbox.addEventListener('change', (e) => this.toggleQuietHours(e.target.checked));
        }
    }

    renderPreferences() {
        const container = document.getElementById('preferences-container');
        if (!container) return;

        // Get all notification types from defaults
        const notificationTypes = Object.keys(this.defaults);

        let html = '<div class="preferences-list">';

        notificationTypes.forEach((type) => {
            const pref = this.preferences[type] || {};
            const def = this.defaults[type] || {};

            html += `
                <div class="preference-item">
                    <div class="preference-header">
                        <h3>${this.formatNotificationType(type)}</h3>
                        <p class="preference-description">${def.description || ''}</p>
                    </div>

                    <div class="preference-controls">
                        <!-- Enable/Disable Toggle -->
                        <div class="control-group">
                            <label>
                                <input type="checkbox" 
                                       class="pref-enabled" 
                                       data-type="${type}" 
                                       ${pref.enabled !== false ? 'checked' : ''}>
                                Enable ${this.formatNotificationType(type)} notifications
                            </label>
                        </div>

                        <!-- Delivery Methods -->
                        <div class="control-group">
                            <label>Delivery Methods:</label>
                            <div class="delivery-methods">
                                <label>
                                    <input type="checkbox" 
                                           class="pref-delivery" 
                                           data-type="${type}" 
                                           data-method="toast" 
                                           ${this.hasDeliveryMethod(pref, 'toast') ? 'checked' : ''}>
                                    In-App Toast
                                </label>
                                <label>
                                    <input type="checkbox" 
                                           class="pref-delivery" 
                                           data-type="${type}" 
                                           data-method="email" 
                                           ${this.hasDeliveryMethod(pref, 'email') ? 'checked' : ''}>
                                    Email
                                </label>
                                <label>
                                    <input type="checkbox" 
                                           class="pref-delivery" 
                                           data-type="${type}" 
                                           data-method="sms" 
                                           ${this.hasDeliveryMethod(pref, 'sms') ? 'checked' : ''}>
                                    SMS
                                </label>
                                <label>
                                    <input type="checkbox" 
                                           class="pref-delivery" 
                                           data-type="${type}" 
                                           data-method="webhook" 
                                           ${this.hasDeliveryMethod(pref, 'webhook') ? 'checked' : ''}>
                                    Webhook
                                </label>
                            </div>
                        </div>

                        <!-- Frequency -->
                        <div class="control-group">
                            <label>Frequency:</label>
                            <select class="pref-frequency" data-type="${type}">
                                <option value="instant" ${(pref.frequency || 'instant') === 'instant' ? 'selected' : ''}>Instant</option>
                                <option value="daily" ${(pref.frequency || 'instant') === 'daily' ? 'selected' : ''}>Daily Digest</option>
                                <option value="weekly" ${(pref.frequency || 'instant') === 'weekly' ? 'selected' : ''}>Weekly Digest</option>
                                <option value="never" ${(pref.frequency || 'instant') === 'never' ? 'selected' : ''}>Never</option>
                            </select>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';

        // Add quiet hours section
        html += `
            <div class="quiet-hours-section">
                <h3>Quiet Hours (Do Not Disturb)</h3>
                <label>
                    <input type="checkbox" id="enable-quiet-hours">
                    Enable quiet hours
                </label>
                <div class="quiet-hours-controls" style="display: none;">
                    <div class="control-group">
                        <label>From:</label>
                        <input type="time" id="quiet-hours-start" value="22:00">
                    </div>
                    <div class="control-group">
                        <label>To:</label>
                        <input type="time" id="quiet-hours-end" value="08:00">
                    </div>
                    <label>
                        <input type="checkbox" id="quiet-hours-override">
                        Allow critical notifications during quiet hours
                    </label>
                </div>
            </div>
        `;

        container.innerHTML = html;

        // Re-attach event listeners after rendering
        this.setupEventListeners();
    }

    hasDeliveryMethod(pref, method) {
        if (!pref.delivery_methods) return method === 'toast';
        return pref.delivery_methods.includes(method);
    }

    formatNotificationType(type) {
        return type
            .split('_')
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    toggleQuietHours(enabled) {
        const controls = document.querySelector('.quiet-hours-controls');
        if (controls) {
            controls.style.display = enabled ? 'block' : 'none';
        }
    }

    async savePreferences() {
        try {
            const preferences = [];

            // Collect all preferences
            document.querySelectorAll('.preference-item').forEach((item) => {
                const enabledCheckbox = item.querySelector('.pref-enabled');
                const type = enabledCheckbox.dataset.type;

                // Get delivery methods
                const deliveryMethods = [];
                item.querySelectorAll('.pref-delivery:checked').forEach((checkbox) => {
                    deliveryMethods.push(checkbox.dataset.method);
                });

                // Get frequency
                const frequencySelect = item.querySelector('.pref-frequency');
                const frequency = frequencySelect.value;

                preferences.push({
                    notification_type: type,
                    enabled: enabledCheckbox.checked,
                    delivery_methods: deliveryMethods.length > 0 ? deliveryMethods : ['toast'],
                    frequency: frequency,
                    quiet_hours_start: null,
                    quiet_hours_end: null,
                    created_at_override: false,
                });
            });

            // Add quiet hours if enabled
            const quietHoursCheckbox = document.getElementById('enable-quiet-hours');
            if (quietHoursCheckbox && quietHoursCheckbox.checked) {
                const quietStart = document.getElementById('quiet-hours-start').value;
                const quietEnd = document.getElementById('quiet-hours-end').value;
                const override = document.getElementById('quiet-hours-override').checked;

                // Apply quiet hours to all preferences
                preferences.forEach((pref) => {
                    pref.quiet_hours_start = quietStart;
                    pref.quiet_hours_end = quietEnd;
                    pref.created_at_override = override;
                });
            }

            // Send to server
            const response = await fetch('/api/notifications/preferences', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(preferences),
            });

            if (!response.ok) {
                throw new Error('Failed to save preferences');
            }

            const result = await response.json();
            this.showSuccess(`Preferences saved! (${result.total} updated)`);
            await this.loadPreferences();
            this.renderPreferences();
        } catch (error) {
            console.error('Failed to save preferences:', error);
            this.showError('Failed to save preferences');
        }
    }

    async resetPreferences() {
        if (!confirm('Reset all preferences to defaults?')) {
            return;
        }

        try {
            const response = await fetch('/api/notifications/preferences/reset', {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Failed to reset preferences');
            }

            this.showSuccess('Preferences reset to defaults');
            await this.loadPreferences();
            this.renderPreferences();
        } catch (error) {
            console.error('Failed to reset preferences:', error);
            this.showError('Failed to reset preferences');
        }
    }

    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success';
        alert.textContent = message;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 3000);
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-error';
        alert.textContent = message;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationPreferencesManager = new NotificationPreferencesManager();
});
