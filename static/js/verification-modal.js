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
  await loadCountries();
}

async function loadCountries() {
  try {
    const response = await fetch('/api/countries/');
    const data = await response.json();
    verificationState.countries = data.countries || [];
    
    const select = document.getElementById('country-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">-- Select Country --</option>';
    
    verificationState.countries.forEach(country => {
      const option = document.createElement('option');
      option.value = country.code;
      option.textContent = `${country.name} (${country.code})`;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Failed to load countries:', error);
  }
}

async function onCountryChange() {
  const country = document.getElementById('country-select').value;
  verificationState.country = country;
  
  if (!country) {
    document.getElementById('service-select').innerHTML = '<option value="">-- Select Service --</option>';
    return;
  }

  try {
    const response = await fetch(`/api/countries/${country}/services`);
    const data = await response.json();
    verificationState.services[country] = data.services || [];
    
    const select = document.getElementById('service-select');
    select.innerHTML = '<option value="">-- Select Service --</option>';
    
    verificationState.services[country].forEach(service => {
      const option = document.createElement('option');
      option.value = service.name;
      option.textContent = service.name;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Failed to load services:', error);
  }
}

function onServiceChange() {
  const service = document.getElementById('service-select').value;
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
  if (step === 2 && !verificationState.country) {
    alert('Please select a country');
    return;
  }
  
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
    const countryName = document.querySelector(`option[value="${verificationState.country}"]`)?.textContent || verificationState.country;
    document.getElementById('confirm-country').textContent = countryName;
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

function openVerificationModal() {
  document.getElementById('verification-modal').style.display = 'flex';
  initVerificationModal();
  goToStep(1);
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
window.onCountryChange = onCountryChange;
window.onServiceChange = onServiceChange;
window.purchaseVerification = purchaseVerification;
window.copyToClipboard = copyToClipboard;
