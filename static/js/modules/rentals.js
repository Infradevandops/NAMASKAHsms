// Rentals Module
import axios from 'axios'

export function initRentals() {
  const rentForm = document.getElementById('rent-form')
  const renewBtn = document.getElementById('renew-btn')

  if (rentForm) rentForm.addEventListener('submit', handleRent)
  if (renewBtn) renewBtn.addEventListener('click', handleRenew)

  loadRentals()
}

async function loadRentals() {
  try {
    const response = await axios.get('/api/rentals')
    const rentalsEl = document.getElementById('rentals-list')
    if (!rentalsEl) return

    rentalsEl.innerHTML = ''
    response.data.forEach(rental => {
      const div = document.createElement('div')
      div.className = 'rental-item'
      div.innerHTML = `
        <p>Phone: ${rental.phone_number}</p>
        <p>Service: ${rental.service_name}</p>
        <p>Expires: ${new Date(rental.expires_at).toLocaleString()}</p>
        <p>Cost: $${rental.cost}</p>
        <button onclick="renewRental('${rental.id}')">Renew</button>
      `
      rentalsEl.appendChild(div)
    })
  } catch (error) {
    console.error('Failed to load rentals:', error)
  }
}

async function handleRent(e) {
  e.preventDefault()
  try {
    const response = await axios.post('/api/rentals/create', {
      country: document.getElementById('country').value,
      service: document.getElementById('service').value,
      duration_hours: parseInt(document.getElementById('duration').value)
    })
    alert('Rental created! Phone: ' + response.data.phone_number)
    loadRentals()
  } catch (error) {
    alert('Rental failed: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

async function handleRenew() {
  const rentalId = document.getElementById('rental-id').value
  try {
    await axios.post(`/api/rentals/${rentalId}/renew`)
    alert('Rental renewed!')
    loadRentals()
  } catch (error) {
    alert('Renewal failed: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

async function renewRental(id) {
  try {
    await axios.post(`/api/rentals/${id}/renew`)
    alert('Rental renewed!')
    loadRentals()
  } catch (error) {
    alert('Renewal failed: ' + (error.response?.data?.detail || 'Unknown error'))
  }
}

export { loadRentals, handleRent, handleRenew, renewRental }
