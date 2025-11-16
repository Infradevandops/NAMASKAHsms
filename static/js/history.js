// History & Transactions Module
let historyRefreshInterval = null;

function startHistoryRefresh() {
    if (historyRefreshInterval) clearInterval(historyRefreshInterval);
    historyRefreshInterval = setInterval(() => {
        loadHistory(true);
    }, 30000);
}

function stopHistoryRefresh() {
    if (historyRefreshInterval) {
        clearInterval(historyRefreshInterval);
        historyRefreshInterval = null;
    }
}

async function loadHistory(silent = false, showAll = false) {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/verifications/history`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('verifications');
            const verifications = data.verifications;
            
            if (verifications.length === 0) {
                list.innerHTML = '<p style="color: #6b7280;">No verifications yet. Create one above!</p>';
            } else {
                const displayItems = showAll ? verifications : verifications.slice(0, 5);
                list.textContent = displayItems.map(v => `
                    <div class="verification-item" onclick="loadVerification('${v.id}')">
                        <div style="display: flex;  // XSS Fix: Use textContent instead of innerHTML justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${formatServiceName(v.service_name)}</strong>
                                <div style="font-size: 14px; color: #6b7280;">${formatPhoneNumber(v.phone_number)}</div>
                            </div>
                            <span class="badge ${v.status}">${v.status}</span>
                        </div>
                        <div style="font-size: 12px; color: #9ca3af; margin-top: 5px;">
                            ${new Date(v.created_at).toLocaleString()}
                        </div>
                    </div>
                `).join('');
                
                if (!showAll && verifications.length > 5) {
                    list.innerHTML += `<button onclick="loadHistory(false, true)" style="width: 100%; margin-top: 10px; background: #667eea;">Show All (${verifications.length})</button>`;
                }
            }
            
            if (!silent) showNotification('History loaded', 'success');
        }
    } catch (err) {
        if (!silent) showNotification('Failed to load history', 'error');
    }
}

async function loadVerification(id) {
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${id}`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        showLoading(false);
        
        if (res.ok) {
            const data = await res.json();
            currentVerificationId = id;
            displayVerification(data);
            
            if (data.status === 'pending') {
                startAutoRefresh();
            }
            
            checkMessages(true);
        }
    } catch (err) {
        showLoading(false);
        showNotification('Failed to load verification', 'error');
    }
}

async function loadTransactions(silent = false, showAll = false) {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/transactions/history`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('transactions');
            const transactions = data.transactions;
            
            if (transactions.length === 0) {
                list.innerHTML = '<p style="color: #6b7280;">No transactions yet.</p>';
            } else {
                const displayItems = showAll ? transactions : transactions.slice(0, 5);
                list.textContent = displayItems.map(t => {
                    const isCredit = t.type === 'credit';  // XSS Fix: Use textContent instead of innerHTML
                    const color = isCredit ? '#10b981' : '#ef4444';
                    const sign = isCredit ? '+' : '';
                    return `
                        <div style="background: #f9fafb; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid ${color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 14px; color: #374151;">${t.description}</div>
                                    <div style="font-size: 12px; color: #9ca3af; margin-top: 3px;">
                                        ${new Date(t.created_at).toLocaleString()}
                                    </div>
                                </div>
                                <div style="font-weight: bold; font-size: 16px; color: ${color};">
                                    ${sign}₵${Math.abs(t.amount).toFixed(2)}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
                
                if (!showAll && transactions.length > 5) {
                    list.innerHTML += `<button onclick="loadTransactions(false, true)" style="width: 100%; margin-top: 10px; background: #667eea;">Show All (${transactions.length})</button>`;
                }
            }
            
            if (!silent) showNotification('Transactions loaded', 'success');
        }
    } catch (err) {
        if (!silent) showNotification('Failed to load transactions', 'error');
    }
}

async function exportTransactions() {
    if (!token) return;
    try {
        const res = await fetch(`${API_BASE}/transactions/export`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transactions_${Date.now()}.csv`;
            a.click();
            showNotification('✅ Exported successfully', 'success');
        } else {
            showNotification('❌ Export failed', 'error');
        }
    } catch (err) {
        showNotification('❌ Export failed', 'error');
    }
}

async function exportVerifications() {
    if (!token) return;
    try {
        const res = await fetch(`${API_BASE}/verifications/export`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `verifications_${Date.now()}.csv`;
            a.click();
            showNotification('✅ Exported successfully', 'success');
        } else {
            showNotification('❌ Export failed', 'error');
        }
    } catch (err) {
        showNotification('❌ Export failed', 'error');
    }
}

function toggleHistory() {
    const section = document.getElementById('verifications-list');
    const btn = document.getElementById('toggle-history-btn');
    if (section.style.display === 'none') {
        section.style.display = 'block';
        btn.textContent = '❌ Hide Verifications';
        btn.style.background = '#ef4444';
        loadHistory();
        window.scrollTo({ top: section.offsetTop - 100, behavior: 'smooth' });
    } else {
        section.style.display = 'none';
        btn.textContent = '📜 Show Verifications';
        btn.style.background = '#667eea';
    }
}

function toggleTransactions() {
    const section = document.getElementById('transactions-list');
    const btn = document.getElementById('toggle-transactions-btn');
    if (section.style.display === 'none') {
        section.style.display = 'block';
        btn.textContent = '❌ Hide Transactions';
        btn.style.background = '#ef4444';
        loadTransactions();
        window.scrollTo({ top: section.offsetTop - 100, behavior: 'smooth' });
    } else {
        section.style.display = 'none';
        btn.textContent = '💳 Show Transactions';
        btn.style.background = '#667eea';
    }
}
