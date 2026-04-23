/**
 * Admin Operational Intelligence Manager
 * Phase 6.0: Vitality, Governance, and Audit
 */

const IntelligenceManager = {
    signupChart: null,

    async init() {
        console.log('Intelligence Manager initialized');
        await this.loadOverview();
        await this.loadHeatmap();
    },

    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    },

    async loadOverview() {
        try {
            const token = this.getToken();
            const res = await fetch('/api/v1/admin/dashboard/v2/stats', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            
            // Basic Metrics
            document.getElementById('stat-total-users').textContent = data.overview.total_users;
            document.getElementById('stat-success-rate').textContent = `${data.overview.success_rate}%`;
            document.getElementById('stat-net-revenue').textContent = '$' + data.financial.net.toFixed(2);
            
            // Load Vitality briefly for DAU
            const vitRes = await fetch('/api/admin/intelligence/vitality', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const vitData = await vitRes.json();
            document.getElementById('stat-dau').textContent = vitData.dau;

            // Provider Table
            const pBody = document.getElementById('provider-table');
            pBody.innerHTML = data.providers.map(p => `
                <tr>
                    <td><span class="font-bold">${p.name.toUpperCase()}</span></td>
                    <td>${p.total_volume}</td>
                    <td>
                         <div style="display:flex; align-items:center; gap:8px;">
                            <div style="flex:1; height:4px; background:rgba(255,255,255,0.05); border-radius:2px; overflow:hidden;">
                                <div style="width:${p.success_rate}%; height:100%; background:${p.success_rate > 90 ? 'var(--admin-success)' : 'var(--admin-warning)'};"></div>
                            </div>
                            <span>${p.success_rate}%</span>
                        </div>
                    </td>
                    <td><span class="badge ${p.success_rate > 80 ? 'badge-success' : 'badge-warning'}">Stable</span></td>
                </tr>
            `).join('');

        } catch (e) {
            console.error('[Intelligence] Overview fetch failed:', e);
        }
    },

    async loadHeatmap() {
        try {
            const res = await fetch('/api/admin/intelligence/load-heatmap', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            const container = document.getElementById('load-heatmap');
            const max = Math.max(...data.map(h => h.count), 1);
            
            container.innerHTML = data.map(h => `
                <div class="heatmap-bar" 
                     style="height: ${(h.count / max * 100)}%" 
                     data-hour="${h.hour}" 
                     title="${h.count} attempts at ${h.hour}:00 UTC">
                </div>
            `).join('');
        } catch (e) { console.error(e); }
    },

    async loadVitality() {
        try {
            const res = await fetch('/api/admin/intelligence/vitality', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            // Signup Chart
            const ctx = document.getElementById('signupChart').getContext('2d');
            if (this.signupChart) this.signupChart.destroy();
            this.signupChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.signup_velocity.map(s => s.date),
                    datasets: [{
                        label: 'New Registrations',
                        data: data.signup_velocity.map(s => s.count),
                        borderColor: '#6366f1',
                        borderWidth: 2,
                        tension: 0.1,
                        fill: true,
                        backgroundColor: 'rgba(99, 102, 241, 0.05)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } } }
                }
            });

            // Power Users
            const puBody = document.getElementById('power-user-table');
            puBody.innerHTML = data.power_users.map(u => `
                <tr>
                    <td class="font-bold">${u.email}</td>
                    <td class="text-muted">${u.volume}</td>
                    <td class="font-bold text-success">$${u.spend.toFixed(2)}</td>
                </tr>
            `).join('');
        } catch (e) { console.error(e); }
    },

    async loadAudit() {
        try {
            const token = this.getToken();
            
            // Margin Drift
            const driftRes = await fetch('/api/admin/intelligence/audit/margin', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const driftData = await driftRes.json();
            document.getElementById('drift-count').textContent = driftData.incidents_count;
            document.getElementById('drift-total').textContent = '$' + driftData.total_leakage.toFixed(2);
            
            const dBody = document.getElementById('drift-table');
            dBody.innerHTML = driftData.incidents.map(i => `
                <tr>
                    <td class="font-bold">${i.service}</td>
                    <td class="text-danger">$${i.user_price.toFixed(2)}</td>
                    <td class="text-success">$${i.expected_price.toFixed(2)}</td>
                    <td class="text-danger">-$${i.drift_amount.toFixed(2)}</td>
                    <td class="text-muted" style="font-size: 11px;">${new Date(i.created_at).toLocaleString()}</td>
                </tr>
            `).join('');

            // Audit Trail
            const trailRes = await fetch('/api/admin/intelligence/audit/trail', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const trailData = await trailRes.json();
            const aBody = document.getElementById('audit-table');
            aBody.innerHTML = trailData.map(t => `
                <tr>
                    <td><span class="badge ${t.action === 'activated' ? 'badge-success' : 'badge-secondary'}">${t.action.toUpperCase()}</span></td>
                    <td>${t.changed_by}</td>
                    <td><span class="text-muted">${t.notes}</span></td>
                    <td style="font-size: 11px;">${new Date(t.timestamp).toLocaleString()}</td>
                </tr>
            `).join('');

        } catch (e) { console.error(e); }
    }
};

document.addEventListener('DOMContentLoaded', () => IntelligenceManager.init());
