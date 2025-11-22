// Main entry point with lazy loading and code splitting

// Core modules - loaded immediately
import { initAuth } from './modules/auth.js'
import { initDashboard } from './modules/dashboard.js'

// Lazy loaded modules
const loadVerification = () => import('./modules/verification.js')
const loadAnalytics = () => import('./modules/analytics.js')
const loadWallet = () => import('./modules/wallet.js')
const loadRentals = () => import('./modules/rentals.js')

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  // Initialize core modules
  initAuth()
  initDashboard()

  // Lazy load based on page context
  const page = document.body.dataset.page

  switch (page) {
    case 'verification':
      const { initVerification } = await loadVerification()
      initVerification()
      break
    case 'analytics':
      const { initAnalytics } = await loadAnalytics()
      initAnalytics()
      break
    case 'wallet':
      const { initWallet } = await loadWallet()
      initWallet()
      break
    case 'rentals':
      const { initRentals } = await loadRentals()
      initRentals()
      break
  }

  // Performance monitoring
  if (window.performance && window.performance.timing) {
    window.addEventListener('load', () => {
      const perfData = window.performance.timing
      const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart
      console.info(`Page load time: ${pageLoadTime}ms`)
    })
  }
})

// Service worker registration
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js').catch(err => {
    console.warn('Service Worker registration failed:', err)
  })
}
