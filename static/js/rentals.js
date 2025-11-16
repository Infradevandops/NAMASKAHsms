// Rental Management Module
let activeRentals = [];
let rentalRefreshInterval = null;

// Load active rentals
async function loadActiveRentals() {
    if (!window.token) return;
    
    try {
        const res = await fetch(`${API_BASE}/rentals/active`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            activeRentals = data.rentals || [];
            displayActiveRentals();
        } else if (res.status === 401) {
            showNotification('🔒 Session expired', 'error');
            setTimeout(() => logout(), 2000);
        }
    } catch (err) {
        console.error('Load rentals error:', err);
    }
}

// Display active rentals
function displayActiveRentals() {
    const container = document.getElementById('active-rentals');
    if (!container) return;
    
    if (activeRentals.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No active rentals</p>';
        return;
    }
    
    container.textContent = activeRentals.map(rental => `
        <div class="rental-card" style="border: 1px solid #e5e7eb;  // XSS Fix: Use textContent instead of innerHTML border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 8px;">
                <strong>${formatPhoneNumber(rental.phone_number)}</strong>
                <span class="badge active">${rental.service_name}</span>
            </div>
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 12px;">
                Expires: ${new Date(rental.expires_at).toLocaleString()}
                <br>Time remaining: ${formatTimeRemaining(rental.time_remaining_seconds)}
            </div>
            <div style="display: flex; gap: 8px;">
                <button onclick="extendRental('${rental.id}')" style="background: #10b981; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                    Extend
                </button>
                <button onclick="releaseRental('${rental.id}')" style="background: #ef4444; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                    Release
                </button>
                <button onclick="checkRentalMessages('${rental.id}')" style="background: #3b82f6; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                    Messages
                </button>
            </div>
        </div>
    `).join('');
}

// Format time remaining
function formatTimeRemaining(seconds) {
    if (seconds <= 0) return 'Expired';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Extend rental
async function extendRental(rentalId) {
    const hours = prompt('How many hours to extend?', '1');
    if (!hours || isNaN(hours) || hours <= 0) return;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/${rentalId}/extend`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({additional_hours: parseFloat(hours)})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            showNotification(`✅ Extended by ${hours}h. Cost: N${data.extension_cost}`, 'success');
            if (typeof updateUserCredits === 'function') {
                updateUserCredits(data.remaining_credits);
            }
            loadActiveRentals();
        } else {
            if (res.status === 402) {
                showNotification(`💳 ${data.detail}`, 'error');
            } else {
                showNotification(`❌ ${data.detail || 'Failed to extend rental'}`, 'error');
            }
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

// Release rental
async function releaseRental(rentalId) {
    if (!confirm('Release this rental early? You\'ll get 50% refund for unused time.')) return;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/${rentalId}/release`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            showNotification(`✅ Released! Refunded N${data.refund}`, 'success');
            if (typeof updateUserCredits === 'function') {
                updateUserCredits(data.remaining_credits);
            }
            loadActiveRentals();
        } else {
            showNotification(`❌ ${data.detail || 'Failed to release rental'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

// Check rental messages
async function checkRentalMessages(rentalId) {
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/${rentalId}/messages`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            showRentalMessages(data);
        } else {
            showNotification(`❌ ${data.detail || 'Failed to get messages'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

// Show rental messages modal
function showRentalMessages(data) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    
    const messagesHtml = data.messages.length > 0 
        ? data.messages.map(msg => `
            <div style="background: #f3f4f6; padding: 12px; margin: 8px 0; border-radius: 6px;">
                <code style="font-family: monospace;">${msg}</code>
            </div>
        `).join('')
        : '<p style="color: #6b7280;">No messages received yet</p>';
    
    modal.textContent = `
        <div class="modal-content" style="max-width: 600px;  // XSS Fix: Use textContent instead of innerHTML">
            <h2>Rental Messages</h2>
            <div style="margin: 16px 0;">
                <strong>Phone:</strong> ${formatPhoneNumber(data.phone_number)}<br>
                <strong>Service:</strong> ${data.service_name}<br>
                <strong>Messages:</strong> ${data.message_count}
            </div>
            <div style="max-height: 300px; overflow-y: auto;">
                ${messagesHtml}
            </div>
            <button onclick="closeModal()" style="margin-top: 16px; background: #6b7280; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer;">
                Close
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Close modal
function closeModal() {
    const modal = document.querySelector('.modal');
    if (modal) modal.remove();
}

// Start rental auto-refresh
function startRentalRefresh() {
    if (rentalRefreshInterval) clearInterval(rentalRefreshInterval);
    
    rentalRefreshInterval = setInterval(() => {
        loadActiveRentals();
    }, 30000); // Refresh every 30 seconds
}

// Stop rental auto-refresh
function stopRentalRefresh() {
    if (rentalRefreshInterval) {
        clearInterval(rentalRefreshInterval);
        rentalRefreshInterval = null;
    }
}

// Initialize rentals module
function initRentals() {
    loadActiveRentals();
    startRentalRefresh();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopRentalRefresh();
});