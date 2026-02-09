/**
 * Auto-Copy SMS Code Module
 * Automatically copy SMS codes to clipboard when received
 */

class AutoCopySMS {
    constructor() {
        this.enabled = this.loadPreference();
        this.init();
    }

    init() {
        this.setupToggle();
        this.observeSMSCode();
    }

    loadPreference() {
        return localStorage.getItem('auto_copy_sms') === 'true';
    }

    savePreference(enabled) {
        localStorage.setItem('auto_copy_sms', enabled.toString());
    }

    setupToggle() {
        const toggle = document.getElementById('auto-copy-toggle');
        if (!toggle) return;

        toggle.checked = this.enabled;
        toggle.addEventListener('change', (e) => {
            this.enabled = e.target.checked;
            this.savePreference(this.enabled);
            this.showToast(
                this.enabled ? 'Auto-copy enabled' : 'Auto-copy disabled',
                'info'
            );
        });
    }

    observeSMSCode() {
        const codeElement = document.getElementById('sms-code');
        if (!codeElement) return;

        // Watch for changes to SMS code input
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                    const code = codeElement.value;
                    if (code && this.enabled) {
                        this.copyCode(code);
                    }
                }
            });
        });

        observer.observe(codeElement, {
            attributes: true,
            attributeFilter: ['value']
        });

        // Also watch for input events
        codeElement.addEventListener('input', () => {
            const code = codeElement.value;
            if (code && this.enabled) {
                this.copyCode(code);
            }
        });
    }

    async copyCode(code) {
        try {
            await navigator.clipboard.writeText(code);
            this.showToast('✓ SMS code copied to clipboard!', 'success');
            this.flashCopyIndicator();
        } catch (error) {
            console.error('Auto-copy failed:', error);
        }
    }

    flashCopyIndicator() {
        const indicator = document.getElementById('copy-indicator');
        if (!indicator) return;

        indicator.classList.remove('d-none');
        indicator.classList.add('animate__animated', 'animate__fadeIn');
        
        setTimeout(() => {
            indicator.classList.add('animate__fadeOut');
            setTimeout(() => {
                indicator.classList.add('d-none');
                indicator.classList.remove('animate__animated', 'animate__fadeIn', 'animate__fadeOut');
            }, 500);
        }, 2000);
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

// Enhanced copy button with visual feedback
function enhancedCopyToClipboard(elementId, buttonId) {
    const element = document.getElementById(elementId);
    const button = document.getElementById(buttonId);
    
    if (!element || !button) return;

    const text = element.value;

    navigator.clipboard.writeText(text).then(() => {
        // Update button
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-success');
        button.disabled = true;

        // Reset after 2 seconds
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-primary');
            button.disabled = false;
        }, 2000);

        // Show toast
        const toast = document.createElement('div');
        toast.className = 'alert alert-success position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '9999';
        toast.innerHTML = '<i class="fas fa-check-circle"></i> Copied to clipboard!';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }).catch(() => {
        // Fallback
        element.select();
        document.execCommand('copy');
    });
}

// Initialize
let autoCopySMS;
document.addEventListener('DOMContentLoaded', () => {
    autoCopySMS = new AutoCopySMS();
});
