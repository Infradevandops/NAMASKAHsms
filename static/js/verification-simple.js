// SMS Verification App
let currentStep = 1;
let selectedService = null;
let selectedCountry = null;
let selectedTier = 'standard';
let selectedOperator = 'any';

// Sample data
const popularServices = [
    { id: 'whatsapp', name: 'WhatsApp', icon: '📱' },
    { id: 'telegram', name: 'Telegram', icon: '✈️' },
    { id: 'discord', name: 'Discord', icon: '🎮' },
    { id: 'instagram', name: 'Instagram', icon: '📷' },
    { id: 'facebook', name: 'Facebook', icon: '👥' },
    { id: 'twitter', name: 'Twitter', icon: '🐦' },
    { id: 'tiktok', name: 'TikTok', icon: '🎵' },
    { id: 'google', name: 'Google', icon: '🔍' }
];

const popularCountries = [
    { code: 'US', name: 'United States', flag: '🇺🇸', price: '$0.15' },
    { code: 'GB', name: 'United Kingdom', flag: '🇬🇧', price: '$0.18' },
    { code: 'CA', name: 'Canada', flag: '🇨🇦', price: '$0.16' },
    { code: 'DE', name: 'Germany', flag: '🇩🇪', price: '$0.20' },
    { code: 'FR', name: 'France', flag: '🇫🇷', price: '$0.19' },
    { code: 'AU', name: 'Australia', flag: '🇦🇺', price: '$0.22' },
    { code: 'NG', name: 'Nigeria', flag: '🇳🇬', price: '$0.12' },
    { code: 'IN', name: 'India', flag: '🇮🇳', price: '$0.10' }
];

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    loadPopularServices();
    loadPopularCountries();
    setupEventListeners();
});

function loadPopularServices() {
    const container = document.getElementById('popular-services');
    container.innerHTML = popularServices.map(service => `
        <div class="service-card border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500" 
             onclick="selectService('${service.id}', '${service.name}')">
            <div class="text-2xl mb-2">${service.icon}</div>
            <div class="font-semibold text-gray-900">${service.name}</div>
        </div>
    `).join('');
}

function loadPopularCountries() {
    const container = document.getElementById('popular-countries');
    container.innerHTML = popularCountries.map(country => `
        <div class="country-card border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500" 
             onclick="selectCountry('${country.code}', '${country.name}')">
            <div class="text-2xl mb-2">${country.flag}</div>
            <div class="font-semibold text-gray-900">${country.name}</div>
            <div class="text-sm text-gray-600">${country.price}</div>
        </div>
    `).join('');
}

function setupEventListeners() {
    // Service search
    document.getElementById('service-search').addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase();
        // Filter services based on search
    });

    // Country search
    document.getElementById('country-search').addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase();
        // Filter countries based on search
    });

    // Show all services
    document.getElementById('show-all-services').addEventListener('click', function() {
        document.getElementById('all-services').classList.toggle('hidden');
        this.textContent = this.textContent.includes('Show') ? 'Hide All Services' : 'Show All Services';
    });

    // Show all countries
    document.getElementById('show-all-countries').addEventListener('click', function() {
        document.getElementById('all-countries').classList.toggle('hidden');
        this.textContent = this.textContent.includes('Show') ? 'Hide All Countries' : 'Show All Countries';
    });

    // Tier selection
    document.querySelectorAll('.tier-card').forEach(card => {
        card.addEventListener('click', function() {
            document.querySelectorAll('.tier-card').forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
            selectedTier = this.dataset.tier;
        });
    });

    // Start verification
    document.getElementById('start-verification').addEventListener('click', startVerification);
    
    // Back button
    document.getElementById('back-to-options').addEventListener('click', () => goToStep(3));
}

function selectService(serviceId, serviceName) {
    selectedService = { id: serviceId, name: serviceName };
    updateSummary();
    goToStep(2);
}

function selectCountry(countryCode, countryName) {
    selectedCountry = { code: countryCode, name: countryName };
    updateSummary();
    goToStep(3);
}

function goToStep(step) {
    // Hide all steps
    document.getElementById('service-selection').classList.add('hidden');
    document.getElementById('country-selection').classList.add('hidden');
    document.getElementById('options-selection').classList.add('hidden');
    document.getElementById('verification-process').classList.add('hidden');

    // Update step indicators
    for (let i = 1; i <= 4; i++) {
        const stepEl = document.getElementById(`step${i}`);
        if (i <= step) {
            stepEl.className = 'w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold';
        } else {
            stepEl.className = 'w-8 h-8 bg-gray-200 text-gray-600 rounded-full flex items-center justify-center text-sm font-bold';
        }
    }

    // Show current step
    switch(step) {
        case 1:
            document.getElementById('service-selection').classList.remove('hidden');
            break;
        case 2:
            document.getElementById('country-selection').classList.remove('hidden');
            break;
        case 3:
            document.getElementById('options-selection').classList.remove('hidden');
            loadAvailability();
            break;
        case 4:
            document.getElementById('verification-process').classList.remove('hidden');
            break;
    }
    
    currentStep = step;
}

function updateSummary() {
    if (selectedService) {
        document.getElementById('summary-service').textContent = selectedService.name;
    }
    if (selectedCountry) {
        document.getElementById('summary-country').textContent = selectedCountry.name;
    }
    document.getElementById('summary-tier').textContent = selectedTier === 'standard' ? 'Standard' : 'Premium';
    document.getElementById('summary-cost').textContent = selectedTier === 'standard' ? '$0.15' : '$0.26';
}

function loadAvailability() {
    // Simulate loading availability
    document.getElementById('numbers-available').textContent = Math.floor(Math.random() * 50) + 10;
    document.getElementById('success-rate').textContent = (Math.random() * 20 + 80).toFixed(1);
}

async function startVerification() {
    showLoading('Starting verification...');
    
    try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        hideLoading();
        showVerificationStatus();
        
    } catch (error) {
        hideLoading();
        showMessage('Error starting verification: ' + error.message, 'error');
    }
}

function showVerificationStatus() {
    const statusContainer = document.getElementById('verification-status');
    statusContainer.classList.remove('hidden');
    
    statusContainer.innerHTML = `
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div class="flex items-center mb-4">
                <div class="w-4 h-4 bg-blue-500 rounded-full animate-pulse mr-3"></div>
                <span class="font-semibold text-blue-900">Getting phone number...</span>
            </div>
            <div class="text-sm text-blue-700">
                Please wait while we assign a phone number for your verification.
            </div>
        </div>
    `;
    
    // Simulate getting phone number
    setTimeout(() => {
        const phoneNumber = '+1' + Math.floor(Math.random() * 9000000000 + 1000000000);
        statusContainer.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-4">
                <div class="flex items-center mb-4">
                    <div class="w-4 h-4 bg-green-500 rounded-full mr-3"></div>
                    <span class="font-semibold text-green-900">Phone number assigned!</span>
                </div>
                <div class="text-2xl font-mono font-bold text-center py-4 bg-white rounded border">
                    ${phoneNumber}
                </div>
                <div class="text-sm text-green-700 mt-2">
                    Use this number to verify your ${selectedService.name} account.
                </div>
            </div>
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <div class="flex items-center mb-4">
                    <div class="w-4 h-4 bg-yellow-500 rounded-full animate-pulse mr-3"></div>
                    <span class="font-semibold text-yellow-900">Waiting for SMS...</span>
                </div>
                <div class="text-sm text-yellow-700">
                    We're monitoring for incoming SMS messages. This usually takes 30-60 seconds.
                </div>
            </div>
        `;
        
        // Simulate SMS arrival
        setTimeout(() => {
            const code = Math.floor(Math.random() * 900000 + 100000);
            statusContainer.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="w-4 h-4 bg-green-500 rounded-full mr-3"></div>
                        <span class="font-semibold text-green-900">SMS received!</span>
                    </div>
                    <div class="text-3xl font-mono font-bold text-center py-6 bg-white rounded border text-green-600">
                        ${code}
                    </div>
                    <div class="text-sm text-green-700 mt-2 text-center">
                        Your verification code is ready to use!
                    </div>
                </div>
            `;
        }, 5000);
        
    }, 3000);
}

function showLoading(text) {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('message-container');
    const bgColor = type === 'error' ? 'bg-red-50 border-red-200 text-red-800' : 'bg-blue-50 border-blue-200 text-blue-800';
    
    container.innerHTML = `
        <div class="${bgColor} border rounded-lg p-4">
            ${message}
        </div>
    `;
    
    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}