/**
 * API Key Management JavaScript
 * Handles API key generation, listing, revoking, and copying
 */

class APIKeyManager {
    constructor() {
        this.apiKeys = [];
        this.init();
    }

    async init() {
        await this.loadAPIKeys();
        this.render();
        this.setupEventListeners();
    }

    async loadAPIKeys() {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/keys/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 402) {
                // User doesn't have API access
                this.showUpgradePrompt();
                return;
            }

            if (response.ok) {
                this.apiKeys = await response.json();
            }
        } catch (error) {
            console.error('Failed to load API keys:', error);
        }
    }

    render() {
        const container = document.getElementById('api-keys-list');
        if (!container) return;

        if (this.apiKeys.length === 0) {
            container.innerHTML = this.renderEmptyState();
        } else {
            container.innerHTML = this.apiKeys.map(key => this.renderKeyCard(key)).join('');
        }

        this.renderLimitInfo();
    }

    renderEmptyState() {
        return `
      <div class="empty-state">
        <i class="ph ph-key"></i>
        <h3>No API Keys Yet</h3>
        <p>Generate your first API key to start using the API</p>
      </div>
    `;
    }

    renderKeyCard(key) {
        const createdDate = new Date(key.created_at).toLocaleDateString();
        const lastUsed = key.last_used ? new Date(key.last_used).toLocaleString() : 'Never';

        return `
      <div class="api-key-card" data-key-id="${key.id}">
        <div class="api-key-info">
          <div>
            <div class="api-key-name">${key.name}</div>
            <div class="api-key-preview">${key.key_preview}</div>
          </div>
          <div class="api-key-actions">
            <button class="api-key-btn" onclick="apiKeyManager.rotateKey('${key.id}')">
              <i class="ph ph-arrows-clockwise"></i> Rotate
            </button>
            <button class="api-key-btn danger" onclick="apiKeyManager.confirmRevoke('${key.id}')">
              <i class="ph ph-trash"></i> Revoke
            </button>
          </div>
        </div>
        <div class="api-key-stats">
          <div class="api-key-stat">
            <i class="ph ph-calendar"></i>
            Created: ${createdDate}
          </div>
          <div class="api-key-stat">
            <i class="ph ph-clock"></i>
            Last used: ${lastUsed}
          </div>
          <div class="api-key-stat">
            <i class="ph ph-chart-bar"></i>
            ${key.request_count || 0} requests
          </div>
        </div>
      </div>
    `;
    }

    renderLimitInfo() {
        const limitContainer = document.getElementById('api-key-limit-info');
        if (!limitContainer) return;

        // Get tier info from tierManager
        const tier = window.tierManager?.currentTier || 'freemium';
        const limits = {
            'freemium': { max: 0, display: 'No API access' },
            'starter': { max: 5, display: '5 keys max' },
            'turbo': { max: -1, display: 'Unlimited' }
        };

        const tierLimit = limits[tier];
        const used = this.apiKeys.length;
        const maxDisplay = tierLimit.max === -1 ? '∞' : tierLimit.max;

        limitContainer.innerHTML = `
      <div class="tier-limit-info">
        <div class="tier-limit-text">
          <strong>Your Plan:</strong> ${tier.charAt(0).toUpperCase() + tier.slice(1)} 
          (${tierLimit.display})
        </div>
        <div class="tier-limit-progress">
          ${used} / ${maxDisplay} keys used
        </div>
      </div>
    `;
    }

    setupEventListeners() {
        const generateBtn = document.getElementById('generate-api-key-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.showGenerateModal());
        }
    }

    showGenerateModal() {
        const modal = document.createElement('div');
        modal.className = 'upgrade-modal-overlay active';
        modal.id = 'generate-key-modal';
        modal.innerHTML = `
      <div class="upgrade-modal">
        <div class="upgrade-modal-header">
          <h2>Generate New API Key</h2>
          <p>Give your API key a descriptive name</p>
        </div>

        <div style="margin: 25px 0;">
          <label for="api-key-name" style="display: block; margin-bottom: 8px; font-weight: 600;">
            Key Name
          </label>
          <input 
            type="text" 
            id="api-key-name" 
            placeholder="e.g., Production Server" 
            style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px;"
          >
        </div>

        <div class="upgrade-cta-buttons">
          <button class="btn-upgrade btn-upgrade-secondary" onclick="apiKeyManager.closeModal()">
            Cancel
          </button>
          <button class="btn-upgrade btn-upgrade-primary" onclick="apiKeyManager.generateKey()">
            Generate Key
          </button>
        </div>
      </div>
    `;

        document.body.appendChild(modal);
    }

    async generateKey() {
        const nameInput = document.getElementById('api-key-name');
        const name = nameInput?.value.trim() || 'Unnamed Key';

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/keys/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name })
            });

            if (response.status === 402) {
                this.closeModal();
                tierManager.showUpgradeModal({
                    required_tier: 'starter',
                    feature: 'API Keys',
                    message: 'API key access requires Starter tier or higher'
                });
                return;
            }

            if (response.status === 429) {
                alert('API key limit reached. Upgrade to Turbo for unlimited keys.');
                this.closeModal();
                return;
            }

            if (response.ok) {
                const keyData = await response.json();
                this.showNewKeyModal(keyData);
                await this.loadAPIKeys();
                this.render();
            } else {
                const error = await response.json();
                alert(error.detail || 'Failed to generate API key');
            }
        } catch (error) {
            console.error('Failed to generate key:', error);
            alert('Failed to generate API key. Please try again.');
        }
    }

    showNewKeyModal(keyData) {
        this.closeModal();

        const modal = document.createElement('div');
        modal.className = 'upgrade-modal-overlay active';
        modal.id = 'new-key-modal';
        modal.innerHTML = `
      <div class="upgrade-modal">
        <div class="upgrade-modal-header">
          <i class="ph ph-check-circle feature-locked-icon" style="color: #10b981;"></i>
          <h2>API Key Generated!</h2>
          <p style="color: #ef4444; font-weight: 600;">
            ⚠️ Copy this key now - it won't be shown again!
          </p>
        </div>

        <div style="margin: 25px 0; background: #f9fafb; padding: 20px; border-radius: 8px;">
          <div style="margin-bottom: 10px; font-weight: 600; color: #374151;">
            ${keyData.name}
          </div>
          <div style="display: flex; gap: 10px; align-items: center;">
            <input 
              type="text" 
              id="new-api-key-value" 
              value="${keyData.key}" 
              readonly 
              style="flex: 1; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-family: monospace; font-size: 13px;"
            >
            <button 
              class="api-key-btn" 
              onclick="apiKeyManager.copyNewKey()" 
              style="padding: 12px 20px;"
            >
              <i class="ph ph-copy"></i> Copy
            </button>
          </div>
        </div>

        <div style="background: #eff6ff; border: 1px solid #dbeafe; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
          <div style="color: #1e40af; font-size: 14px;">
            <strong>Next Steps:</strong>
            <ol style="margin: 10px 0 0 20px; line-height: 1.8;">
              <li>Copy your API key and store it securely</li>
              <li>Use it in your Authorization header: <code>Bearer ${keyData.key_preview}</code></li>
              <li>See our <a href="/docs" style="color: #2563eb;">API documentation</a> for examples</li>
            </ol>
          </div>
        </div>

        <button class="btn-upgrade btn-upgrade-primary" onclick="apiKeyManager.closeModal()" style="width: 100%;">
          I've Copied My Key
        </button>
      </div>
    `;

        document.body.appendChild(modal);
    }

    copyNewKey() {
        const input = document.getElementById('new-api-key-value');
        if (input) {
            input.select();
            document.execCommand('copy');

            const btn = event.target.closest('button');
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<i class="ph ph-check"></i> Copied!';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
            }, 2000);
        }
    }

    confirmRevoke(keyId) {
        if (confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
            this.revokeKey(keyId);
        }
    }

    async revokeKey(keyId) {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/keys/${keyId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                await this.loadAPIKeys();
                this.render();
                this.showToast('API key revoked successfully', 'success');
            } else {
                alert('Failed to revoke API key');
            }
        } catch (error) {
            console.error('Failed to revoke key:', error);
            alert('Failed to revoke API key. Please try again.');
        }
    }

    async rotateKey(keyId) {
        if (!confirm('This will generate a new key and revoke the old one. Continue?')) {
            return;
        }

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/keys/${keyId}/rotate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const newKeyData = await response.json();
                this.showNewKeyModal(newKeyData);
                await this.loadAPIKeys();
                this.render();
            } else {
                alert('Failed to rotate API key');
            }
        } catch (error) {
            console.error('Failed to rotate key:', error);
            alert('Failed to rotate API key. Please try again.');
        }
    }

    closeModal() {
        const modals = document.querySelectorAll('.upgrade-modal-overlay');
        modals.forEach(modal => modal.remove());
    }

    showUpgradePrompt() {
        tierManager?.showUpgradeModal({
            required_tier: 'starter',
            feature: 'API Keys',
            message: 'API key access is available in Starter tier and above'
        });
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: ${type === 'success' ? '#10b981' : '#667eea'};
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10001;
      animation: slideUp 0.3s ease;
    `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize API key manager on API keys page
let apiKeyManager;
if (window.location.href.includes('api-keys') || document.getElementById('api-keys-list')) {
    document.addEventListener('DOMContentLoaded', () => {
        apiKeyManager = new APIKeyManager();
    });
}

// Export for use in other scripts
window.APIKeyManager = APIKeyManager;
window.apiKeyManager = apiKeyManager;
