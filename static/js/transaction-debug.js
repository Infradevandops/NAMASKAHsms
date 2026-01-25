/**
 * Emergency fix for transaction history not loading
 * Add this script to debug and fix transaction history issues
 */

(function() {
    'use strict';
    
    console.log('💳 Transaction History Debug Script Loaded');
    
    function debugTransactionHistory() {
        const token = localStorage.getItem('access_token');
        console.log('Token exists:', !!token);
        
        if (!token) {
            console.error('❌ No access token found');
            return;
        }
        
        // Test different possible endpoints
        const endpoints = [
            '/api/v1/verify/history',
            '/api/verify/history', 
            '/api/billing/history',
            '/api/wallet/transactions'
        ];
        
        console.log('🔍 Testing transaction endpoints...');
        
        endpoints.forEach(async (endpoint, index) => {
            try {
                console.log(`Testing ${endpoint}...`);
                const response = await fetch(endpoint, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                console.log(`${endpoint}: ${response.status}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log(`✅ ${endpoint} works:`, data);
                    
                    // If this is verification history, check structure
                    if (endpoint.includes('verify') && data.verifications) {
                        console.log(`📱 Found ${data.verifications.length} verifications`);
                        if (data.verifications.length > 0) {
                            console.log('Sample verification:', data.verifications[0]);
                        }
                    }
                    
                    // If this is transaction history, check structure  
                    if (data.transactions || data.payments) {
                        const items = data.transactions || data.payments;
                        console.log(`💳 Found ${items.length} transactions`);
                        if (items.length > 0) {
                            console.log('Sample transaction:', items[0]);
                        }
                    }
                } else {
                    const errorText = await response.text();
                    console.log(`❌ ${endpoint}: ${errorText}`);
                }
            } catch (error) {
                console.error(`❌ ${endpoint} error:`, error);
            }
        });
    }
    
    // Enhanced loadHistory function
    window.debugLoadHistory = async function() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.error('No token found');
            return;
        }
        
        console.log('🔄 Loading transaction history...');
        
        try {
            // Try verification history first
            const verifyRes = await fetch('/api/v1/verify/history?limit=100', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            console.log('Verify history status:', verifyRes.status);
            
            if (verifyRes.ok) {
                const verifyData = await verifyRes.json();
                console.log('Verification history:', verifyData);
                
                const tbody = document.getElementById('history-body');
                if (tbody && verifyData.verifications) {
                    if (verifyData.verifications.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px;">No verifications found</td></tr>';
                    } else {
                        // Render the data
                        tbody.innerHTML = verifyData.verifications.map(item => {
                            const status = item.status || 'unknown';
                            let statusColor = '#f3f4f6';
                            let statusText = '#374151';
                            
                            switch (status.toLowerCase()) {
                                case 'completed':
                                    statusColor = '#dcfce7';
                                    statusText = '#166534';
                                    break;
                                case 'pending':
                                    statusColor = '#fef9c3';
                                    statusText = '#854d0e';
                                    break;
                                case 'failed':
                                case 'cancelled':
                                case 'timeout':
                                    statusColor = '#fee2e2';
                                    statusText = '#991b1b';
                                    break;
                            }
                            
                            const smsCode = item.sms_code ? 
                                `<span style="font-family: monospace; font-weight: bold; background: #eee; padding: 2px 6px; border-radius: 4px;">${item.sms_code}</span>` : 
                                '<span style="color: #9ca3af;">-</span>';
                            
                            return `
                                <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                                    <td style="padding: 12px;">${item.service_name}</td>
                                    <td style="padding: 12px;">🇺🇸</td>
                                    <td style="padding: 12px;">${item.carrier || 'Auto'}</td>
                                    <td style="padding: 12px;">${item.phone_number}</td>
                                    <td style="padding: 12px;">${smsCode}</td>
                                    <td style="padding: 12px;">
                                        <span style="padding: 4px 8px; border-radius: 4px; font-size: 12px; background: ${statusColor}; color: ${statusText};">
                                            ${status}
                                        </span>
                                    </td>
                                    <td style="padding: 12px;">$${item.cost.toFixed(2)}</td>
                                    <td style="padding: 12px;">${new Date(item.created_at).toLocaleDateString()}</td>
                                    <td style="padding: 12px;">
                                        ${item.sms_text ? '<button onclick="alert(\\'Message: ' + item.sms_text.replace(/'/g, "\\'") + '\\')" style="padding: 4px 8px; font-size: 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">Msg</button>' : ''}
                                    </td>
                                </tr>
                            `;
                        }).join('');
                        
                        console.log('✅ Transaction history rendered');
                    }
                }
            } else {
                console.error('Failed to load verification history:', await verifyRes.text());
            }
            
        } catch (error) {
            console.error('Error loading history:', error);
        }
    };
    
    // Run debug
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', debugTransactionHistory);
    } else {
        debugTransactionHistory();
    }
    
    // Add button to manually test
    setTimeout(() => {
        if (document.getElementById('history-body')) {
            const button = document.createElement('button');
            button.textContent = '🔧 Debug Load History';
            button.style.cssText = 'position: fixed; top: 10px; right: 10px; z-index: 9999; padding: 8px 12px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;';
            button.onclick = window.debugLoadHistory;
            document.body.appendChild(button);
        }
    }, 1000);
    
    console.log('💳 Transaction history debug script initialized');
})();