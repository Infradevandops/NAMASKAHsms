/**
 * Secure Analytics Module - XSS-Safe Implementation
 * Replaces enhanced-analytics.js with security fixes
 */

class SecureAnalytics {
  constructor() {
    this.charts = {};
    this.realTimeInterval = null;
    this.currentPeriod = 30;
    this.init();
  }

  async init() {
    try {
      await this.loadAnalytics();
      this.setupRealTimeUpdates();
      this.setupEventListeners();
    } catch (error) {
      this.handleError('Initialization failed', error);
    }
  }

  async loadAnalytics() {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token');
      }

      const [analyticsResponse, businessResponse, competitiveResponse] = await Promise.all([
        fetch(`/analytics/usage?period=${this.currentPeriod}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/analytics/business-metrics', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/analytics/competitive-analysis')
      ]);

      if (!analyticsResponse.ok) throw new Error('Analytics API failed');
      if (!businessResponse.ok) throw new Error('Business metrics API failed');
      if (!competitiveResponse.ok) throw new Error('Competitive analysis API failed');

      const analytics = await analyticsResponse.json();
      const business = await businessResponse.json();
      const competitive = await competitiveResponse.json();

      this.displayAnalytics(analytics, business, competitive);
    } catch (error) {
      this.handleError('Failed to load analytics', error);
    }
  }

  displayAnalytics(analytics, business, competitive) {
    try {
      this.updateMetrics(analytics, business);
      this.updateCharts(analytics);
      this.updateInsights(analytics);
      this.updatePredictions(analytics.predictions);
      this.updateRecommendations(analytics.recommendations);
    } catch (error) {
      this.handleError('Failed to display analytics', error);
    }
  }

  updateMetrics(analytics, business) {
    const updates = {
      'total-verifications': analytics.total_verifications,
      'success-rate': `${analytics.success_rate}%`,
      'total-spent': `$${analytics.total_spent.toFixed(2)}`,
      'efficiency-score': analytics.efficiency_score
    };

    if (business) {
      Object.assign(updates, {
        revenue: `$${business.revenue.toFixed(2)}`,
        'profit-margin': `${business.profit_margin}%`,
        'growth-rate': `${business.growth_rate}%`,
        clv: `$${business.customer_lifetime_value.toFixed(2)}`
      });
    }

    Object.entries(updates).forEach(([id, value]) => {
      this.updateElementSafe(id, String(value));
    });

    this.updateEfficiencyScore(analytics.efficiency_score);
  }

  updateEfficiencyScore(score) {
    const circle = document.getElementById('efficiency-circle');
    const scoreElement = document.getElementById('efficiency-score');
    
    if (circle && scoreElement) {
      const degrees = Math.min(360, Math.max(0, (score / 100) * 360));
      circle.style.setProperty('--score-deg', `${degrees}deg`);
      scoreElement.textContent = String(score);
      
      const color = score >= 85 ? '#10b981' : score >= 70 ? '#f59e0b' : '#ef4444';
      circle.style.background = `conic-gradient(${color} 0deg, ${color} ${degrees}deg, #f3f4f6 ${degrees}deg)`;
    }
  }

  updateCharts(analytics) {
    try {
      this.createUsageTrendChart(analytics.daily_usage);
      this.createServicePerformanceChart(analytics.popular_services);
      if (analytics.country_performance) {
        this.createCountryChart(analytics.country_performance);
      }
      if (analytics.cost_trends) {
        this.createCostTrendChart(analytics.cost_trends);
      }
    } catch (error) {
      this.handleError('Chart creation failed', error);
    }
  }

  createUsageTrendChart(dailyUsage) {
    const ctx = document.getElementById('usage-trend-chart');
    if (!ctx || !Array.isArray(dailyUsage)) return;

    if (this.charts.usageTrend) {
      this.charts.usageTrend.destroy();
    }

    this.charts.usageTrend = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dailyUsage.map(d => new Date(d.date).toLocaleDateString()),
        datasets: [{
          label: 'Verifications',
          data: dailyUsage.map(d => Number(d.count) || 0),
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4,
          fill: true
        }, {
          label: 'Success Rate (%)',
          data: dailyUsage.map(d => Number(d.success_rate) || 0),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
          yAxisID: 'y1'
        }]
      },
      options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: 'Verifications' } },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: { display: true, text: 'Success Rate (%)' },
            grid: { drawOnChartArea: false },
            max: 100
          }
        }
      }
    });
  }

  createServicePerformanceChart(services) {
    const ctx = document.getElementById('service-performance-chart');
    if (!ctx || !Array.isArray(services)) return;

    if (this.charts.servicePerformance) {
      this.charts.servicePerformance.destroy();
    }

    this.charts.servicePerformance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: services.map(s => String(s.service || 'Unknown')),
        datasets: [{
          label: 'Count',
          data: services.map(s => Number(s.count) || 0),
          backgroundColor: 'rgba(102, 126, 234, 0.8)',
          yAxisID: 'y'
        }, {
          label: 'Success Rate (%)',
          data: services.map(s => Number(s.success_rate) || 0),
          backgroundColor: 'rgba(16, 185, 129, 0.8)',
          yAxisID: 'y1'
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true, title: { display: true, text: 'Count' } },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: { display: true, text: 'Success Rate (%)' },
            grid: { drawOnChartArea: false },
            max: 100
          }
        }
      }
    });
  }

  updatePredictions(predictions) {
    const container = document.getElementById('predictions-container');
    if (!container || !Array.isArray(predictions)) return;

    // Clear container safely
    container.textContent = '';

    if (predictions.length === 0) {
      const noPredictions = document.createElement('p');
      noPredictions.className = 'no-predictions';
      noPredictions.textContent = 'No predictions available';
      container.appendChild(noPredictions);
      return;
    }

    predictions.forEach((pred, index) => {
      const item = document.createElement('div');
      item.className = 'prediction-item';
      item.style.animationDelay = `${index * 0.1}s`;

      const header = document.createElement('div');
      header.className = 'prediction-header';

      const metric = document.createElement('span');
      metric.className = 'prediction-metric';
      metric.textContent = this.formatMetricName(pred.metric || 'Unknown');

      const timeframe = document.createElement('span');
      timeframe.className = 'prediction-timeframe';
      timeframe.textContent = String(pred.timeframe || 'Unknown');

      header.appendChild(metric);
      header.appendChild(timeframe);

      const value = document.createElement('div');
      value.className = 'prediction-value';
      value.textContent = String(pred.prediction || 'N/A');

      const confidenceBar = document.createElement('div');
      confidenceBar.className = 'confidence-bar';

      const confidenceFill = document.createElement('div');
      confidenceFill.className = 'confidence-fill';
      const confidence = Math.min(100, Math.max(0, (pred.confidence || 0) * 100));
      confidenceFill.style.width = `${confidence}%`;

      const confidenceText = document.createElement('span');
      confidenceText.className = 'confidence-text';
      confidenceText.textContent = `${Math.round(confidence)}% confidence`;

      confidenceBar.appendChild(confidenceFill);
      confidenceBar.appendChild(confidenceText);

      item.appendChild(header);
      item.appendChild(value);
      item.appendChild(confidenceBar);
      container.appendChild(item);
    });
  }

  updateRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    if (!container) return;

    container.textContent = '';

    if (!Array.isArray(recommendations) || recommendations.length === 0) {
      const noRecs = document.createElement('p');
      noRecs.className = 'no-recommendations';
      noRecs.textContent = 'No recommendations at this time';
      container.appendChild(noRecs);
      return;
    }

    recommendations.forEach((rec, index) => {
      const item = document.createElement('div');
      item.className = 'recommendation-item';
      item.style.animationDelay = `${index * 0.1}s`;

      const icon = document.createElement('div');
      icon.className = 'recommendation-icon';
      icon.textContent = '💡';

      const text = document.createElement('div');
      text.className = 'recommendation-text';
      text.textContent = String(rec || 'No recommendation text');

      item.appendChild(icon);
      item.appendChild(text);
      container.appendChild(item);
    });
  }

  setupRealTimeUpdates() {
    this.realTimeInterval = setInterval(async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch('/analytics/real-time-insights', {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
          const insights = await response.json();
          this.updateRealTimeInsights(insights);
        }
      } catch (error) {
        console.error('Real-time update failed:', error);
      }
    }, 30000);
  }

  updateRealTimeInsights(insights) {
    const container = document.getElementById('realtime-insights');
    if (!container || !insights) return;

    container.textContent = '';

    const metrics = [
      { label: 'Last 24h Verifications:', value: insights.last_24h?.verifications || 0 },
      { label: 'Current Hour:', value: insights.current_hour?.verifications || 0 },
      { label: 'System Status:', value: insights.system_status || 'unknown' }
    ];

    metrics.forEach(metric => {
      const div = document.createElement('div');
      div.className = 'realtime-metric';

      const label = document.createElement('span');
      label.className = 'metric-label';
      label.textContent = metric.label;

      const value = document.createElement('span');
      value.className = `metric-value ${metric.label.includes('Status') ? `status-${metric.value}` : ''}`;
      value.textContent = String(metric.value);

      div.appendChild(label);
      div.appendChild(value);
      container.appendChild(div);
    });
  }

  setupEventListeners() {
    document.querySelectorAll('.period-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        const period = parseInt(e.target.dataset.period);
        if (!isNaN(period)) {
          this.setPeriod(period);
        }
      });
    });

    const exportBtn = document.getElementById('export-analytics');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportAnalytics());
    }

    const refreshBtn = document.getElementById('refresh-analytics');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.loadAnalytics());
    }
  }

  setPeriod(period) {
    this.currentPeriod = period;
    
    document.querySelectorAll('.period-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`[data-period="${period}"]`);
    if (activeBtn) {
      activeBtn.classList.add('active');
    }
    
    this.loadAnalytics();
  }

  async exportAnalytics() {
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`/analytics/export?period=${this.currentPeriod}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      const data = await response.json();
      this.downloadJSON(data, `analytics-${this.currentPeriod}d.json`);
    } catch (error) {
      this.handleError('Export failed', error);
    }
  }

  downloadJSON(data, filename) {
    try {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      this.handleError('Download failed', error);
    }
  }

  updateElementSafe(id, content) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = content;
    }
  }

  formatMetricName(metric) {
    return String(metric).replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  handleError(message, error) {
    console.error(message, error);
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
      errorContainer.textContent = '';
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message';
      errorDiv.textContent = message;
      errorContainer.appendChild(errorDiv);
      
      setTimeout(() => {
        errorContainer.textContent = '';
      }, 5000);
    }
  }

  destroy() {
    if (this.realTimeInterval) {
      clearInterval(this.realTimeInterval);
    }
    
    Object.values(this.charts).forEach(chart => {
      if (chart && typeof chart.destroy === 'function') {
        chart.destroy();
      }
    });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.secureAnalytics = new SecureAnalytics();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.secureAnalytics) {
    window.secureAnalytics.destroy();
  }
});

window.SecureAnalytics = SecureAnalytics;