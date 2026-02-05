/**
 * SMS Display Module
 * Handles real-time SMS display and updates
 */

class SMSDisplay {
    constructor() {
        this.pollingInterval = null;
        this.countdownInterval = null;
        this.maxPolls = 600; // 20 minutes at 2-second intervals
        this.pollCount = 0;
    }

    /**
     * Start polling for SMS updates
     */
    startPolling(verificationId) {
        this.pollCount = 0;
        
        this.pollingInterval = setInterval(async () => {
            this.pollCount++;
            
            try {
                const response = await axios.get(`/api/verification/${verificationId}`);
                const verification = response.data;

                // Check if SMS received
                if (verification.status === 'completed' && verification.sms_code) {
                    this.displaySMS(verification);
                    this.stopPolling();
                    return;
                }

                // Check if timeout reached
                if (this.pollCount >= this.maxPolls) {
                    this.handleTimeout();
                    this.stopPolling();
                    return;
                }
            } catch (error) {
                console.error('Polling error:', error);
                // Continue polling even on error
            }
        }, 2000);
    }

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Display SMS code and text
     */
    displaySMS(verification) {
        // Hide waiting message
        const waitingEl = document.getElementById('sms-waiting');
        if (waitingEl) waitingEl.classList.add('d-none');

        // Show received message
        const receivedEl = document.getElementById('sms-received');
        if (receivedEl) receivedEl.classList.remove('d-none');

        // Display SMS code with animation
        const codeElement = document.getElementById('sms-code');
        if (codeElement) {
            codeElement.value = verification.sms_code;
            codeElement.style.animation = 'none';
            setTimeout(() => {
                codeElement.style.animation = 'slideIn 0.5s ease';
            }, 10);
        }

        // Show SMS code section
        const codeSectionEl = document.getElementById('sms-code-section');
        if (codeSectionEl) codeSectionEl.classList.remove('d-none');

        // Display full SMS text
        if (verification.sms_text) {
            const textElement = document.getElementById('sms-text');
            if (textElement) {
                textElement.value = verification.sms_text;
            }
            const textSectionEl = document.getElementById('sms-text-section');
            if (textSectionEl) textSectionEl.classList.remove('d-none');
        }

        // Display receipt timestamp
        if (verification.sms_received_at) {
            this.displayTimestamp(verification.sms_received_at);
        }

        // Update countdown
        this.updateCountdownToComplete();
    }

    /**
     * Display receipt timestamp
     */
    displayTimestamp(timestamp) {
        const receivedTime = new Date(timestamp).toLocaleTimeString();
        const codeSectionEl = document.getElementById('sms-code-section');
        
        if (codeSectionEl) {
            // Remove existing timestamp if any
            const existingTimestamp = codeSectionEl.querySelector('.sms-timestamp');
            if (existingTimestamp) {
                existingTimestamp.remove();
            }

            // Add new timestamp
            const timestampEl = document.createElement('small');
            timestampEl.className = 'text-muted d-block mt-2 sms-timestamp';
            timestampEl.textContent = `Received at: ${receivedTime}`;
            codeSectionEl.appendChild(timestampEl);
        }
    }

    /**
     * Update countdown to show completion
     */
    updateCountdownToComplete() {
        const barEl = document.getElementById('countdown-bar');
        const textEl = document.getElementById('countdown-text');
        
        if (barEl) barEl.style.width = '100%';
        if (textEl) textEl.textContent = 'SMS Received!';
        
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
    }

    /**
     * Handle SMS timeout
     */
    handleTimeout() {
        // Hide waiting message
        const waitingEl = document.getElementById('sms-waiting');
        if (waitingEl) waitingEl.classList.add('d-none');

        // Show timeout message
        const timeoutEl = document.getElementById('sms-timeout');
        if (timeoutEl) timeoutEl.classList.remove('d-none');

        // Update countdown bar
        const barEl = document.getElementById('countdown-bar');
        const textEl = document.getElementById('countdown-text');
        if (barEl) barEl.style.width = '0%';
        if (textEl) textEl.textContent = '0:00';

        // Show error modal with helpful message
        this.showTimeoutError();
    }

    /**
     * Show timeout error with helpful information
     */
    showTimeoutError() {
        const errorModal = document.getElementById('error-modal');
        if (!errorModal) return;

        const errorMessageEl = document.getElementById('error-message');
        if (errorMessageEl) {
            errorMessageEl.innerHTML = `
                <strong>SMS Timeout!</strong><br>
                No SMS received within 20 minutes.<br><br>
                <small style="color: #666;">This can happen if:</small>
                <ul style="margin-top: 0.5rem; margin-bottom: 0.5rem; padding-left: 1.5rem;">
                    <li>The service is experiencing delays</li>
                    <li>The phone number is invalid</li>
                    <li>The SMS was blocked by carrier</li>
                </ul>
                <br>
                <a href="/billing" class="alert-link">Add more credits</a> to try again with a different number.
            `;
        }

        const modal = new bootstrap.Modal(errorModal);
        modal.show();
    }

    /**
     * Start countdown timer
     */
    startCountdown() {
        let timeRemaining = 1200; // 20 minutes in seconds

        this.countdownInterval = setInterval(() => {
            timeRemaining--;

            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;

            const textEl = document.getElementById('countdown-text');
            if (textEl) textEl.textContent = timeString;

            const percentage = (timeRemaining / 1200) * 100;
            const barEl = document.getElementById('countdown-bar');
            if (barEl) barEl.style.width = percentage + '%';

            if (timeRemaining <= 0) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
            }
        }, 1000);
    }

    /**
     * Stop countdown timer
     */
    stopCountdown() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
    }

    /**
     * Reset display
     */
    reset() {
        this.stopPolling();
        this.stopCountdown();

        // Reset all display elements
        const elements = [
            'sms-waiting',
            'sms-received',
            'sms-timeout',
            'sms-code-section',
            'sms-text-section'
        ];

        elements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (id === 'sms-waiting') {
                    el.classList.remove('d-none');
                } else {
                    el.classList.add('d-none');
                }
            }
        });

        // Reset countdown
        const barEl = document.getElementById('countdown-bar');
        const textEl = document.getElementById('countdown-text');
        if (barEl) barEl.style.width = '100%';
        if (textEl) textEl.textContent = '20:00';
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SMSDisplay;
}
