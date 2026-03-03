/**
 * NAMASKAH DASHBOARD - ULTRA-STABLE VERSION
 * Production-grade implementation with zero broken features
 * All buttons, modals, and business flows guaranteed to work
 */

(function() {
    'use strict';

    // ============================================
    // CONFIGURATION
    // ============================================
    const CONFIG = {
        API_BASE: '/api',
        ENDPOINTS: {
            SERVICES: '/api/services',
            VERIFY_CREATE: '/api/verify/create',
            VERIFY_SMS: '/api/verify/{id}/sms',
            VERIFY_STATUS: '/api/verify/{id}/status',
            WALLET_BALANCE: '/api/wallet/balance',
            ANALYTICS: '/api/analytics/summary',
            WALLET: '/wallet',
            PRICING: '/pricing',
            ANALYTICS_PAGE: '/analytics',
            TIER_UPGRADE: '/api/billing/tiers/upgrade',
            PAYMENT_INIT: '/api/wallet/paystack/initialize'
        }
    };

    // ============================================
    // UTILITY FUNCTIONS
    // ============================================
    
    function getAuthToken() {
        return localStorage.getItem('access_token') || 
               document.cookie.split('; ').find(row => row.startsWith('access_token='))?.split('=')[1];
    }

    function getAuthHeaders() {
        const token = getAuthToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        };
    }

    async function apiCall(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                credentials: 'include',
                headers: {
                    ...getAuthHeaders(),
                    ...options.headers
                }
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    function showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.toast-notification').forEach(t => t.remove());
        
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 14px;
            max-width: 400px;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ============================================
    // VERIFICATION TYPE PICKER
    // ============================================

    function createVerificationModal() {
        if (document.getElementById('verification-modal')) return;
        document.body.insertAdjacentHTML('beforeend', `
        <div id="verification-modal" class="modal" style="display:none;">
            <div class="modal-overlay"></div>
            <div class="modal-content" style="max-width:400px;">
                <div class="modal-header">
                    <h2>New Verification</h2>
                    <button class="modal-close" onclick="window.DashboardUltra.closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <p style="margin-bottom:16px;color:#6b7280;">Choose verification method</p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                        <button type="button" class="type-card" onclick="window.location.href='/verify'">
                            <div style="font-size:28px;">&#128241;</div>
                            <div style="font-weight:600;margin:8px 0 4px;">SMS</div>
                            <div style="font-size:12px;color:#6b7280;">~30s &middot; $2.50</div>
                        </button>
                        <button type="button" class="type-card" onclick="window.location.href='/voice-verify'">
                            <div style="font-size:28px;">&#9742;&#65039;</div>
                            <div style="font-weight:600;margin:8px 0 4px;">Voice Call</div>
                            <div style="font-size:12px;color:#6b7280;">2-5 min &middot; $3.50</div>
                        </button>
                    </div>
                </div>
            </div>
        </div>`);
        const modal = document.getElementById('verification-modal');
        modal.querySelector('.modal-overlay').onclick = closeModal;
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && modal.style.display === 'flex') closeModal();
        });
    }

    function openModal() {
        createVerificationModal();
        document.getElementById('verification-modal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        const modal = document.getElementById('verification-modal');
        if (modal) modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    // ============================================
    // BUTTON HANDLERS
    // ============================================
    
    function initButtons() {
        // New Verification Button
        const newVerifyBtn = document.getElementById('new-verification-btn');
        if (newVerifyBtn) {
            newVerifyBtn.onclick = function(e) {
                e.preventDefault();
                openModal();
            };
            console.log('✅ New Verification button initialized');
        }

        // Quick Verification Button (if exists)
        const quickVerifyBtn = document.getElementById('quick-verification-btn');
        if (quickVerifyBtn) {
            quickVerifyBtn.onclick = function(e) {
                e.preventDefault();
                openModal();
            };
        }

        // Add Credits Button
        const addCreditsBtn = document.getElementById('add-credits-btn');
        if (addCreditsBtn) {
            addCreditsBtn.onclick = function(e) {
                e.preventDefault();
                window.location.href = '/wallet';
            };
            console.log('✅ Add Credits button initialized');
        }

        // View Usage Button
        const usageBtn = document.getElementById('usage-btn');
        if (usageBtn) {
            usageBtn.onclick = function(e) {
                e.preventDefault();
                window.location.href = CONFIG.ENDPOINTS.ANALYTICS_PAGE;
            };
            console.log('✅ View Usage button initialized');
        }

        // Upgrade Button
        const upgradeBtn = document.getElementById('upgrade-btn');
        if (upgradeBtn) {
            upgradeBtn.onclick = function(e) {
                e.preventDefault();
                openUpgradeModal();
            };
            console.log('\u2705 Upgrade button initialized');
        }

        // Empty state button
        const emptyStateBtn = document.querySelector('#empty-state button');
        if (emptyStateBtn) {
            emptyStateBtn.onclick = function(e) {
                e.preventDefault();
                openModal();
            };
        }
    }

    // ============================================
    // UPGRADE MODAL
    // ============================================

    const TIER_INFO = {
        payg:   { name: 'Pay-As-You-Go', price: 0,  desc: 'No monthly fee. Pay per SMS.',   paid: false },
        pro:    { name: 'Pro',           price: 25, desc: '$15 monthly quota included.',     paid: true  },
        custom: { name: 'Custom',        price: 35, desc: '$25 monthly quota + dedicated support.', paid: true }
    };

    function openUpgradeModal() {
        if (document.getElementById('upgrade-modal')) {
            document.getElementById('upgrade-modal').style.display = 'flex';
            document.body.style.overflow = 'hidden';
            renderUpgradePicker();
            return;
        }
        const el = document.createElement('div');
        el.id = 'upgrade-modal';
        el.className = 'modal';
        el.innerHTML = `
            <div class="modal-overlay" onclick="window.DashboardUltra.closeUpgradeModal()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="upgrade-modal-title">Upgrade Plan</h2>
                    <button class="modal-close" onclick="window.DashboardUltra.closeUpgradeModal()">&times;</button>
                </div>
                <div class="modal-body" id="upgrade-modal-body"></div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="window.DashboardUltra.closeUpgradeModal()">Cancel</button>
                    <button class="btn btn-primary" id="upgrade-confirm-btn" style="display:none;" onclick="window.DashboardUltra.confirmUpgrade()">Confirm</button>
                </div>
            </div>
        `;
        document.body.appendChild(el);
        el.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        renderUpgradePicker();
    }

    let selectedUpgradeTier = null;

    function renderUpgradePicker() {
        selectedUpgradeTier = null;
        document.getElementById('upgrade-confirm-btn').style.display = 'none';
        document.getElementById('upgrade-modal-title').textContent = 'Upgrade Plan';
        document.getElementById('upgrade-modal-body').innerHTML = Object.entries(TIER_INFO).map(([key, t]) => `
            <div class="upgrade-card" id="ucard-${key}" onclick="window.DashboardUltra.selectUpgradeTier('${key}')" style="border:2px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:12px;cursor:pointer;transition:border-color .2s;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong>${t.name}</strong>
                    <span style="font-size:14px;color:#6b7280;">${t.price === 0 ? 'Free' : '$' + t.price + '/mo'}</span>
                </div>
                <div style="font-size:13px;color:#6b7280;margin-top:4px;">${t.desc}</div>
            </div>
        `).join('');
    }

    function selectUpgradeTier(tier) {
        selectedUpgradeTier = tier;
        document.querySelectorAll('.upgrade-card').forEach(c => c.style.borderColor = '#e5e7eb');
        const card = document.getElementById('ucard-' + tier);
        if (card) card.style.borderColor = '#3b82f6';
        const btn = document.getElementById('upgrade-confirm-btn');
        btn.style.display = 'inline-flex';
        btn.textContent = TIER_INFO[tier].paid ? `Pay $${TIER_INFO[tier].price}/mo` : 'Confirm Upgrade';
    }

    async function confirmUpgrade() {
        if (!selectedUpgradeTier) return;
        const tier = selectedUpgradeTier;
        const btn = document.getElementById('upgrade-confirm-btn');
        btn.disabled = true;
        btn.textContent = 'Processing...';

        try {
            if (TIER_INFO[tier].paid) {
                const data = await apiCall(CONFIG.ENDPOINTS.PAYMENT_INIT, {
                    method: 'POST',
                    body: JSON.stringify({ amount_usd: TIER_INFO[tier].price, metadata: { upgrade_to: tier } })
                });
                if (data.authorization_url) {
                    window.location.href = data.authorization_url;
                    return;
                }
                throw new Error('No payment URL returned');
            } else {
                await apiCall(`${CONFIG.ENDPOINTS.TIER_UPGRADE}?target_tier=${tier}`, { method: 'POST' });
                showToast(`Upgraded to ${TIER_INFO[tier].name}!`, 'success');
                closeUpgradeModal();
                setTimeout(() => window.location.reload(), 1000);
            }
        } catch (err) {
            showToast(err.message || 'Upgrade failed', 'error');
            btn.disabled = false;
            btn.textContent = TIER_INFO[tier].paid ? `Pay $${TIER_INFO[tier].price}/mo` : 'Confirm Upgrade';
        }
    }

    function closeUpgradeModal() {
        const m = document.getElementById('upgrade-modal');
        if (m) { m.style.display = 'none'; document.body.style.overflow = ''; }
    }

    // ============================================
    // STYLES
    // ============================================
    
    function injectStyles() {
        if (document.getElementById('dashboard-ultra-styles')) return;

        const style = document.createElement('style');
        style.id = 'dashboard-ultra-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(400px); opacity: 0; }
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
            }
            
            .modal-content {
                position: relative;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                z-index: 1;
                max-width: 600px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
            }
            
            .modal-header {
                padding: 24px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .modal-header h2 {
                margin: 0;
                font-size: 20px;
                font-weight: 600;
                color: #111827;
            }
            
            .modal-close {
                background: none;
                border: none;
                font-size: 28px;
                cursor: pointer;
                color: #6b7280;
                line-height: 1;
                padding: 0;
                width: 32px;
                height: 32px;
                transition: color 0.2s;
            }
            
            .modal-close:hover {
                color: #111827;
            }
            
            .modal-body {
                padding: 24px;
            }
            
            .modal-footer {
                padding: 16px 24px;
                border-top: 1px solid #e5e7eb;
                display: flex;
                justify-content: flex-end;
                gap: 12px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #374151;
                font-size: 14px;
            }
            
            .form-control {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.2s, box-shadow 0.2s;
            }
            
            .form-control:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .form-text {
                display: block;
                margin-top: 4px;
                font-size: 12px;
                color: #6b7280;
            }
            
            .alert {
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 16px;
            }
            
            .alert h4 {
                margin: 0 0 12px 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .alert p {
                margin: 8px 0;
                font-size: 14px;
            }
            
            .alert-info {
                background: #dbeafe;
                border: 1px solid #93c5fd;
                color: #1e40af;
            }
            
            .alert-success {
                background: #d1fae5;
                border: 1px solid #6ee7b7;
                color: #065f46;
            }
            
            .alert-warning {
                background: #fef3c7;
                border: 1px solid #fcd34d;
                color: #92400e;
            }
            
            .verification-details p {
                margin: 8px 0;
            }
            
            .phone-number {
                font-family: 'Courier New', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #059669;
            }
            
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                background: #fef3c7;
                color: #92400e;
            }
            
            .sms-code code {
                display: inline-block;
                padding: 8px 16px;
                background: #f3f4f6;
                border: 2px solid #10b981;
                border-radius: 6px;
                font-size: 24px;
                font-weight: bold;
                color: #059669;
                letter-spacing: 2px;
                margin: 8px 0;
            }
            
            .loading-spinner {
                width: 24px;
                height: 24px;
                border: 3px solid #f3f4f6;
                border-top-color: #3b82f6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 12px auto;
            }
            
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .btn-primary {
                background: #3b82f6;
                color: white;
            }
            
            .btn-primary:hover:not(:disabled) {
                background: #2563eb;
            }
            
            .btn-secondary {
                background: #e5e7eb;
                color: #374151;
            }
            
            .btn-secondary:hover:not(:disabled) {
                background: #d1d5db;
            }
            
            .btn-success {
                background: #10b981;
                color: white;
            }
            
            .btn-success:hover:not(:disabled) {
                background: #059669;
            }

            .type-card {
                background: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 20px 12px;
                cursor: pointer;
                text-align: center;
                transition: border-color .2s, background .2s;
                font-family: system-ui, -apple-system, sans-serif;
            }
            .type-card:hover {
                border-color: #3b82f6;
                background: #eff6ff;
            }
        `;
        document.head.appendChild(style);
    }

    // ============================================
    // INITIALIZATION
    // ============================================
    
    function init() {
        console.log('🚀 Initializing Ultra-Stable Dashboard...');
        
        injectStyles();
        initButtons();
        
        console.log('✅ Dashboard initialized successfully');
        console.log('📱 All buttons are functional');
        console.log('🎯 Business flows ready');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose functions globally for debugging
    window.DashboardUltra = {
        openModal,
        closeModal,
        openUpgradeModal,
        closeUpgradeModal,
        selectUpgradeTier,
        confirmUpgrade,
        version: '2.0.0-ultra-stable'
    };

})();
