// Authentication Module
import axios from 'axios'

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
  try {
    const response = await axios.post('/api/auth/login', {
      email: document.getElementById('email').value,
      password: document.getElementById('password').value
    })
    localStorage.setItem('token', response.data.token)
    window.location.href = '/dashboard'
  } catch (error) {
    alert('Login failed: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

async function handleRegister(e) {
  e.preventDefault()
  try {
    await axios.post('/api/auth/register', {
      email: document.getElementById('email').value,
      password: document.getElementById('password').value
    })
    alert('Registration successful! Please log in.')
    window.location.href = '/login'
  } catch (error) {
    alert('Registration failed: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

async function handleLogout() {
  localStorage.removeItem('token')
  window.location.href = '/login'
}

export { handleLogin, handleRegister, handleLogout }
