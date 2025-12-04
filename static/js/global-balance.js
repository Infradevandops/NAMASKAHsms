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
            const formatted = '$' + balance.toFixed(2);
            
            const headerBalance = document.getElementById('header-balance');
            const statBalance = document.getElementById('stat-balance');
            const walletBalance = document.getElementById('wallet-balance');
            const balanceAmount = document.getElementById('balance-amount');
            
            if (headerBalance) headerBalance.textContent = 'Balance: ' + formatted;
            if (statBalance) statBalance.textContent = formatted;
            if (walletBalance) walletBalance.textContent = formatted;
            if (balanceAmount) balanceAmount.textContent = formatted;
        } catch (error) {
            console.error('Balance load failed:', error);
        }
    }
    
    document.addEventListener('DOMContentLoaded', loadBalance);
    window.addEventListener('focus', loadBalance);
    window.syncBalance = loadBalance;
})();
