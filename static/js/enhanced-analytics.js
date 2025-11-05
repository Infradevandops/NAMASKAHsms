/**
 * Enhanced Analytics Module
 * Advanced analytics with real-time insights, predictions, and business intelligence
 */

class EnhancedAnalytics {
    constructor() {
        this.charts = {};
        this.realTimeInterval = null;
        this.currentPeriod = 30;
        this.init();
    }

    async init() {
        await this.loadAnalytics();
        this.setupRealTimeUpdates();
        this.setupEventListeners();
    }

    async loadAnalytics() {
        try {
            const token = localStorage.getItem('token');
            
            // Load main analytics
            const analyticsResponse = await fetch(`/analytics/usage?period=${this.currentPeriod}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const analytics = await analyticsResponse.json();
            
            // Load business metrics
            const businessResponse = await fetch('/analytics/business-metrics', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const business = await businessResponse.json();
            
            // Load competitive analysis
            const competitiveResponse = await fetch('/analytics/competitive-analysis');
            const competitive = await competitiveResponse.json();
            
            this.displayAnalytics(analytics, business, competitive);
        } catch (error) {
            console.error('Failed to load analytics:', error);
            this.showError('Failed to load analytics data');
        }
    }

    displayAnalytics(analytics, business, competitive) {
        this.updateMetrics(analytics, business);
        this.updateCharts(analytics);
        this.updateInsights(analytics);
        this.updateCompetitiveAnalysis(competitive);
        this.updatePredictions(analytics.predictions);
        this.updateRecommendations(analytics.recommendations);
    }

    updateMetrics(analytics, business) {
        // Core metrics
        this.updateElement('total-verifications', analytics.total_verifications);
        this.updateElement('success-rate', `${analytics.success_rate}%`);
        this.updateElement('total-spent', `$${analytics.total_spent.toFixed(2)}`);
        this.updateElement('efficiency-score', analytics.efficiency_score);
        
        // Business metrics
        if (business) {
            this.updateElement('revenue', `$${business.revenue.toFixed(2)}`);
            this.updateElement('profit-margin', `${business.profit_margin}%`);
            this.updateElement('growth-rate', `${business.growth_rate}%`);
            this.updateElement('clv', `$${business.customer_lifetime_value.toFixed(2)}`);
        }
        
        // Update efficiency score circle
        this.updateEfficiencyScore(analytics.efficiency_score);
    }

    updateEfficiencyScore(score) {
        const circle = document.getElementById('efficiency-circle');
        const scoreElement = document.getElementById('efficiency-score');
        
        if (circle && scoreElement) {
            const degrees = (score / 100) * 360;
            circle.style.setProperty('--score-deg', `${degrees}deg`);
            scoreElement.textContent = score;
            
            // Add color coding
            let color = '#ef4444'; // Red for low scores
            if (score >= 70) color = '#f59e0b'; // Yellow for medium
            if (score >= 85) color = '#10b981'; // Green for high
            
            circle.style.background = `conic-gradient(${color} 0deg, ${color} ${degrees}deg, #f3f4f6 ${degrees}deg)`;
        }
    }

    updateCharts(analytics) {
        this.createUsageTrendChart(analytics.daily_usage);
        this.createServicePerformanceChart(analytics.popular_services);
        this.createCountryChart(analytics.country_performance);
        this.createCostTrendChart(analytics.cost_trends);
    }

    createUsageTrendChart(dailyUsage) {
        const ctx = document.getElementById('usage-trend-chart');
        if (!ctx) return;

        if (this.charts.usageTrend) {
            this.charts.usageTrend.destroy();
        }

        this.charts.usageTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dailyUsage.map(d => new Date(d.date).toLocaleDateString()),
                datasets: [{
                    label: 'Verifications',
                    data: dailyUsage.map(d => d.count),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Success Rate (%)',
                    data: dailyUsage.map(d => d.success_rate),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Verifications' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Success Rate (%)' },
                        grid: { drawOnChartArea: false },
                        max: 100
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const dataIndex = context.dataIndex;
                                const cost = dailyUsage[dataIndex].cost;
                                return `Cost: $${cost.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    createServicePerformanceChart(services) {
        const ctx = document.getElementById('service-performance-chart');
        if (!ctx) return;

        if (this.charts.servicePerformance) {
            this.charts.servicePerformance.destroy();
        }

        this.charts.servicePerformance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: services.map(s => s.service),
                datasets: [{
                    label: 'Count',
                    data: services.map(s => s.count),
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    yAxisID: 'y'
                }, {
                    label: 'Success Rate (%)',
                    data: services.map(s => s.success_rate),
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Count' }
                    },
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

    createCountryChart(countries) {
        const ctx = document.getElementById('country-chart');
        if (!ctx || !countries.length) return;

        if (this.charts.country) {
            this.charts.country.destroy();
        }

        this.charts.country = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: countries.map(c => c.country),
                datasets: [{
                    data: countries.map(c => c.count),
                    backgroundColor: [
                        '#667eea', '#10b981', '#f59e0b', '#ef4444',
                        '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const country = countries[context.dataIndex];
                                return [
                                    `Success Rate: ${country.success_rate}%`,
                                    `Avg Cost: $${country.avg_cost}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }

    createCostTrendChart(trends) {
        const ctx = document.getElementById('cost-trend-chart');
        if (!ctx || !trends.length) return;

        if (this.charts.costTrend) {
            this.charts.costTrend.destroy();
        }

        this.charts.costTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trends.map(t => t.period),
                datasets: [{
                    label: 'Weekly Cost',
                    data: trends.map(t => t.value),
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Cost ($)' }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const trend = trends[context.dataIndex];
                                if (trend.change_percent !== null) {
                                    const direction = trend.change_percent >= 0 ? '↑' : '↓';
                                    return `Change: ${direction} ${Math.abs(trend.change_percent)}%`;
                                }
                                return '';
                            }
                        }
                    }
                }
            }
        });
    }

    updateInsights(analytics) {
        // Update efficiency insights
        const efficiencyInsights = this.generateEfficiencyInsights(analytics);
        this.updateElement('efficiency-insights', efficiencyInsights, true);
        
        // Update cost optimization insights
        const costInsights = this.generateCostInsights(analytics);
        this.updateElement('cost-insights', costInsights, true);
    }

    generateEfficiencyInsights(analytics) {
        const insights = [];
        
        if (analytics.success_rate < 70) {
            insights.push('⚠️ Success rate below optimal threshold');
        } else if (analytics.success_rate > 90) {
            insights.push('✅ Excellent success rate performance');
        }
        
        if (analytics.efficiency_score > 85) {
            insights.push('🎯 High efficiency score - great optimization');
        } else if (analytics.efficiency_score < 60) {
            insights.push('📈 Efficiency can be improved');
        }
        
        return insights.length > 0 ? insights.join('<br>') : 'No specific insights available';
    }

    generateCostInsights(analytics) {
        const insights = [];
        
        if (analytics.popular_services.length > 0) {
            const cheapestService = analytics.popular_services.reduce((min, service) => 
                service.avg_cost < min.avg_cost ? service : min
            );
            insights.push(`💰 Most cost-effective: ${cheapestService.service} ($${cheapestService.avg_cost})`);
            
            const mostExpensive = analytics.popular_services.reduce((max, service) => 
                service.avg_cost > max.avg_cost ? service : max
            );
            if (mostExpensive.avg_cost > cheapestService.avg_cost * 1.5) {
                insights.push(`💸 Consider alternatives to ${mostExpensive.service} for cost savings`);
            }
        }
        
        return insights.length > 0 ? insights.join('<br>') : 'No cost insights available';
    }

    updateCompetitiveAnalysis(competitive) {
        if (!competitive) return;
        
        // Update market position
        this.updateElement('market-position', competitive.market_position);
        
        // Update performance benchmark
        this.updateElement('performance-benchmark', `${competitive.performance_benchmark}%`);
        
        // Create cost comparison chart
        this.createCostComparisonChart(competitive.cost_comparison);
    }

    createCostComparisonChart(costComparison) {
        const ctx = document.getElementById('cost-comparison-chart');
        if (!ctx) return;

        if (this.charts.costComparison) {
            this.charts.costComparison.destroy();
        }

        const services = Object.keys(costComparison);
        const costs = Object.values(costComparison);

        this.charts.costComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: services,
                datasets: [{
                    label: 'Market Price ($)',
                    data: costs,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Price ($)' }
                    }
                }
            }
        });
    }

    updatePredictions(predictions) {
        const container = document.getElementById('predictions-container');
        if (!container || !predictions.length) return;

        container.innerHTML = predictions.map(pred => `
            <div class="prediction-item">
                <div class="prediction-header">
                    <span class="prediction-metric">${this.formatMetricName(pred.metric)}</span>
                    <span class="prediction-timeframe">${pred.timeframe}</span>
                </div>
                <div class="prediction-value">${pred.prediction}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${pred.confidence * 100}%"></div>
                    <span class="confidence-text">${Math.round(pred.confidence * 100)}% confidence</span>
                </div>
            </div>
        `).join('');
    }

    updateRecommendations(recommendations) {
        const container = document.getElementById('recommendations-container');
        if (!container) return;

        if (!recommendations.length) {
            container.innerHTML = '<p class="no-recommendations">No recommendations at this time</p>';
            return;
        }

        container.innerHTML = recommendations.map((rec, index) => `
            <div class="recommendation-item" style="animation-delay: ${index * 0.1}s">
                <div class="recommendation-icon">💡</div>
                <div class="recommendation-text">${rec}</div>
            </div>
        `).join('');
    }

    setupRealTimeUpdates() {
        // Update real-time insights every 30 seconds
        this.realTimeInterval = setInterval(async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch('/analytics/real-time-insights', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const insights = await response.json();
                this.updateRealTimeInsights(insights);
            } catch (error) {
                console.error('Failed to load real-time insights:', error);
            }
        }, 30000);
    }

    updateRealTimeInsights(insights) {
        const container = document.getElementById('realtime-insights');
        if (!container) return;

        container.innerHTML = `
            <div class="realtime-metric">
                <span class="metric-label">Last 24h Verifications:</span>
                <span class="metric-value">${insights.last_24h.verifications}</span>
            </div>
            <div class="realtime-metric">
                <span class="metric-label">Current Hour:</span>
                <span class="metric-value">${insights.current_hour.verifications}</span>
            </div>
            <div class="realtime-metric">
                <span class="metric-label">System Status:</span>
                <span class="metric-value status-${insights.system_status}">${insights.system_status}</span>
            </div>
        `;
    }

    setupEventListeners() {
        // Period selector
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const period = parseInt(e.target.dataset.period);
                this.setPeriod(period);
            });
        });

        // Export functionality
        const exportBtn = document.getElementById('export-analytics');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportAnalytics());
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-analytics');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadAnalytics());
        }
    }

    setPeriod(period) {
        this.currentPeriod = period;
        
        // Update active button
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-period="${period}"]`).classList.add('active');
        
        this.loadAnalytics();
    }

    async exportAnalytics() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/analytics/export?period=${this.currentPeriod}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            const data = await response.json();
            this.downloadJSON(data, `analytics-${this.currentPeriod}d.json`);
        } catch (error) {
            console.error('Export failed:', error);
            this.showError('Failed to export analytics');
        }
    }

    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    updateElement(id, content, isHTML = false) {
        const element = document.getElementById(id);
        if (element) {
            if (isHTML) {
                element.innerHTML = content;
            } else {
                element.textContent = content;
            }
        }
    }

    formatMetricName(metric) {
        return metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    showError(message) {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
            setTimeout(() => {
                errorContainer.innerHTML = '';
            }, 5000);
        }
    }

    destroy() {
        // Clean up intervals
        if (this.realTimeInterval) {
            clearInterval(this.realTimeInterval);
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedAnalytics = new EnhancedAnalytics();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.enhancedAnalytics) {
        window.enhancedAnalytics.destroy();
    }
});

// Export for global use
window.EnhancedAnalytics = EnhancedAnalytics;