/**
 * Currency Selector - Ultra Stable & Functional
 * Handles currency selection, persistence, and real-time updates
 */

(function() {
    'use strict';

    // Supported currencies with symbols and names
    const CURRENCIES = [
        { code: 'USD', symbol: '$', name: 'US Dollar', flag: '🇺🇸' },
        { code: 'EUR', symbol: '€', name: 'Euro', flag: '🇪🇺' },
        { code: 'GBP', symbol: '£', name: 'British Pound', flag: '🇬🇧' },
        { code: 'NGN', symbol: '₦', name: 'Nigerian Naira', flag: '🇳🇬' },
        { code: 'INR', symbol: '₹', name: 'Indian Rupee', flag: '🇮🇳' },
        { code: 'CNY', symbol: '¥', name: 'Chinese Yuan', flag: '🇨🇳' },
        { code: 'JPY', symbol: '¥', name: 'Japanese Yen', flag: '🇯🇵' },
        { code: 'BRL', symbol: 'R$', name: 'Brazilian Real', flag: '🇧🇷' },
        { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar', flag: '🇨🇦' },
        { code: 'AUD', symbol: 'A$', name: 'Australian Dollar', flag: '🇦🇺' }
    ];

    // Exchange rates (updated periodically)
    let exchangeRates = {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'NGN': 1550.0,
        'INR': 83.0,
        'CNY': 7.24,
        'JPY': 149.0,
        'BRL': 4.97,
        'CAD': 1.36,
        'AUD': 1.52
    };

    let currentCurrency = 'USD';
    let isDropdownOpen = false;

    /**
     * Initialize currency selector
     */
    function init() {
        console.log('[Currency] Initializing currency selector...');

        // Load saved currency from localStorage
        const savedCurrency = localStorage.getItem('user_currency');
        if (savedCurrency && CURRENCIES.find(c => c.code === savedCurrency)) {
            currentCurrency = savedCurrency;
        }

        // Load from API if user is logged in
        loadUserCurrency();

        // Update display
        updateCurrencyDisplay();

        // Render currency list
        renderCurrencyList();

        // Setup event listeners
        setupEventListeners();

        // Fetch latest exchange rates
        fetchExchangeRates();

        console.log('[Currency] Initialized with currency:', currentCurrency);
    }

    /**
     * Load user's saved currency from API
     */
    async function loadUserCurrency() {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        try {
            const response = await fetch('/api/user/preferences', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.currency) {
                    currentCurrency = data.currency;
                    localStorage.setItem('user_currency', currentCurrency);
                    updateCurrencyDisplay();
                    console.log('[Currency] Loaded from API:', currentCurrency);
                }
            }
        } catch (error) {
            console.warn('[Currency] Failed to load from API:', error);
        }
    }

    /**
     * Save currency preference to API
     */
    async function saveCurrencyPreference(currency) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            // Guest user - only save to localStorage
            localStorage.setItem('user_currency', currency);
            return;
        }

        try {
            const response = await fetch('/api/user/preferences', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ currency: currency })
            });

            if (response.ok) {
                console.log('[Currency] Saved to API:', currency);
            } else {
                console.warn('[Currency] Failed to save to API');
            }
        } catch (error) {
            console.error('[Currency] Error saving to API:', error);
        }

        // Always save to localStorage as backup
        localStorage.setItem('user_currency', currency);
    }

    /**
     * Fetch latest exchange rates
     */
    async function fetchExchangeRates() {
        try {
            // Check cache first
            const cached = localStorage.getItem('exchange_rates');
            const cacheTime = localStorage.getItem('exchange_rates_time');
            
            if (cached && cacheTime) {
                const age = Date.now() - parseInt(cacheTime);
                // Use cache if less than 1 hour old
                if (age < 3600000) {
                    exchangeRates = JSON.parse(cached);
                    console.log('[Currency] Using cached exchange rates');
                    return;
                }
            }

            // Fetch from API (fallback to static rates if fails)
            const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
            if (response.ok) {
                const data = await response.json();
                exchangeRates = {
                    'USD': 1.0,
                    'EUR': data.rates.EUR || 0.92,
                    'GBP': data.rates.GBP || 0.79,
                    'NGN': data.rates.NGN || 1550.0,
                    'INR': data.rates.INR || 83.0,
                    'CNY': data.rates.CNY || 7.24,
                    'JPY': data.rates.JPY || 149.0,
                    'BRL': data.rates.BRL || 4.97,
                    'CAD': data.rates.CAD || 1.36,
                    'AUD': data.rates.AUD || 1.52
                };

                // Cache for 1 hour
                localStorage.setItem('exchange_rates', JSON.stringify(exchangeRates));
                localStorage.setItem('exchange_rates_time', Date.now().toString());
                
                console.log('[Currency] Fetched latest exchange rates');
            }
        } catch (error) {
            console.warn('[Currency] Failed to fetch exchange rates, using defaults:', error);
        }
    }

    /**
     * Update currency display in header
     */
    function updateCurrencyDisplay() {
        const displayEl = document.getElementById('selected-currency-display');
        if (displayEl) {
            const currency = CURRENCIES.find(c => c.code === currentCurrency);
            displayEl.textContent = currency ? `${currency.flag} ${currency.code}` : currentCurrency;
        }

        // Update all prices on the page
        updateAllPrices();

        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('currencyChanged', { 
            detail: { currency: currentCurrency } 
        }));
    }

    /**
     * Render currency list in dropdown
     */
    function renderCurrencyList() {
        const listEl = document.getElementById('currency-list');
        if (!listEl) return;

        listEl.innerHTML = CURRENCIES.map(currency => `
            <button class="currency-option" 
                    data-currency="${currency.code}"
                    role="menuitem"
                    style="width: 100%; text-align: left; padding: 10px 12px; border: none; background: ${currency.code === currentCurrency ? 'rgba(254, 60, 114, 0.1)' : 'transparent'}; cursor: pointer; border-radius: 8px; display: flex; align-items: center; gap: 8px; transition: background 0.2s; font-size: 14px;"
                    onmouseover="this.style.background='rgba(254, 60, 114, 0.05)'"
                    onmouseout="this.style.background='${currency.code === currentCurrency ? 'rgba(254, 60, 114, 0.1)' : 'transparent'}'">
                <span style="font-size: 18px;">${currency.flag}</span>
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: var(--text-primary, #1f2937);">${currency.code}</div>
                    <div style="font-size: 12px; color: var(--text-muted, #6b7280);">${currency.name}</div>
                </div>
                ${currency.code === currentCurrency ? '<span style="color: #FE3C72;">✓</span>' : ''}
            </button>
        `).join('');

        // Add click handlers
        listEl.querySelectorAll('.currency-option').forEach(btn => {
            btn.addEventListener('click', () => {
                selectCurrency(btn.dataset.currency);
            });
        });
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        const btn = document.getElementById('currency-selector-btn');
        const dropdown = document.getElementById('currency-dropdown');
        const searchInput = document.getElementById('currency-search');

        if (!btn || !dropdown) return;

        // Toggle dropdown
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown();
        });

        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                filterCurrencies(e.target.value);
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (isDropdownOpen && !dropdown.contains(e.target) && e.target !== btn) {
                closeDropdown();
            }
        });

        // Keyboard navigation
        btn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleDropdown();
            }
        });
    }

    /**
     * Toggle dropdown visibility
     */
    function toggleDropdown() {
        if (isDropdownOpen) {
            closeDropdown();
        } else {
            openDropdown();
        }
    }

    /**
     * Open dropdown
     */
    function openDropdown() {
        const dropdown = document.getElementById('currency-dropdown');
        const btn = document.getElementById('currency-selector-btn');
        
        if (dropdown && btn) {
            dropdown.style.display = 'block';
            btn.setAttribute('aria-expanded', 'true');
            isDropdownOpen = true;

            // Focus search input
            const searchInput = document.getElementById('currency-search');
            if (searchInput) {
                setTimeout(() => searchInput.focus(), 100);
            }
        }
    }

    /**
     * Close dropdown
     */
    function closeDropdown() {
        const dropdown = document.getElementById('currency-dropdown');
        const btn = document.getElementById('currency-selector-btn');
        
        if (dropdown && btn) {
            dropdown.style.display = 'none';
            btn.setAttribute('aria-expanded', 'false');
            isDropdownOpen = false;

            // Clear search
            const searchInput = document.getElementById('currency-search');
            if (searchInput) {
                searchInput.value = '';
                filterCurrencies('');
            }
        }
    }

    /**
     * Filter currencies by search term
     */
    function filterCurrencies(searchTerm) {
        const listEl = document.getElementById('currency-list');
        if (!listEl) return;

        const term = searchTerm.toLowerCase();
        const options = listEl.querySelectorAll('.currency-option');

        options.forEach(option => {
            const currency = CURRENCIES.find(c => c.code === option.dataset.currency);
            if (!currency) return;

            const matches = 
                currency.code.toLowerCase().includes(term) ||
                currency.name.toLowerCase().includes(term);

            option.style.display = matches ? 'flex' : 'none';
        });
    }

    /**
     * Select a currency
     */
    function selectCurrency(currencyCode) {
        console.log('[Currency] Selecting currency:', currencyCode);

        currentCurrency = currencyCode;
        
        // Update display
        updateCurrencyDisplay();
        
        // Re-render list to show checkmark
        renderCurrencyList();
        
        // Save preference
        saveCurrencyPreference(currencyCode);
        
        // Close dropdown
        closeDropdown();

        // Show toast notification
        const currency = CURRENCIES.find(c => c.code === currencyCode);
        if (currency && window.toast) {
            window.toast.success(`Currency changed to ${currency.name}`);
        }
    }

    /**
     * Convert amount from USD to selected currency
     */
    function convertAmount(amountUSD) {
        const rate = exchangeRates[currentCurrency] || 1.0;
        return amountUSD * rate;
    }

    /**
     * Format amount in selected currency
     */
    function formatAmount(amountUSD, options = {}) {
        const converted = convertAmount(amountUSD);
        const currency = CURRENCIES.find(c => c.code === currentCurrency);
        
        const decimals = options.decimals !== undefined ? options.decimals : 
                        (currentCurrency === 'JPY' ? 0 : 2);

        const formatted = converted.toFixed(decimals);
        
        if (options.showSymbol !== false && currency) {
            return `${currency.symbol}${formatted}`;
        }
        
        return formatted;
    }

    /**
     * Update all prices on the page
     */
    function updateAllPrices() {
        // Update elements with data-usd-amount attribute
        document.querySelectorAll('[data-usd-amount]').forEach(el => {
            const usdAmount = parseFloat(el.dataset.usdAmount);
            if (!isNaN(usdAmount)) {
                el.textContent = formatAmount(usdAmount);
            }
        });

        // Update balance display if it exists
        const balanceEl = document.querySelector('.balance-amount');
        if (balanceEl && balanceEl.dataset.usdAmount) {
            const usdAmount = parseFloat(balanceEl.dataset.usdAmount);
            if (!isNaN(usdAmount)) {
                balanceEl.textContent = formatAmount(usdAmount);
            }
        }
    }

    /**
     * Get current currency
     */
    function getCurrentCurrency() {
        return currentCurrency;
    }

    /**
     * Get currency symbol
     */
    function getCurrencySymbol() {
        const currency = CURRENCIES.find(c => c.code === currentCurrency);
        return currency ? currency.symbol : '$';
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export functions globally
    window.currencySelector = {
        getCurrentCurrency,
        getCurrencySymbol,
        formatAmount,
        convertAmount,
        selectCurrency,
        updateAllPrices
    };

    console.log('[Currency] Currency selector module loaded');
})();
