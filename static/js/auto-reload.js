// Auto-Reload Manager
class AutoReload {
    constructor() {
        this.threshold = 5.0;
        this.enabled = false;
        this.amount = 25;
        this.load();
    }

    load() {
        const stored = localStorage.getItem('auto_reload_settings');
        if (stored) {
            const settings = JSON.parse(stored);
            this.threshold = settings.threshold || 5.0;
            this.enabled = settings.enabled || false;
            this.amount = settings.amount || 25;
        }
    }

    save() {
        localStorage.setItem('auto_reload_settings', JSON.stringify({
            threshold: this.threshold,
            enabled: this.enabled,
            amount: this.amount
        }));
    }

    check(balance) {
        if (this.enabled && balance < this.threshold) {
            const lastAlert = localStorage.getItem('last_reload_alert');
            const now = Date.now();
            if (!lastAlert || now - parseInt(lastAlert) > 3600000) { // 1 hour
                this.showAlert(balance);
                localStorage.setItem('last_reload_alert', now.toString());
            }
        }
    }

    showAlert(balance) {
        const alert = document.createElement('div');
        alert.style.cssText = 'position: fixed; top: 80px; right: 20px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 16px 20px; border-radius: 12px; box-shadow: 0 10px 40px rgba(239, 68, 68, 0.3); z-index: 10000; max-width: 320px; animation: slideIn 0.3s ease-out;';
        alert.innerHTML = `
            <div style="display: flex; align-items: start; gap: 12px;">
                <div style="font-size: 24px;">⚠️</div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px;">Low Balance Alert</div>
                    <div style="font-size: 13px; opacity: 0.95; margin-bottom: 12px;">Balance: $${balance.toFixed(2)} (threshold: $${this.threshold})</div>
                    <button onclick="window.location.href='/wallet'" style="width: 100%; padding: 8px; background: white; color: #ef4444; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px;">Add Credits Now</button>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; opacity: 0.8; padding: 0; line-height: 1;">&times;</button>
            </div>
        `;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 10000);
    }

    renderSettings(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 20px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h4 style="font-size: 14px; font-weight: 600; margin: 0;">Auto-Reload Settings</h4>
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="auto-reload-toggle" ${this.enabled ? 'checked' : ''} onchange="autoReload.toggle(this.checked)" style="width: 18px; height: 18px; cursor: pointer;">
                        <span style="font-size: 13px; font-weight: 500;">${this.enabled ? 'Enabled' : 'Disabled'}</span>
                    </label>
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 6px; color: #6b7280;">Alert when balance falls below:</label>
                    <input type="number" id="reload-threshold" value="${this.threshold}" min="1" max="50" step="1" onchange="autoReload.setThreshold(this.value)" style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                </div>
                <div style="font-size: 11px; color: #6b7280; background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #e5e7eb;">
                    💡 You'll receive a notification when your balance drops below $${this.threshold.toFixed(2)}
                </div>
            </div>
        `;
    }

    toggle(enabled) {
        this.enabled = enabled;
        this.save();
        this.renderSettings('auto-reload-settings');
    }

    setThreshold(value) {
        this.threshold = parseFloat(value) || 5.0;
        this.save();
    }
}

window.autoReload = new AutoReload();
