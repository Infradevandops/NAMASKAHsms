// Verification Module
import axios from 'axios'

export function initVerification() {
  const verifyForm = document.getElementById('verify-form')
  const countrySelect = document.getElementById('country')
  const serviceSelect = document.getElementById('service')

  if (verifyForm) verifyForm.addEventListener('submit', handleVerify)
  if (countrySelect) countrySelect.addEventListener('change', loadServices)
  if (serviceSelect) serviceSelect.addEventListener('change', updatePrice)
}

async function loadServices(e) {
  const country = e.target.value
  try {
    const response = await axios.get(`/api/countries/${country}/services`)
    const serviceSelect = document.getElementById('service')
    serviceSelect.innerHTML = '<option value="">Select Service</option>'
    response.data.forEach(service => {
      const option = document.createElement('option')
      option.value = service.id
      option.textContent = service.name
      serviceSelect.appendChild(option)
    })
  } catch (error) {
    console.error('Failed to load services:', error)
  }
}

async function updatePrice() {
  const country = document.getElementById('country').value
  const service = document.getElementById('service').value
  try {
    const response = await axios.get(`/api/verify/price?country=${country}&service=${service}`)
    document.getElementById('price').textContent = '$' + response.data.price.toFixed(2)
  } catch (error) {
    console.error('Failed to get price:', error)
  }
}

async function handleVerify(e) {
  e.preventDefault()
  try {
    const response = await axios.post('/api/verify/create', {
      country: document.getElementById('country').value,
      service: document.getElementById('service').value
    })
    alert('Verification started! ID: ' + response.data.id)
    checkStatus(response.data.id)
  } catch (error) {
    alert('Verification failed: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

async function checkStatus(id) {
  const maxAttempts = 60
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await axios.get(`/api/verify/status/${id}`)
      if (response.data.status === 'completed') {
        alert('SMS Code: ' + response.data.code)
        return
      }
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      console.error('Status check failed:', error)
    }
  }
  alert('Verification timeout')
}

export { loadServices, updatePrice, handleVerify, checkStatus }
