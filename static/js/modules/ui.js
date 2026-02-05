/**
 * UI Helpers Module
 * Common UI functions
 */

/**
 * Show toast notification
 * @param {string} message - Message text
 * @param {string} type - Type (success, error, warning, info)
 * @returns {void}
 */
export function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 3000);
}

/**
 * Hide all modals
 * @returns {void}
 */
export function hideModals() {
  document.querySelectorAll('.modal').forEach(modal => {
    modal.classList.remove('show');
  });
  document.body.style.overflow = '';
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
export function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Format date
 * @param {string} dateString - Date string
 * @returns {string} Formatted date
 */
export function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Update balance display
 * @param {number} balance - Balance amount
 * @returns {void}
 */
export function updateBalanceDisplay(balance) {
  const formatted = `$${balance.toFixed(2)}`;
  const elements = [
    document.getElementById('header-balance'),
    document.getElementById('stat-balance'),
    document.getElementById('wallet-balance')
  ];
  elements.forEach(el => {
    if (el) el.textContent = formatted;
  });
}

/**
 * Show loading state
 * @param {string} elementId - Element ID
 * @returns {void}
 */
export function showLoading(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.add('loading');
}

/**
 * Hide loading state
 * @param {string} elementId - Element ID
 * @returns {void}
 */
export function hideLoading(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.remove('loading');
}
