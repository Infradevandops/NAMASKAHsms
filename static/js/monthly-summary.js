// Monthly Summary Manager
class MonthlySummary {
    constructor() {
        this.data = null;
    }

    async fetch() {
        const token = localStorage.getItem('access_token');
        if (!token) return null;

        try {
            const now = new Date();
            const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
            const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59).toISOString();

            const res = await fetch(`/api/billing/history?start_date=${monthStart}&end_date=${monthEnd}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.data = this.process(data.transactions || []);
                return this.data;
            }
        } catch (e) {
            console.error('Failed to fetch monthly summary:', e);
        }
        return null;
    }

    process(transactions) {
        const summary = {
            totalSpent: 0,
            totalAdded: 0,
            verifications: 0,
            topServices: {},
            dailySpending: {}
        };

        transactions.forEach(tx => {
            const amount = Math.abs(tx.amount || 0);
            const date = new Date(tx.created_at).toISOString().split('T')[0];

            if (tx.type === 'debit' || (tx.amount && tx.amount < 0)) {
                summary.totalSpent += amount;
                summary.verifications++;
                
                const service = tx.description?.split(' ')[0] || 'Other';
                summary.topServices[service] = (summary.topServices[service] || 0) + amount;
                summary.dailySpending[date] = (summary.dailySpending[date] || 0) + amount;
            } else {
                summary.totalAdded += amount;
            }
        });

        summary.topServices = Object.entries(summary.topServices)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);

        return summary;
    }

    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container || !this.data) return;

        const monthName = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

        container.innerHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 16px;">📊 ${monthName} Summary</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 20px;">
                    <div>
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Total Spent</div>
                        <div style="font-size: 28px; font-weight: 700;">$${this.data.totalSpent.toFixed(2)}</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Credits Added</div>
                        <div style="font-size: 28px; font-weight: 700;">$${this.data.totalAdded.toFixed(2)}</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">Verifications</div>
                        <div style="font-size: 28px; font-weight: 700;">${this.data.verifications}</div>
                    </div>
                </div>

                ${this.data.topServices.length > 0 ? `
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                        <div style="font-size: 13px; font-weight: 600; margin-bottom: 12px; opacity: 0.95;">Top Services</div>
                        ${this.data.topServices.map(([service, amount]) => `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 13px;">${service}</span>
                                <span style="font-weight: 600;">$${amount.toFixed(2)}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    async renderModal() {
        await this.fetch();
        
        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000; padding: 20px;';
        modal.onclick = (e) => { if (e.target === modal) modal.remove(); };

        const content = document.createElement('div');
        content.style.cssText = 'background: white; border-radius: 16px; max-width: 600px; width: 100%; max-height: 80vh; overflow-y: auto; padding: 0;';
        
        const monthName = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        
        content.innerHTML = `
            <div style="position: sticky; top: 0; background: white; padding: 24px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                <h2 style="font-size: 20px; font-weight: 700; margin: 0;">📊 ${monthName} Summary</h2>
                <button onclick="this.closest('[style*=fixed]').remove()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #6b7280;">&times;</button>
            </div>
            
            <div style="padding: 24px;">
                ${this.data ? `
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;">
                        <div style="text-align: center; padding: 16px; background: #fef3c7; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: 700; color: #d97706;">$${this.data.totalSpent.toFixed(2)}</div>
                            <div style="font-size: 12px; color: #92400e; margin-top: 4px;">Total Spent</div>
                        </div>
                        <div style="text-align: center; padding: 16px; background: #d1fae5; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: 700; color: #059669;">$${this.data.totalAdded.toFixed(2)}</div>
                            <div style="font-size: 12px; color: #065f46; margin-top: 4px;">Credits Added</div>
                        </div>
                        <div style="text-align: center; padding: 16px; background: #dbeafe; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: 700; color: #1e40af;">${this.data.verifications}</div>
                            <div style="font-size: 12px; color: #1e3a8a; margin-top: 4px;">Verifications</div>
                        </div>
                    </div>

                    ${this.data.topServices.length > 0 ? `
                        <div style="margin-bottom: 24px;">
                            <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 12px;">Top Services</h3>
                            <div style="background: #f9fafb; border-radius: 8px; padding: 16px;">
                                ${this.data.topServices.map(([service, amount], i) => `
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; ${i < this.data.topServices.length - 1 ? 'border-bottom: 1px solid #e5e7eb;' : ''}">
                                        <div style="display: flex; align-items: center; gap: 12px;">
                                            <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 14px;">${i + 1}</div>
                                            <span style="font-weight: 600;">${service}</span>
                                        </div>
                                        <span style="font-weight: 700; color: #f59e0b;">$${amount.toFixed(2)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <div style="text-align: center; padding: 16px; background: #f0f9ff; border-radius: 8px;">
                        <div style="font-size: 13px; color: #1e40af;">
                            ${this.data.totalSpent > 0 ? `Average per verification: <strong>$${(this.data.totalSpent / this.data.verifications).toFixed(2)}</strong>` : 'No spending this month'}
                        </div>
                    </div>
                ` : '<div style="text-align: center; padding: 40px; color: #9ca3af;">Loading...</div>'}
            </div>
        `;

        modal.appendChild(content);
        document.body.appendChild(modal);
    }
}

window.monthlySummary = new MonthlySummary();
