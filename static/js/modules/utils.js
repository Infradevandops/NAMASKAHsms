/**
 * Utility Functions - Error handling, logging, notifications, etc.
 */

// Error handler
export function handleError(error, context = '') {
  console.error(`Error${context ? ` in ${context}` : ''}:`, error)
  
  // Show user-friendly error message
  showErrorNotification(
    error.message || 'An error occurred. Please try again.'
  )
}

// Notification system
export function showErrorNotification(message) {
  const notification = document.createElement('div')
  notification.className = 'notification notification-error'
  notification.textContent = message
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #ef4444;
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 9999;
    animation: slideIn 0.3s ease-in-out;
  `
  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease-in-out'
    setTimeout(() => notification.remove(), 300)
  }, 5000)
}

export function showSuccessNotification(message) {
  const notification = document.createElement('div')
  notification.className = 'notification notification-success'
  notification.textContent = message
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #10b981;
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 9999;
    animation: slideIn 0.3s ease-in-out;
  `
  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease-in-out'
    setTimeout(() => notification.remove(), 300)
  }, 3000)
}

export function showWarningNotification(message) {
  const notification = document.createElement('div')
  notification.className = 'notification notification-warning'
  notification.textContent = message
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #f59e0b;
    color: #111827;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 9999;
    animation: slideIn 0.3s ease-in-out;
  `
  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease-in-out'
    setTimeout(() => notification.remove(), 300)
  }, 4000)
}

// API helper
export async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    handleError(error, 'API call')
    throw error
  }
}

// Debounce helper
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Throttle helper
export function throttle(func, limit) {
  let inThrottle
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// Local storage helper
export function setLocalStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.error('Failed to set localStorage:', error)
  }
}

export function getLocalStorage(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : defaultValue
  } catch (error) {
    console.error('Failed to get localStorage:', error)
    return defaultValue
  }
}

export function removeLocalStorage(key) {
  try {
    localStorage.removeItem(key)
  } catch (error) {
    console.error('Failed to remove localStorage:', error)
  }
}

// Session storage helper
export function setSessionStorage(key, value) {
  try {
    sessionStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.error('Failed to set sessionStorage:', error)
  }
}

export function getSessionStorage(key, defaultValue = null) {
  try {
    const item = sessionStorage.getItem(key)
    return item ? JSON.parse(item) : defaultValue
  } catch (error) {
    console.error('Failed to get sessionStorage:', error)
    return defaultValue
  }
}

// Format helpers
export function formatDate(date, format = 'MM/DD/YYYY') {
  const d = new Date(date)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  
  return format
    .replace('DD', day)
    .replace('MM', month)
    .replace('YYYY', year)
}

export function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount)
}

// Validation helpers
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export function isValidPhone(phone) {
  const phoneRegex = /^\+?[\d\s\-()]{10,}$/
  return phoneRegex.test(phone)
}

export function isValidURL(url) {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

// Global error handlers
export function setupGlobalErrorHandlers() {
  // Handle uncaught errors
  window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error)
    handleError(event.error, 'Global error handler')
  })

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason)
    handleError(event.reason, 'Unhandled promise rejection')
  })
}

// Add animation styles
export function addAnimationStyles() {
  const style = document.createElement('style')
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `
  document.head.appendChild(style)
}
