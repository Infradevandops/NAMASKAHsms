/**
 * Export Verification History - Task 3
 * Allows users to download their verification history as CSV
 */

// Export verification history with filters
async function exportVerificationHistory(filters = {}) {
    try {
        // Show loading state
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.disabled = true;
            exportBtn.textContent = 'Exporting...';
        }
        
        // Build query parameters
        const params = new URLSearchParams();
        
        if (filters.service) {
            params.append('service', filters.service);
        }
        if (filters.status) {
            params.append('verification_status', filters.status);
        }
        if (filters.start_date) {
            params.append('start_date', filters.start_date);
        }
        if (filters.end_date) {
            params.append('end_date', filters.end_date);
        }
        
        // Get token
        const token = localStorage.getItem('token');
        if (!token) {
            showExportError('Please login to export history');
            return;
        }
        
        // Make request
        const response = await fetch(`/api/verify/history/export?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Export failed');
        }
        
        // Get the CSV data
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `namaskah_verifications_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Show success
        showExportSuccess('History exported successfully!');
        
    } catch (error) {
        console.error('Export error:', error);
        showExportError(error.message || 'Export failed. Please try again.');
    } finally {
        // Reset button
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.disabled = false;
            exportBtn.textContent = '📥 Export CSV';
        }
    }
}

// Show export success message
function showExportSuccess(message) {
    showExportNotification(message, 'success');
}

// Show export error message
function showExportError(message) {
    showExportNotification(message, 'error');
}

// Show notification
function showExportNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.export-notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = 'export-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: slideInRight 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.background = '#10b981';
        notification.textContent = '✅ ' + message;
    } else if (type === 'error') {
        notification.style.background = '#ef4444';
        notification.textContent = '❌ ' + message;
    } else {
        notification.style.background = '#3b82f6';
        notification.textContent = 'ℹ️ ' + message;
    }
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export with date range picker
function showExportDialog() {
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'export-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeIn 0.2s ease;
    `;
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 16px; padding: 32px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
            <h2 style="margin: 0 0 24px 0; color: #1f2937; font-size: 24px;">📥 Export History</h2>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 600;">Date Range (Optional)</label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div>
                        <label style="display: block; margin-bottom: 4px; color: #6b7280; font-size: 13px;">Start Date</label>
                        <input type="date" id="export-start-date" style="width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px;">
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 4px; color: #6b7280; font-size: 13px;">End Date</label>
                        <input type="date" id="export-end-date" style="width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px;">
                    </div>
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 600;">Filter by Service (Optional)</label>
                <input type="text" id="export-service" placeholder="e.g., telegram, whatsapp" style="width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px;">
            </div>
            
            <div style="margin-bottom: 24px;">
                <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 600;">Filter by Status (Optional)</label>
                <select id="export-status" style="width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px; cursor: pointer;">
                    <option value="">All Statuses</option>
                    <option value="completed">Completed</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                    <option value="cancelled">Cancelled</option>
                    <option value="timeout">Timeout</option>
                </select>
            </div>
            
            <div style="color: #6b7280; font-size: 13px; margin-bottom: 24px; padding: 12px; background: #f3f4f6; border-radius: 8px;">
                💡 <strong>Tip:</strong> Leave filters empty to export all verifications. Maximum 10,000 records per export.
            </div>
            
            <div style="display: flex; gap: 12px;">
                <button onclick="closeExportDialog()" style="flex: 1; padding: 12px; border: 2px solid #e5e7eb; background: white; color: #374151; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;">
                    Cancel
                </button>
                <button onclick="confirmExport()" style="flex: 1; padding: 12px; border: none; background: #6366f1; color: white; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;">
                    📥 Export CSV
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Set default end date to today
    document.getElementById('export-end-date').valueAsDate = new Date();
}

function closeExportDialog() {
    const modal = document.getElementById('export-modal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.2s ease';
        setTimeout(() => modal.remove(), 200);
    }
}

function confirmExport() {
    const filters = {
        start_date: document.getElementById('export-start-date').value || null,
        end_date: document.getElementById('export-end-date').value || null,
        service: document.getElementById('export-service').value || null,
        status: document.getElementById('export-status').value || null
    };
    
    closeExportDialog();
    exportVerificationHistory(filters);
}

// Add fadeIn/fadeOut animations
const fadeStyle = document.createElement('style');
fadeStyle.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(fadeStyle);
