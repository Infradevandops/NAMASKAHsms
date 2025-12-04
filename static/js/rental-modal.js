let rentalState = {
  country: null,
  service: null,
  duration: null,
  cost: 0,
  rentalId: null,
  phoneNumber: null,
  expiresAt: null,
  countries: [],
  services: {}
};

const DURATIONS = {
  '12h': { hours: 12, cost: 6.00, label: '12 hours' },
  '24h': { hours: 24, cost: 12.00, label: '24 hours' },
  '3d': { hours: 72, cost: 30.00, label: '3 days' },
  '1w': { hours: 168, cost: 50.00, label: '1 week' },
  '1m': { hours: 720, cost: 150.00, label: '1 month' }
};

async function openRentalModal() {
  document.getElementById('rental-modal').style.display = 'flex';
  await loadCountries();
  goToStep(1);
}

function closeRentalModal() {
  document.getElementById('rental-modal').style.display = 'none';
  rentalState = {
    country: null,
    service: null,
    duration: null,
    cost: 0,
    rentalId: null,
    phoneNumber: null,
    expiresAt: null,
    countries: rentalState.countries,
    services: rentalState.services
  };
}

async function loadCountries() {
  try {
    const response = await fetch('/api/countries/');
    const data = await response.json();
    rentalState.countries = data.countries || [];
    
    const select = document.getElementById('rental-country-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">-- Select Country --</option>';
    rentalState.countries.forEach(country => {
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
  const country = document.getElementById('rental-country-select').value;
  rentalState.country = country;
  
  if (!country) {
    document.getElementById('rental-service-select').innerHTML = '<option value="">-- Select Service --</option>';
    return;
  }

  try {
    const response = await fetch(`/api/countries/${country}/services`);
    const data = await response.json();
    rentalState.services[country] = data.services || [];
    
    const select = document.getElementById('rental-service-select');
    select.innerHTML = '<option value="">-- Select Service --</option>';
    rentalState.services[country].forEach(service => {
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
  const service = document.getElementById('rental-service-select').value;
  rentalState.service = service;
}

function onDurationChange() {
  const durationKey = document.getElementById('rental-duration-select').value;
  if (durationKey && DURATIONS[durationKey]) {
    rentalState.duration = DURATIONS[durationKey].hours;
    rentalState.cost = DURATIONS[durationKey].cost;
  }
}

function goToStep(step) {
  if (step === 2 && !rentalState.country) {
    alert('Please select a country');
    return;
  }
  
  if (step === 3 && !rentalState.service) {
    alert('Please select a service');
    return;
  }

  if (step === 4 && !rentalState.duration) {
    alert('Please select a duration');
    return;
  }

  document.querySelectorAll('.rental-progress-step').forEach(el => {
    const s = parseInt(el.dataset.step);
    el.classList.remove('active', 'completed');
    if (s < step) el.classList.add('completed');
    if (s === step) el.classList.add('active');
  });

  document.querySelectorAll('.rental-step').forEach(el => {
    el.classList.remove('active');
  });
  document.querySelector(`[data-step="${step}"]`).classList.add('active');

  if (step === 4) {
    const countryName = document.querySelector(`option[value="${rentalState.country}"]`)?.textContent || rentalState.country;
    document.getElementById('rental-confirm-country').textContent = countryName;
    document.getElementById('rental-confirm-service').textContent = rentalState.service;
    document.getElementById('rental-confirm-duration').textContent = Object.values(DURATIONS).find(d => d.hours === rentalState.duration)?.label || '';
    document.getElementById('rental-confirm-cost').textContent = `$${rentalState.cost.toFixed(2)}`;
    
    fetch('/api/user/balance')
      .then(r => r.json())
      .then(data => {
        document.getElementById('rental-confirm-balance').textContent = `$${parseFloat(data.credits).toFixed(2)}`;
      });
  }
}

async function purchaseRental() {
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = 'Processing...';

  try {
    const response = await fetch('/api/rentals/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        country_code: rentalState.country,
        service_name: rentalState.service,
        duration_hours: rentalState.duration,
        auto_extend: false
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

    rentalState.rentalId = data.id;
    rentalState.phoneNumber = data.phone_number;
    rentalState.expiresAt = data.expires_at;
    document.getElementById('rental-phone-value').textContent = data.phone_number;
    goToStep(5);
    if (window.syncBalance) window.syncBalance();
  } catch (error) {
    alert(`Network error: ${error.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Purchase Now';
  }
}

function copyToClipboard(elementId) {
  const element = document.getElementById(elementId);
  const text = element.textContent;
  
  navigator.clipboard.writeText(text).then(() => {
    const btn = event.target.closest('.copy-btn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '✓ Copied';
    
    setTimeout(() => {
      btn.innerHTML = originalHTML;
    }, 2000);
  });
}

window.openRentalModal = openRentalModal;
window.closeRentalModal = closeRentalModal;
window.goToStep = goToStep;
window.onCountryChange = onCountryChange;
window.onServiceChange = onServiceChange;
window.onDurationChange = onDurationChange;
window.purchaseRental = purchaseRental;
window.copyToClipboard = copyToClipboard;
