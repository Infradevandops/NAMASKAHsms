// Spending Alerts Manager
class SpendingAlerts {
    constructor() {
        this.thresholds = [50, 100, 200];
        this.alerts = {};
        this.load();
    }

    load() {
        const stored = localStorage.getItem('spending_alerts');
        this.alerts = stored ? JSON.parse(stored) : {};
    }

    save() {
        localStorage.setItem('spending_alerts', JSON.stringify(this.alerts));
    }

    check(currentSpending) {
        const monthKey = new Date().toISOString().slice(0, 7);
        
        this.thresholds.forEach(threshold => {
            const alertKey = `${monthKey}-${threshold}`;
            if (currentSpending >= threshold && !this.alerts[alertKey]) {
                this.showAlert(threshold, currentSpending);
                this.alerts[alertKey] = Date.now();
                this.save();
            }
        });
    }

    showAlert(threshold, current) {
        const alert = document.createElement('div');
        alert.style.cssText = 'position: fixed; top: 80px; right: 20px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 16px 20px; border-radius: 12px; box-shadow: 0 10px 40px rgba(245, 158, 11, 0.3); z-index: 10000; max-width: 320px; animation: slideIn 0.3s ease-out;';
        alert.innerHTML = `
            <div style="display: flex; align-items: start; gap: 12px;">
                <div style="font-size: 24px;">💰</div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px;">Spending Alert</div>
                    <div style="font-size: 13px; opacity: 0.95;">You've spent $${current.toFixed(2)} this month (threshold: $${threshold})</div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; opacity: 0.8; padding: 0; line-height: 1;">&times;</button>
            </div>
        `;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 8000);
    }

    reset() {
        const monthKey = new Date().toISOString().slice(0, 7);
        Object.keys(this.alerts).forEach(key => {
            if (!key.startsWith(monthKey)) delete this.alerts[key];
        });
        this.save();
    }

    renderSettings(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 16px; background: #f9fafb; border-radius: 8px;">
                <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Spending Alert Thresholds</h4>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    ${this.thresholds.map(t => `
                        <div style="padding: 8px 16px; background: white; border: 2px solid #e5e7eb; border-radius: 6px; font-weight: 600; color: #f59e0b;">$${t}</div>
                    `).join('')}
                </div>
                <p style="font-size: 12px; color: #6b7280; margin-top: 8px;">You'll be notified when your monthly spending reaches these amounts.</p>
            </div>
        `;
    }
}

window.spendingAlerts = new SpendingAlerts();
