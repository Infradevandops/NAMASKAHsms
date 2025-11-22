// Dashboard Module
import axios from 'axios'

export function initDashboard() {
  loadDashboardData()
  setInterval(loadDashboardData, 30000)
}

async function loadDashboardData() {
  try {
    const response = await axios.get('/api/dashboard/stats')
    updateDashboard(response.data)
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
}

function updateDashboard(data) {
  const creditsEl = document.getElementById('credits')
  const verificationsEl = document.getElementById('verifications')
  const successRateEl = document.getElementById('success-rate')

  if (creditsEl) creditsEl.textContent = '$' + data.credits.toFixed(2)
  if (verificationsEl) verificationsEl.textContent = data.total_verifications
  if (successRateEl) successRateEl.textContent = (data.success_rate * 100).toFixed(1) + '%'
}

async function loadHistory() {
  try {
    const response = await axios.get('/api/verify/history')
    const historyEl = document.getElementById('history')
    if (!historyEl) return

    historyEl.innerHTML = ''
    response.data.forEach(item => {
      const row = document.createElement('tr')
      row.innerHTML = `
        <td>${item.service_name}</td>
        <td>${item.country}</td>
        <td>${item.status}</td>
        <td>$${item.cost.toFixed(2)}</td>
        <td>${new Date(item.created_at).toLocaleString()}</td>
      `
      historyEl.appendChild(row)
    })
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

export { loadDashboardData, updateDashboard, loadHistory }
