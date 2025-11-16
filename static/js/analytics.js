/**
 * Verification Analytics - Task 4
 * Display success rates and statistics
 */

// Load and display analytics
async function loadAnalytics() {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            showAnalyticsError('Please login to view analytics');
            return;
        }
        
        // Show loading state
        showAnalyticsLoading();
        
        const response = await fetch('/api/verify/analytics', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load analytics');
        }
        
        const data = await response.json();
        
        if (data.success) {
            displayAnalytics(data);
        } else {
            showAnalyticsError(data.error || 'Failed to load analytics');
        }
        
    } catch (error) {
        console.error('Analytics error:', error);
        showAnalyticsError('Failed to load analytics. Please try again.');
    }
}

// Display analytics data
function displayAnalytics(data) {
    const container = document.getElementById('analytics-container');
    
    if (!container) {
        console.error('Analytics container not found');
        return;
    }
    
    // Check if user has any verifications
    if (data.total_verifications === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #6b7280;">
                <div style="font-size: 4rem; margin-bottom: 16px; opacity: 0.5;">📊</div>
                <h3 style="color: #374151; margin-bottom: 8px;">No Analytics Yet</h3>
                <p>Start using verifications to see your success rates and statistics</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <!-- Overall Stats -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px;">
            <div class="stat-card">
                <div class="stat-value" style="color: #6366f1;">${data.overall_rate}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #10b981;">${data.successful}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #ef4444;">${data.failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #f59e0b;">${data.pending || 0}</div>
                <div class="stat-label">Pending</div>
            </div>
        </div>
        
        <!-- By Service -->
        <div style="margin-bottom: 32px;">
            <h3 style="color: #1f2937; margin-bottom: 16px; font-size: 18px; font-weight: 600;">📱 Success Rate by Service</h3>
            <div id="service-stats"></div>
        </div>
        
        <!-- By Country -->
        <div style="margin-bottom: 32px;">
            <h3 style="color: #1f2937; margin-bottom: 16px; font-size: 18px; font-weight: 600;">🌍 Success Rate by Country</h3>
            <div id="country-stats"></div>
        </div>
        
        <!-- Recent Trend -->
        <div style="margin-bottom: 32px;">
            <h3 style="color: #1f2937; margin-bottom: 16px; font-size: 18px; font-weight: 600;">📈 Recent Trend (Last 30 Days)</h3>
            <div id="trend-chart"></div>
        </div>
        
        <!-- Recommendations -->
        <div id="recommendations"></div>
    `;
    
    // Add CSS for stat cards
    addAnalyticsStyles();
    
    // Display service stats
    displayServiceStats(data.by_service);
    
    // Display country stats
    displayCountryStats(data.by_country);
    
    // Display trend
    displayTrend(data.recent_trend);
    
    // Display recommendations
    displayRecommendations(data);
}

// Display service statistics
function displayServiceStats(byService) {
    const container = document.getElementById('service-stats');
    
    if (!byService || Object.keys(byService).length === 0) {
        container.innerHTML = '<p style="color: #6b7280;">No service data available</p>';
        return;
    }
    
    let html = '';
    for (const [service, stats] of Object.entries(byService)) {
        const rateColor = stats.rate >= 80 ? '#10b981' : stats.rate >= 60 ? '#f59e0b' : '#ef4444';
        html += `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: #f9fafb; border-radius: 8px; margin-bottom: 8px;">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #1f2937; text-transform: capitalize;">${service}</div>
                    <div style="font-size: 13px; color: #6b7280;">${stats.successful}/${stats.total} successful</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: 700; color: ${rateColor};">${stats.rate.toFixed(1)}%</div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Display country statistics
function displayCountryStats(byCountry) {
    const container = document.getElementById('country-stats');
    
    if (!byCountry || Object.keys(byCountry).length === 0) {
        container.innerHTML = '<p style="color: #6b7280;">No country data available</p>';
        return;
    }
    
    let html = '';
    for (const [country, stats] of Object.entries(byCountry)) {
        const rateColor = stats.rate >= 80 ? '#10b981' : stats.rate >= 60 ? '#f59e0b' : '#ef4444';
        html += `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: #f9fafb; border-radius: 8px; margin-bottom: 8px;">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #1f2937; text-transform: uppercase;">${country}</div>
                    <div style="font-size: 13px; color: #6b7280;">${stats.successful}/${stats.total} successful</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: 700; color: ${rateColor};">${stats.rate.toFixed(1)}%</div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Display trend chart (simple bar chart)
function displayTrend(trend) {
    const container = document.getElementById('trend-chart');
    
    if (!trend || trend.length === 0) {
        container.innerHTML = '<p style="color: #6b7280;">No recent activity</p>';
        return;
    }
    
    // Find max for scaling
    const maxTotal = Math.max(...trend.map(t => t.total));
    
    let html = '<div style="display: flex; gap: 4px; align-items: flex-end; height: 200px;">';
    
    for (const day of trend) {
        const height = (day.total / maxTotal) * 180;
        const rateColor = day.rate >= 80 ? '#10b981' : day.rate >= 60 ? '#f59e0b' : '#ef4444';
        
        html += `
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;">
                <div style="width: 100%; background: ${rateColor}; height: ${height}px; border-radius: 4px 4px 0 0; position: relative; cursor: pointer;" 
                     title="${day.date}: ${day.successful}/${day.total} (${day.rate}%)">
                </div>
                <div style="font-size: 10px; color: #6b7280; writing-mode: vertical-rl; transform: rotate(180deg);">
                    ${day.date.split('-')[2]}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    html += '<div style="margin-top: 12px; font-size: 12px; color: #6b7280; text-align: center;">Last 30 days</div>';
    
    container.innerHTML = html;
}

// Display recommendations
function displayRecommendations(data) {
    const container = document.getElementById('recommendations');
    
    const recommendations = [];
    
    // Low overall rate
    if (data.overall_rate < 70) {
        recommendations.push({
            icon: '⚠️',
            title: 'Low Success Rate',
            message: 'Your overall success rate is below 70%. Try using different countries or services.',
            type: 'warning'
        });
    }
    
    // High success rate
    if (data.overall_rate >= 90) {
        recommendations.push({
            icon: '🎉',
            title: 'Excellent Success Rate!',
            message: 'You\'re doing great! Your success rate is above 90%.',
            type: 'success'
        });
    }
    
    // Find best service
    if (data.by_service && Object.keys(data.by_service).length > 0) {
        const bestService = Object.entries(data.by_service)
            .sort((a, b) => b[1].rate - a[1].rate)[0];
        
        if (bestService && bestService[1].rate >= 80) {
            recommendations.push({
                icon: '⭐',
                title: 'Best Service',
                message: `${bestService[0]} has your highest success rate (${bestService[1].rate.toFixed(1)}%)`,
                type: 'info'
            });
        }
    }
    
    // Find best country
    if (data.by_country && Object.keys(data.by_country).length > 0) {
        const bestCountry = Object.entries(data.by_country)
            .sort((a, b) => b[1].rate - a[1].rate)[0];
        
        if (bestCountry && bestCountry[1].rate >= 80) {
            recommendations.push({
                icon: '🌟',
                title: 'Best Country',
                message: `${bestCountry[0].toUpperCase()} has your highest success rate (${bestCountry[1].rate.toFixed(1)}%)`,
                type: 'info'
            });
        }
    }
    
    if (recommendations.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<h3 style="color: #1f2937; margin-bottom: 16px; font-size: 18px; font-weight: 600;">💡 Recommendations</h3>';
    
    for (const rec of recommendations) {
        const bgColor = rec.type === 'success' ? '#d1fae5' : rec.type === 'warning' ? '#fef3c7' : '#dbeafe';
        const borderColor = rec.type === 'success' ? '#10b981' : rec.type === 'warning' ? '#f59e0b' : '#3b82f6';
        
        html += `
            <div style="padding: 16px; background: ${bgColor}; border-left: 4px solid ${borderColor}; border-radius: 8px; margin-bottom: 12px;">
                <div style="display: flex; align-items: start; gap: 12px;">
                    <div style="font-size: 24px;">${rec.icon}</div>
                    <div>
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 4px;">${rec.title}</div>
                        <div style="color: #374151; font-size: 14px;">${rec.message}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Show loading state
function showAnalyticsLoading() {
    const container = document.getElementById('analytics-container');
    if (container) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <div class="loading" style="width: 40px; height: 40px; border-width: 4px; margin: 0 auto 16px;"></div>
                <p style="color: #6b7280;">Loading analytics...</p>
            </div>
        `;
    }
}

// Show error
function showAnalyticsError(message) {
    const container = document.getElementById('analytics-container');
    if (container) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 4rem; margin-bottom: 16px; opacity: 0.5;">❌</div>
                <h3 style="color: #374151; margin-bottom: 8px;">Error</h3>
                <p style="color: #6b7280;">${message}</p>
                <button onclick="loadAnalytics()" style="margin-top: 16px; padding: 10px 20px; background: #6366f1; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    Retry
                </button>
            </div>
        `;
    }
}

// Add CSS styles
function addAnalyticsStyles() {
    if (document.getElementById('analytics-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'analytics-styles';
    style.textContent = `
        .stat-card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 14px;
            font-weight: 500;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #e5e7eb;
            border-radius: 50%;
            border-top-color: #6366f1;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

// Auto-load on page load if container exists
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('analytics-container')) {
        loadAnalytics();
    }
});
