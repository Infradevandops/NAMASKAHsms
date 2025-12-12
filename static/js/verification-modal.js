let verificationState = {
  country: null,
  service: null,
  cost: 0,
  verificationId: null,
  activationId: null,
  pollingInterval: null,
  countries: [],
  services: {}
};

async function initVerificationModal() {
  verificationState.country = 'usa';
  await loadServices();
}

async function loadServices() {
  const select = document.getElementById('serviceSelect');
  if (!select) return;
  
  select.innerHTML = '<option value="">Loading services...</option>';
  select.disabled = true;
  
  try {
    const response = await fetch('/api/countries/usa/services');
    const data = await response.json();
    
    if (!data.success || !data.services) {
      console.error('Failed to load services:', data);
      select.innerHTML = '<option value="">Failed to load services</option>';
      return;
    }
    
    verificationState.services['usa'] = data.services;
    select.innerHTML = '<option value="">Choose a service...</option>';
    
    data.services.forEach(service => {
      const option = document.createElement('option');
      option.value = service.name;
      option.textContent = service.name;
      select.appendChild(option);
    });
    
    select.disabled = false;
    console.log(`✅ Loaded ${data.services.length} services`);
  } catch (error) {
    console.error('❌ Failed to load services:', error);
    select.innerHTML = '<option value="">Error loading services</option>';
  }
}

// Country change not needed - USA only

function onServiceChange() {
  const service = document.getElementById('serviceSelect').value;
  verificationState.service = service;
  
  if (service && verificationState.country) {
    const serviceData = verificationState.services[verificationState.country]?.find(s => s.name === service);
    if (serviceData) {
      verificationState.cost = serviceData.cost || 0.50;
      document.getElementById('price-value').textContent = `$${verificationState.cost.toFixed(2)}`;
      document.getElementById('service-price').style.display = 'block';
    }
  }
}

function goToStep(step) {
  if (step === 3 && !verificationState.service) {
    alert('Please select a service');
    return;
  }

  document.querySelectorAll('.progress-step').forEach(el => {
    const s = parseInt(el.dataset.step);
    el.classList.remove('active', 'completed');
    if (s < step) el.classList.add('completed');
    if (s === step) el.classList.add('active');
  });

  document.querySelectorAll('.verification-step').forEach(el => {
    el.classList.remove('active');
  });
  document.querySelector(`[data-step="${step}"]`).classList.add('active');

  if (step === 3) {
    document.getElementById('confirm-country').textContent = 'United States';
    document.getElementById('confirm-service').textContent = verificationState.service;
    document.getElementById('confirm-cost').textContent = `$${verificationState.cost.toFixed(2)}`;
    
    fetch('/api/user/balance')
      .then(r => r.json())
      .then(data => {
        document.getElementById('confirm-balance').textContent = `$${parseFloat(data.credits).toFixed(2)}`;
      });
  }
}

async function purchaseVerification() {
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = 'Processing...';

  try {
    const response = await fetch('/api/verify/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        country: verificationState.country,
        service_name: verificationState.service,
        capability: 'sms'
      })
    });

    const data = await response.json();

    if (response.status === 402) {
      alert('Insufficient credits. Please add credits.');
      return;
    }
    if (response.status === 503) {
      alert('Service temporarily unavailable. Please try again.');
      return;
    }
    if (!response.ok) {
      alert(`Error: ${data.detail || 'Purchase failed'}`);
      return;
    }

    verificationState.verificationId = data.verification_id;
    verificationState.activationId = data.activation_id;
    document.getElementById('phone-value').textContent = data.phone_number;
    goToStep(4);
    startSMSPolling();
    if (window.syncBalance) window.syncBalance();
  } catch (error) {
    alert(`Network error: ${error.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Purchase Now';
  }
}

function startSMSPolling() {
  const pollInterval = setInterval(async () => {
    try {
      const response = await fetch(`/api/verify/${verificationState.verificationId}/status`);
      const data = await response.json();

      if (data.sms_code) {
        clearInterval(pollInterval);
        
        document.getElementById('code-value').textContent = data.sms_code;
        document.getElementById('sms-text').textContent = data.sms_text || '';
        document.getElementById('sms-code-container').style.display = 'block';
        document.getElementById('polling-status').style.display = 'none';
        document.getElementById('copy-code-btn').style.display = 'block';
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, 2000);

  verificationState.pollingInterval = pollInterval;

  setTimeout(() => {
    clearInterval(pollInterval);
  }, 5 * 60 * 1000);
}

function copyToClipboard(elementId) {
  const element = document.getElementById(elementId);
  const text = element.textContent;
  
  navigator.clipboard.writeText(text).then(() => {
    const btn = event.target.closest('.copy-btn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    
    setTimeout(() => {
      btn.innerHTML = originalHTML;
    }, 2000);
  });
}

async function openVerificationModal() {
  document.getElementById('verification-modal').style.display = 'flex';
  goToStep(2);
  await initVerificationModal();
}

function closeVerificationModal() {
  document.getElementById('verification-modal').style.display = 'none';
  
  if (verificationState.pollingInterval) {
    clearInterval(verificationState.pollingInterval);
  }

  verificationState = {
    country: null,
    service: null,
    cost: 0,
    verificationId: null,
    activationId: null,
    pollingInterval: null,
    countries: verificationState.countries,
    services: verificationState.services
  };
}

window.openVerificationModal = openVerificationModal;
window.closeVerificationModal = closeVerificationModal;
window.goToStep = goToStep;
window.onServiceChange = onServiceChange;
window.purchaseVerification = purchaseVerification;
window.copyToClipboard = copyToClipboard;
