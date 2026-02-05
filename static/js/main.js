/**
 * Main Entry Point - Hybrid Loading Strategy
 * Loads core modules eagerly, optional modules lazily
 */

// Intercept fetch to add auth token and handle 401 - Task 1.2 Fix
const originalFetch = window.fetch
window.fetch = async function (...args) {
  // Ensure token is valid before making request
  const { ensureValidToken } = await import('./modules/auth.js')
  await ensureValidToken()

  const token = localStorage.getItem('access_token')
  if (token && args[1]) {
    args[1].headers = args[1].headers || {}
    args[1].headers['Authorization'] = `Bearer ${token}`
  }

  const response = await originalFetch.apply(this, args)

  // Handle 401 responses
  if (response.status === 401) {
    localStorage.clear()
    window.location.href = '/auth/login'
  }

  return response
}

import { loadModule, preloadModule } from './moduleLoader.js'
import { setupGlobalErrorHandlers, addAnimationStyles } from './modules/utils.js'
import { initScrollTimeline } from './modules/scroll-timeline.js'

// Core modules - loaded immediately
import { initAuth } from './modules/auth.js'
import { init as initDashboard } from './dashboard.js'

// Loading indicator
function showLoadingIndicator() {
  const indicator = document.createElement('div')
  indicator.id = 'module-loading'
  indicator.className = 'module-loading'
  indicator.innerHTML = '<span class="spinner"></span>'
  indicator.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 9998;
  `
  document.body.appendChild(indicator)
}

function hideLoadingIndicator() {
  const indicator = document.getElementById('module-loading')
  if (indicator) indicator.remove()
}

// Initialize app
async function initializeApp() {
  try {
    // Setup global error handlers
    setupGlobalErrorHandlers()
    addAnimationStyles()

    // Initialize scroll timeline if on landing page
    const isLandingPage = document.body.classList.contains('landing-page') ||
      document.querySelectorAll('[data-timeline-section]').length > 0
    if (isLandingPage) {
      initScrollTimeline()
    }

    // Initialize core modules
    initAuth()
    initDashboard()

    // Load optional modules based on page
    const page = document.body.dataset.page
    if (page) {
      showLoadingIndicator()
      const module = await loadModule(page)
      hideLoadingIndicator()

      // Call init function if available
      const initFn = module[`init${capitalize(page)}`]
      if (initFn) {
        initFn()
      }
    }

    // Preload other modules in background
    preloadModule('verification')
    preloadModule('analytics')
    preloadModule('wallet')
    preloadModule('rentals')
  } catch (error) {
    hideLoadingIndicator()
    console.error('Failed to initialize app:', error)
  }
}

// Helper function
function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

// Start initialization
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp)
} else {
  initializeApp()
}

// Export for use in other modules
export { initAuth, initDashboard, loadModule, preloadModule }
