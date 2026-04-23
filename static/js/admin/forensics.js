/**
 * Verification Forensics Manager
 * Handles 90-day history with Profit & Margin Drift Analysis
 */

const ForensicsManager = {
    limit: 50,
    offset: 0,
    currentPage: 1,

    async init() {
        console.log('Forensics Manager initialized');
        await this.loadHistory();
    },

    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || '';
    },

    async loadHistory() {
        try {
            const res = await fetch(`/api/admin/intelligence/forensics/history?limit=${this.limit}&offset=${this.offset}`, {
                headers: { 'Authorization': `Bearer ${this.getToken()}` }
            });
            const data = await res.json();
            
            this.savedHistory = data.history; // Store for export
            
            const tbody = document.getElementById('forensics-history-table');
            tbody.innerHTML = data.history.map(f => {
                const profitClass = f.profit >= 0 ? 'profit-pos' : 'profit-neg';
                const driftClass = f.drift > 0 ? 'profit-neg' : 'profit-pos';
                
                return `
                    <tr style="${f.drift > 0.05 ? 'background:rgba(239, 68, 68, 0.05);' : ''}">
                        <td>#${f.audit_id}</td>
                        <td><div style="font-size:12px; font-weight:600;">${f.identifier}</div></td>
                        <td><span class="badge badge-secondary">${f.service}</span></td>
                        <td>${f.phone}</td>
                        <td style="font-weight:600;">$${f.platform_price.toFixed(2)}</td>
                        <td class="${profitClass}">$${f.profit.toFixed(2)}</td>
                        <td class="${driftClass}">$${f.drift.toFixed(2)}</td>
                        <td style="font-size:11px; color:var(--admin-text-muted);">${new Date(f.timestamp).toLocaleString()}</td>
                    </tr>
                `;
            }).join('');

            this.currentPage = Math.floor(this.offset / this.limit) + 1;
            document.getElementById('forensics-page-info').textContent = `Page ${this.currentPage} of ${Math.ceil(data.total / this.limit)}`;
            
        } catch (e) { console.error('[Forensics] History fetch failed:', e); }
    },

    exportToCSV() {
        if (!this.savedHistory || this.savedHistory.length === 0) return;
        
        const headers = ["Audit ID", "Identifier", "Service", "Phone", "Price", "Profit", "Drift", "Timestamp"];
        const rows = this.savedHistory.map(f => [
            f.audit_id, f.identifier, f.service, f.phone, f.platform_price, f.profit, f.drift, f.timestamp
        ]);
        
        let csvContent = "data:text/csv;charset=utf-8," 
            + headers.join(",") + "\n"
            + rows.map(e => e.join(",")).join("\n");
            
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `forensics_export_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    nextPage() {
        this.offset += this.limit;
        this.loadHistory();
    },

    prevPage() {
        if (this.offset >= this.limit) {
            this.offset -= this.limit;
            this.loadHistory();
        }
    }
};

// Expose to window for inline HTML onclick handlers
window.ForensicsManager = ForensicsManager;
