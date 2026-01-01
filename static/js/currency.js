class CurrencyFormatter {
    constructor() {
        this.currency = localStorage.getItem('currency') || 'USD';
        this.rates = {};
        this.lastUpdate = null;
        this.init();
    }

    async init() {
        await this.loadRates();
        this.setupEventListeners();
    }

    async loadRates() {
        try {
            const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
            const data = await response.json();
            this.rates = data.rates;
            this.lastUpdate = new Date();
            localStorage.setItem('exchange_rates', JSON.stringify(this.rates));
            localStorage.setItem('rates_updated', this.lastUpdate.toISOString());
        } catch (error) {
            const cached = localStorage.getItem('exchange_rates');
            if (cached) {
                this.rates = JSON.parse(cached);
            } else {
                this.rates = {
                    USD: 1, EUR: 0.92, GBP: 0.79, NGN: 1580,
                    INR: 83, CNY: 7.24, JPY: 149, BRL: 4.97,
                    CAD: 1.36, AUD: 1.52
                };
            }
        }
    }

    convert(amount, fromCurrency = 'USD', toCurrency = null) {
        const target = toCurrency || this.currency;
        if (fromCurrency === target) return amount;
        const inUSD = amount / this.rates[fromCurrency];
        return inUSD * this.rates[target];
    }

    format(amount, fromCurrency = 'USD') {
        const converted = this.convert(amount, fromCurrency);
        const locale = i18n?.locale || 'en';
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: this.currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(converted);
    }

    getSymbol(currency = null) {
        const curr = currency || this.currency;
        const symbols = {
            USD: '$', EUR: '€', GBP: '£', NGN: '₦',
            INR: '₹', CNY: '¥', JPY: '¥', BRL: 'R$',
            CAD: 'C$', AUD: 'A$'
        };
        return symbols[curr] || curr;
    }

    async changeCurrency(newCurrency) {
        this.currency = newCurrency;
        localStorage.setItem('currency', newCurrency);
        document.querySelectorAll('[data-currency]').forEach(el => {
            const amount = parseFloat(el.dataset.amount);
            const from = el.dataset.from || 'USD';
            el.textContent = this.format(amount, from);
        });
        try {
            await fetch('/api/user/preferences', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ currency: newCurrency })
            });
        } catch (error) {
            console.error('Failed to save currency preference:', error);
        }
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.formatAllCurrencyElements();
        });
    }

    formatAllCurrencyElements() {
        document.querySelectorAll('[data-currency]').forEach(el => {
            const amount = parseFloat(el.dataset.amount);
            const from = el.dataset.from || 'USD';
            el.textContent = this.format(amount, from);
        });
    }
}

const currency = new CurrencyFormatter();
