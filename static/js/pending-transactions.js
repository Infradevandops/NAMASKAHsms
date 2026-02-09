// Pending Transactions Manager
class PendingTransactions {
    constructor() {
        this.pending = [];
    }

    async fetch() {
        const token = localStorage.getItem('access_token');
        if (!token) return [];

        try {
            const res = await fetch('/api/billing/history?status=pending', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.pending = (data.transactions || []).filter(t => 
                    t.status === 'pending' || t.status === 'processing'
                );
                return this.pending;
            }
        } catch (e) {
            console.error('Failed to fetch pending transactions:', e);
        }
        return [];
    }

    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (this.pending.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        container.innerHTML = `
            <div style="background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <div style="font-size: 20px;">⏳</div>
                    <div>
                        <div style="font-weight: 600; font-size: 14px; color: #92400e;">Pending Transactions</div>
                        <div style="font-size: 12px; color: #78350f;">${this.pending.length} transaction${this.pending.length > 1 ? 's' : ''} processing</div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    ${this.pending.map(tx => `
                        <div style="background: white; padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: 600; font-size: 13px; color: #1f2937;">${tx.description || 'Payment'}</div>
                                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">${new Date(tx.created_at).toLocaleString()}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-weight: 700; color: #f59e0b;">$${Math.abs(tx.amount || 0).toFixed(2)}</div>
                                <div style="font-size: 10px; color: #d97706; text-transform: uppercase; margin-top: 2px;">Processing</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    async poll() {
        await this.fetch();
        this.render('pending-transactions');
    }

    startPolling(interval = 10000) {
        this.poll();
        setInterval(() => this.poll(), interval);
    }
}

window.pendingTransactions = new PendingTransactions();
