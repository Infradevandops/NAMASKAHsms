/**
 * Bulk Verification Module
 * Request multiple verifications at once
 */

class BulkVerification {
    constructor() {
        this.verifications = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('bulk-verify-btn')?.addEventListener('click', () => this.showBulkModal());
        document.getElementById('start-bulk-btn')?.addEventListener('click', () => this.startBulk());
    }

    showBulkModal() {
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;

        if (!service || !country) {
            this.showToast('Please select a service and country first', 'warning');
            return;
        }

        // Pre-fill modal
        document.getElementById('bulk-service').textContent = service;
        document.getElementById('bulk-country').textContent = country;
        document.getElementById('bulk-quantity').value = 2;

        this.updateBulkEstimate();

        const modal = new bootstrap.Modal(document.getElementById('bulk-verification-modal'));
        modal.show();
    }

    async updateBulkEstimate() {
        const quantity = parseInt(document.getElementById('bulk-quantity').value) || 1;
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;

        try {
            const response = await axios.get('/api/pricing/estimate', {
                params: { service, country, tier: 'STANDARD', quantity }
            });

            const total = response.data.total_cost;
            document.getElementById('bulk-total-cost').textContent = `$${total.toFixed(2)}`;

            // Check balance
            const balanceText = document.getElementById('user-balance').textContent;
            const balance = parseFloat(balanceText.replace('$', ''));

            if (balance < total) {
                document.getElementById('bulk-insufficient-alert').classList.remove('d-none');
                document.getElementById('start-bulk-btn').disabled = true;
            } else {
                document.getElementById('bulk-insufficient-alert').classList.add('d-none');
                document.getElementById('start-bulk-btn').disabled = false;
            }
        } catch (error) {
            console.error('Failed to estimate bulk cost:', error);
        }
    }

    async startBulk() {
        const quantity = parseInt(document.getElementById('bulk-quantity').value) || 1;
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;

        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('bulk-verification-modal')).hide();

        // Show progress modal
        const progressModal = new bootstrap.Modal(document.getElementById('bulk-progress-modal'));
        progressModal.show();

        this.verifications = [];
        const progressBar = document.getElementById('bulk-progress-bar');
        const progressText = document.getElementById('bulk-progress-text');
        const resultsList = document.getElementById('bulk-results-list');
        resultsList.innerHTML = '';

        for (let i = 0; i < quantity; i++) {
            progressText.textContent = `Requesting ${i + 1} of ${quantity}...`;
            progressBar.style.width = `${((i + 1) / quantity) * 100}%`;

            try {
                const response = await axios.post('/api/verification/request', {
                    service,
                    country,
                    capability: 'sms'
                });

                this.verifications.push(response.data);

                // Add to results
                resultsList.innerHTML += `
                    <div class="alert alert-success mb-2">
                        <i class="fas fa-check-circle"></i>
                        <strong>${response.data.phone_number}</strong>
                        <button class="btn btn-sm btn-outline-primary float-end" 
                                onclick="bulkVerification.copyNumber('${response.data.phone_number}')">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                `;

                // Small delay between requests
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch (error) {
                resultsList.innerHTML += `
                    <div class="alert alert-danger mb-2">
                        <i class="fas fa-times-circle"></i>
                        Failed: ${error.response?.data?.detail || 'Unknown error'}
                    </div>
                `;
            }
        }

        progressText.textContent = `Completed ${quantity} verifications`;
        progressBar.style.width = '100%';

        // Show export button
        document.getElementById('export-bulk-btn').classList.remove('d-none');
    }

    copyNumber(number) {
        navigator.clipboard.writeText(number).then(() => {
            this.showToast('Number copied!', 'success');
        });
    }

    exportResults() {
        const csv = 'Phone Number,Service,Country,Status\n' +
            this.verifications.map(v => 
                `${v.phone_number},${v.service},${v.country},${v.status}`
            ).join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bulk-verifications-${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
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
let bulkVerification;
document.addEventListener('DOMContentLoaded', () => {
    bulkVerification = new BulkVerification();
    
    // Setup quantity change listener
    document.getElementById('bulk-quantity')?.addEventListener('input', () => {
        bulkVerification.updateBulkEstimate();
    });
});
