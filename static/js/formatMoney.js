/**
 * formatMoney — Global currency formatter.
 *
 * Every money figure on the platform MUST go through this function.
 * It reads the user's selected currency from localStorage, converts
 * from USD using cached exchange rates, and returns a formatted string.
 *
 * Usage:  formatMoney(1.65)        → "$1.65" or "₦2,557.50" etc.
 *         formatMoney(1.65, true)  → "1.65"  (no symbol, for inputs)
 */
(function () {
    'use strict';

    var RATES_KEY = 'exchange_rates';
    var RATES_TIME_KEY = 'exchange_rates_time';
    var CURRENCY_KEY = 'user_currency';
    var RATES_TTL = 3600000; // 1 hour

    var FALLBACK_RATES = {
        USD: 1, EUR: 0.92, GBP: 0.79, NGN: 1580,
        INR: 83, CNY: 7.24, JPY: 149, BRL: 4.97,
        CAD: 1.36, AUD: 1.52
    };

    var SYMBOLS = {
        USD: '$', EUR: '€', GBP: '£', NGN: '₦',
        INR: '₹', CNY: '¥', JPY: '¥', BRL: 'R$',
        CAD: 'C$', AUD: 'A$'
    };

    var _rates = null;
    var _fetching = false;

    function getRates() {
        if (_rates) return _rates;
        try {
            var cached = localStorage.getItem(RATES_KEY);
            if (cached) {
                _rates = JSON.parse(cached);
                return _rates;
            }
        } catch (e) { }
        _rates = FALLBACK_RATES;
        return _rates;
    }

    function getCurrency() {
        return localStorage.getItem(CURRENCY_KEY) || 'USD';
    }

    function convert(amountUSD) {
        var currency = getCurrency();
        if (currency === 'USD') return amountUSD;
        var rates = getRates();
        var rate = rates[currency];
        if (!rate) return amountUSD;
        return amountUSD * rate;
    }

    function formatMoney(amountUSD, noSymbol) {
        if (amountUSD == null || isNaN(amountUSD)) return noSymbol ? '0.00' : '$0.00';
        var currency = getCurrency();
        var converted = convert(amountUSD);
        var decimals = currency === 'JPY' ? 0 : 2;
        var formatted = converted.toFixed(decimals);

        // Add thousand separators
        var parts = formatted.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        formatted = parts.join('.');

        if (noSymbol) return formatted;
        var symbol = SYMBOLS[currency] || currency + ' ';
        return symbol + formatted;
    }

    // Refresh exchange rates in background (non-blocking)
    function refreshRates() {
        if (_fetching) return;
        try {
            var cacheTime = localStorage.getItem(RATES_TIME_KEY);
            if (cacheTime && (Date.now() - parseInt(cacheTime)) < RATES_TTL) return;
        } catch (e) { }

        _fetching = true;
        fetch('https://api.exchangerate-api.com/v4/latest/USD')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && data.rates) {
                    var rates = {};
                    Object.keys(FALLBACK_RATES).forEach(function (k) {
                        rates[k] = data.rates[k] || FALLBACK_RATES[k];
                    });
                    _rates = rates;
                    localStorage.setItem(RATES_KEY, JSON.stringify(rates));
                    localStorage.setItem(RATES_TIME_KEY, Date.now().toString());
                }
            })
            .catch(function () { })
            .finally(function () { _fetching = false; });
    }

    // Re-format all elements with data-usd attribute when currency changes
    function refreshAllMoneyElements() {
        document.querySelectorAll('[data-usd]').forEach(function (el) {
            var amount = parseFloat(el.getAttribute('data-usd'));
            if (!isNaN(amount)) el.textContent = formatMoney(amount);
        });
    }

    // Listen for currency changes from currency-selector.js
    window.addEventListener('currencyChanged', function () {
        _rates = null; // force re-read from localStorage
        refreshAllMoneyElements();
    });

    // Expose globally
    window.formatMoney = formatMoney;
    window.refreshAllMoneyElements = refreshAllMoneyElements;

    // Kick off rate fetch
    refreshRates();
})();
