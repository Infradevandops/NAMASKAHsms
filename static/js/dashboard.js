/**
 * Namaskah Dashboard - Refactored Main Entry Point
 * Uses modular architecture with StateManager, API layer, and event bus
 */

import { stateManager } from './modules/state.js';
import { api } from './modules/api.js';
import { handleError, logError } from './modules/errors.js';
import { validateVerification } from './modules/validation.js';
import { showToast, hideModals, escapeHtml, formatDate, updateBalanceDisplay, showLoading, hideLoading } from './modules/ui.js';
import { cache } from './utils/cache.js';
import { eventBus, events } from './utils/events.js';

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);

/**
 * Initialize dashboard
 * @returns {void}
 */
function init() {
  setupEventListeners();
  setupOfflineDetection();
  hideModals();
  setupViewSwitching();

  // Load recent activity
  loadRecentActivity();

  // Load user data with error handling
  loadUserData().catch(err => {
    console.error('Failed to load user data:', err);
    showToast('Could not load user profile. Using defaults.', 'warning');
  });

  loadBalance().catch(err => {
    console.error('Failed to load balance:', err);
    showToast('Could not load balance. Please refresh.', 'warning');
  });
}

/**
 * Setup event listeners
 * @returns {void}
 */
function setupEventListeners() {
  // Sidebar toggle
  const sidebarToggle = document.getElementById('sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
  }

  // User menu
  const userAvatarBtn = document.getElementById('user-avatar-btn');
  if (userAvatarBtn) {
    userAvatarBtn.addEventListener('click', toggleUserDropdown);
  }

  // Close dropdown when clicking outside
  document.addEventListener('click', function (e) {
    const dropdown = document.getElementById('user-dropdown');
    const avatarBtn = document.getElementById('user-avatar-btn');
    if (dropdown && !dropdown.contains(e.target) && !avatarBtn.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });

  // Logout buttons
  document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
  document.getElementById('dropdown-logout')?.addEventListener('click', handleLogout);

  // Verification modal
  document.getElementById('new-verification-btn')?.addEventListener('click', openVerificationModal);
  document.getElementById('quick-verification-btn')?.addEventListener('click', openVerificationModal);
  document.getElementById('verification-close-btn')?.addEventListener('click', closeVerificationModal);
  document.getElementById('step1-cancel')?.addEventListener('click', closeVerificationModal);
  document.getElementById('step1-next')?.addEventListener('click', () => goToVerificationStep(2));
  document.getElementById('step2-back')?.addEventListener('click', () => goToVerificationStep(1));
  document.getElementById('step2-next')?.addEventListener('click', () => goToVerificationStep(3));
  document.getElementById('step3-back')?.addEventListener('click', () => goToVerificationStep(2));
  document.getElementById('step3-purchase')?.addEventListener('click', purchaseVerification);
  document.getElementById('step4-close')?.addEventListener('click', closeVerificationModal);

  // Area code and service selects
  document.getElementById('area-code-select')?.addEventListener('change', onAreaCodeChange);
  document.getElementById('service-select')?.addEventListener('change', onServiceChange);
  document.getElementById('carrier-select')?.addEventListener('change', onCarrierChange);

  // Close modals on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      hideModals();
    }
  });

  // Refresh balance on window focus
  window.addEventListener('focus', loadBalance);

  setupCreditHandlers();
  setupRentalHandlers();
}

/**
 * Setup offline detection
 * @returns {void}
 */
function setupOfflineDetection() {
  window.addEventListener('online', () => {
    showToast('Back online! Syncing data...', 'success');
    loadUserData();
    loadBalance();
  });

  window.addEventListener('offline', () => {
    showToast('You are offline. Some features may not work.', 'warning');
  });

  if (!navigator.onLine) {
    showToast('You are offline. Some features may not work.', 'warning');
  }
}

/**
 * Toggle sidebar
 * @returns {void}
 */
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
  }
}

/**
 * Toggle user dropdown
 * @returns {void}
 */
function toggleUserDropdown() {
  const dropdown = document.getElementById('user-dropdown');
  if (dropdown) {
    dropdown.classList.toggle('show');
  }
}

/**
 * Load user data
 * @async
 * @returns {void}
 */
async function loadUserData() {
  try {
    // Set a timeout to prevent hanging (increased to 10s)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch('/api/user/profile', {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      if (response.status === 401) {
        showToast('Session expired. Redirecting to login...', 'warning');
        setTimeout(() => window.location.href = '/auth/login', 1500);
        return;
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const user = await response.json();
    stateManager.setState({ user });

    const emailEl = document.getElementById('dropdown-email');
    const initialsEl = document.getElementById('user-initials');

    if (emailEl) emailEl.textContent = user.email || 'User';
    if (initialsEl) {
      const initials = (user.email || 'U').charAt(0).toUpperCase();
      initialsEl.textContent = initials;
    }
  } catch (error) {
    logError('loadUserData', error);

    // Set default user display if endpoint fails
    const emailEl = document.getElementById('dropdown-email');
    const initialsEl = document.getElementById('user-initials');
    if (emailEl) emailEl.textContent = 'User';
    if (initialsEl) initialsEl.textContent = 'U';

    // Only show error if it's not an abort (timeout is expected if server is down)
    if (error.name !== 'AbortError') {
      console.warn('Could not load user profile:', error.message);
    }
  }
}

/**
 * Handle logout
 * @async
 * @param {Event} e - Event object
 * @returns {void}
 */
async function handleLogout(e) {
  e.preventDefault();
  if (!confirm('Are you sure you want to logout?')) return;

  try {
    await fetch('/api/auth/logout', { method: 'POST' });
  } catch (error) {
    logError('handleLogout', error);
  }
  localStorage.clear();
  window.location.href = '/auth/login';
}

/**
 * Load balance
 * @async
 * @returns {void}
 */
async function loadBalance() {
  try {
    // Set a timeout to prevent hanging (increased to 10s)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch('/api/user/balance', {
      headers: { 'Cache-Control': 'no-cache' },
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      if (response.status === 401) {
        showToast('Session expired. Redirecting to login...', 'warning');
        setTimeout(() => window.location.href = '/auth/login', 1500);
        return;
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    const balance = parseFloat(data.credits) || 0;
    stateManager.setState({ balance });
    updateBalanceDisplay(balance);
  } catch (error) {
    logError('loadBalance', error);

    // Set default balance if endpoint fails
    updateBalanceDisplay(0);

    // Only show error if it's not an abort
    if (error.name !== 'AbortError') {
      console.warn('Could not load balance:', error.message);
    }
  }
}

/**
 * Setup view switching
 * @returns {void}
 */
function setupViewSwitching() {
  const urlParams = new URLSearchParams(window.location.search);
  const view = urlParams.get('view') || 'home';
  switchView(view);

  document.querySelectorAll('.nav-item[data-view]').forEach(item => {
    item.addEventListener('click', function (e) {
      e.preventDefault();
      const targetView = this.getAttribute('data-view');
      switchView(targetView);
      updateURL(targetView);
    });
  });

  if (localStorage.getItem('sidebarCollapsed') === 'true') {
    document.getElementById('sidebar')?.classList.add('collapsed');
  }
}

/**
 * Switch view
 * @param {string} viewName - View name
 * @returns {void}
 */
function switchView(viewName) {
  stateManager.setState({ currentView: viewName });

  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const targetView = document.getElementById(`${viewName}-view`);
  if (targetView) {
    targetView.classList.add('active');
  }

  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    }
  });

  // Initialize view content
  switch (viewName) {
    case 'rentals':
      loadRentalsView();
      break;
    case 'wallet':
      loadWalletView();
      break;
    case 'profile':
      loadProfileView();
      break;
    case 'settings':
      loadSettingsView();
      break;
  }
}

/**
 * Update URL
 * @param {string} view - View name
 * @returns {void}
 */
function updateURL(view) {
  const url = view === 'home' ? '/dashboard' : `/dashboard?view=${view}`;
  window.history.pushState({ view }, '', url);
}

/**
 * Open verification modal
 * @returns {void}
 */
function openVerificationModal() {
  const modal = document.getElementById('verification-modal');
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    resetVerificationState();
    loadAreaCodes();
    loadCarriers();
    goToVerificationStep(1);
  }
}

/**
 * Close verification modal
 * @returns {void}
 */
function closeVerificationModal() {
  const modal = document.getElementById('verification-modal');
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }

  const state = stateManager.getState();
  if (state.verification.pollingInterval) {
    clearInterval(state.verification.pollingInterval);
  }
}

/**
 * Reset verification state
 * @returns {void}
 */
function resetVerificationState() {
  stateManager.setState({
    verification: {
      step: 1,
      areaCode: null,
      service: null,
      carrier: null,
      cost: 0,
      verificationId: null,
      pollingInterval: null,
      areaCodes: [],
      services: [],
      carriers: []
    }
  });

  document.getElementById('area-code-select').value = '';
  document.getElementById('service-select').innerHTML = '<option value="">-- Select Service --</option>';
  document.getElementById('carrier-select').innerHTML = '<option value="">-- Any Carrier --</option>';
}

/**
 * Load area codes
 * @async
 * @returns {void}
 */
async function loadAreaCodes() {
  try {
    showLoading('area-code-select');

    const cached = cache.get('areaCodes');
    let data;

    if (cached) {
      data = cached;
    } else {
      const response = await api.getAreaCodes();
      if (!response.success) throw new Error('Failed to load area codes');
      data = response;
      cache.set('areaCodes', data, 86400000); // 24 hours
    }

    const select = document.getElementById('area-code-select');
    select.innerHTML = '<option value="">-- Select Area Code --</option>';

    // Check tier access
    if (window.tierManager && !window.tierManager.checkFeatureAccess('area_codes')) {
      window.tierManager.lockFeature(select.parentElement, 'area_codes', 'starter');
      select.disabled = true;
      return;
    }

    data.area_codes.forEach(code => {
      const option = document.createElement('option');
      option.value = code.area_code;
      option.textContent = `${code.area_code} (${code.state})`;
      select.appendChild(option);
    });

    console.log(`Loaded ${data.area_codes.length} area codes`);
  } catch (error) {
    logError('loadAreaCodes', error);
    showToast(handleError(error), 'error');
  } finally {
    hideLoading('area-code-select');
  }
}

/**
 * Load carriers
 * @async
 * @returns {void}
 */
async function loadCarriers() {
  try {
    const cached = cache.get('carriers');
    let data;

    if (cached) {
      data = cached;
    } else {
      const response = await api.getCarriers();
      if (!response.success) throw new Error('Failed to load carriers');
      data = response;
      cache.set('carriers', data, 86400000); // 24 hours
    }

    const select = document.getElementById('carrier-select');
    select.innerHTML = '<option value="">-- Any Carrier --</option>';

    // Check tier access
    if (window.tierManager && !window.tierManager.checkFeatureAccess('isp_filter')) {
      window.tierManager.lockFeature(select.parentElement, 'isp_filter', 'turbo');
      select.disabled = true;
      return;
    }

    data.carriers.forEach(carrier => {
      const option = document.createElement('option');
      option.value = carrier.id;
      option.textContent = carrier.name;
      select.appendChild(option);
    });

    console.log(`Loaded ${data.carriers.length} carriers`);
  } catch (error) {
    logError('loadCarriers', error);
    showToast(handleError(error), 'error');
  }
}

/**
 * Handle area code change
 * @async
 * @returns {void}
 */
async function onAreaCodeChange() {
  const areaCode = document.getElementById('area-code-select').value;
  stateManager.setState({ verification: { areaCode } });
  eventBus.emit(events.AREA_CODE_CHANGED, areaCode);

  await loadServices(areaCode);
  await updatePricing();
}

/**
 * Load services
 * @async
 * @param {string} areaCode - Area code
 * @returns {void}
 */
async function loadServices(areaCode) {
  try {
    showLoading('service-select');

    const cacheKey = `services_${areaCode}`;
    const cached = cache.get(cacheKey);
    let data;

    if (cached) {
      data = cached;
    } else {
      const response = await api.getServices(areaCode);
      if (!response.success) throw new Error('Failed to load services');
      data = response;
      cache.set(cacheKey, data, 3600000); // 1 hour
    }

    const select = document.getElementById('service-select');
    select.innerHTML = '<option value="">-- Select Service --</option>';

    data.services.forEach(service => {
      const option = document.createElement('option');
      option.value = service.name;
      option.textContent = service.name;
      option.dataset.cost = service.cost || 0;
      select.appendChild(option);
    });

    console.log(`Loaded ${data.services.length} services`);
  } catch (error) {
    logError('loadServices', error);
    showToast(handleError(error), 'error');
  } finally {
    hideLoading('service-select');
  }
}

/**
 * Handle service change
 * @returns {void}
 */
function onServiceChange() {
  const service = document.getElementById('service-select').value;
  stateManager.setState({ verification: { service } });
  eventBus.emit(events.SERVICE_CHANGED, service);
  updatePricing();
}

/**
 * Handle carrier change
 * @returns {void}
 */
function onCarrierChange() {
  const carrier = document.getElementById('carrier-select').value;
  stateManager.setState({ verification: { carrier } });
  eventBus.emit(events.CARRIER_CHANGED, carrier);
  updatePricing();
}

/**
 * Update pricing
 * @async
 * @returns {void}
 */
async function updatePricing() {
  const state = stateManager.getState();
  const service = state.verification.service;
  const areaCode = state.verification.areaCode || 'any';
  const carrier = state.verification.carrier || 'any';

  if (!service) return;

  try {
    const cacheKey = `pricing_${service}_${areaCode}_${carrier}`;
    const cached = cache.get(cacheKey);
    let pricing;

    if (cached) {
      pricing = cached;
    } else {
      pricing = await api.getPricing(service, areaCode, carrier);
      cache.set(cacheKey, pricing, 300000); // 5 minutes
    }

    const priceEl = document.getElementById('service-price');
    priceEl.innerHTML = `
      <div class="pricing-breakdown">
        <div class="pricing-line">
          <span>Base price:</span>
          <span>$${pricing.base_price.toFixed(2)}</span>
        </div>
        ${pricing.area_code_premium > 0 ? `
          <div class="pricing-line">
            <span>Area code premium:</span>
            <span>+$${pricing.area_code_premium.toFixed(2)}</span>
          </div>
        ` : ''}
        ${pricing.carrier_premium > 0 ? `
          <div class="pricing-line">
            <span>Carrier premium:</span>
            <span>+$${pricing.carrier_premium.toFixed(2)}</span>
          </div>
        ` : ''}
        <div class="pricing-line total">
          <span>Total:</span>
          <span>$${pricing.total_price.toFixed(2)}</span>
        </div>
      </div>
    `;

    stateManager.setState({ verification: { cost: pricing.total_price } });
  } catch (error) {
    logError('updatePricing', error);
  }
}

/**
 * Go to verification step
 * @param {number} step - Step number
 * @returns {void}
 */
function goToVerificationStep(step) {
  const state = stateManager.getState();

  if (step === 2 && !state.verification.areaCode) {
    showToast('Please select an area code', 'warning');
    return;
  }
  if (step === 3 && !state.verification.service) {
    showToast('Please select a service', 'warning');
    return;
  }

  stateManager.setState({ verification: { step } });

  document.querySelectorAll('.progress-step').forEach(el => {
    const s = parseInt(el.dataset.step);
    el.classList.remove('active', 'completed');
    if (s < step) el.classList.add('completed');
    if (s === step) el.classList.add('active');
  });

  document.querySelectorAll('[id^="step"]').forEach(el => {
    el.style.display = 'none';
  });
  const stepEl = document.getElementById(`step${step}`);
  if (stepEl) stepEl.style.display = 'block';
}

/**
 * Purchase verification
 * @async
 * @returns {void}
 */
async function purchaseVerification() {
  const state = stateManager.getState();
  const { service, areaCode, carrier, cost } = state.verification;

  const validation = validateVerification({ service, areaCode, carrier });
  if (!validation.valid) {
    const errors = Object.values(validation.errors).join(', ');
    showToast(errors, 'error');
    return;
  }

  if (state.balance < cost) {
    showToast('Insufficient balance. Please add credits.', 'error');
    return;
  }

  try {
    eventBus.emit(events.VERIFICATION_STARTED, { service, areaCode, carrier });
    const result = await api.purchaseVerification(service, areaCode, carrier);

    if (result.success) {
      showToast('Verification purchased successfully', 'success');
      eventBus.emit(events.VERIFICATION_COMPLETED, result);
      goToVerificationStep(4);
      loadBalance();
    } else {
      throw new Error(result.detail || 'Purchase failed');
    }
  } catch (error) {
    logError('purchaseVerification', error);
    eventBus.emit(events.ERROR_OCCURRED, error);
    showToast(handleError(error), 'error');
  }
}

/**
 * Load Rentals View
 */
async function loadRentalsView() {
  const rentalsListEl = document.getElementById('rentals-list');
  if (!rentalsListEl) return;

  try {
    const response = await fetch('/api/rentals');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const rentals = data.rentals || data || [];

    if (rentals.length === 0) {
      rentalsListEl.innerHTML = '<div class="empty-state" style="padding: 60px 20px; text-align: center;"><i class="ph ph-phone" style="font-size: 64px; opacity: 0.3; display: block; margin-bottom: 16px;"></i><h3 style="margin: 0 0 8px 0;">No Active Rentals</h3><p style="color: var(--gray-500); margin: 0;">You don\'t have any active phone rentals yet.</p></div>';
    } else {
      rentalsListEl.innerHTML = rentals.map(r => `<div class="activity-item" style="padding: 16px; border-bottom: 1px solid #e5e7eb;"><div><div style="font-weight: 600;">${escapeHtml(r.phone_number || 'N/A')}</div><div style="font-size: 14px; color: #6b7280;">${escapeHtml(r.service_name || 'Unknown')}</div></div><div style="text-align: right;"><div style="font-weight: 600;">$${(r.cost || 0).toFixed(2)}</div></div></div>`).join('');
    }
  } catch (error) {
    logError('loadRentalsView', error);
    rentalsListEl.innerHTML = '<div class="empty-state" style="padding: 40px 20px; text-align: center;"><i class="ph ph-warning-circle" style="font-size: 48px; opacity: 0.5; color: #ef4444;"></i><p>Failed to load rentals</p></div>';
  }
}

/**
 * Load Wallet View
 */
async function loadWalletView() {
  const transactionsListEl = document.getElementById('transactions-list');
  if (!transactionsListEl) return;

  try {
    const response = await fetch('/api/wallet/transactions');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const transactions = data.transactions || data || [];

    if (transactions.length === 0) {
      transactionsListEl.innerHTML = '<div class="empty-state" style="padding: 60px 20px; text-align: center;"><i class="ph ph-receipt" style="font-size: 64px; opacity: 0.3; display: block; margin-bottom: 16px;"></i><h3 style="margin: 0 0 8px 0;">No Transactions</h3><p style="color: var(--gray-500); margin: 0;">Your transaction history will appear here.</p></div>';
    } else {
      transactionsListEl.innerHTML = transactions.map(tx => `<div class="activity-item" style="padding: 16px; border-bottom: 1px solid #e5e7eb;"><div><div style="font-weight: 600;">${escapeHtml(tx.type || 'Transaction')}</div><div style="font-size: 14px; color: #6b7280;">${escapeHtml(tx.description || '')}</div></div><div style="text-align: right; color: ${tx.amount >= 0 ? '#10b981' : '#ef4444'};">${tx.amount >= 0 ? '+' : ''}$${Math.abs(tx.amount || 0).toFixed(2)}</div></div>`).join('');
    }
  } catch (error) {
    logError('loadWalletView', error);
    transactionsListEl.innerHTML = '<div class="empty-state" style="padding: 40px 20px; text-align: center;"><i class="ph ph-warning-circle" style="font-size: 48px; opacity: 0.5; color: #ef4444;"></i><p>Failed to load transactions</p></div>';
  }
}

/**
 * Load Profile View
 */
async function loadProfileView() {
  const profileContainerEl = document.getElementById('profile-form-container');
  if (!profileContainerEl) return;

  try {
    const response = await fetch('/api/user/profile', {
      credentials: 'include'
    });
    if (!response.ok) {
      if (response.status === 401) {
        window.location.href = '/auth/login';
        return;
      }
      throw new Error(`HTTP ${response.status}`);
    }
    const user = await response.json();
    profileContainerEl.innerHTML = `<form style="max-width: 600px;"><div style="margin-bottom: 20px;"><label style="display: block; margin-bottom: 8px; font-weight: 500;">Email</label><input type="email" value="${escapeHtml(user.email || '')}" readonly style="width: 100%; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f9fafb;"><small style="display: block; margin-top: 4px; color: #6b7280;">Email cannot be changed</small></div><div style="margin-bottom: 20px;"><label style="display: block; margin-bottom: 8px; font-weight: 500;">User ID</label><input type="text" value="${escapeHtml(user.id || '')}" readonly style="width: 100%; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f9fafb; font-family: monospace;"></div><div style="margin-bottom: 20px;"><label style="display: block; margin-bottom: 8px; font-weight: 500;">Member Since</label><input type="text" value="${user.created_at ? formatDate(user.created_at) : 'N/A'}" readonly style="width: 100%; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f9fafb;"></div></form>`;
  } catch (error) {
    logError('loadProfileView', error);
    profileContainerEl.innerHTML = '<div class="empty-state" style="padding: 40px 20px; text-align: center;"><i class="ph ph-warning-circle" style="font-size: 48px; opacity: 0.5; color: #ef4444;"></i><p>Failed to load profile</p></div>';
  }
}

/**
 * Load Settings View
 */
async function loadSettingsView() {
  const settingsContainerEl = document.getElementById('settings-form-container');
  if (!settingsContainerEl) return;

  // Render form
  settingsContainerEl.innerHTML = `
    <div style="max-width: 600px;">
      <h3 style="margin: 0 0 24px 0;">Account Settings</h3>
      
      <div class="card" style="padding: 20px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 16px 0;">Notifications</h4>
        <label style="display: flex; align-items: center; cursor: pointer; margin-bottom: 12px;">
          <input type="checkbox" id="email-notifications" checked style="margin-right: 12px; width: 18px; height: 18px;">
          <span>Email notifications (Verification updates)</span>
        </label>
        <label style="display: flex; align-items: center; cursor: pointer; margin-bottom: 12px;">
          <input type="checkbox" id="payment-notifications" checked style="margin-right: 12px; width: 18px; height: 18px;">
          <span>Payment receipts</span>
        </label>
      </div>

      <div class="card" style="padding: 20px; margin-bottom: 20px;">
         <h4 style="margin: 0 0 16px 0;">Privacy</h4>
         <label style="display: flex; align-items: center; cursor: pointer; margin-bottom: 12px;">
            <input type="checkbox" id="profile-visibility" style="margin-right: 12px;">
            <span>Profile Visibility (Public)</span>
         </label>
         <label style="display: flex; align-items: center; cursor: pointer;">
            <input type="checkbox" id="analytics-tracking" checked style="margin-right: 12px;">
            <span>Allow Analytics</span>
         </label>
      </div>

      <div class="card" style="padding: 20px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 16px 0;">Security</h4>
        <button class="btn btn-secondary btn-sm" onclick="window.location.href='/auth/password-reset'">
          <i class="ph ph-lock"></i> Change Password
        </button>
        <div style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
             <button class="btn btn-danger btn-sm" id="delete-account-btn">Delete Account</button>
        </div>
      </div>

      <div style="padding-top: 20px; border-top: 1px solid #e5e7eb;">
        <button id="save-settings-btn" class="btn btn-primary">
          <i class="ph ph-floppy-disk"></i> Save Settings
        </button>
      </div>
    </div>`;

  // Bind Events
  document.getElementById('save-settings-btn')?.addEventListener('click', async () => {
    const notifData = {
      verification_alerts: document.getElementById('email-notifications').checked,
      payment_receipts: document.getElementById('payment-notifications').checked
    };
    const privacyData = {
      profile_visibility: document.getElementById('profile-visibility').checked,
      analytics_tracking: document.getElementById('analytics-tracking').checked
    };

    try {
      const btn = document.getElementById('save-settings-btn');
      btn.innerHTML = '<div class="spinner-small"></div> Saving...';
      btn.disabled = true;

      await Promise.all([
        api.saveSettings('notifications', notifData),
        api.saveSettings('privacy', privacyData)
      ]);
      showToast('Settings saved successfully', 'success');
    } catch (e) {
      showToast(e.message, 'error');
      logError('saveSettings', e);
    } finally {
      const btn = document.getElementById('save-settings-btn');
      if (btn) {
        btn.innerHTML = '<i class="ph ph-floppy-disk"></i> Save Settings';
        btn.disabled = false;
      }
    }
  });

  document.getElementById('delete-account-btn')?.addEventListener('click', () => {
    const pwd = prompt("Enter your password to confirm deletion:");
    if (pwd) {
      api.deleteAccount(pwd).then(() => {
        alert('Account deleted.');
        window.location.href = '/auth/register';
      }).catch(err => showToast(err.message, 'error'));
    }
  });
}

/**
 * Setup Credit Handlers (Modal & Payment)
 */
function setupCreditHandlers() {
  const modal = document.getElementById('credits-modal');
  const openBtns = [document.getElementById('quick-credits-btn'), document.getElementById('add-credits-btn')];
  const closeBtns = [document.getElementById('credits-close-btn'), document.getElementById('credits-cancel-btn')];
  const proceedBtn = document.getElementById('credits-proceed-btn');
  const customInput = document.getElementById('credit-amount');
  const packages = document.querySelectorAll('.package');

  let selectedAmount = 0;

  function openModal() {
    if (modal) modal.classList.add('show');
  }

  function closeModal() {
    if (modal) modal.classList.remove('show');
    packages.forEach(p => p.classList.remove('selected'));
    if (customInput) customInput.value = '';
    selectedAmount = 0;
  }

  openBtns.forEach(btn => btn?.addEventListener('click', openModal));
  closeBtns.forEach(btn => btn?.addEventListener('click', closeModal));

  packages.forEach(pkg => {
    pkg.addEventListener('click', () => {
      packages.forEach(p => p.classList.remove('selected'));
      pkg.classList.add('selected');
      selectedAmount = parseFloat(pkg.dataset.amount);
      if (customInput) customInput.value = '';
    });
  });

  customInput?.addEventListener('input', () => {
    packages.forEach(p => p.classList.remove('selected'));
    selectedAmount = parseFloat(customInput.value);
  });

  proceedBtn?.addEventListener('click', async () => {
    if (!selectedAmount || selectedAmount < 1) {
      showToast('Please select an amount (minimum $1)', 'warning');
      return;
    }

    try {
      const originalText = proceedBtn.innerHTML;
      proceedBtn.innerHTML = '<div class="spinner-small"></div> Processing...';
      proceedBtn.disabled = true;

      const result = await api.initializePayment(selectedAmount);
      if (result.authorization_url) {
        window.location.href = result.authorization_url;
      } else {
        throw new Error('No payment URL returned');
      }
    } catch (e) {
      showToast(e.message, 'error');
      proceedBtn.disabled = false;
      proceedBtn.innerHTML = 'Proceed to Payment';
    }
  });
}

// Export for testing
export { init, loadAreaCodes, loadServices, updatePricing, purchaseVerification, setupCreditHandlers };
