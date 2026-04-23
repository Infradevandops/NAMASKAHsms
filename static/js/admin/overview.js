/**
 * Institutional Overview Manager
 * Focuses on Growth Targets (350 Users) and High-Level Velocity
 */

const OverviewManager = {
    signupChart: null,

    async init() {
        console.log('Overview Manager initialized');
        await this.loadGrowthTarget();
        await this.loadSignupVelocity();
        await this.loadHeatmap();
    },

    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    },

    async loadGrowthTarget() {
        try {
            const res = await fetch('/api/admin/intelligence/targets', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            document.getElementById('target-count').textContent = `${data.current} / ${data.target}`;
            document.getElementById('target-progress').style.width = `${data.percentage}%`;
            
            document.getElementById('stat-velocity').textContent = `${data.velocity} / day`;
            const statusElem = document.getElementById('stat-velocity-status');
            
            if (data.projected_date) {
                statusElem.textContent = `Projected Target: ${data.projected_date}`;
            } else {
                statusElem.textContent = `Status: ${data.status}`;
            }
            
            statusElem.style.color = data.status === 'On Track' ? 'var(--admin-success)' : 'var(--admin-danger)';

            // Fetch DAU separately from vitality as before or update if needed
            const vitRes = await fetch('/api/admin/intelligence/vitality', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const vitData = await vitRes.json();
            document.getElementById('stat-dau').textContent = vitData.dau;
            document.getElementById('stat-net-revenue').textContent = `$${vitData.monthly_revenue.toFixed(2)}`;
        } catch (e) {
            console.error('[Overview] Target fetch failed:', e);
        }
    },

    async loadSignupVelocity() {
        try {
            const res = await fetch('/api/admin/intelligence/vitality', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            const ctx = document.getElementById('signupChart').getContext('2d');
            if (this.signupChart) this.signupChart.destroy();
            this.signupChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.signup_velocity.map(s => s.date),
                    datasets: [{
                        label: 'Institutional Onboarding',
                        data: data.signup_velocity.map(s => s.count),
                        borderColor: '#6366f1',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: '#6366f1',
                        tension: 0.3,
                        fill: true,
                        backgroundColor: 'rgba(99, 102, 241, 0.05)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { 
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.03)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        } catch (e) { console.error(e); }
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
                <div style="flex:1; background:var(--admin-accent); border-radius:3px 3px 0 0; position:relative; height: ${(h.count / max * 100)}%" 
                     title="${h.count} attempts at ${h.hour}:00 UTC">
                     <span style="position:absolute; bottom:-18px; left:50%; transform:translateX(-50%); font-size:9px; color:var(--admin-text-muted);">${h.hour}</span>
                </div>
            `).join('');
        } catch (e) { console.error(e); }
    }
};

document.addEventListener('DOMContentLoaded', () => OverviewManager.init());
