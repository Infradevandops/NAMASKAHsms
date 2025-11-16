// Settings & Support Module

async function loadNotificationSettings() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/notifications/settings`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            document.getElementById('email-on-sms').checked = data.email_on_sms;
            document.getElementById('email-on-low-balance').checked = data.email_on_low_balance;
            document.getElementById('low-balance-threshold').value = data.low_balance_threshold;
        }
    } catch (err) {
        console.error('Failed to load notification settings:', err);
    }
}

async function updateNotificationSettings() {
    if (!token) return;
    
    const emailOnSms = document.getElementById('email-on-sms').checked;
    const emailOnLowBalance = document.getElementById('email-on-low-balance').checked;
    const threshold = parseFloat(document.getElementById('low-balance-threshold').value);
    
    try {
        const res = await fetch(`${API_BASE}/notifications/settings?email_on_sms=${emailOnSms}&email_on_low_balance=${emailOnLowBalance}&low_balance_threshold=${threshold}`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            showNotification('✅ Notification settings updated', 'success');
        }
    } catch (err) {
        showNotification('❌ Failed to update settings', 'error');
    }
}

async function loadReferralStats() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/referrals/stats`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const userEmail = document.getElementById('user-email').textContent;
            const userName = userEmail.split('@')[0];
            const liveUrl = window.location.hostname === 'localhost' ? 'https://namaskah.app' : window.location.origin;
            const referralLink = `${liveUrl}/?ref=${userName}_${data.referral_code}`;
            
            document.getElementById('referral-code').textContent = data.referral_code;
            document.getElementById('referral-link').value = referralLink;
            document.getElementById('total-referrals').textContent = data.total_referrals;
            document.getElementById('referral-earnings').textContent = `₵${data.total_earnings.toFixed(2)}`;
            
            const usersList = document.getElementById('referred-users');
            if (data.referred_users.length === 0) {
                usersList.innerHTML = '<p style="color: #6b7280; text-align: center; margin-top: 15px;">No referrals yet. Share your link to start earning!</p>';
            } else {
                usersList.innerHTML = `
                    <h4 style="margin: 15px 0 10px 0;">Referred Users</h4>
                    ${data.referred_users.map(u => `
                        <div style="background: #f9fafb; padding: 10px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 14px; color: #374151;">${u.email}</div>
                                <div style="font-size: 12px; color: #6b7280;">${new Date(u.joined_at).toLocaleDateString()}</div>
                            </div>
                            <div style="color: #10b981; font-weight: bold;">+₵${u.reward.toFixed(2)}</div>
                        </div>
                    `).join('')}
                `;
            }
        }
    } catch (err) {
        console.error('Failed to load referral stats:', err);
    }
}

function copyReferralLink() {
    const link = document.getElementById('referral-link').value;
    navigator.clipboard.writeText(link);
    showNotification('✅ Referral link copied!', 'success');
}

function showSupportModal() {
    const modal = document.getElementById('support-modal');
    modal.classList.remove('hidden');
    
    // Pre-fill email if user is logged in
    const userEmail = document.getElementById('user-email')?.textContent;
    if (userEmail) {
        document.getElementById('support-email').value = userEmail;
    }
}

function closeSupportModal() {
    document.getElementById('support-modal').classList.add('hidden');
    document.getElementById('support-form').reset();
}

async function submitSupport(event) {
    event.preventDefault();
    const name = document.getElementById('support-name').value;
    const email = document.getElementById('support-email').value;
    const category = document.getElementById('support-category').value;
    const message = document.getElementById('support-message').value;
    
    showLoading(true);
    
    try {
        const headers = {'Content-Type': 'application/json'};
        if (token) headers['Authorization'] = `Bearer ${window.token}`;
        
        const res = await fetch(`${API_BASE}/support/submit`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ name, email, category, message })
        });
        
        showLoading(false);
        
        if (res.ok) {
            const data = await res.json();
            showNotification(`✅ Support request submitted! Ticket ID: ${data.ticket_id}`, 'success');
            closeSupportModal();
        } else {
            showNotification('❌ Failed to submit request', 'error');
        }
    } catch (error) {
        showLoading(false);
        showNotification('❌ Network error', 'error');
    }
}

function toggleAdvanced() {
    const section = document.getElementById('advanced-section');
    const btn = document.getElementById('advanced-toggle-btn');
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        btn.textContent = '🔓 Hide Advanced';
        btn.style.background = '#ef4444';
        window.scrollTo({ top: section.offsetTop - 100, behavior: 'smooth' });
    } else {
        section.classList.add('hidden');
        btn.textContent = '🔓 Show Advanced';
        btn.style.background = '#667eea';
    }
}
