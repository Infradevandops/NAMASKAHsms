/**
 * Analytics Manager Module
 * Handles dashboard analytics, statistics, charts, filters, and exports
 */

class AnalyticsManager {
  constructor() {
    this.charts = {};
    this.filters = {
      dateFrom: null,
      dateTo: null,
      services: [],
      countries: [],
      status: []
    };
    this.data = {
      statistics: {},
      dailyStats: [],
      serviceBreakdown: [],
      countryBreakdown: []
    };
  }

  /**
   * Initialize analytics dashboard
   */
  async init() {
    try {
      console.log('Initializing analytics dashboard...');
      
      // Load initial data
      await this.loadStatistics();
      await this.loadCharts();
      
      // Setup filters
      this.setupFilters();
      
      // Setup export buttons
      this.setupExport();
      
      // Setup auto-refresh
      this.setupAutoRefresh();
      
      console.log('Analytics dashboard initialized successfully');
    } catch (error) {
      console.error('Error initializing analytics:', error);
      this.showError('Failed to initialize analytics dashboard');
    }
  }

  /**
   * Load statistics cards
   */
  async loadStatistics() {
    try {
      const token = localStorage.getItem('access_token');
      console.log('Loading statistics with token:', token ? 'present' : 'missing');
      
      const response = await axios.get('/api/analytics/summary', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Statistics loaded:', response.data);
      this.data.statistics = response.data;
      this.renderStatistics();
    } catch (error) {
      console.error('Error loading statistics:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      this.showError('Failed to load statistics');
    }
  }

  /**
   * Render statistics cards
   */
  renderStatistics() {
    const stats = this.data.statistics;
    
    // Total Verifications
    const totalCard = document.getElementById('stat-total-verifications');
    if (totalCard) {
      totalCard.innerHTML = `
        <div class="stat-card">
          <div class="stat-icon bg-primary">
            <i class="fas fa-check-circle"></i>
          </div>
          <div class="stat-content">
            <h6 class="stat-label">Total Verifications</h6>
            <h3 class="stat-value">${stats.total_verifications || 0}</h3>
            <small class="stat-trend ${stats.total_trend > 0 ? 'text-success' : 'text-danger'}">
              <i class="fas fa-${stats.total_trend > 0 ? 'arrow-up' : 'arrow-down'}"></i>
              ${Math.abs(stats.total_trend || 0)}% this month
            </small>
          </div>
        </div>
      `;
    }

    // Success Rate
    const successCard = document.getElementById('stat-success-rate');
    if (successCard) {
      successCard.innerHTML = `
        <div class="stat-card">
          <div class="stat-icon bg-success">
            <i class="fas fa-percentage"></i>
          </div>
          <div class="stat-content">
            <h6 class="stat-label">Success Rate</h6>
            <h3 class="stat-value">${(stats.success_rate || 0).toFixed(1)}%</h3>
            <small class="stat-trend ${stats.success_trend > 0 ? 'text-success' : 'text-danger'}">
              <i class="fas fa-${stats.success_trend > 0 ? 'arrow-up' : 'arrow-down'}"></i>
              ${Math.abs(stats.success_trend || 0).toFixed(1)}% change
            </small>
          </div>
        </div>
      `;
    }

    // Active Rentals
    const activeCard = document.getElementById('stat-active-rentals');
    if (activeCard) {
      activeCard.innerHTML = `
        <div class="stat-card">
          <div class="stat-icon bg-info">
            <i class="fas fa-phone"></i>
          </div>
          <div class="stat-content">
            <h6 class="stat-label">Active Rentals</h6>
            <h3 class="stat-value">${stats.active_rentals || 0}</h3>
            <small class="stat-trend text-muted">
              <i class="fas fa-clock"></i>
              Currently active
            </small>
          </div>
        </div>
      `;
    }

    // Credit Balance
    const creditCard = document.getElementById('stat-credit-balance');
    if (creditCard) {
      creditCard.innerHTML = `
        <div class="stat-card">
          <div class="stat-icon bg-warning">
            <i class="fas fa-coins"></i>
          </div>
          <div class="stat-content">
            <h6 class="stat-label">Credit Balance</h6>
            <h3 class="stat-value">$${(stats.credit_balance || 0).toFixed(2)}</h3>
            <small class="stat-trend text-muted">
              <i class="fas fa-wallet"></i>
              Available balance
            </small>
          </div>
        </div>
      `;
    }
  }

  /**
   * Load chart data
   */
  async loadCharts() {
    try {
      // Build query params from filters
      const params = this.buildFilterParams();
      
      // Load daily stats
      const dailyResponse = await axios.get('/api/analytics/daily-stats', { params });
      this.data.dailyStats = dailyResponse.data;
      
      // Load service breakdown
      const serviceResponse = await axios.get('/api/analytics/service-breakdown', { params });
      this.data.serviceBreakdown = serviceResponse.data;
      
      // Load country breakdown
      const countryResponse = await axios.get('/api/analytics/country-breakdown', { params });
      this.data.countryBreakdown = countryResponse.data;
      
      // Render charts
      this.renderCharts();
    } catch (error) {
      console.error('Error loading chart data:', error);
      this.showError('Failed to load chart data');
    }
  }

  /**
   * Render all charts
   */
  renderCharts() {
    // Destroy existing charts
    Object.values(this.charts).forEach(chart => {
      if (chart) chart.destroy();
    });
    this.charts = {};

    // Create line chart for verifications over time
    this.createVerificationsChart();
    
    // Create line chart for success rate trend
    this.createSuccessRateChart();
    
    // Create pie chart for service breakdown
    this.createServiceChart();
    
    // Create bar chart for country breakdown
    this.createCountryChart();
  }

  /**
   * Create verifications over time chart
   */
  createVerificationsChart() {
    const ctx = document.getElementById('chart-verifications');
    if (!ctx) return;

    const labels = this.data.dailyStats.map(d => d.date);
    const data = this.data.dailyStats.map(d => d.count);

    this.charts.verifications = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Verifications',
          data: data,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: '#007bff',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          title: {
            display: true,
            text: 'Verifications Over Time'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          }
        }
      }
    });
  }

  /**
   * Create success rate trend chart
   */
  createSuccessRateChart() {
    const ctx = document.getElementById('chart-success-rate');
    if (!ctx) return;

    const labels = this.data.dailyStats.map(d => d.date);
    const data = this.data.dailyStats.map(d => d.success_rate);

    this.charts.successRate = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Success Rate (%)',
          data: data,
          borderColor: '#28a745',
          backgroundColor: 'rgba(40, 167, 69, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: '#28a745',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          title: {
            display: true,
            text: 'Success Rate Trend'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function(value) {
                return value + '%';
              }
            }
          }
        }
      }
    });
  }

  /**
   * Create service breakdown pie chart
   */
  createServiceChart() {
    const ctx = document.getElementById('chart-service-breakdown');
    if (!ctx) return;

    const labels = this.data.serviceBreakdown.map(d => d.service);
    const data = this.data.serviceBreakdown.map(d => d.count);
    const colors = [
      '#007bff', '#28a745', '#ffc107', '#dc3545',
      '#17a2b8', '#6f42c1', '#e83e8c', '#fd7e14'
    ];

    this.charts.service = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors.slice(0, labels.length),
          borderColor: '#fff',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'bottom'
          },
          title: {
            display: true,
            text: 'Service Breakdown'
          }
        }
      }
    });
  }

  /**
   * Create country breakdown bar chart
   */
  createCountryChart() {
    const ctx = document.getElementById('chart-country-breakdown');
    if (!ctx) return;

    const labels = this.data.countryBreakdown.map(d => d.country);
    const data = this.data.countryBreakdown.map(d => d.count);

    this.charts.country = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Verifications',
          data: data,
          backgroundColor: '#007bff',
          borderColor: '#0056b3',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        indexAxis: 'y',
        plugins: {
          legend: {
            display: false
          },
          title: {
            display: true,
            text: 'Country Breakdown'
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          }
        }
      }
    });
  }

  /**
   * Setup filter controls
   */
  setupFilters() {
    // Date range filter
    const dateFromInput = document.getElementById('filter-date-from');
    const dateToInput = document.getElementById('filter-date-to');
    
    if (dateFromInput) {
      dateFromInput.addEventListener('change', (e) => {
        this.filters.dateFrom = e.target.value;
        this.applyFilters();
      });
    }
    
    if (dateToInput) {
      dateToInput.addEventListener('change', (e) => {
        this.filters.dateTo = e.target.value;
        this.applyFilters();
      });
    }

    // Service filter
    const serviceFilter = document.getElementById('filter-service');
    if (serviceFilter) {
      serviceFilter.addEventListener('change', (e) => {
        this.filters.services = Array.from(e.target.selectedOptions, option => option.value);
        this.applyFilters();
      });
    }

    // Country filter
    const countryFilter = document.getElementById('filter-country');
    if (countryFilter) {
      countryFilter.addEventListener('change', (e) => {
        this.filters.countries = Array.from(e.target.selectedOptions, option => option.value);
        this.applyFilters();
      });
    }

    // Status filter
    const statusFilter = document.getElementById('filter-status');
    if (statusFilter) {
      statusFilter.addEventListener('change', (e) => {
        this.filters.status = Array.from(e.target.selectedOptions, option => option.value);
        this.applyFilters();
      });
    }

    // Clear filters button
    const clearBtn = document.getElementById('btn-clear-filters');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearFilters());
    }

    // Load filters from localStorage
    this.loadFiltersFromStorage();
  }

  /**
   * Apply filters and reload charts
   */
  async applyFilters() {
    try {
      // Save filters to localStorage
      this.saveFiltersToStorage();
      
      // Reload charts with new filters
      await this.loadCharts();
      
      // Update filter indicators
      this.updateFilterIndicators();
    } catch (error) {
      console.error('Error applying filters:', error);
      this.showError('Failed to apply filters');
    }
  }

  /**
   * Clear all filters
   */
  async clearFilters() {
    this.filters = {
      dateFrom: null,
      dateTo: null,
      services: [],
      countries: [],
      status: []
    };

    // Reset form inputs
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    document.getElementById('filter-service').selectedIndex = -1;
    document.getElementById('filter-country').selectedIndex = -1;
    document.getElementById('filter-status').selectedIndex = -1;

    // Clear localStorage
    localStorage.removeItem('analytics-filters');

    // Reload charts
    await this.loadCharts();
    this.updateFilterIndicators();
  }

  /**
   * Build filter parameters for API
   */
  buildFilterParams() {
    const params = {};
    
    if (this.filters.dateFrom) params.date_from = this.filters.dateFrom;
    if (this.filters.dateTo) params.date_to = this.filters.dateTo;
    if (this.filters.services.length > 0) params.services = this.filters.services.join(',');
    if (this.filters.countries.length > 0) params.countries = this.filters.countries.join(',');
    if (this.filters.status.length > 0) params.status = this.filters.status.join(',');
    
    return params;
  }

  /**
   * Update filter indicators
   */
  updateFilterIndicators() {
    const indicator = document.getElementById('filter-indicator');
    if (!indicator) return;

    const activeFilters = [
      this.filters.dateFrom ? 1 : 0,
      this.filters.dateTo ? 1 : 0,
      this.filters.services.length,
      this.filters.countries.length,
      this.filters.status.length
    ].reduce((a, b) => a + b, 0);

    if (activeFilters > 0) {
      indicator.innerHTML = `<span class="badge bg-primary">${activeFilters} active</span>`;
      indicator.style.display = 'inline-block';
    } else {
      indicator.style.display = 'none';
    }
  }

  /**
   * Save filters to localStorage
   */
  saveFiltersToStorage() {
    localStorage.setItem('analytics-filters', JSON.stringify(this.filters));
  }

  /**
   * Load filters from localStorage
   */
  loadFiltersFromStorage() {
    const stored = localStorage.getItem('analytics-filters');
    if (stored) {
      try {
        this.filters = JSON.parse(stored);
        
        // Restore form values
        if (this.filters.dateFrom) {
          document.getElementById('filter-date-from').value = this.filters.dateFrom;
        }
        if (this.filters.dateTo) {
          document.getElementById('filter-date-to').value = this.filters.dateTo;
        }
      } catch (error) {
        console.error('Error loading filters from storage:', error);
      }
    }
  }

  /**
   * Setup export functionality
   */
  setupExport() {
    const csvBtn = document.getElementById('btn-export-csv');
    const pdfBtn = document.getElementById('btn-export-pdf');
    const emailBtn = document.getElementById('btn-export-email');

    if (csvBtn) {
      csvBtn.addEventListener('click', () => this.exportCSV());
    }

    if (pdfBtn) {
      pdfBtn.addEventListener('click', () => this.exportPDF());
    }

    if (emailBtn) {
      emailBtn.addEventListener('click', () => this.exportEmail());
    }
  }

  /**
   * Export data to CSV
   */
  async exportCSV() {
    try {
      const params = this.buildFilterParams();
      const response = await axios.post('/api/analytics/export', {
        format: 'csv',
        ...params
      }, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analytics-${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);

      this.showSuccess('Analytics exported to CSV');
    } catch (error) {
      console.error('Error exporting CSV:', error);
      this.showError('Failed to export CSV');
    }
  }

  /**
   * Export data to PDF
   */
  async exportPDF() {
    try {
      const params = this.buildFilterParams();
      const response = await axios.post('/api/analytics/export', {
        format: 'pdf',
        ...params
      }, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analytics-${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);

      this.showSuccess('Analytics exported to PDF');
    } catch (error) {
      console.error('Error exporting PDF:', error);
      this.showError('Failed to export PDF');
    }
  }

  /**
   * Export data via email
   */
  async exportEmail() {
    try {
      const email = prompt('Enter email address to send report:');
      if (!email) return;

      const params = this.buildFilterParams();
      await axios.post('/api/analytics/export', {
        format: 'email',
        email: email,
        ...params
      });

      this.showSuccess(`Report sent to ${email}`);
    } catch (error) {
      console.error('Error exporting email:', error);
      this.showError('Failed to send email report');
    }
  }

  /**
   * Setup auto-refresh
   */
  setupAutoRefresh() {
    // Refresh statistics every 30 seconds
    setInterval(() => {
      this.loadStatistics();
    }, 30000);

    // Refresh charts every 5 minutes
    setInterval(() => {
      this.loadCharts();
    }, 300000);
  }

  /**
   * Show success message
   */
  showSuccess(message) {
    // Use toast notification if available
    if (window.showToast) {
      window.showToast(message, 'success');
    } else {
      alert(message);
    }
  }

  /**
   * Show error message
   */
  showError(message) {
    // Use toast notification if available
    if (window.showToast) {
      window.showToast(message, 'error');
    } else {
      alert(message);
    }
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  const analytics = new AnalyticsManager();
  analytics.init();
  window.analyticsManager = analytics;
});
