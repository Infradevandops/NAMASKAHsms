/**
 * Quick Retry Module
 * One-click retry for failed verifications
 */

class QuickRetry {
    constructor() {
        this.lastVerification = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadLastVerification();
    }

    setupEventListeners() {
        document.getElementById('quick-retry-btn')?.addEventListener('click', () => this.retry());
    }

    loadLastVerification() {
        const stored = localStorage.getItem('last_verification');
        if (stored) {
            this.lastVerification = JSON.parse(stored);
            this.showRetryButton();
        }
    }

    saveLastVerification(service, country, capability = 'sms') {
        this.lastVerification = { service, country, capability };
        localStorage.setItem('last_verification', JSON.stringify(this.lastVerification));
    }

    showRetryButton() {
        const btn = document.getElementById('quick-retry-btn');
        if (!btn || !this.lastVerification) return;

        btn.classList.remove('d-none');
        btn.innerHTML = `
            <i class="fas fa-redo"></i>
            Retry ${this.lastVerification.service} (${this.lastVerification.country})
        `;
    }

    async retry() {
        if (!this.lastVerification) {
            this.showToast('No previous verification to retry', 'warning');
            return;
        }

        const { service, country, capability } = this.lastVerification;

        // Check balance first
        try {
            const estimate = await axios.get('/api/pricing/estimate', {
                params: { service, country, tier: 'STANDARD', quantity: 1 }
            });

            const balanceText = document.getElementById('user-balance').textContent;
            const balance = parseFloat(balanceText.replace('$', ''));

            if (balance < estimate.data.total_cost) {
                this.showToast('Insufficient balance for retry', 'danger');
                return;
            }
        } catch (error) {
            console.error('Failed to check balance:', error);
        }

        // Show loading
        const btn = document.getElementById('quick-retry-btn');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Retrying...';
        btn.disabled = true;

        try {
            const response = await axios.post('/api/verification/request', {
                service,
                country,
                capability
            });

            // Update form with new verification
            if (window.verificationManager) {
                window.verificationManager.currentVerification = response.data;
                window.verificationManager.displayVerificationResult();
                window.verificationManager.startPolling();
                window.verificationManager.startCountdown();

                // Show result section
                document.getElementById('verification-form').parentElement.classList.add('d-none');
                document.getElementById('verification-result').classList.remove('d-none');
            }

            this.showToast('Retry successful! New number requested.', 'success');
        } catch (error) {
            const message = error.response?.data?.detail || 'Retry failed';
            this.showToast(message, 'danger');
        } finally {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

// Initialize
let quickRetry;
document.addEventListener('DOMContentLoaded', () => {
    quickRetry = new QuickRetry();
});

// Hook into verification manager to save last verification
if (window.verificationManager) {
    const originalConfirmPurchase = window.verificationManager.confirmPurchase;
    window.verificationManager.confirmPurchase = async function() {
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;
        const capability = document.querySelector('input[name="capability"]:checked').value;
        
        if (window.quickRetry) {
            window.quickRetry.saveLastVerification(service, country, capability);
        }
        
        return originalConfirmPurchase.call(this);
    };
}
