/**
 * User Intelligence Manager
 * Handles 90-day retention and Unified User Control Table
 */

const UsersManager = {
    retentionChart: null,

    async init() {
        console.log('Users Manager initialized');
        await this.loadRetention();
        await this.loadUserList();
    },

    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    },

    async loadRetention() {
        try {
            const res = await fetch('/api/admin/intelligence/cohorts', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            const ctx = document.getElementById('retentionChart').getContext('2d');
            if (this.retentionChart) this.retentionChart.destroy();
            
            // We'll plot the latest cohort's retention curve
            const latestCohort = data.cohorts[data.cohorts.length - 1];
            
            this.retentionChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['W0', 'W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
                    datasets: [{
                        label: `Latest Cohort (${latestCohort.cohort})`,
                        data: latestCohort.retention,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.05)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { title: { display: true, text: '90-Day Retention Curve', color: '#fff' } },
                    scales: { 
                        y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.03)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        } catch (e) {
            console.error('[Users] Retention fetch failed:', e);
        }
    },

    async loadUserList() {
        try {
            // Reusing legacy endpoint but with new styling
            const res = await fetch('/api/admin/tiers/users?limit=50', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            const tbody = document.getElementById('user-intelligence-table');
            tbody.innerHTML = data.users.map(u => `
                <tr>
                    <td>
                        <div style="font-weight:600;">${u.email}</div>
                        <div style="font-size:10px; color:var(--admin-text-muted); font-family:monospace;">${u.id.substring(0, 8)}...</div>
                    </td>
                    <td><span class="badge badge-info">${u.tier.toUpperCase()}</span></td>
                    <td><span class="font-bold">$${u.credits.toFixed(2)}</span></td>
                    <td><span class="badge ${u.is_active ? 'badge-success' : 'badge-danger'}">${u.is_active ? 'Active' : 'Suspended'}</span></td>
                    <td>
                        <button class="btn-secondary" style="padding:2px 8px; font-size:10px;" onclick="UsersManager.openTierModal('${u.id}', '${u.email}')">Manage</button>
                    </td>
                </tr>
            `).join('');
        } catch (e) { console.error(e); }
    },

    openTierModal(userId, email) {
        const modal = document.getElementById('tier-modal');
        const content = document.getElementById('tier-modal-content');
        content.innerHTML = `
            <div style="margin-bottom:12px; font-size:13px; color:var(--admin-text-muted);">Configuring: ${email}</div>
            <div class="form-group">
                <label style="display:block; margin-bottom:4px; font-size:12px;">Subscription Tier</label>
                <select id="new-tier" style="width:100%; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); color:white; padding:8px; border-radius:4px;">
                    <option value="freemium">Freemium</option>
                    <option value="payg">PAYG</option>
                    <option value="pro">Pro</option>
                    <option value="custom">Custom</option>
                </select>
            </div>
            <div class="form-group" style="margin-top:12px;">
                <label style="display:block; margin-bottom:4px; font-size:12px;">Credit Adjustment</label>
                <input type="number" id="credit-adj" step="0.01" value="0.00" style="width:100%; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); color:white; padding:8px; border-radius:4px;">
            </div>
        `;
        
        document.getElementById('save-tier-btn').onclick = () => this.saveUserChanges(userId);
        modal.style.display = 'flex';
    },

    async saveUserChanges(userId) {
        const tier = document.getElementById('new-tier').value;
        const credits = document.getElementById('credit-adj').value;
        
        try {
            // Tier change
            await fetch(`/api/admin/tiers/users/${userId}/tier`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tier, duration_days: 30 })
            });
            
            // Credit adjustment
            if (parseFloat(credits) !== 0) {
                 await fetch(`/api/admin/users/${userId}/credits`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.getToken()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ amount: parseFloat(credits), reason: 'Admin adjustment' })
                });
            }
            
            document.getElementById('tier-modal').style.display = 'none';
            this.loadUserList();
            showToast('User updated successfully', 'success');
        } catch (e) {
            console.error(e);
            showToast('Failed to save changes', 'error');
        }
    }
};
