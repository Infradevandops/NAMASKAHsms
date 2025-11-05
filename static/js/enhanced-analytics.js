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

    // Input sanitization methods
    sanitizeString(input) {
        if (typeof input !== 'string') {
            return String(input || '');
        }
        return input.replace(/[<>"'&]/g, (match) => {
            const entities = {
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;',
                '&': '&amp;'
            };
            return entities[match] || match;
        });
    }

    validateNumeric(value, min = 0, max = Number.MAX_SAFE_INTEGER) {
        const num = Number(value);
        if (isNaN(num)) return 0;
        return Math.min(Math.max(num, min), max);
    }

    validatePeriod(period) {
        const validPeriods = [7, 30, 90];
        return validPeriods.includes(Number(period)) ? Number(period) : 30;
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
            const safePeriod = this.validatePeriod(this.currentPeriod);
            const analyticsResponse = await fetch(`/analytics/usage?period=${safePeriod}`, {
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
        // Core metrics with validation
        this.updateElement('total-verifications', this.validateNumeric(analytics.total_verifications));
        this.updateElement('success-rate', `${this.validateNumeric(analytics.success_rate, 0, 100).toFixed(1)}%`);
        this.updateElement('total-spent', `$${this.validateNumeric(analytics.total_spent).toFixed(2)}`);
        this.updateElement('efficiency-score', this.validateNumeric(analytics.efficiency_score, 0, 100));
        
        // Business metrics with validation
        if (business) {
            this.updateElement('revenue', `$${this.validateNumeric(business.revenue).toFixed(2)}`);
            this.updateElement('profit-margin', `${this.validateNumeric(business.profit_margin, -100, 100).toFixed(1)}%`);
            this.updateElement('growth-rate', `${this.validateNumeric(business.growth_rate, -100, 1000).toFixed(1)}%`);
            this.updateElement('clv', `$${this.validateNumeric(business.customer_lifetime_value).toFixed(2)}`);
        }
        
        // Update efficiency score circle
        this.updateEfficiencyScore(analytics.efficiency_score);
    }

    updateEfficiencyScore(score) {
        const circle = document.getElementById('efficiency-circle');
        const scoreElement = document.getElementById('efficiency-score');
        
        if (circle && scoreElement) {
            const safeScore = this.validateNumeric(score, 0, 100);
            const degrees = (safeScore / 100) * 360;
            circle.style.setProperty('--score-deg', `${degrees}deg`);
            scoreElement.textContent = safeScore;
            
            // Add color coding with safe values
            let color = '#ef4444'; // Red for low scores
            if (safeScore >= 70) {color = '#f59e0b';} // Yellow for medium
            if (safeScore >= 85) {color = '#10b981';} // Green for high
            
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
        if (!ctx) {return;}

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
        if (!ctx) {return;}

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
        if (!ctx || !countries.length) {return;}

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
        if (!ctx || !trends.length) {return;}

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
        this.updateElement('efficiency-insights', efficiencyInsights);
        
        // Update cost optimization insights
        const costInsights = this.generateCostInsights(analytics);
        this.updateElement('cost-insights', costInsights);
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
        
        return insights.length > 0 ? insights.join(' | ') : 'No specific insights available';
    }

    generateCostInsights(analytics) {
        const insights = [];
        
        if (analytics.popular_services && analytics.popular_services.length > 0) {
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
        
        return insights.length > 0 ? insights.join(' | ') : 'No cost insights available';
    }

    updateCompetitiveAnalysis(competitive) {
        if (!competitive) {return;}
        
        // Update market position with sanitization
        this.updateElement('market-position', this.sanitizeString(competitive.market_position));
        
        // Update performance benchmark with validation
        this.updateElement('performance-benchmark', `${this.validateNumeric(competitive.performance_benchmark, 0, 100).toFixed(1)}%`);
        
        // Create cost comparison chart
        this.createCostComparisonChart(competitive.cost_comparison);
    }

    createCostComparisonChart(costComparison) {
        const ctx = document.getElementById('cost-comparison-chart');
        if (!ctx) {return;}

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
        if (!container) {return;}

        container.textContent = '';

        if (!predictions.length) {
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
            metric.textContent = this.sanitizeString(this.formatMetricName(pred.metric || 'Unknown'));

            const timeframe = document.createElement('span');
            timeframe.className = 'prediction-timeframe';
            timeframe.textContent = this.sanitizeString(pred.timeframe || 'Unknown');

            header.appendChild(metric);
            header.appendChild(timeframe);

            const value = document.createElement('div');
            value.className = 'prediction-value';
            value.textContent = this.sanitizeString(pred.prediction || 'N/A');

            const confidenceBar = document.createElement('div');
            confidenceBar.className = 'confidence-bar';

            const confidenceFill = document.createElement('div');
            confidenceFill.className = 'confidence-fill';
            const confidence = this.validateNumeric((pred.confidence || 0) * 100, 0, 100);
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
        if (!container) {return;}

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
            text.textContent = this.sanitizeString(rec || 'No recommendation text');

            item.appendChild(icon);
            item.appendChild(text);
            container.appendChild(item);
        });
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
        if (!container || !insights) {return;}

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
            value.className = metric.label.includes('Status') ? `metric-value status-${String(metric.value)}` : 'metric-value';
            value.textContent = String(metric.value);

            div.appendChild(label);
            div.appendChild(value);
            container.appendChild(div);
        });
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
        this.currentPeriod = this.validatePeriod(period);
        
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
            const safePeriod = this.validatePeriod(this.currentPeriod);
            const response = await fetch(`/analytics/export?period=${safePeriod}`, {
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
        const safeFilename = this.sanitizeString(filename).replace(/[^a-zA-Z0-9.-]/g, '_');
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = safeFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = this.sanitizeString(content || '');
        }
    }

    formatMetricName(metric) {
        const safeMetric = this.sanitizeString(metric || '');
        return safeMetric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    showError(message) {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.textContent = '';
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = this.sanitizeString(message || 'An error occurred');
            errorContainer.appendChild(errorDiv);
            
            setTimeout(() => {
                errorContainer.textContent = '';
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
            if (chart) {chart.destroy();}
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