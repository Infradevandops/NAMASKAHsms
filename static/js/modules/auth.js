// Authentication Module - Task 1.2 Fix

// Store tokens with expiry
function storeTokens(data) {
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
  localStorage.setItem('token_type', data.token_type)
  // Store expiry time (24 hours from now)
  localStorage.setItem('token_expires_at', Date.now() + (data.expires_in * 1000))
}

// Check if token needs refresh
async function ensureValidToken() {
  const expiresAt = localStorage.getItem('token_expires_at')
  const now = Date.now()
  
  // Refresh if token expires in less than 5 minutes
  if (expiresAt && now > (expiresAt - 300000)) {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }
      
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        storeTokens(data)
        return true
      } else {
        // Refresh failed, redirect to login
        localStorage.clear()
        window.location.href = '/auth/login'
        return false
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      localStorage.clear()
      window.location.href = '/auth/login'
      return false
    }
  }
  
  return true
}

export function initAuth() {
  const loginForm = document.getElementById('login-form')
  const registerForm = document.getElementById('register-form')
  const logoutBtn = document.getElementById('logout-btn')

  if (loginForm) loginForm.addEventListener('submit', handleLogin)
  if (registerForm) registerForm.addEventListener('submit', handleRegister)
  if (logoutBtn) logoutBtn.addEventListener('click', handleLogout)
}

async function handleLogin(e) {
  e.preventDefault()
  const emailInput = document.getElementById('email')
  const passwordInput = document.getElementById('password')
  
  if (!emailInput || !passwordInput) {
    console.error('Login form inputs not found')
    return
  }

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: emailInput.value,
        password: passwordInput.value
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data = await response.json()
    storeTokens(data)
    window.location.href = '/dashboard'
  } catch (error) {
    console.error('Login error:', error)
    alert('Login failed: ' + error.message)
  }
}

async function handleRegister(e) {
  e.preventDefault()
  const emailInput = document.getElementById('email')
  const passwordInput = document.getElementById('password')
  
  if (!emailInput || !passwordInput) {
    console.error('Register form inputs not found')
    return
  }

  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: emailInput.value,
        password: passwordInput.value
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    alert('Registration successful! Please log in.')
    window.location.href = '/auth/login'
  } catch (error) {
    console.error('Register error:', error)
    alert('Registration failed: ' + error.message)
  }
}

async function handleLogout() {
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
    }
  } catch (error) {
    console.error('Logout error:', error)
  }
  
  localStorage.clear()
  window.location.href = '/auth/login'
}

export { handleLogin, handleRegister, handleLogout, ensureValidToken, storeTokens }
