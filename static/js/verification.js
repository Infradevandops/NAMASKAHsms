// Verification Module - Consolidated and Secure
let currentVerificationId = null;
let autoRefreshInterval = null;
let countdownInterval = null;
let currentServiceName = null;
let currentCapability = 'sms';

// Secure pricing function with fallback
async function getServicePrice(serviceName, capability = 'sms') {
    if (!serviceName || !window.SecurityUtils?.validateInput(serviceName, 'service')) {
        return '1.00';
    }
    
    try {
        const response = await window.SecurityUtils.secureFetch(`${API_BASE}/services/price/${encodeURIComponent(serviceName)}`);
        if (response.ok) {
            const data = await response.json();
            return capability === 'voice' 
                ? (data.base_price + data.voice_premium).toFixed(2)
                : data.base_price.toFixed(2);
        }
    } catch (err) {
        console.error('Price fetch error:', err);
    }
    
    // Secure fallback pricing
    const fallbackPrices = {
        'whatsapp': 0.75, 'telegram': 0.75, 'discord': 0.75, 'google': 0.75,
        'instagram': 1.00, 'facebook': 1.00, 'twitter': 1.00, 'tiktok': 1.00,
        'paypal': 1.50
    };
    
    const basePrice = fallbackPrices[serviceName.toLowerCase()] || 1.00;
    return capability === 'voice' ? (basePrice + 0.30).toFixed(2) : basePrice.toFixed(2);
}

// Get tier name for display
function getTierName(serviceName) {
    const tierMap = {
        'whatsapp': 'High-Demand',
        'telegram': 'High-Demand', 
        'discord': 'High-Demand',
        'google': 'High-Demand',
        'instagram': 'Standard',
        'facebook': 'Standard',
        'twitter': 'Standard',
        'tiktok': 'Standard',
        'paypal': 'Premium',
        'venmo': 'Premium',
        'cashapp': 'Premium'
    };
    return tierMap[serviceName.toLowerCase()] || 'Specialty';
}

const serviceTimers = {
    'google': 60, 'discord': 60, 'whatsapp': 90, 'telegram': 90,
    'instagram': 120, 'facebook': 90, 'twitter': 75, 'tiktok': 90,
    'snapchat': 75, 'default': 60
};

function getServiceTimer(serviceName) {
    return serviceTimers[serviceName.toLowerCase()] || serviceTimers['default'];
}

async function createVerification() {
    const service = document.getElementById('service-select').value;
    const capabilityEl = document.querySelector('input[name="capability"]:checked');
    const capability = capabilityEl ? capabilityEl.value : 'sms';
    
    if (!service) {
        showNotification('⚠️ Please select a service', 'error');
        return;
    }
    
    if (!window.token) {
        showNotification('🔒 Please login first', 'error');
        return;
    }
    
    // Store current verification details
    currentServiceName = service;
    currentCapability = capability;
    verificationStartTime = Date.now();
    currentRetryCount = 0;
    
    // Get dynamic price before creating (now always returns a price)
    const price = await getServicePrice(service, capability);
    console.log(`Service: ${service}, Capability: ${capability}, Price: N${price}`);
    
    // Get carrier and area code selections
    const carrierSelect = document.getElementById('carrier-select');
    const areaCodeSelect = document.getElementById('area-code-select');
    const carrier = carrierSelect ? carrierSelect.value : null;
    const areaCode = areaCodeSelect ? areaCodeSelect.value : null;
    
    showLoading(true);
    
    // Build request body with optional carrier and area code
    const requestBody = {
        service_name: service, 
        capability: capability
    };
    
    if (carrier) requestBody.carrier = carrier;
    if (areaCode) requestBody.area_code = areaCode;
    
    try {
        const res = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': window.csrfToken || ''
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            
            // Track verification purchase
            if (typeof trackVerificationPurchase === 'function') {
                trackVerificationPurchase(data.id, service, data.cost);
            }
            
            const capabilityText = capability === 'voice' ? '📞 Voice' : '📱 SMS';
            showNotification(`✅ ${capabilityText} verification created! Cost: N${data.cost} (${getTierName(service)})`, 'success');
            
            startAutoRefresh();
            startSmartCountdown(service, capability);
            
            if (typeof loadHistory === 'function') loadHistory();
            if (typeof loadTransactions === 'function') loadTransactions(true);
            
            if (!firstVerificationCompleted) {
                firstVerificationCompleted = true;
            }
        } else {
            if (res.status === 402) {
                showNotification(`💳 Insufficient funds. ${data.detail}`, 'error');
            } else if (res.status === 401) {
                showNotification('🔒 Session expired. Please login again', 'error');
                setTimeout(() => logout(), 2000);
            } else if (res.status === 503) {
                if (data.detail && data.detail.includes('API key')) {
                    showNotification('🔑 INVALID API KEY: TextVerified API key is missing or invalid. Contact admin to configure real API key.', 'error');
                } else {
                    showNotification(`⚠️ Service unavailable: ${service}. Try another service`, 'error');
                }
            } else if (res.status === 400 && data.detail && data.detail.includes('API key')) {
                showNotification('🔑 CONFIGURATION ERROR: TextVerified API key is invalid. This is not a demo - real API key required.', 'error');
            } else {
                showNotification(`❌ ${data.detail || 'Failed to create verification'}`, 'error');
            }
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error. Check your connection', 'error');
    }
}

function displayVerification(data) {
    const formattedPhone = formatPhoneNumber(data.phone_number);
    document.getElementById('phone-number').textContent = formattedPhone || 'Loading...';
    document.getElementById('service-name').textContent = formatServiceName(data.service_name);
    currentServiceName = data.service_name;
    currentCapability = data.capability || 'sms';
    
    const statusBadge = document.getElementById('status');
    statusBadge.textContent = data.status;
    statusBadge.className = `badge status-badge-compact ${data.status}`;
    
    // Enhanced info display with capability indicator
    const infoContainer = document.getElementById('verification-info');
    if (infoContainer) {
        let infoHTML = '';
        
        // Capability indicator
        const capabilityIcon = data.capability === 'voice' ? '📞' : '📱';
        const capabilityText = data.capability === 'voice' ? 'Voice Call' : 'SMS Text';
        infoHTML += `<div class="detail-compact" style="background: var(--bg-secondary); padding: 8px; border-radius: 6px; font-size: 12px;"><strong>Type:</strong><br><span>${capabilityIcon} ${capabilityText}</span></div>`;
        
        // Carrier info
        if (data.carrier_info && data.carrier_info.name) {
            infoHTML += `<div class="detail-compact" style="background: var(--bg-secondary); padding: 8px; border-radius: 6px; font-size: 12px;"><strong>Carrier:</strong><br><span>${data.carrier_info.full_display || data.carrier_info.name}</span></div>`;
        }
        
        // User selections
        if (data.user_selections) {
            if (data.user_selections.requested_carrier) {
                infoHTML += `<div class="detail-compact" style="background: var(--bg-secondary); padding: 8px; border-radius: 6px; font-size: 12px;"><strong>Requested:</strong><br><span class="requested-badge">${data.user_selections.requested_carrier}</span></div>`;
            }
            if (data.user_selections.requested_area_code) {
                infoHTML += `<div class="detail-compact" style="background: var(--bg-secondary); padding: 8px; border-radius: 6px; font-size: 12px;"><strong>Area Code:</strong><br><span class="requested-badge">${data.user_selections.requested_area_code}</span></div>`;
            }
        }
        
        // Cost and tier info
        const tierName = getTierName(data.service_name);
        infoHTML += `<div class="detail-compact" style="background: var(--bg-secondary); padding: 8px; border-radius: 6px; font-size: 12px;"><strong>Cost:</strong><br><span>N${data.cost} (${tierName})</span></div>`;
        
        infoContainer.textContent = infoHTML;  // XSS Fix: Use textContent instead of innerHTML
    }
    
    document.getElementById('verification-details').classList.remove('hidden');
    document.getElementById('messages-section').classList.add('hidden');
    document.getElementById('retry-btn').classList.add('hidden');
    
    // Enhanced button visibility logic
    const isVoice = data.capability === 'voice';
    const checkMessagesBtn = document.getElementById('check-messages-btn');
    const checkVoiceBtn = document.getElementById('check-voice-btn');
    
    if (checkMessagesBtn) {
        checkMessagesBtn.classList.toggle('hidden', isVoice);
        checkMessagesBtn.textContent = isVoice ? '📞 Check Call' : '📱 Check SMS';
    }
    
    if (checkVoiceBtn) {
        checkVoiceBtn.classList.toggle('hidden', !isVoice);
    }
    
    // Scroll to verification details for better UX
    document.getElementById('verification-details').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    
    // Smart refresh intervals based on capability and time elapsed
    const getRefreshInterval = () => {
        if (!verificationStartTime) return 10000;
        
        const elapsed = Date.now() - verificationStartTime;
        const isVoice = currentCapability === 'voice';
        
        // More frequent checks for voice and in first 30 seconds
        if (elapsed < 30000) return isVoice ? 3000 : 5000;
        if (elapsed < 60000) return isVoice ? 5000 : 8000;
        return 10000;
    };
    
    const refreshCheck = async () => {
        if (currentVerificationId) {
            if (currentCapability === 'voice') {
                await checkVoiceCall(true);
            } else {
                await checkMessages(true);
            }
            await updateVerificationStatus();
        }
        
        // Schedule next check with dynamic interval
        if (autoRefreshInterval) {
            clearTimeout(autoRefreshInterval);
            autoRefreshInterval = setTimeout(refreshCheck, getRefreshInterval());
        }
    };
    
    // Start first check
    autoRefreshInterval = setTimeout(refreshCheck, getRefreshInterval());
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearTimeout(autoRefreshInterval);
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

function startSmartCountdown(serviceName, capability) {
    const baseTimer = getServiceTimer(serviceName);
    const isVoice = capability === 'voice';
    
    // Voice calls typically take longer to receive
    const duration = isVoice ? Math.max(baseTimer + 30, 90) : baseTimer;
    
    startCountdown(duration);
}

function startCountdown(duration = 60) {
    countdownSeconds = duration;
    const timerRow = document.getElementById('timer-row');
    const countdownEl = document.getElementById('countdown');
    
    if (timerRow) timerRow.style.display = 'block';
    if (countdownEl) countdownEl.textContent = `${countdownSeconds}s`;
    
    if (countdownInterval) clearInterval(countdownInterval);
    
    countdownInterval = setInterval(() => {
        countdownSeconds--;
        if (countdownEl) countdownEl.textContent = `${countdownSeconds}s`;
        
        // Enhanced color coding with capability awareness
        if (countdownEl) {
            const isVoice = currentCapability === 'voice';
            const warningThreshold = isVoice ? 20 : 10;
            const cautionThreshold = isVoice ? 45 : 30;
            
            if (countdownSeconds <= warningThreshold) {
                countdownEl.style.color = '#ef4444';
            } else if (countdownSeconds <= cautionThreshold) {
                countdownEl.style.color = '#f59e0b';
            } else {
                countdownEl.style.color = '#10b981';
            }
        }
        
        if (countdownSeconds <= 0) {
            clearInterval(countdownInterval);
            autoCancel();
        }
    }, 1000);
}

function stopCountdown() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
    document.getElementById('timer-row').style.display = 'none';
}

function showRetryModal() {
    const isVoice = currentCapability === 'voice';
    const elapsedTime = verificationStartTime ? Math.floor((Date.now() - verificationStartTime) / 1000) : 0;
    
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    
    const title = isVoice ? 'No Voice Call Received' : 'No SMS Received';
    const description = isVoice 
        ? 'The voice verification call was not received or processed. Choose an option:'
        : 'The SMS verification code was not received. Choose an option:';
    
    const titleEl = document.createElement('h2');
    titleEl.textContent = title;
    
    const descEl = document.createElement('p');
    descEl.style.cssText = 'color: #6b7280; margin-bottom: 15px;';
    descEl.textContent = description;
    
    const detailsDiv = document.createElement('div');
    detailsDiv.style.cssText = 'background: #f3f4f6; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; color: #374151;';
    detailsDiv.innerHTML = `<strong>Verification Details:</strong><br>Service: ${formatServiceName(currentServiceName)}<br>Type: ${isVoice ? '📞 Voice Call' : '📱 SMS Text'}<br>Elapsed: ${elapsedTime}s`;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modalContent.style.maxWidth = '500px';
    modalContent.appendChild(titleEl);
    modalContent.appendChild(descEl);
    modalContent.appendChild(detailsDiv);
    
    modal.appendChild(modalContent);
    
    const buttonsDiv = document.createElement('div');
    buttonsDiv.style.cssText = 'display: flex; flex-direction: column; gap: 12px;';
    
    if (!isVoice) {
        const voiceBtn = document.createElement('button');
        voiceBtn.textContent = '📞 Try Voice Verification';
        voiceBtn.style.cssText = 'background: #10b981; padding: 15px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; color: white;';
        voiceBtn.onclick = retryWithVoice;
        buttonsDiv.appendChild(voiceBtn);
    } else {
        const smsBtn = document.createElement('button');
        smsBtn.textContent = '📱 Try SMS Verification';
        smsBtn.style.cssText = 'background: #10b981; padding: 15px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; color: white;';
        smsBtn.onclick = retryWithSMS;
        buttonsDiv.appendChild(smsBtn);
    }
    
    const retryBtn = document.createElement('button');
    retryBtn.textContent = '🔄 Retry Same Number';
    retryBtn.style.cssText = 'background: #667eea; padding: 15px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; color: white;';
    retryBtn.onclick = retryWithSame;
    buttonsDiv.appendChild(retryBtn);
    
    const newBtn = document.createElement('button');
    newBtn.textContent = '🆕 Get New Number';
    newBtn.style.cssText = 'background: #f59e0b; padding: 15px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; color: white;';
    newBtn.onclick = retryWithNew;
    buttonsDiv.appendChild(newBtn);
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel & Refund';
    cancelBtn.style.cssText = 'background: #ef4444; padding: 12px; border: none; border-radius: 8px; cursor: pointer; color: white; font-weight: 600;';
    cancelBtn.onclick = closeRetryModal;
    buttonsDiv.appendChild(cancelBtn);
    
    modalContent.appendChild(buttonsDiv);
    document.body.appendChild(modal);
}

function closeRetryModal() {
    const modal = document.querySelector('.modal');
    if (modal) modal.remove();
}

async function retryWithVoice() {
    closeRetryModal();
    currentRetryCount++;
    
    if (currentRetryCount > maxRetries) {
        showNotification('⚠️ Maximum retry attempts reached', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/retry`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({retry_type: 'voice'})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentCapability = 'voice';
            displayVerification(data);
            showNotification('✅ Switched to voice verification', 'success');
            startAutoRefresh();
            startSmartCountdown(currentServiceName, 'voice');
        } else {
            showNotification(`❌ ${data.detail || 'Failed to switch to voice'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function retryWithSMS() {
    closeRetryModal();
    currentRetryCount++;
    
    if (currentRetryCount > maxRetries) {
        showNotification('⚠️ Maximum retry attempts reached', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/retry`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({retry_type: 'sms'})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentCapability = 'sms';
            displayVerification(data);
            showNotification('✅ Switched to SMS verification', 'success');
            startAutoRefresh();
            startSmartCountdown(currentServiceName, 'sms');
        } else {
            showNotification(`❌ ${data.detail || 'Failed to switch to SMS'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function retryWithSame() {
    closeRetryModal();
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/retry`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({retry_type: 'same'})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            displayVerification(data);
            showNotification('✅ Retrying with same number', 'success');
            startAutoRefresh();
        } else {
            showNotification(`❌ ${data.detail || 'Failed to retry'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function retryWithNew() {
    closeRetryModal();
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/retry`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({retry_type: 'new'})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            showNotification('✅ New number assigned', 'success');
            startAutoRefresh();
        } else {
            showNotification(`❌ ${data.detail || 'Failed to get new number'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function autoCancel() {
    if (!currentVerificationId) return;
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/messages`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            if (data.messages && data.messages.length > 0) {
                stopCountdown();
                showNotification('SMS received!', 'success');
                checkMessages(true);
                return;
            }
        }
    } catch (err) {}
    
    stopAutoRefresh();
    stopCountdown();
    showRetryModal();
}

async function retryVerification() {
    if (!currentServiceName) return;
    
    document.getElementById('retry-btn').classList.add('hidden');
    document.getElementById('verification-details').classList.add('hidden');
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({service_name: currentServiceName})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            showNotification(`New number! Cost: ₵${data.cost}`, 'success');
            startAutoRefresh();
            loadHistory();
            loadTransactions(true);
        } else {
            showNotification(data.detail || 'Failed to retry', 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('Network error', 'error');
    }
}

async function updateVerificationStatus() {
    if (!currentVerificationId) return;
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const statusBadge = document.getElementById('status');
            statusBadge.textContent = data.status;
            statusBadge.className = `badge ${data.status}`;
            
            if (data.status === 'completed') {
                stopAutoRefresh();
                stopCountdown();
                showNotification('Verification completed!', 'success');
            }
        }
    } catch (err) {}
}

function copyPhone() {
    const phone = document.getElementById('phone-number').textContent;
    navigator.clipboard.writeText(phone);
    showNotification('Phone number copied!', 'success');
}

async function checkMessages(silent = false) {
    if (!currentVerificationId) return;
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/messages`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (!res.ok) {
            if (!silent) {
                if (res.status === 404) {
                    showNotification('❌ Verification not found or expired', 'error');
                } else if (res.status === 401) {
                    showNotification('🔒 Session expired', 'error');
                    setTimeout(() => logout(), 2000);
                } else {
                    showNotification('⚠️ Failed to get messages', 'error');
                }
            }
            return;
        }
        
        const data = await res.json();
        const messagesList = document.getElementById('messages-list');
        
        if (data.messages.length === 0) {
            messagesList.innerHTML = '<p>No messages yet. Auto-checking... <span class="auto-refresh">🔄 Auto-refresh ON</span></p>';
        } else {
            stopCountdown();
            stopAutoRefresh();
            
            const extractedCodes = data.messages.map(msg => {
                const codeMatch = msg.match(/\b\d{4,8}\b/);
                return codeMatch ? codeMatch[0] : msg;
            });
            
            messagesList.textContent = '';  // XSS Fix: Use textContent instead of innerHTML
            
            const headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'background: #10b981; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;';
            headerDiv.innerHTML = '<h2 style="margin: 0 0 8px 0; font-size: 20px;">Verification Code Received</h2><p style="margin: 0; opacity: 0.9;">Your verification code has arrived successfully</p>';
            messagesList.appendChild(headerDiv);
            
            const messagesDiv = document.createElement('div');
            messagesDiv.style.cssText = 'background: #f0fdf4; padding: 15px; border-radius: 8px; border: 2px solid #10b981; margin-bottom: 15px;';
            
            const title = document.createElement('h4');
            title.style.cssText = 'color: #166534; margin: 0 0 10px 0;';
            title.textContent = 'SMS Messages:';
            messagesDiv.appendChild(title);
            
            data.messages.forEach((msg, idx) => {
                const code = extractedCodes[idx];
                const msgDiv = document.createElement('div');
                msgDiv.style.cssText = 'background: white; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #d1fae5;';
                
                const codeHeader = document.createElement('div');
                codeHeader.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;';
                
                const codeLabel = document.createElement('strong');
                codeLabel.style.color = '#166534';
                codeLabel.textContent = 'Code:';
                
                const copyBtn = document.createElement('button');
                copyBtn.style.cssText = 'background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600;';
                copyBtn.textContent = 'Copy Code';
                copyBtn.onclick = () => copyCode(code);
                
                codeHeader.appendChild(codeLabel);
                codeHeader.appendChild(copyBtn);
                
                const codeEl = document.createElement('code');
                codeEl.style.cssText = 'font-family: monospace; font-size: 18px; color: #166534; display: block; background: #f0fdf4; padding: 10px; border-radius: 4px; text-align: center; font-weight: bold;';
                codeEl.textContent = code;
                
                const details = document.createElement('details');
                details.style.marginTop = '8px';
                
                const summary = document.createElement('summary');
                summary.style.cssText = 'cursor: pointer; color: #6b7280; font-size: 13px;';
                summary.textContent = 'Full message';
                
                const fullMsg = document.createElement('div');
                fullMsg.style.cssText = 'margin-top: 8px; font-size: 13px; color: #6b7280;';
                fullMsg.textContent = msg;
                
                details.appendChild(summary);
                details.appendChild(fullMsg);
                
                msgDiv.appendChild(codeHeader);
                msgDiv.appendChild(codeEl);
                msgDiv.appendChild(details);
                
                messagesDiv.appendChild(msgDiv);
            });
            
            const tryBtn = document.createElement('button');
            tryBtn.style.cssText = 'margin-top: 15px; width: 100%; background: #667eea; color: white; padding: 14px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer;';
            tryBtn.textContent = 'Try Another Service';
            tryBtn.onclick = tryAnotherService;
            
            messagesList.appendChild(messagesDiv);
            messagesList.appendChild(tryBtn);
            
            if (!silent) {
                // Track verification success
                if (typeof trackVerificationSuccess === 'function' && currentServiceName) {
                    const price = await getServicePrice(currentServiceName, currentCapability);
                    trackVerificationSuccess(currentServiceName, price);
                }
                
                showNotification('🎉 Verification successful!', 'success');
                
                if (firstVerificationCompleted && !hasShownPricingOffer) {
                    setTimeout(() => showPricingOffer(), 2000);
                }
            }
        }
        
        document.getElementById('messages-section').classList.remove('hidden');
    } catch (err) {
        if (!silent) showNotification('🌐 Network error checking messages', 'error');
    }
}

function copyCode(code) {
    navigator.clipboard.writeText(code).then(() => {
        showNotification(`Code ${code} copied to clipboard`, 'success');
    }).catch(() => {
        showNotification('Failed to copy code', 'error');
    });
}

function tryAnotherService() {
    clearSession();
    document.getElementById('service-select').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('service-select').focus();
    showNotification('Select a new service to verify', 'success');
}

async function cancelVerification() {
    if (!currentVerificationId) {
        showNotification('⚠️ No active verification to cancel', 'error');
        return;
    }
    
    if (!confirm('Cancel this verification and get refund?')) return;
    
    showLoading(true);
    stopCountdown();
    stopAutoRefresh();
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            if (typeof updateUserCredits === 'function') {
                updateUserCredits(data.new_balance);
            } else {
                document.getElementById('user-credits').textContent = data.new_balance.toFixed(2);
            }
            showNotification(`✅ Cancelled! Refunded N${data.refunded.toFixed(2)}`, 'success');
            clearSession();
            if (typeof loadHistory === 'function') loadHistory();
            if (typeof loadTransactions === 'function') loadTransactions(true);
        } else {
            if (res.status === 404) {
                showNotification('❌ Verification not found or already cancelled', 'error');
            } else if (res.status === 401) {
                showNotification('🔒 Session expired. Please login again', 'error');
                setTimeout(() => logout(), 2000);
            } else {
                showNotification(`❌ ${data.detail || 'Failed to cancel verification'}`, 'error');
            }
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error. Please try again', 'error');
        console.error('Cancel verification error:', err);
    }
}

async function checkVoiceCall(silent = false) {
    if (!currentVerificationId) return;
    
    if (!silent) showLoading(true);
    
    try {
        // First check verification status
        const statusRes = await fetch(`${API_BASE}/verify/${currentVerificationId}`, {
            headers: { 'Authorization': `Bearer ${window.token}` }
        });
        
        if (statusRes.ok) {
            const statusData = await statusRes.json();
            
            // If completed, try to get voice details
            if (statusData.status === 'completed') {
                const voiceRes = await fetch(`${API_BASE}/verify/${currentVerificationId}/voice`, {
                    headers: { 'Authorization': `Bearer ${window.token}` }
                });
                
                if (!silent) showLoading(false);
                
                if (voiceRes.ok) {
                    const data = await voiceRes.json();
                    displayVoiceResults(data);
                    stopAutoRefresh();
                    stopCountdown();
                    if (!silent) showNotification('📞 Voice verification completed!', 'success');
                    return true;
                } else {
                    // Voice endpoint might not be ready yet, check messages endpoint
                    return await checkMessages(silent);
                }
            } else if (!silent) {
                showLoading(false);
                showNotification(`🔄 Voice call status: ${statusData.status}`, 'info');
            }
        } else if (!silent) {
            showLoading(false);
            showNotification('Failed to check voice call status', 'error');
        }
    } catch (error) {
        if (!silent) {
            showLoading(false);
            showNotification('Network error checking voice call', 'error');
        }
    }
    
    return false;
}

function displayVoiceResults(data) {
    const messagesList = document.getElementById('messages-list');
    if (!messagesList) return;
    
    const transcriptionCode = data.transcription ? data.transcription.match(/\b\d{4,8}\b/)?.[0] : null;
    const hasTranscription = data.transcription && data.transcription.trim();
    
    messagesList.textContent = '';  // XSS Fix: Use textContent instead of innerHTML
    
    const headerDiv = document.createElement('div');
    headerDiv.style.cssText = 'background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;';
    headerDiv.innerHTML = '<h2 style="margin: 0 0 8px 0; font-size: 20px;">📞 Voice Verification Complete</h2><p style="margin: 0; opacity: 0.9;">Your voice verification call has been processed</p>';
    messagesList.appendChild(headerDiv);
    
    const detailsDiv = document.createElement('div');
    detailsDiv.style.cssText = 'background: #f0fdf4; padding: 15px; border-radius: 8px; border: 2px solid #10b981; margin-bottom: 15px;';
    
    const phoneDiv = document.createElement('div');
    phoneDiv.style.marginBottom = '10px';
    phoneDiv.innerHTML = `<strong>Phone:</strong> ${formatPhoneNumber(data.phone_number)}`;
    detailsDiv.appendChild(phoneDiv);
    
    const durationDiv = document.createElement('div');
    durationDiv.style.marginBottom = '10px';
    durationDiv.innerHTML = `<strong>Call Duration:</strong> ${data.call_duration ? `${data.call_duration}s` : 'N/A'}`;
    detailsDiv.appendChild(durationDiv);
    
    const statusDiv = document.createElement('div');
    statusDiv.style.marginBottom = '10px';
    statusDiv.innerHTML = `<strong>Status:</strong> ${data.call_status || 'Completed'}`;
    detailsDiv.appendChild(statusDiv);
    
    if (hasTranscription) {
        const transcriptionDiv = document.createElement('div');
        transcriptionDiv.style.cssText = 'background: white; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #d1fae5;';
        
        const codeHeader = document.createElement('div');
        codeHeader.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;';
        
        const codeLabel = document.createElement('strong');
        codeLabel.style.color = '#166534';
        codeLabel.textContent = 'Verification Code:';
        
        const copyBtn = document.createElement('button');
        copyBtn.style.cssText = 'background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600;';
        copyBtn.textContent = 'Copy Code';
        copyBtn.onclick = () => copyCode(transcriptionCode || data.transcription);
        
        codeHeader.appendChild(codeLabel);
        codeHeader.appendChild(copyBtn);
        
        const codeEl = document.createElement('code');
        codeEl.style.cssText = 'font-family: monospace; font-size: 18px; color: #166534; display: block; background: #f0fdf4; padding: 10px; border-radius: 4px; text-align: center; font-weight: bold;';
        codeEl.textContent = transcriptionCode || data.transcription;
        
        transcriptionDiv.appendChild(codeHeader);
        transcriptionDiv.appendChild(codeEl);
        
        detailsDiv.appendChild(transcriptionDiv);
    }
    
    if (data.audio_url) {
        const audioDiv = document.createElement('div');
        audioDiv.style.marginTop = '15px';
        
        const audioLabel = document.createElement('strong');
        audioLabel.style.color = '#166534';
        audioLabel.textContent = 'Audio Recording:';
        
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.src = data.audio_url;
        audio.style.cssText = 'width: 100%; margin-top: 8px;';
        
        audioDiv.appendChild(audioLabel);
        audioDiv.appendChild(audio);
        detailsDiv.appendChild(audioDiv);
    }
    
    const tryBtn = document.createElement('button');
    tryBtn.style.cssText = 'margin-top: 15px; width: 100%; background: #667eea; color: white; padding: 14px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer;';
    tryBtn.textContent = 'Try Another Service';
    tryBtn.onclick = tryAnotherService;
    
    messagesList.appendChild(detailsDiv);
    messagesList.appendChild(tryBtn);
    
    document.getElementById('messages-section').classList.remove('hidden');
}

function clearSession() {
    currentVerificationId = null;
    currentServiceName = null;
    currentCapability = 'sms';
    verificationStartTime = null;
    currentRetryCount = 0;
    
    stopAutoRefresh();
    stopCountdown();
    
    document.getElementById('verification-details').classList.add('hidden');
    document.getElementById('messages-section').classList.add('hidden');
    
    // Reset capability selection to SMS
    const smsRadio = document.querySelector('input[name="capability"][value="sms"]');
    if (smsRadio) smsRadio.checked = true;
    
    // Clear any existing retry modals
    const existingModal = document.querySelector('.modal');
    if (existingModal) existingModal.remove();
}
