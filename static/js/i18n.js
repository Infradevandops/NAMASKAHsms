class I18n {
    constructor() {
        this.locale = localStorage.getItem('language') || 'en';
        this.translations = {};
        this.fallback = {};
        this.loaded = false;
        this.supportedLanguages = ['en', 'es', 'fr', 'de', 'pt', 'zh', 'ja', 'ar', 'hi'];
    }

    async loadTranslations() {
        if (this.loaded) return;

        if (!this.supportedLanguages.includes(this.locale)) {
            console.warn(`Unsupported language: ${this.locale}, falling back to English`);
            this.locale = 'en';
            localStorage.setItem('language', 'en');
        }

        console.log('[i18n] Loading translations for locale:', this.locale);

        // Always load English as fallback with retry logic
        if (!this.fallback || Object.keys(this.fallback).length === 0) {
            let retries = 3;
            while (retries > 0) {
                try {
                    console.log(`[i18n] Fetching fallback (en.json)... (attempt ${4 - retries}/3)`);
                    const res = await fetch('/static/locales/en.json', {
                        cache: 'no-cache',
                        headers: {
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                        }
                    });
                    
                    if (res.ok) {
                        this.fallback = await res.json();
                        console.log('[i18n] ✅ Fallback loaded:', Object.keys(this.fallback).length, 'top-level keys');
                        console.log('[i18n] Fallback keys:', Object.keys(this.fallback));
                        break; // Success, exit retry loop
                    } else {
                        console.error(`[i18n] Failed to fetch en.json: ${res.status}`);
                        retries--;
                        if (retries > 0) {
                            console.log(`[i18n] Retrying in 500ms...`);
                            await new Promise(resolve => setTimeout(resolve, 500));
                        }
                    }
                } catch (e) {
                    console.error('[i18n] Failed to load English fallback:', e);
                    retries--;
                    if (retries > 0) {
                        console.log(`[i18n] Retrying in 500ms...`);
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                }
            }
            
            if (Object.keys(this.fallback).length === 0) {
                console.error('[i18n] ❌ Failed to load translations after 3 attempts!');
                return;
            }
        }

        if (this.locale === 'en') {
            this.translations = this.fallback;
            this.loaded = true;
            console.log('[i18n] Using English, translations:', Object.keys(this.translations).length, 'keys');
            
            // Test a few translations
            const testKeys = ['dashboard.title', 'common.dashboard', 'tiers.current_plan'];
            testKeys.forEach(key => {
                const value = this.t(key);
                console.log(`[i18n] Test: ${key} = "${value}"`);
            });
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
        
        if (!value) {
            console.warn(`[i18n] Translation not found for key: ${key}`);
            console.log('[i18n] translations keys:', Object.keys(this.translations));
            console.log('[i18n] fallback keys:', Object.keys(this.fallback));
            return key;
        }
        
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
        if (!this.loaded) {
            console.warn('[i18n] translatePage() called but translations not loaded yet');
            return;
        }
        
        const elements = document.querySelectorAll('[data-i18n]');
        console.log(`[i18n] Translating ${elements.length} elements`);
        
        elements.forEach(el => {
            const key = el.getAttribute('data-i18n');
            const params = el.getAttribute('data-i18n-params')
                ? JSON.parse(el.getAttribute('data-i18n-params'))
                : {};

            // Handle placeholders for inputs
            if (el.tagName === 'INPUT' && el.getAttribute('placeholder')) {
                // If we want to translate placeholder, maybe use data-i18n-placeholder
            } else {
                const translated = this.t(key, params);
                console.log(`[i18n] ${key} → "${translated}"`);
                el.textContent = translated;
            }
        });
        
        console.log('[i18n] Translation complete');
    }

    /**
     * Set element content while preserving i18n attributes
     * Use this instead of direct textContent assignment
     */
    setContent(elementOrId, content, translationKey = null) {
        const el = typeof elementOrId === 'string' 
            ? document.getElementById(elementOrId) 
            : elementOrId;
        
        if (!el) return;

        if (translationKey) {
            // Set translation key and translate
            el.setAttribute('data-i18n', translationKey);
            el.textContent = this.t(translationKey);
        } else {
            // Direct content, remove translation key
            el.removeAttribute('data-i18n');
            el.textContent = content;
        }
    }

    /**
     * Set element HTML while preserving i18n for child elements
     */
    setHTML(elementOrId, html) {
        const el = typeof elementOrId === 'string' 
            ? document.getElementById(elementOrId) 
            : elementOrId;
        
        if (!el) return;

        el.innerHTML = html;
        // Re-translate any new elements with data-i18n
        if (this.loaded) {
            el.querySelectorAll('[data-i18n]').forEach(child => {
                const key = child.getAttribute('data-i18n');
                const params = child.getAttribute('data-i18n-params')
                    ? JSON.parse(child.getAttribute('data-i18n-params'))
                    : {};
                child.textContent = this.t(key, params);
            });
        }
    }

    /**
     * Update element content and re-translate if it has data-i18n
     */
    updateContent(elementOrId, content) {
        const el = typeof elementOrId === 'string' 
            ? document.getElementById(elementOrId) 
            : elementOrId;
        
        if (!el) return;

        const hasI18n = el.hasAttribute('data-i18n');
        
        if (hasI18n) {
            // Element has translation key, preserve it
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        } else {
            // No translation key, set content directly
            el.textContent = content;
        }
    }

    /**
     * Setup MutationObserver to auto-translate dynamically added content
     */
    observeDOM() {
        if (this.observer) return; // Already observing

        this.observer = new MutationObserver((mutations) => {
            if (!this.loaded) return;

            for (const mutation of mutations) {
                // Check added nodes
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        // Translate if it has data-i18n
                        if (node.hasAttribute && node.hasAttribute('data-i18n')) {
                            const key = node.getAttribute('data-i18n');
                            const params = node.getAttribute('data-i18n-params')
                                ? JSON.parse(node.getAttribute('data-i18n-params'))
                                : {};
                            node.textContent = this.t(key, params);
                        }
                        // Translate children with data-i18n
                        if (node.querySelectorAll) {
                            node.querySelectorAll('[data-i18n]').forEach(el => {
                                const key = el.getAttribute('data-i18n');
                                const params = el.getAttribute('data-i18n-params')
                                    ? JSON.parse(el.getAttribute('data-i18n-params'))
                                    : {};
                                el.textContent = this.t(key, params);
                            });
                        }
                    }
                });
            }
        });

        // Start observing
        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        console.log('✓ i18n DOM observer active');
    }
}

const i18n = new I18n();

async function initI18n() {
    console.log('[i18n] Initializing...');
    await i18n.loadTranslations();
    console.log('[i18n] Translations loaded, translating page...');
    i18n.translatePage();
    console.log('[i18n] Starting DOM observer...');
    i18n.observeDOM(); // Start observing for dynamic content
    console.log('[i18n] Initialization complete!');
}

// Initialize immediately if DOM is ready, otherwise wait
if (document.readyState === 'loading') {
    console.log('[i18n] DOM still loading, waiting for DOMContentLoaded...');
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[i18n] DOMContentLoaded fired');
        initI18n();
    });
} else {
    console.log('[i18n] DOM already loaded, initializing immediately');
    initI18n();
}

// Create promise for other scripts to wait on
window.i18nReady = new Promise((resolve) => {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => initI18n().then(resolve));
    } else {
        initI18n().then(resolve);
    }
});

// Expose i18n globally for use in other scripts
window.i18n = i18n;
