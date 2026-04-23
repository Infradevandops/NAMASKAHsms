/**
 * Institutional Compliance & Governance Manager
 * Handles SOC 2 Status and Persistent Audit Logs
 */

const ComplianceManager = {
    async init() {
        console.log('Compliance Manager initialized');
        await this.loadComplianceReport();
        await this.loadAuditLogs();
    },

    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    },

    async loadComplianceReport() {
        try {
            const res = await fetch('/api/admin/intelligence/compliance/report', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            // Render basic summary (we'll add this to the Control & Audit tab)
            const summaryGrid = document.getElementById('full-audit-table'); // We'll put it elsewhere if needed
            
            // Build a compliance HUD
            const hud = document.createElement('div');
            hud.className = 'glass-card';
            hud.style.marginBottom = '24px';
            hud.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 class="card-title">SOC 2 Type II Security Posture</h3>
                    <div style="font-size:24px; font-weight:bold; color:${data.overall_status === 'compliant' ? 'var(--admin-success)' : 'var(--admin-danger)'}">
                        ${data.compliance_score}%
                    </div>
                </div>
                <div class="target-progress-container">
                    <div class="target-progress-bar" style="width: ${data.compliance_score}%; background:${data.overall_status === 'compliant' ? 'var(--admin-success)' : 'var(--admin-danger)'}"></div>
                </div>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:12px; margin-top:16px;">
                    ${Object.entries(data.controls_summary).slice(0, 3).map(([id, ctrl]) => `
                        <div style="font-size:11px; padding:8px; background:rgba(255,255,255,0.03); border-radius:4px;">
                            <div style="font-weight:bold;">${ctrl.description || id}</div>
                            <div style="color:${ctrl.compliant ? 'var(--admin-success)' : 'var(--admin-danger)'}">
                                ${ctrl.compliant ? '● Compliant' : '○ Needs Change'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            const container = document.getElementById('page-audit');
            container.insertBefore(hud, container.firstChild);
        } catch (e) { console.error('[Compliance] Report failed:', e); }
    },

    async loadAuditLogs() {
        try {
            const res = await fetch('/api/admin/intelligence/audit/logs?limit=50', {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const logs = await res.json();
            
            const tbody = document.getElementById('full-audit-table');
            tbody.innerHTML = logs.map(l => `
                <tr>
                    <td><span class="badge badge-secondary">${l.action}</span></td>
                    <td>${l.user_id ? l.user_id.substring(0, 8) : 'System'}</td>
                    <td>
                        <div style="font-size:11px; color:var(--admin-text-muted);">${l.resource_type}</div>
                        <div style="font-size:10px;">${JSON.stringify(l.details).substring(0, 50)}...</div>
                    </td>
                    <td style="font-size:11px;">${new Date(l.created_at).toLocaleString()}</td>
                </tr>
            `).join('');
        } catch (e) {
            console.error('[Compliance] Logs failed:', e);
            document.getElementById('full-audit-table').innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--admin-danger);">Failed to load audit trail</td></tr>';
        }
    }
};

// Global for tab switching
window.ComplianceManager = ComplianceManager;
