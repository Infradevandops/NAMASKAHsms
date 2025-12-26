// Admin Dashboard JavaScript - Real API Integration

let authToken = null;
let refreshInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

async function initializeDashboard() {
    try {
        // Get auth token from cookies first
        authToken = getCookie('access_token');
        
        if (!authToken) {
            // Try to login with admin credentials
            const loginResponse = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: 'admin@namaskah.app',
                    password: 'admin123'
                })
            });
            
            if (loginResponse.ok) {
                const loginData = await loginResponse.json();
                authToken = loginData.access_token;
            } else {
                showToast('Authentication failed - redirecting to login', 'error');
                setTimeout(() => window.location.href = '/auth/login', 2000);
                return;
            }
        }
        
        // Load dashboard data
        await loadDashboardData();
        
        // Set up auto-refresh
        refreshInterval = setInterval(loadDashboardData, 30000);
        
        showToast('Dashboard loaded successfully', 'success');
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        showToast('Failed to initialize dashboard', 'error');
    }
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

async function loadDashboardData() {
    try {
        // Load basic stats
        const statsResponse = await fetch('/api/admin/stats', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            updateBasicMetrics(statsData);
        } else {
            console.error('Stats API failed:', statsResponse.status);
            // Show fallback data
            updateBasicMetrics({
                users: 1,
                verifications: 0, 
                success_rate: 0,
                revenue: 0
            });
        }
        
        // Load recent verifications
        await loadRecentVerifications();
        
        // Load pricing templates
        await loadPricingTemplates();
        
        // Update system status
        updateSystemStatus();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showToast('Error loading data', 'error');
    }
}

function updateBasicMetrics(stats) {
    document.getElementById('total-users').textContent = stats.users || 0;
    document.getElementById('active-users').textContent = `${stats.active_users || 0} active`;
    
    document.getElementById('total-verifications').textContent = stats.verifications || 0;
    document.getElementById('pending-verifications').textContent = `${stats.pending_verifications || 0} pending`;
    
    document.getElementById('success-rate').textContent = `${stats.success_rate || 0}%`;
    document.getElementById('success-count').textContent = `${stats.success_verifications || 0} completed`;
    
    document.getElementById('total-revenue').textContent = `$${stats.revenue || 0}`;
}

async function loadRecentVerifications() {
    try {
        const response = await fetch('/api/admin/verification-history/recent', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const tbody = document.getElementById('verifications-tbody');
        
        if (response.ok) {
            const verifications = await response.json();
            
            if (verifications.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="no-data">No verifications yet</td></tr>';
            } else {
                tbody.innerHTML = verifications.map(v => `
                    <tr>
                        <td><span class="verification-id">${v.id.substring(0, 8)}...</span></td>
                        <td><span class="user-id">${v.user_id}</span></td>
                        <td><span class="user-email">${v.user_email}</span></td>
                        <td><span class="service-name">${v.service_name}</span></td>
                        <td><span class="phone-number">${v.phone_number}</span></td>
                        <td><span class="status-badge status-${v.status}">${v.status}</span></td>
                        <td><span class="cost">$${v.cost}</span></td>
                        <td><span class="date">${new Date(v.created_at).toLocaleDateString()}</span></td>
                        <td>
                            ${v.status === 'pending' ? 
                                `<button class="btn-action btn-cancel" onclick="cancelVerification('${v.id}')">Cancel</button>` : 
                                `<button class="btn-action btn-view" onclick="viewVerification('${v.id}')">View</button>`
                            }
                        </td>
                    </tr>
                `).join('');
            }
        } else {
            tbody.innerHTML = '<tr><td colspan="9" class="error">Failed to load verifications</td></tr>';
        }
    } catch (error) {
        console.error('Error loading verifications:', error);
        document.getElementById('verifications-tbody').innerHTML = 
            '<tr><td colspan="9" class="error">Error loading data</td></tr>';
    }
}

async function loadPricingTemplates() {
    try {
        const response = await fetch('/api/admin/pricing-templates', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const container = document.getElementById('pricing-controls');
        
        if (response.ok) {
            const data = await response.json();
            const templates = data.templates || [];
            
            if (templates.length === 0) {
                container.innerHTML = '<div class="no-data">No pricing templates found</div>';
            } else {
                container.innerHTML = templates.map(template => `
                    <div class="pricing-template ${template.active ? 'active' : 'inactive'}">
                        <h4>${template.name}</h4>
                        <div class="price">$${template.price}/month</div>
                        <div class="sms-cost">SMS: $${template.sms_cost}</div>
                        <div class="features">
                            ${template.features.map(f => `<span class="feature">${f}</span>`).join('')}
                        </div>
                        <button class="btn-edit" onclick="editTemplate('${template.id}')">Edit</button>
                    </div>
                `).join('');
            }
        } else {
            container.innerHTML = '<div class="error">Failed to load pricing templates</div>';
        }
    } catch (error) {
        console.error('Error loading pricing templates:', error);
        document.getElementById('pricing-controls').innerHTML = 
            '<div class="error">Error loading pricing templates</div>';
    }
}

function updateSystemStatus() {
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
}

function refreshDashboard() {
    loadDashboardData();
    showToast('Dashboard refreshed', 'info');
}

async function cancelVerification(verificationId) {
    if (!confirm('Are you sure you want to cancel this verification?')) return;
    
    try {
        const response = await fetch(`/api/admin/verifications/${verificationId}/cancel`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            showToast('Verification cancelled successfully', 'success');
            await loadRecentVerifications();
        } else {
            showToast('Failed to cancel verification', 'error');
        }
    } catch (error) {
        console.error('Error cancelling verification:', error);
        showToast('Error cancelling verification', 'error');
    }
}

function viewVerification(verificationId) {
    showToast(`Viewing verification: ${verificationId}`, 'info');
}

async function exportAll() {
    try {
        const response = await fetch('/api/admin/export/verifications', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(data.message, 'success');
        } else {
            showToast('Export failed', 'error');
        }
    } catch (error) {
        showToast('Export error', 'error');
    }
}

async function exportVerifications() {
    await exportAll();
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        z-index: 1000;
        font-size: 14px;
    `;
    
    if (type === 'success') toast.style.backgroundColor = '#10b981';
    else if (type === 'error') toast.style.backgroundColor = '#ef4444';
    else toast.style.backgroundColor = '#3b82f6';
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function logout() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    window.location.href = '/auth/login';
}