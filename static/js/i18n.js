class I18n {
    constructor() {
        this.locale = localStorage.getItem('language') || 'en';
        this.translations = {};
        this.fallback = {};
        this.loaded = false;
        this.supportedLanguages = ['en', 'es', 'fr', 'de', 'pt', 'zh', 'ja', 'ar', 'hi'];
    }

    async loadTranslations() {
        if (this.loaded && this.translations[this.locale]) return;

        if (!this.supportedLanguages.includes(this.locale)) {
            console.warn(`Unsupported language: ${this.locale}, falling back to English`);
            this.locale = 'en';
            localStorage.setItem('language', 'en');
        }

        // Always load English as fallback
        if (!this.fallback || Object.keys(this.fallback).length === 0) {
            try {
                const res = await fetch('/static/locales/en.json');
                if (res.ok) this.fallback = await res.json();
            } catch (e) {
                console.error('Failed to load English fallback:', e);
            }
        }

        if (this.locale === 'en') {
            this.translations = this.fallback;
            this.loaded = true;
            return;
        }

        try {
            const response = await fetch(`/static/locales/${this.locale}.json`);
            if (!response.ok) throw new Error(`Failed to load ${this.locale}`);
            this.translations = await response.json();
            this.loaded = true;
            console.log(`✓ Loaded ${this.locale} translations`);
        } catch (error) {
            console.error('Translation load error:', error);
            if (this.locale !== 'en') {
                console.warn(`⚠ Falling back to English from ${this.locale}`);
                this.locale = 'en';
                localStorage.setItem('language', 'en');
                const selector = document.getElementById('lang-switcher');
                if (selector) selector.value = 'en';
                this.translations = this.fallback;
                this.loaded = true;
                if (typeof showToast === 'function') {
                    showToast('Language not available. Using English.', 'warning');
                }
            }
        }
    }

    t(key, params = {}) {
        const value = this.getNestedValue(this.translations, key)
            || this.getNestedValue(this.fallback, key);
        if (!value) return key;
        return this.interpolate(value, params);
    }

    getNestedValue(obj, key) {
        return key.split('.').reduce((o, i) => (o ? o[i] : null), obj);
    }

    interpolate(text, params) {
        return text.replace(/\{(\w+)\}/g, (match, key) => {
            return typeof params[key] !== 'undefined' ? params[key] : match;
        });
    }

    async changeLanguage(lang) {
        if (!this.supportedLanguages.includes(lang)) {
            console.error(`Unsupported language: ${lang}`);
            return;
        }
        this.locale = lang;
        localStorage.setItem('language', lang);
        this.loaded = false;
        await this.loadTranslations();
        this.translatePage();
        document.documentElement.lang = lang;
        if (lang === 'ar') {
            document.documentElement.dir = 'rtl';
        } else {
            document.documentElement.dir = 'ltr';
        }
        try {
            await fetch('/api/user/preferences', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ language: lang })
            });
        } catch (error) {
            console.error('Failed to save language preference:', error);
        }
    }

    translatePage() {
        if (!this.fallback || Object.keys(this.fallback).length === 0) return;
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const params = el.getAttribute('data-i18n-params')
                ? JSON.parse(el.getAttribute('data-i18n-params'))
                : {};

            // Handle placeholders for inputs
            if (el.tagName === 'INPUT' && el.getAttribute('placeholder')) {
                // If we want to translate placeholder, maybe use data-i18n-placeholder
            } else {
                el.textContent = this.t(key, params);
            }
        });
    }
}

const i18n = new I18n();

async function initI18n() {
    await i18n.loadTranslations();
    i18n.translatePage();
}

window.i18nReady = (document.readyState === 'loading')
    ? new Promise(r => document.addEventListener('DOMContentLoaded', () => initI18n().then(r)))
    : initI18n();
