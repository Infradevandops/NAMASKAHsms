/**
 * Admin Pricing Management Component
 * Handles live provider prices, pricing templates, and historical trends.
 */

const PricingManager = {
    templates: [],
    livePrices: [],
    
    async init() {
        console.log('Pricing Manager initialized');
        await this.loadTemplates();
        await this.loadLivePrices();
        await this.loadProviderBalance();
        this.setupAutoRefresh();
    },

    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    },

    async loadProviderBalance() {
        try {
            const res = await fetch('/api/admin/pricing/balance', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            const el = document.getElementById('provider-balance');
            const alertEl = document.getElementById('balance-alert');
            
            if (data.balance !== undefined) {
                el.textContent = `$${data.balance.toFixed(2)}`;
                if (data.balance < 20) {
                    el.style.color = 'var(--admin-danger)';
                    alertEl.textContent = '⚠ CRITICAL: Low balance ($20 threshold)';
                    alertEl.className = 'text-danger font-bold';
                } else {
                    el.style.color = 'var(--admin-success)';
                    alertEl.textContent = 'Healthy';
                    alertEl.className = 'text-success';
                }
            }
        } catch (e) {
            console.error('Balance check failed:', e);
        }
    },

    async loadTemplates() {
        try {
            const response = await fetch('/api/admin/pricing/templates', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await response.json();
            this.templates = data.templates || [];
            this.renderTemplates();
        } catch (error) {
            console.error('Failed to load templates:', error);
        }
    },

    async loadLivePrices(forceRefresh = false) {
        const container = document.getElementById('live-inventory-table');
        if (!container) return;
        
        if (!forceRefresh) {
            container.innerHTML = '<tr><td colspan="5" class="text-center">Syncing with TextVerified...</td></tr>';
        }

        try {
            const url = `/api/admin/pricing/providers/live${forceRefresh ? '?force_refresh=true' : ''}`;
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await response.json();
            this.livePrices = data.prices || [];
            this.renderLivePrices(data);
        } catch (error) {
            console.error('Failed to load live prices:', error);
        }
    },

    renderTemplates() {
        const grid = document.getElementById('template-grid');
        if (!grid) return;
        
        grid.innerHTML = '';
        if (this.templates.length === 0) {
            grid.innerHTML = '<div class="no-data">No pricing templates found.</div>';
            return;
        }

        this.templates.forEach(template => {
            const card = document.createElement('div');
            card.className = `glass-card ${template.is_active ? 'border-primary' : ''}`;
            card.style.padding = '12px';
            card.style.fontSize = '12px';
            
            const markup = template.markup_multiplier || 1.1;
            const markupPct = ((markup - 1) * 100).toFixed(0);

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span class="badge ${template.is_active ? 'badge-success' : 'badge-secondary'}">
                        ${template.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <span class="font-bold">${markupPct}% Markup</span>
                </div>
                <h4 style="margin:4px 0;">${template.name}</h4>
                <p class="text-muted" style="margin-bottom:12px;">${template.description || 'No description'}</p>
                
                ${template.is_promotional ? `<div style="margin-bottom:8px;"><span class="badge badge-warning" style="font-size:10px;">🏷️ ${template.discount_percentage || 0}% OFF</span></div>` : ''}
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    ${!template.is_active ? `<button class="btn-primary" style="font-size:10px; padding:4px 8px;" onclick="PricingManager.activateTemplate(${template.id})">Activate</button>` : ''}
                    <button class="btn-secondary" style="font-size:10px; padding:4px 8px;" onclick="PricingManager.cloneTemplate(${template.id})">Clone</button>
                    ${!template.is_active ? `<button style="font-size:10px; padding:4px 8px; background:var(--admin-danger,#ef4444); color:#fff; border:none; border-radius:4px; cursor:pointer;" onclick="PricingManager.deleteTemplate(${template.id})">Delete</button>` : ''}
                </div>
            `;
            grid.appendChild(card);
        });
    },

    renderLivePrices(data) {
        const container = document.getElementById('live-inventory-table');
        if (!container) return;

        container.innerHTML = this.livePrices.slice(0, 50).map(p => `
            <tr>
                <td class="font-bold">${p.service_name}</td>
                <td class="text-muted">$${p.provider_cost.toFixed(3)}</td>
                <td class="font-bold text-success">$${p.platform_price.toFixed(2)}</td>
                <td><span class="badge badge-info">${p.markup_percentage.toFixed(0)}%</span></td>
                <td>
                    <button class="btn-icon" onclick="PricingManager.showHistory('${p.service_id}', '${p.service_name}')">📈</button>
                </td>
            </tr>
        `).join('');
    },

    exportToCSV() {
        if (!this.livePrices.length) return;
        
        const headers = ["Service", "Provider Cost", "Platform Price", "Markup (%)"];
        const rows = this.livePrices.map(p => [
            p.service_name,
            p.provider_cost,
            p.platform_price,
            p.markup_percentage
        ]);

        let csvContent = "data:text/csv;charset=utf-8," 
            + headers.join(",") + "\n"
            + rows.map(e => e.join(",")).join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `namaskah_pricing_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    async activateTemplate(id) {
        if (!confirm('Are you sure you want to activate this pricing template? This will immediately affect all user purchases.')) return;
        
        try {
            const response = await fetch(`/api/admin/pricing/templates/${id}/activate`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await response.json();
            if (data.status === 'success') {
                showToast('Pricing template activated successfully', 'success');
                await this.loadTemplates();
                await this.loadLivePrices();
            } else {
                showToast(data.detail || 'Activation failed', 'error');
            }
        } catch (error) {
            showToast('Network error during activation', 'error');
        }
    },

    openCreateModal() {
        // Simple implementation for now, can be expanded to a full form
        const name = prompt('Enter template name:');
        if (!name) return;
        const markup = prompt('Enter markup multiplier (e.g. 1.25 for 25%):', '1.10');
        if (!markup) return;

        this.createTemplate({
            name,
            markup_multiplier: parseFloat(markup),
            description: 'Created via admin quick-action'
        });
    },

    async createTemplate(data) {
        try {
            const response = await fetch('/api/admin/pricing/templates', {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (result.status === 'success') {
                showToast('Template created', 'success');
                this.loadTemplates();
            } else {
                showToast(result.detail || 'Failed to create template', 'error');
            }
        } catch (error) {
            showToast('Error creating template', 'error');
        }
    },

    async rollbackPricing() {
        if (!confirm('Rollback to the previously active pricing template?')) return;
        try {
            const response = await fetch('/api/admin/pricing/rollback', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await response.json();
            if (data.status === 'success') {
                showToast(`Rolled back to "${data.template.name}"`, 'success');
                await this.loadTemplates();
                await this.loadLivePrices();
            } else {
                showToast(data.detail || 'Rollback failed', 'error');
            }
        } catch (error) {
            showToast('Network error during rollback', 'error');
        }
    },

    async cloneTemplate(id) {
        const name = prompt('Enter name for the cloned template:');
        if (!name) return;
        try {
            const response = await fetch(`/api/admin/pricing/templates/${id}/clone`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name })
            });
            const data = await response.json();
            if (data.status === 'success') {
                showToast(`Template cloned as "${name}"`, 'success');
                await this.loadTemplates();
            } else {
                showToast(data.detail || 'Clone failed', 'error');
            }
        } catch (error) {
            showToast('Network error during clone', 'error');
        }
    },

    async deleteTemplate(id) {
        if (!confirm('Delete this template? This cannot be undone.')) return;
        try {
            const response = await fetch(`/api/admin/pricing/templates/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await response.json();
            if (data.status === 'success') {
                showToast('Template deleted', 'success');
                await this.loadTemplates();
            } else {
                showToast(data.detail || 'Delete failed', 'error');
            }
        } catch (error) {
            showToast('Network error during delete', 'error');
        }
    },

    async showHistory(service_id, service_name) {
        try {
            const response = await fetch(`/api/admin/pricing/history/${service_id}`, {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await response.json();
            this.renderHistoryChart(service_name, data.history);
        } catch (error) {
            showToast('Failed to load price history', 'error');
        }
    },

    renderHistoryChart(name, history) {
        const modal = document.getElementById('history-modal');
        const title = document.getElementById('history-modal-title');
        const container = document.getElementById('history-chart-container');
        
        title.textContent = `Price History: ${name}`;
        modal.classList.add('active');
        
        container.innerHTML = '<canvas id="priceHistoryChart"></canvas>';
        const ctx = document.getElementById('priceHistoryChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: history.map(h => new Date(h.captured_at).toLocaleDateString()),
                datasets: [
                    {
                        label: 'Provider Cost ($)',
                        data: history.map(h => h.provider_cost),
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        fill: true,
                        tension: 0.1
                    },
                    {
                        label: 'Platform Price ($)',
                        data: history.map(h => h.platform_price),
                        borderColor: '#10b981',
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { beginAtZero: false, ticks: { callback: value => '$' + value.toFixed(2) } }
                }
            }
        });
    },

    setupAutoRefresh() {
        // Refresh live prices every 5 minutes
        setInterval(() => this.loadLivePrices(), 300000);
    },

    showError(id, msg) {
        const div = document.getElementById(id);
        if (div) {
            div.textContent = msg;
            div.style.display = 'block';
        }
    }
};

// Global helpers if needed by inline scripts
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

document.addEventListener('DOMContentLoaded', () => PricingManager.init());

// Ensure showToast exists globally
if (typeof showToast === 'undefined') {
    window.showToast = function(message, type) {
        const toast = document.createElement('div');
        const colors = { success: '#10b981', error: '#ef4444', info: '#6366f1', warning: '#f59e0b' };
        toast.textContent = message;
        toast.style.cssText = `position:fixed;top:20px;right:20px;z-index:9999;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;background:${colors[type]||colors.info};box-shadow:0 4px 12px rgba(0,0,0,0.3);`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    };
}
