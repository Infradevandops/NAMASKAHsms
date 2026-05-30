class PaymentMethodSelector {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.selectedMethod = null;
        this.methods = [];
        this.country = null;
    }

    async init() {
        if (!this.container) return;

        // Show loading state
        this.container.innerHTML = `
            <div class="animate-pulse flex space-x-4">
                <div class="flex-1 space-y-4 py-1">
                    <div class="h-4 bg-white/10 rounded w-3/4"></div>
                    <div class="space-y-2">
                        <div class="h-10 bg-white/10 rounded"></div>
                        <div class="h-10 bg-white/10 rounded"></div>
                    </div>
                </div>
            </div>
        `;

        try {
            const token = localStorage.getItem('access_token');
            const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

            const response = await fetch('/api/billing/payment-method/methods-by-location', {
                headers: headers
            });

            if (!response.ok) throw new Error('Failed to fetch methods');

            const data = await response.json();
            this.country = data.country;
            this.methods = data.recommended_methods;

            this.render();

            // Pre-select first recommended method
            if (this.methods.length > 0) {
                this.selectMethod(this.methods[0].id);
            }
        } catch (error) {
            console.error('Payment method load error:', error);
            this.container.innerHTML = `
                <div class="text-red-400 text-sm">Failed to load payment methods. Please try again later.</div>
            `;
        }
    }

    selectMethod(methodId) {
        this.selectedMethod = methodId;
        localStorage.setItem('preferred_payment_method', methodId);
        this.render();
    }

    render() {
        if (!this.container || this.methods.length === 0) return;

        const html = `
            <label class="block text-white font-semibold mb-2">
                Recommended Payment Method
                <span class="text-xs font-normal text-zinc-400 ml-2">Based on your location (${this.country})</span>
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                ${this.methods.map((m, index) => {
                    const isSelected = this.selectedMethod === m.id;
                    const isRecommended = index === 0;

                    return \`
                        <div onclick="window.paymentMethodSelector.selectMethod('\${m.id}')"
                             class="relative cursor-pointer rounded-lg border p-3 transition-all \${
                                isSelected
                                ? 'border-primary bg-primary/10 shadow-[0_0_10px_rgba(254,60,114,0.2)]'
                                : 'border-white/20 bg-white/5 hover:border-white/40'
                             }">
                            \${isRecommended ? '<div class="absolute -top-2 -right-2 bg-yellow-500 text-black text-[10px] font-bold px-2 py-0.5 rounded-full">⭐ Recommended</div>' : ''}
                            <div class="flex items-center gap-3">
                                <div class="text-2xl">\${m.icon}</div>
                                <div>
                                    <div class="font-medium text-white text-sm">\${m.name}</div>
                                    <div class="text-zinc-400 text-xs">Fee: \${m.fee}%</div>
                                </div>
                            </div>
                        </div>
                    \`;
                }).join('')}
            </div>
            <input type="hidden" id="selected_payment_method" name="selected_payment_method" value="\${this.selectedMethod || ''}">
        `;

        this.container.innerHTML = html;
    }
}

// Global instance
window.paymentMethodSelector = null;

// Auto-init if container exists
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('payment-method-container')) {
        window.paymentMethodSelector = new PaymentMethodSelector('payment-method-container');
        window.paymentMethodSelector.init();
    }
});
