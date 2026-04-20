(function() {
    'use strict';
    
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
            const fmt = typeof formatMoney === 'function' ? formatMoney : (v) => '$' + v.toFixed(2);
            const formatted = fmt(balance);
            
            const headerBalance = document.getElementById('header-balance');
            const statBalance = document.getElementById('stat-balance');
            const walletBalance = document.getElementById('wallet-balance');
            const balanceAmount = document.getElementById('balance-amount');
            const balanceDisplay = document.getElementById('balance-display');
            
            if (headerBalance) {
                headerBalance.removeAttribute('data-i18n');
                headerBalance.textContent = 'Balance: ' + formatted;
            }
            if (statBalance) {
                statBalance.removeAttribute('data-i18n');
                statBalance.textContent = formatted;
            }
            if (walletBalance) {
                walletBalance.removeAttribute('data-i18n');
                walletBalance.textContent = formatted;
            }
            if (balanceAmount) {
                balanceAmount.removeAttribute('data-i18n');
                balanceAmount.textContent = formatted;
            }
            if (balanceDisplay) {
                balanceDisplay.removeAttribute('data-i18n');
                balanceDisplay.textContent = formatted;
            }
        } catch (error) {
            console.error('Balance load failed:', error);
        }
    }
    
    document.addEventListener('DOMContentLoaded', loadBalance);
    window.addEventListener('focus', loadBalance);
    window.syncBalance = loadBalance;
})();
