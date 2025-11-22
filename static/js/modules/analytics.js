// Analytics Module
import axios from 'axios'
import Chart from 'chart.js/auto'

export function initAnalytics() {
  loadAnalyticsData()
  setInterval(loadAnalyticsData, 60000)
}

async function loadAnalyticsData() {
  try {
    const response = await axios.get('/api/analytics/stats')
    updateCharts(response.data)
  } catch (error) {
    console.error('Failed to load analytics:', error)
  }
}

function updateCharts(data) {
  createVerificationChart(data.verifications)
  createRevenueChart(data.revenue)
  createSuccessRateChart(data.success_rates)
}

function createVerificationChart(data) {
  const ctx = document.getElementById('verification-chart')
  if (!ctx) return

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Verifications',
        data: data.values,
        borderColor: '#007bff',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } }
    }
  })
}

function createRevenueChart(data) {
  const ctx = document.getElementById('revenue-chart')
  if (!ctx) return

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Revenue',
        data: data.values,
        backgroundColor: '#28a745'
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } }
    }
  })
}

function createSuccessRateChart(data) {
  const ctx = document.getElementById('success-rate-chart')
  if (!ctx) return

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Success', 'Failed'],
      datasets: [{
        data: [data.success, data.failed],
        backgroundColor: ['#28a745', '#dc3545']
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } }
    }
  })
}

export { loadAnalyticsData, updateCharts, createVerificationChart, createRevenueChart, createSuccessRateChart }
