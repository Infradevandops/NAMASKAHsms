/**
 * Verification Page Module
 * Handles SMS verification purchase and display
 */

class VerificationManager {
    constructor() {
        this.currentVerification = null;
        this.pollingInterval = null;
        this.countdownInterval = null;
        this.services = [];
        this.countries = [];
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadServices();
        await this.loadCountries();
        await this.loadUserBalance();
        await this.loadVerificationHistory();
    }

    setupEventListeners() {
        // Form submission
        document.getElementById('verification-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });

        // Service and country change
        document.getElementById('service-select').addEventListener('change', () => this.updateCostEstimate());
        document.getElementById('country-select').addEventListener('change', () => this.updateCostEstimate());

        // Copy buttons
        document.getElementById('copy-phone-btn')?.addEventListener('click', () => this.copyToClipboard('phone-number'));
        document.getElementById('copy-code-btn')?.addEventListener('click', () => this.copyToClipboard('sms-code'));

        // Action buttons
        document.getElementById('release-btn')?.addEventListener('click', () => this.releaseNumber());
        document.getElementById('new-verification-btn')?.addEventListener('click', () => this.resetForm());

        // Confirmation
        document.getElementById('confirm-purchase-btn')?.addEventListener('click', () => this.confirmPurchase());
    }

    async loadServices() {
        try {
            const response = await axios.get('/api/pricing/services');
            this.services = Object.keys(response.data.services);
            this.populateServiceSelect();
        } catch (error) {
            console.error('Failed to load services:', error);
            this.showError('Failed to load services');
        }
    }

    async loadCountries() {
        try {
            const response = await axios.get('/api/pricing/countries');
            this.countries = Object.keys(response.data.countries);
            this.populateCountrySelect();
        } catch (error) {
            console.error('Failed to load countries:', error);
            this.showError('Failed to load countries');
        }
    }

    async loadUserBalance() {
        try {
            const response = await axios.get('/api/user/balance');
            const balance = response.data.credits;
            document.getElementById('user-balance').textContent = `$${balance.toFixed(2)}`;
            document.getElementById('balance-display').textContent = `$${balance.toFixed(2)}`;
        } catch (error) {
            console.error('Failed to load balance:', error);
        }
    }

    async loadVerificationHistory() {
        try {
            const response = await axios.get('/api/verification/history?limit=10');
            this.populateVerificationHistory(response.data.verifications);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    populateServiceSelect() {
        const select = document.getElementById('service-select');
        this.services.forEach(service => {
            const option = document.createElement('option');
            option.value = service;
            option.textContent = service.charAt(0).toUpperCase() + service.slice(1);
            select.appendChild(option);
        });
    }

    populateCountrySelect() {
        const select = document.getElementById('country-select');
        this.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            select.appendChild(option);
        });
    }

    populateVerificationHistory(verifications) {
        const tbody = document.getElementById('verification-history');
        tbody.innerHTML = '';

        if (verifications.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No verifications yet</td></tr>';
            return;
        }

        verifications.forEach(v => {
            const row = document.createElement('tr');
            const statusBadge = this.getStatusBadge(v.status);
            const date = new Date(v.created_at).toLocaleDateString();

            row.innerHTML = `
                <td>${v.service}</td>
                <td>${v.country}</td>
                <td><code>${v.phone_number}</code></td>
                <td>${statusBadge}</td>
                <td>$${v.cost.toFixed(2)}</td>
                <td>${date}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="verificationManager.viewDetails('${v.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    getStatusBadge(status) {
        const badges = {
            'pending': '<span class="badge bg-warning">Pending</span>',
            'completed': '<span class="badge bg-success">Completed</span>',
            'timeout': '<span class="badge bg-danger">Timeout</span>',
            'released': '<span class="badge bg-secondary">Released</span>'
        };
        return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    async updateCostEstimate() {
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;

        if (!service || !country) {
            document.getElementById('estimated-cost').textContent = '$0.00';
            return;
        }

        try {
            const response = await axios.get('/api/pricing/estimate', {
                params: {
                    service,
                    country,
                    tier: 'STANDARD',
                    quantity: 1
                }
            });

            const cost = response.data.total_cost;
            document.getElementById('estimated-cost').textContent = `$${cost.toFixed(2)}`;

            // Check balance
            const balanceText = document.getElementById('user-balance').textContent;
            const balance = parseFloat(balanceText.replace('$', ''));
            const insufficientAlert = document.getElementById('insufficient-balance-alert');

            if (balance < cost) {
                insufficientAlert.classList.remove('d-none');
                document.getElementById('purchase-btn').disabled = true;
            } else {
                insufficientAlert.classList.add('d-none');
                document.getElementById('purchase-btn').disabled = false;
            }
        } catch (error) {
            console.error('Failed to estimate cost:', error);
        }
    }

    async handleFormSubmit() {
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;
        const capability = document.querySelector('input[name="capability"]:checked').value;

        if (!service || !country) {
            this.showError('Please select a service and country');
            return;
        }

        // Show confirmation modal
        document.getElementById('confirm-service').textContent = service;
        document.getElementById('confirm-country').textContent = country;

        const costText = document.getElementById('estimated-cost').textContent;
        document.getElementById('confirm-cost').textContent = costText;

        const balanceText = document.getElementById('user-balance').textContent;
        const balance = parseFloat(balanceText.replace('$', ''));
        const cost = parseFloat(costText.replace('$', ''));
        document.getElementById('confirm-balance').textContent = `$${(balance - cost).toFixed(2)}`;

        const confirmModal = new bootstrap.Modal(document.getElementById('confirmation-modal'));
        confirmModal.show();
    }

    async confirmPurchase() {
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;
        const capability = document.querySelector('input[name="capability"]:checked').value;

        // Close confirmation modal
        bootstrap.Modal.getInstance(document.getElementById('confirmation-modal')).hide();

        // Show loading modal
        const loadingModal = new bootstrap.Modal(document.getElementById('loading-modal'));
        loadingModal.show();

        try {
            const response = await axios.post('/api/verification/request', {
                service,
                country,
                capability
            });

            this.currentVerification = response.data;
            loadingModal.hide();

            // Show verification result
            this.displayVerificationResult();

            // Start polling for SMS
            this.startPolling();

            // Start countdown
            this.startCountdown();

            // Hide form, show result
            document.getElementById('verification-form').parentElement.classList.add('d-none');
            document.getElementById('verification-result').classList.remove('d-none');
            document.getElementById('help-card').classList.add('d-none');

            this.showSuccess('Verification purchased successfully!');
        } catch (error) {
            loadingModal.hide();
            const message = error.response?.data?.detail || 'Failed to purchase verification';
            this.showError(message);
        }
    }

    displayVerificationResult() {
        const v = this.currentVerification;

        // Display phone number
        document.getElementById('phone-number').value = v.phone_number;

        // Generate QR code
        const qrContainer = document.getElementById('qr-code');
        qrContainer.innerHTML = '';
        new QRCode(qrContainer, {
            text: v.phone_number,
            width: 150,
            height: 150
        });
    }

    startPolling() {
        let pollCount = 0;
        const maxPolls = 600; // 20 minutes at 2-second intervals
        
        // Poll every 2 seconds
        this.pollingInterval = setInterval(async () => {
            pollCount++;
            
            try {
                const response = await axios.get(`/api/verification/${this.currentVerification.verification_id}`);
                const verification = response.data;

                if (verification.status === 'completed' && verification.sms_code) {
                    this.handleSMSReceived(verification);
                    clearInterval(this.pollingInterval);
                    return;
                }

                // Check if timeout reached
                if (pollCount >= maxPolls) {
                    clearInterval(this.pollingInterval);
                    this.handleTimeout();
                    return;
                }
            } catch (error) {
                console.error('Polling error:', error);
                // Continue polling even on error
            }
        }, 2000);
    }

    handleSMSReceived(verification) {
        // Hide waiting message
        document.getElementById('sms-waiting').classList.add('d-none');

        // Show received message
        document.getElementById('sms-received').classList.remove('d-none');

        // Display SMS code with animation
        const codeElement = document.getElementById('sms-code');
        codeElement.value = verification.sms_code;
        codeElement.style.animation = 'none';
        setTimeout(() => {
            codeElement.style.animation = 'slideIn 0.5s ease';
        }, 10);
        document.getElementById('sms-code-section').classList.remove('d-none');

        // Display full SMS text
        if (verification.sms_text) {
            document.getElementById('sms-text').value = verification.sms_text;
            document.getElementById('sms-text-section').classList.remove('d-none');
        }

        // Display receipt timestamp
        if (verification.sms_received_at) {
            const receivedTime = new Date(verification.sms_received_at).toLocaleTimeString();
            const timestampEl = document.createElement('small');
            timestampEl.className = 'text-muted d-block mt-2';
            timestampEl.textContent = `Received at: ${receivedTime}`;
            document.getElementById('sms-code-section').appendChild(timestampEl);
        }

        // Stop countdown
        clearInterval(this.countdownInterval);
        document.getElementById('countdown-bar').style.width = '100%';
        document.getElementById('countdown-text').textContent = 'SMS Received!';

        this.showSuccess('SMS received! Code is ready to use.');
    }

    startCountdown() {
        let timeRemaining = 1200; // 20 minutes in seconds

        this.countdownInterval = setInterval(() => {
            timeRemaining--;

            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;

            document.getElementById('countdown-text').textContent = timeString;

            const percentage = (timeRemaining / 1200) * 100;
            document.getElementById('countdown-bar').style.width = percentage + '%';

            if (timeRemaining <= 0) {
                clearInterval(this.countdownInterval);
                this.handleTimeout();
            }
        }, 1000);
    }

    handleTimeout() {
        // Hide waiting message
        document.getElementById('sms-waiting').classList.add('d-none');

        // Show timeout message
        document.getElementById('sms-timeout').classList.remove('d-none');

        // Stop polling
        clearInterval(this.pollingInterval);
        clearInterval(this.countdownInterval);

        // Update countdown bar to show timeout
        document.getElementById('countdown-bar').style.width = '0%';
        document.getElementById('countdown-text').textContent = '0:00';

        // Show error with retry option
        const errorModal = document.getElementById('error-modal');
        document.getElementById('error-message').innerHTML = `
            <strong>SMS Timeout!</strong><br>
            No SMS received within 20 minutes.<br><br>
            <small>This can happen if:</small>
            <ul style="margin-top: 0.5rem; margin-bottom: 0;">
                <li>The service is experiencing delays</li>
                <li>The phone number is invalid</li>
                <li>The SMS was blocked</li>
            </ul>
            <br>
            <a href="/billing" class="alert-link">Add more credits</a> to try again with a different number.
        `;
        const modal = new bootstrap.Modal(errorModal);
        modal.show();
    }

    async releaseNumber() {
        if (!this.currentVerification) return;

        if (!confirm('Are you sure you want to release this number?')) {
            return;
        }

        try {
            await axios.post(`/api/verification/${this.currentVerification.verification_id}/release`);
            this.showSuccess('Number released successfully');
            this.resetForm();
        } catch (error) {
            const message = error.response?.data?.detail || 'Failed to release number';
            this.showError(message);
        }
    }

    resetForm() {
        // Clear form
        document.getElementById('verification-form').reset();
        this.currentVerification = null;

        // Clear intervals
        clearInterval(this.pollingInterval);
        clearInterval(this.countdownInterval);

        // Show form, hide result
        document.getElementById('verification-form').parentElement.classList.remove('d-none');
        document.getElementById('verification-result').classList.add('d-none');
        document.getElementById('help-card').classList.remove('d-none');

        // Reset SMS sections
        document.getElementById('sms-waiting').classList.remove('d-none');
        document.getElementById('sms-received').classList.add('d-none');
        document.getElementById('sms-timeout').classList.add('d-none');
        document.getElementById('sms-code-section').classList.add('d-none');
        document.getElementById('sms-text-section').classList.add('d-none');

        // Reload history
        this.loadVerificationHistory();
    }

    async viewDetails(verificationId) {
        try {
            const response = await axios.get(`/api/verification/${verificationId}`);
            const v = response.data;

            alert(`
Service: ${v.service}
Country: ${v.country}
Phone: ${v.phone_number}
Status: ${v.status}
Cost: $${v.cost}
${v.sms_code ? `SMS Code: ${v.sms_code}` : ''}
            `);
        } catch (error) {
            this.showError('Failed to load verification details');
        }
    }

    copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        const text = element.value;

        navigator.clipboard.writeText(text).then(() => {
            // Show success toast
            this.showSuccess('Copied to clipboard!');
            
            // Visual feedback on button
            const button = event.target.closest('button');
            if (button) {
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-check"></i> Copied!';
                button.disabled = true;
                
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.disabled = false;
                }, 2000);
            }
        }).catch(() => {
            // Fallback for older browsers
            try {
                element.select();
                document.execCommand('copy');
                this.showSuccess('Copied to clipboard!');
            } catch (err) {
                this.showError('Failed to copy to clipboard');
            }
        });
    }

    showError(message) {
        document.getElementById('error-message').textContent = message;
        const modal = new bootstrap.Modal(document.getElementById('error-modal'));
        modal.show();
    }

    showSuccess(message) {
        document.getElementById('toast-message').textContent = message;
        const toast = new bootstrap.Toast(document.getElementById('success-toast'));
        toast.show();
    }
}

// Initialize on page load
let verificationManager;
document.addEventListener('DOMContentLoaded', () => {
    verificationManager = new VerificationManager();
});
