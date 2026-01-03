/**
 * Language & Currency Selector Component
 * Provides UI controls for switching language and currency
 */

class LocalizationSelector {
    constructor() {
        this.languages = {
            en: { name: 'English', flag: '🇺🇸' },
            es: { name: 'Español', flag: '🇪🇸' },
            fr: { name: 'Français', flag: '🇫🇷' },
            de: { name: 'Deutsch', flag: '🇩🇪' },
            pt: { name: 'Português', flag: '🇵🇹' },
            zh: { name: '中文', flag: '🇨🇳' },
            ja: { name: '日本語', flag: '🇯🇵' },
            ar: { name: 'العربية', flag: '🇸🇦' },
            hi: { name: 'हिन्दी', flag: '🇮🇳' },
            yo: { name: 'Yorùbá', flag: '🇳🇬' }
        };

        this.currencies = {
            USD: { name: 'US Dollar', symbol: '$', region: '🇺🇸' },
            EUR: { name: 'Euro', symbol: '€', region: '🇪🇺' },
            GBP: { name: 'British Pound', symbol: '£', region: '🇬🇧' },
            NGN: { name: 'Nigerian Naira', symbol: '₦', region: '🇳🇬' },
            INR: { name: 'Indian Rupee', symbol: '₹', region: '🇮🇳' },
            CNY: { name: 'Chinese Yuan', symbol: '¥', region: '🇨🇳' },
            JPY: { name: 'Japanese Yen', symbol: '¥', region: '🇯🇵' },
            BRL: { name: 'Brazilian Real', symbol: 'R$', region: '🇧🇷' },
            CAD: { name: 'Canadian Dollar', symbol: 'C$', region: '🇨🇦' },
            AUD: { name: 'Australian Dollar', symbol: 'A$', region: '🇦🇺' }
        };

        this.init();
    }

    init() {
        this.createSelectors();
        this.attachEventListeners();
    }

    createSelectors() {
        const header = document.querySelector('header') || document.querySelector('nav');
        if (!header) return;

        const container = document.createElement('div');
        container.className = 'localization-controls';
        container.innerHTML = `
            <div class="selector-group">
                <label for="lang-selector" class="selector-label">
                    <span class="selector-icon">🌐</span>
                </label>
                <select id="lang-selector" class="selector-input language-selector">
                    ${Object.entries(this.languages).map(([code, data]) => `
                        <option value="${code}" ${code === (i18n?.locale || 'en') ? 'selected' : ''}>
                            ${data.flag} ${data.name}
                        </option>
                    `).join('')}
                </select>
            </div>

            <div class="selector-group">
                <label for="currency-selector" class="selector-label">
                    <span class="selector-icon">💱</span>
                </label>
                <select id="currency-selector" class="selector-input currency-selector">
                    ${Object.entries(this.currencies).map(([code, data]) => `
                        <option value="${code}" ${code === (currency?.currency || 'USD') ? 'selected' : ''}>
                            ${data.region} ${code} (${data.symbol})
                        </option>
                    `).join('')}
                </select>
            </div>
        `;

        header.appendChild(container);
    }

    attachEventListeners() {
        const langSelector = document.getElementById('lang-selector');
        const currencySelector = document.getElementById('currency-selector');

        if (langSelector) {
            langSelector.addEventListener('change', async (e) => {
                const lang = e.target.value;
                if (i18n) {
                    await i18n.changeLanguage(lang);
                    document.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
                    this.showNotification(`Language changed to ${this.languages[lang].name}`);
                }
            });
        }

        if (currencySelector) {
            currencySelector.addEventListener('change', async (e) => {
                const curr = e.target.value;
                if (currency) {
                    await currency.changeCurrency(curr);
                    document.dispatchEvent(new CustomEvent('currencyChanged', { detail: { currency: curr } }));
                    this.showNotification(`Currency changed to ${this.currencies[curr].name}`);
                }
            });
        }
    }

    showNotification(message) {
        if (typeof showToast === 'function') {
            showToast(message, 'success');
        } else {
            console.log(message);
        }
    }

    getLanguageName(code) {
        return this.languages[code]?.name || code;
    }

    getCurrencyName(code) {
        return this.currencies[code]?.name || code;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new LocalizationSelector();
});
