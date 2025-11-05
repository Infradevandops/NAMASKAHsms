// 5SIM Pricing Manager
class PricingManager {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }
    
    async updatePricing(country = 'us', service = 'any') {
        try {
            const cacheKey = `${country}-${service}`;
            const cached = this.cache.get(cacheKey);
            
            if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
                this.displayPricing(cached.data);
                return;
            }
            
            const response = await fetch(`/api/5sim/pricing?country=${country}&service=${service}`, {
                headers: {
                    'Authorization': `Bearer ${window.token || ''}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const pricing = await response.json();
            
            this.cache.set(cacheKey, {
                data: pricing,
                timestamp: Date.now()
            });
            
            this.displayPricing(pricing);
            
        } catch (error) {
            console.error('Pricing update failed:', error);
            this.displayFallbackPricing(service);
        }
    }
    
    displayPricing(pricing) {
        const display = document.getElementById('pricing-display');
        if (!display) return;
        
        if (pricing && typeof pricing === 'object') {
            const cost = pricing.cost || pricing.price || '0.50';
            const count = pricing.count || pricing.available || 'N/A';
            
            display.innerHTML = `
                <span class="price">$${cost}</span>
                <span class="currency">USD</span>
                <span class="availability">${count} available</span>
            `;
        } else {
            this.displayFallbackPricing();
        }
    }
    
    displayFallbackPricing(service = 'default') {
        const display = document.getElementById('pricing-display');
        if (!display) return;
        
        const fallbackPrices = {
            'whatsapp': '0.75',
            'telegram': '0.75', 
            'discord': '0.75',
            'google': '0.75',
            'instagram': '1.00',
            'facebook': '1.00',
            'twitter': '1.00',
            'default': '0.50'
        };
        
        const price = fallbackPrices[service] || fallbackPrices['default'];
        
        display.innerHTML = `
            <span class="price">$${price}</span>
            <span class="currency">USD</span>
            <span class="availability">Available</span>
        `;
    }
}

// Initialize pricing manager
const pricingManager = new PricingManager();

// Auto-update pricing when service changes
document.addEventListener('DOMContentLoaded', () => {
    const serviceSelect = document.getElementById('service-select');
    if (serviceSelect) {
        serviceSelect.addEventListener('change', (e) => {
            pricingManager.updatePricing('us', e.target.value);
        });
        
        // Initial load
        if (serviceSelect.value) {
            pricingManager.updatePricing('us', serviceSelect.value);
        }
    }
});