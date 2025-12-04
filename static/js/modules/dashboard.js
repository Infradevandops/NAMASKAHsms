// Dashboard Module
import axios from 'axios'

export function initDashboard() {
  loadDashboardData()
  loadBalance()
  setInterval(loadDashboardData, 30000)
  setInterval(loadBalance, 30000)
  loadHistory()
  
  // Load tab-specific content based on current view
  const currentView = document.body.dataset.view || 'user'
  loadTabContent(currentView)
}

function loadTabContent(view) {
  switch(view) {
    case 'verification':
      loadVerificationContent()
      break
    case 'rental':
      loadRentalContent()
      break
    case 'wallet':
      loadWalletContent()
      break
    case 'analytics':
      // Analytics is handled by analytics.js
      break
    case 'admin':
      loadAdminContent()
      break
    case 'affiliate':
      loadAffiliateContent()
      break
  }
}

async function loadBalance() {
  try {
    const response = await axios.get('/api/billing/balance')
    const creditsEl = document.querySelector('[data-stat="credits"]')
    if (creditsEl) {
      creditsEl.textContent = response.data.credits.toFixed(2)
    }
  } catch (error) {
    console.error('Failed to load balance:', error)
  }
}

async function loadDashboardData() {
  try {
    const response = await axios.get('/api/analytics/summary')
    updateDashboard(response.data)
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    showDashboardError('Failed to load dashboard stats')
  }
}

function updateDashboard(data) {
  // Update stat cards
  const creditsEl = document.querySelector('[data-stat="credits"]')
  const verificationsEl = document.querySelector('[data-stat="verifications"]')
  const successRateEl = document.querySelector('[data-stat="success-rate"]')
  const rentalsEl = document.querySelector('[data-stat="active-rentals"]')

  if (creditsEl) creditsEl.textContent = data.credit_balance ? data.credit_balance.toFixed(2) : '0.00'
  if (verificationsEl) verificationsEl.textContent = data.total_verifications || 0
  if (successRateEl) successRateEl.textContent = ((data.success_rate || 0) * 100).toFixed(1) + '%'
  if (rentalsEl) rentalsEl.textContent = data.active_rentals || 0

  // Update daily usage chart if available
  if (data.daily_usage && data.daily_usage.length > 0) {
    updateDailyUsageChart(data.daily_usage)
  }
}

function updateDailyUsageChart(dailyUsage) {
  // This would integrate with a charting library like Chart.js
  // For now, just log it
  console.log('Daily usage data:', dailyUsage)
}

async function loadHistory() {
  try {
    const response = await axios.get('/api/dashboard/activity/recent?limit=10')
    const historyEl = document.getElementById('activity-list')
    if (!historyEl) return

    historyEl.innerHTML = ''
    
    if (!response.data.activities || response.data.activities.length === 0) {
      historyEl.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">No recent activity</td></tr>'
      return
    }

    response.data.activities.forEach(item => {
      const row = document.createElement('tr')
      const createdDate = new Date(item.created_at).toLocaleString()
      row.innerHTML = `
        <td>${item.service_name || 'N/A'}</td>
        <td>${item.country || 'N/A'}</td>
        <td><span class="status-badge status-${item.status}">${item.status}</span></td>
        <td>$${item.cost ? item.cost.toFixed(2) : '0.00'}</td>
        <td>${createdDate}</td>
      `
      historyEl.appendChild(row)
    })
  } catch (error) {
    console.error('Failed to load history:', error)
    const historyEl = document.getElementById('activity-list')
    if (historyEl) {
      historyEl.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: red;">Failed to load activity</td></tr>'
    }
  }
}

function showDashboardError(message) {
  const errorEl = document.getElementById('dashboard-error')
  if (errorEl) {
    errorEl.textContent = message
    errorEl.style.display = 'block'
  }
}

async function loadVerificationContent() {
  try {
    const response = await axios.get('/api/verification/history?limit=20')
    const container = document.getElementById('verification-content')
    if (!container) return

    if (!response.data.verifications || response.data.verifications.length === 0) {
      container.innerHTML = '<p style="padding: 20px; text-align: center; color: #999;">No verifications yet</p>'
      return
    }

    let html = '<table class="table table-hover"><thead><tr><th>Service</th><th>Country</th><th>Phone</th><th>Status</th><th>Cost</th><th>Date</th></tr></thead><tbody>'
    
    response.data.verifications.forEach(v => {
      const date = new Date(v.created_at || v.date).toLocaleDateString()
      const statusClass = `status-${v.status}`
      html += `
        <tr>
          <td>${v.service || 'N/A'}</td>
          <td>${v.country || 'N/A'}</td>
          <td><code>${v.phone_number || 'N/A'}</code></td>
          <td><span class="status-badge ${statusClass}">${v.status}</span></td>
          <td>${v.cost ? v.cost.toFixed(2) : '0.00'}</td>
          <td>${date}</td>
        </tr>
      `
    })
    
    html += '</tbody></table>'
    container.innerHTML = html
  } catch (error) {
    console.error('Failed to load verification content:', error)
    const container = document.getElementById('verification-content')
    if (container) {
      container.innerHTML = '<p style="padding: 20px; color: red;">Failed to load verification history</p>'
    }
  }
}

async function loadRentalContent() {
  try {
    const response = await axios.get('/api/rentals?limit=20')
    const container = document.getElementById('rental-content')
    if (!container) return

    if (!response.data.rentals || response.data.rentals.length === 0) {
      container.innerHTML = '<p style="padding: 20px; text-align: center; color: #999;">No active rentals</p>'
      return
    }

    let html = '<table class="table table-hover"><thead><tr><th>Service</th><th>Country</th><th>Phone</th><th>Status</th><th>Expires</th><th>Cost/Day</th></tr></thead><tbody>'
    
    response.data.rentals.forEach(r => {
      const expiresDate = new Date(r.expires_at).toLocaleDateString()
      const statusClass = `status-${r.status}`
      html += `
        <tr>
          <td>${r.service || 'N/A'}</td>
          <td>${r.country || 'N/A'}</td>
          <td><code>${r.phone_number || 'N/A'}</code></td>
          <td><span class="status-badge ${statusClass}">${r.status}</span></td>
          <td>${expiresDate}</td>
          <td>${r.daily_cost ? r.daily_cost.toFixed(2) : '0.00'}</td>
        </tr>
      `
    })
    
    html += '</tbody></table>'
    container.innerHTML = html
  } catch (error) {
    console.error('Failed to load rental content:', error)
    const container = document.getElementById('rental-content')
    if (container) {
      container.innerHTML = '<p style="padding: 20px; color: #999;">No rental data available</p>'
    }
  }
}

async function loadWalletContent() {
  try {
    const response = await axios.get('/api/user/balance')
    const container = document.getElementById('wallet-content')
    if (!container) return

    let html = `
      <div style="padding: 20px;">
        <div class="card" style="margin-bottom: 20px;">
          <div class="card-body">
            <h5 class="card-title">Account Balance</h5>
            <h2 style="color: #007bff; margin: 20px 0;">$${response.data.credits.toFixed(2)}</h2>
            <p class="text-muted">Available credits</p>
          </div>
        </div>
        <a href="/billing" class="btn btn-primary">Add Credits</a>
      </div>
    `
    container.innerHTML = html
  } catch (error) {
    console.error('Failed to load wallet content:', error)
    const container = document.getElementById('wallet-content')
    if (container) {
      container.innerHTML = '<p style="padding: 20px; color: red;">Failed to load wallet information</p>'
    }
  }
}

async function loadAdminContent() {
  try {
    const response = await axios.get('/api/admin/dashboard/stats')
    const container = document.getElementById('admin-content')
    if (!container) return

    let html = `
      <div style="padding: 20px;">
        <div class="row">
          <div class="col-md-3">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">Total Users</h6>
                <h3>${response.data.total_users || 0}</h3>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">Total Verifications</h6>
                <h3>${response.data.total_verifications || 0}</h3>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">Revenue</h6>
                <h3>$${(response.data.revenue || 0).toFixed(2)}</h3>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">Success Rate</h6>
                <h3>${(response.data.success_rate || 0).toFixed(1)}%</h3>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
    container.innerHTML = html
  } catch (error) {
    console.error('Failed to load admin content:', error)
    const container = document.getElementById('admin-content')
    if (container) {
      container.innerHTML = '<p style="padding: 20px; color: #999;">Admin dashboard data not available</p>'
    }
  }
}

async function loadAffiliateContent() {
  try {
    const response = await axios.get('/api/affiliate/dashboard')
    const container = document.getElementById('affiliate-content')
    if (!container) return

    let html = `
      <div style="padding: 20px;">
        <div class="row">
          <div class="col-md-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">Referrals</h6>
                <h3>${response.data.referral_count || 0}</h3>
              </div>
            </div>
          </div>
          <div class="col-md-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">Commission</h6>
                <h3>$${(response.data.commission || 0).toFixed(2)}</h3>
              </div>
            </div>
          </div>
          <div class="col-md-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">Conversion Rate</h6>
                <h3>${(response.data.conversion_rate || 0).toFixed(1)}%</h3>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
    container.innerHTML = html
  } catch (error) {
    console.error('Failed to load affiliate content:', error)
    const container = document.getElementById('affiliate-content')
    if (container) {
      container.innerHTML = '<p style="padding: 20px; color: #999;">Affiliate dashboard data not available</p>'
    }
  }
}

export { loadDashboardData, updateDashboard, loadHistory, loadTabContent, loadBalance }
