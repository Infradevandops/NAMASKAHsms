// Dashboard Data Loader - Minimal fix for loading dropdowns
class DashboardLoader {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    async init() {
        if (!this.token) {
            window.location.href = '/auth/login';
            return;
        }
        
        // Load data immediately
        await Promise.all([
            this.loadServices(),
            this.loadCountries(),
            this.loadUserBalance()
        ]);
    }

    async loadServices() {
        try {
            const response = await fetch('/verify/services', {
                headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {}
            });
            
            if (response.ok) {
                const data = await response.json();
                this.populateServices(data.services || []);
            } else {
                throw new Error('Failed to load services');
            }
        } catch (error) {
            console.error('Services error:', error);
            // Use fallback services
            this.populateServices([
                {name: 'telegram', price: 0.75, category: 'Social Media'},
                {name: 'whatsapp', price: 0.75, category: 'Social Media'},
                {name: 'discord', price: 0.75, category: 'Social Media'},
                {name: 'google', price: 0.75, category: 'Business'},
                {name: 'instagram', price: 1.00, category: 'Social Media'},
                {name: 'facebook', price: 1.00, category: 'Social Media'},
                {name: 'twitter', price: 1.00, category: 'Social Media'},
                {name: 'tiktok', price: 1.00, category: 'Social Media'}
            ]);
        }
    }

    async loadCountries() {
        try {
            const response = await fetch('/countries/popular', {
                headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {}
            });
            
            if (response.ok) {
                const data = await response.json();
                this.populateCountries(data.countries || []);
            } else {
                throw new Error('Failed to load countries');
            }
        } catch (error) {
            console.error('Countries error:', error);
            // Use fallback countries
            this.populateCountries([
                {code: 'US', name: 'United States', voice_supported: true},
                {code: 'GB', name: 'United Kingdom', voice_supported: true},
                {code: 'CA', name: 'Canada', voice_supported: true},
                {code: 'DE', name: 'Germany', voice_supported: true},
                {code: 'FR', name: 'France', voice_supported: true},
                {code: 'AU', name: 'Australia', voice_supported: true},
                {code: 'JP', name: 'Japan', voice_supported: true},
                {code: 'IN', name: 'India', voice_supported: false},
                {code: 'BR', name: 'Brazil', voice_supported: false},
                {code: 'MX', name: 'Mexico', voice_supported: false}
            ]);
        }
    }

    populateServices(services) {
        const select = document.getElementById('service-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select a service...</option>';
        
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.name;
            option.textContent = `${service.name.charAt(0).toUpperCase() + service.name.slice(1)} - $${service.price}`;
            select.appendChild(option);
        });
    }

    populateCountries(countries) {
        const select = document.getElementById('country-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select a country...</option>';
        
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.name} ${country.voice_supported ? '(Voice Available)' : '(SMS Only)'}`;
            option.dataset.voiceSupported = country.voice_supported;
            select.appendChild(option);
        });
    }

    async loadUserBalance() {
        try {
            const response = await fetch('/auth/me', {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
            
            if (response.ok) {
                const user = await response.json();
                const balanceEl = document.getElementById('balance-display');
                if (balanceEl) {
                    balanceEl.textContent = `$${user.credits.toFixed(2)}`;
                }
            }
        } catch (error) {
            console.error('Balance error:', error);
        }
    }
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    const loader = new DashboardLoader();
    loader.init();
});