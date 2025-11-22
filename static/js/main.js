// Main entry point for Vite build
import '../css/base.css'
import '../css/theme.css'
import '../css/responsive.css'
import '../css/accessibility.css'

// Core modules
import { initAuth } from './modules/auth.js'
import { initVerification } from './modules/verification.js'
import { initDashboard } from './modules/dashboard.js'
import { initWallet } from './modules/wallet.js'
import { initRentals } from './modules/rentals.js'
import { initAnalytics } from './modules/analytics.js'

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp)
} else {
  initializeApp()
}

function initializeApp() {
  initAuth()
  initVerification()
  initDashboard()
  initWallet()
  initRentals()
  initAnalytics()
}

// Export for use in other modules
export { initAuth, initVerification, initDashboard, initWallet, initRentals, initAnalytics }
