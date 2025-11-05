/**
 * Enhanced Analytics Module
 * Advanced analytics with real-time insights, predictions, and business intelligence
 */

class EnhancedAnalytics {
    constructor() {
        this.charts = {};
        this.realTimeInterval = null;
        this.currentPeriod = 30;
        this.errorCount = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000;
        this.isOnline = navigator.onLine;
        this.setupGlobalErrorHandling();
        this.init();
    }

    setupGlobalErrorHandling() {
        // Global error handler for unhandled errors
        window.addEventListener('error', (event) => {
            this.handleGlobalError('JavaScript Error', event.error);
        });

        // Global handler for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleGlobalError('Promise Rejection', event.reason);
            event.preventDefault();
        });

        // Network status monitoring
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showNotification('Connection restored', 'success');
            this.loadAnalytics();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showNotification('Connection lost - working offline', 'warning');
        });
    }

    handleGlobalError(type, error) {
        console.error(`${type}:`, error);
        this.errorCount++;
        
        if (this.errorCount > 5) {
            this.showError('Multiple errors detected. Please refresh the page.');
            return;
        }
        
        this.showError(`${type}: ${error.message || error}`);
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
        try {
            this.showLoadingState(true);
            await this.loadAnalytics();
            this.setupRealTimeUpdates();
            this.setupEventListeners();
            this.showLoadingState(false);
        } catch (error) {
            this.handleInitError(error);
        }
    }

    handleInitError(error) {
        console.error('Initialization failed:', error);
        this.showLoadingState(false);
        this.showError('Failed to initialize analytics. Please refresh the page.');
        
        // Retry initialization after delay
        setTimeout(() => {
            if (this.errorCount < this.maxRetries) {
                this.init();
            }
        }, this.retryDelay * this.errorCount);
    }

    showLoadingState(isLoading) {
        const loadingElements = document.querySelectorAll('.loading-indicator');
        const contentElements = document.querySelectorAll('.analytics-content');
        
        loadingElements.forEach(el => {
            el.style.display = isLoading ? 'block' : 'none';
        });
        
        contentElements.forEach(el => {
            el.style.opacity = isLoading ? '0.5' : '1';
        });
    }

    async loadAnalytics() {
        if (!this.isOnline) {
            this.showError('No internet connection. Please check your network.');
            return;
        }

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('Authentication token not found');
            }

            this.showLoadingState(true);
            
            // Load analytics with timeout and retry logic
            const analytics = await this.fetchWithRetry('/analytics/usage', {
                period: this.validatePeriod(this.currentPeriod)
            }, token);
            
            const business = await this.fetchWithRetry('/analytics/business-metrics', {}, token);
            const competitive = await this.fetchWithRetry('/analytics/competitive-analysis', {});
            
            this.displayAnalytics(analytics, business, competitive);
            this.errorCount = 0; // Reset error count on success
            this.showLoadingState(false);
            
        } catch (error) {
            this.handleLoadError(error);
        }
    }

    async fetchWithRetry(endpoint, params = {}, token = null, retries = 3) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        for (let i = 0; i < retries; i++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
                
                const response = await fetch(url, {
                    headers,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    if (response.status === 401) {
                        throw new Error('Authentication failed. Please log in again.');
                    }
                    if (response.status === 403) {
                        throw new Error('Access denied. Insufficient permissions.');
                    }
                    if (response.status >= 500) {
                        throw new Error(`Server error (${response.status}). Please try again later.`);
                    }
                    throw new Error(`Request failed with status ${response.status}`);
                }
                
                return await response.json();
                
            } catch (error) {
                if (error.name === 'AbortError') {
                    throw new Error('Request timeout. Please check your connection.');
                }
                
                if (i === retries - 1) {
                    throw error;
                }
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * (i + 1)));
            }
        }
    }

    handleLoadError(error) {
        console.error('Failed to load analytics:', error);
        this.showLoadingState(false);
        this.errorCount++;
        
        let errorMessage = 'Failed to load analytics data';
        
        if (error.message.includes('Authentication')) {
            errorMessage = 'Session expired. Please log in again.';
            setTimeout(() => {
                window.location.href = '/login';
            }, 3000);
        } else if (error.message.includes('timeout')) {
            errorMessage = 'Request timed out. Please try again.';
        } else if (error.message.includes('Server error')) {
            errorMessage = 'Server is temporarily unavailable. Please try again later.';
        }
        
        this.showError(errorMessage);
        
        // Show retry button for recoverable errors
        if (!error.message.includes('Authentication')) {
            this.showRetryOption();
        }
    }

    displayAnalytics(analytics, business, competitive) {
        try {
            if (!analytics) {
                throw new Error('Analytics data is missing');
            }
            
            this.updateMetrics(analytics, business);
            this.updateCharts(analytics);
            this.updateInsights(analytics);
            this.updateCompetitiveAnalysis(competitive);
            this.updatePredictions(analytics.predictions || []);
            this.updateRecommendations(analytics.recommendations || []);
            
        } catch (error) {
            console.error('Failed to display analytics:', error);
            this.showError('Failed to display analytics data');
        }
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
        
        } catch (error) {
            console.error('Failed to create usage trend chart:', error);
            this.showChartError(document.getElementById('usage-trend-chart'), 'Failed to load chart');
        }
    }

    showChartError(canvas, message) {
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#6b7280';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(message, canvas.width / 2, canvas.height / 2);
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
            item.style.animationDelay = `${this.validateNumeric(index * 0.1, 0, 10)}s`;

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
            confidenceFill.style.width = `${this.validateNumeric(confidence, 0, 100)}%`;

            const confidenceText = document.createElement('span');
            confidenceText.className = 'confidence-text';
            confidenceText.textContent = `${this.validateNumeric(Math.round(confidence), 0, 100)}% confidence`;

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
            item.style.animationDelay = `${this.validateNumeric(index * 0.1, 0, 10)}s`;

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
            label.textContent = this.sanitizeString(metric.label);

            const value = document.createElement('span');
            value.className = metric.label.includes('Status') ? `metric-value status-${this.sanitizeString(metric.value)}` : 'metric-value';
            value.textContent = this.sanitizeString(metric.value);

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
            }, 8000);
        }
        
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = this.sanitizeString(message);
        
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '6px',
            color: 'white',
            fontWeight: '500',
            zIndex: '10000',
            maxWidth: '400px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        });
        
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, type === 'error' ? 8000 : 5000);
    }

    showRetryOption() {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            const retryBtn = document.createElement('button');
            retryBtn.textContent = 'Retry';
            retryBtn.className = 'retry-btn';
            retryBtn.style.cssText = `
                margin-left: 10px;
                padding: 6px 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            `;
            
            retryBtn.addEventListener('click', () => {
                errorContainer.textContent = '';
                this.loadAnalytics();
            });
            
            errorContainer.appendChild(retryBtn);
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