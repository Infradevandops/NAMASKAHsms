(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', init);

    function init() {
        setupSidebarToggle();
        setupViewSwitching();
        loadDashboardData();
        setupAutoRefresh();
    }

    function setupSidebarToggle() {
        const toggleBtn = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('sidebar');
        
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            });

            if (localStorage.getItem('sidebarCollapsed') === 'true') {
                sidebar.classList.add('collapsed');
            }
        }
    }

    function setupViewSwitching() {
        const urlParams = new URLSearchParams(window.location.search);
        const view = urlParams.get('view') || 'home';
        switchView(view);

        document.querySelectorAll('.nav-item[data-view]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetView = item.getAttribute('data-view');
                switchView(targetView);
                updateURL(targetView);
            });
        });
    }

    function switchView(viewName) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
            
            if (viewName === 'wallet') {
                loadWalletContent();
            } else if (viewName === 'profile') {
                loadProfileContent();
            } else if (viewName === 'settings') {
                loadSettingsContent();
            }
        }

        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-view') === viewName) {
                item.classList.add('active');
            }
        });

        const titles = {
            home: 'Dashboard',
            wallet: 'Wallet',
            profile: 'Profile',
            settings: 'Settings'
        };
        document.getElementById('page-title').textContent = titles[viewName] || 'Dashboard';
    }

    function updateURL(view) {
        const url = view === 'home' ? '/dashboard' : `/dashboard?view=${view}`;
        window.history.pushState({view}, '', url);
    }

    async function loadDashboardData() {
        loadRecentActivity();
        loadBalance();
    }

    async function loadBalance() {
        try {
            const response = await fetch('/api/user/balance', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
            if (!response.ok) return;
            const data = await response.json();
            const balance = parseFloat(data.credits) || 0;
            const formatted = '$' + balance.toFixed(2);
            
            const headerBalance = document.getElementById('header-balance');
            const statBalance = document.getElementById('stat-balance');
            const walletBalance = document.getElementById('wallet-balance');
            
            if (headerBalance) headerBalance.textContent = 'Balance: ' + formatted;
            if (statBalance) statBalance.textContent = formatted;
            if (walletBalance) walletBalance.textContent = formatted;
        } catch (error) {
            console.error('Balance load failed:', error);
        }
    }

    async function loadRecentActivity() {
        const container = document.getElementById('recent-activity');
        
        try {
            const response = await fetch('/api/dashboard/activity/recent');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            
            if (!data.activities || data.activities.length === 0) {
                container.innerHTML = '<div class="loading">No recent activity</div>';
                return;
            }

            container.innerHTML = data.activities.map(activity => `
                <div class="activity-item">
                    <div class="activity-info">
                        <div class="activity-service">${activity.service_name || 'Unknown'}</div>
                        <div class="activity-details">
                            ${[activity.country, activity.phone_number, `$${(activity.cost || 0).toFixed(2)}`].filter(Boolean).join(' • ')}
                        </div>
                    </div>
                    <span class="activity-status status-${activity.status || 'pending'}">
                        ${activity.status || 'pending'}
                    </span>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load activity:', error);
            container.innerHTML = '<div class="loading">No activity available</div>';
        }
    }



    async function loadWalletContent() {
        loadTransactions();
    }

    async function loadTransactions() {
        const container = document.getElementById('transactions-list');
        
        try {
            const response = await fetch('/api/billing/transactions?limit=10');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            
            if (!data.transactions || data.transactions.length === 0) {
                container.innerHTML = '<div class="loading">No transactions</div>';
                return;
            }

            container.innerHTML = data.transactions.map(t => `
                <div class="activity-item">
                    <div class="activity-info">
                        <div class="activity-service">${t.type}</div>
                        <div class="activity-details">${t.description || ''}</div>
                    </div>
                    <span class="activity-status status-${t.status || 'completed'}">
                        ${t.amount >= 0 ? '+' : ''}$${Math.abs(t.amount).toFixed(2)}
                    </span>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load transactions:', error);
            container.innerHTML = '<div class="loading">No transactions available</div>';
        }
    }

    async function loadProfileContent() {
        const container = document.getElementById('profile-form-container');
        
        try {
            const response = await fetch('/api/user/profile');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const user = await response.json();
            
            container.innerHTML = `
                <form id="profile-form" onsubmit="updateProfile(event)">
                    <div style="margin-bottom: 15px;">
                        <label>Email</label>
                        <input type="email" value="${user.email}" disabled style="background:#f3f4f6;cursor:not-allowed;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Full Name</label>
                        <input type="text" id="profile-name" value="${user.name || ''}" placeholder="Your name">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Phone</label>
                        <input type="text" id="profile-phone" value="${user.phone || ''}" placeholder="Your phone">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Country</label>
                        <input type="text" id="profile-country" value="${user.country || ''}" placeholder="Your country">
                    </div>
                    <div style="display:flex;gap:10px;">
                        <button type="submit" class="btn btn-primary" style="flex:1;">Save Changes</button>
                        <button type="button" class="btn btn-secondary" style="flex:1;" onclick="loadProfileContent()">Cancel</button>
                    </div>
                </form>
            `;
        } catch (error) {
            console.error('Failed to load profile:', error);
            container.innerHTML = '<div class="loading">Unable to load profile</div>';
        }
    }

    async function loadSettingsContent() {
        const container = document.getElementById('settings-form-container');
        
        container.innerHTML = `
            <div style="margin-bottom: 20px;">
                <h3>Account Settings</h3>
                <div style="margin-top: 15px;">
                    <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
                        <input type="checkbox" id="email-notifications" checked>
                        <span>Email Notifications</span>
                    </label>
                </div>
                <div style="margin-top: 15px;">
                    <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
                        <input type="checkbox" id="sms-notifications" checked>
                        <span>SMS Notifications</span>
                    </label>
                </div>
            </div>
            <div style="margin-bottom: 20px;">
                <h3>Security</h3>
                <button class="btn btn-secondary" style="width:100%;margin-top:10px;" onclick="changePassword()">Change Password</button>
            </div>
            <div style="margin-bottom: 20px;">
                <h3>Data</h3>
                <button class="btn btn-secondary" style="width:100%;margin-top:10px;" onclick="exportData()">Export My Data</button>
            </div>
        `;
    }

    function setupAutoRefresh() {
        // Balance loaded on page load and window focus via global-balance.js
    }

    window.logout = async function() {
        if (!confirm('Are you sure you want to logout?')) return;
        
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            localStorage.clear();
            window.location.href = '/auth/login';
        } catch (error) {
            console.error('Logout failed:', error);
            window.location.href = '/auth/login';
        }
    };

    window.updateProfile = async function(event) {
        event.preventDefault();
        
        const data = {
            name: document.getElementById('profile-name').value,
            phone: document.getElementById('profile-phone').value,
            country: document.getElementById('profile-country').value
        };

        try {
            const response = await fetch('/api/user/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                alert('Profile updated successfully');
                loadProfileContent();
            } else {
                alert('Failed to update profile');
            }
        } catch (error) {
            console.error('Update failed:', error);
            alert('Error updating profile');
        }
    };

    window.showAddCreditsModal = function() {
        document.getElementById('add-credits-modal').style.display = 'flex';
    };

    window.closeAddCreditsModal = function() {
        document.getElementById('add-credits-modal').style.display = 'none';
        document.getElementById('credit-amount').value = '';
        document.querySelectorAll('.package').forEach(p => p.classList.remove('selected'));
    };

    window.selectPackage = function(amount, bonus) {
        const total = amount + bonus;
        document.getElementById('credit-amount').value = total.toFixed(2);
        
        document.querySelectorAll('.package').forEach(p => p.classList.remove('selected'));
        const pkg = event.target.closest('.package');
        if (pkg) pkg.classList.add('selected');
    };

    window.proceedToPayment = async function() {
        const amount = parseFloat(document.getElementById('credit-amount').value);
        
        if (!amount || amount <= 0) {
            alert('Please enter a valid amount');
            return;
        }

        try {
            const response = await fetch('/api/billing/add-credits', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                },
                body: JSON.stringify({ amount: amount })
            });

            const data = await response.json();
            
            if (response.ok) {
                alert(`Credits added successfully! New balance: $${data.new_balance.toFixed(2)}`);
                closeAddCreditsModal();
                
                setTimeout(() => {
                    if (window.syncBalance) window.syncBalance();
                    loadBalance();
                    loadTransactions();
                }, 100);
            } else {
                alert(`Error: ${data.detail || 'Failed to add credits'}`);
            }
        } catch (error) {
            console.error('Payment failed:', error);
            alert(`Error: ${error.message}`);
        }
    };

    window.changePassword = function() {
        const newPassword = prompt('Enter new password:');
        if (!newPassword) return;
        
        if (newPassword.length < 8) {
            alert('Password must be at least 8 characters');
            return;
        }

        fetch('/api/user/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: newPassword })
        }).then(() => {
            alert('Password changed successfully');
        }).catch(error => {
            console.error('Password change failed:', error);
            alert('Failed to change password');
        });
    };

    window.exportData = function() {
        fetch('/api/gdpr/export')
            .then(r => r.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'my-data.json';
                a.click();
            })
            .catch(error => {
                console.error('Export failed:', error);
                alert('Failed to export data');
            });
    };

    window.addEventListener('popstate', (e) => {
        const view = e.state?.view || 'home';
        switchView(view);
    });
})();
