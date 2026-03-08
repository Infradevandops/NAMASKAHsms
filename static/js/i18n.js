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

        // STRATEGY 1: Try embedded translations first (fastest, most reliable)
        if (window.EMBEDDED_TRANSLATIONS) {
            console.log('[i18n] ✅ Using embedded translations');
            this.translations = window.EMBEDDED_TRANSLATIONS;
            this.fallback = window.EMBEDDED_TRANSLATIONS;
            this.loaded = true;
            
            // Cache in localStorage for future visits
            try {
                localStorage.setItem(`translations_${this.locale}`, JSON.stringify(this.translations));
                localStorage.setItem('translations_cached_at', Date.now().toString());
                console.log('[i18n] Cached translations in localStorage');
            } catch (e) {
                console.warn('[i18n] Failed to cache translations:', e);
            }
            
            this._logSuccess();
            return;
        }

        // STRATEGY 2: Try localStorage cache (instant load)
        const cached = localStorage.getItem(`translations_${this.locale}`);
        const cachedAt = localStorage.getItem('translations_cached_at');
        const cacheAge = cachedAt ? Date.now() - parseInt(cachedAt) : Infinity;
        const cacheMaxAge = 24 * 60 * 60 * 1000; // 24 hours

        if (cached && cacheAge < cacheMaxAge) {
            try {
                this.translations = JSON.parse(cached);
                this.fallback = this.translations;
                this.loaded = true;
                console.log('[i18n] ✅ Using cached translations from localStorage');
                this._logSuccess();
                
                // Fetch fresh copy in background for next visit
                this._fetchAndCacheInBackground();
                return;
            } catch (e) {
                console.warn('[i18n] Failed to parse cached translations:', e);
                localStorage.removeItem(`translations_${this.locale}`);
            }
        }

        // STRATEGY 3: Fetch from server with retry logic (fallback)
        await this._fetchTranslations();
    }

    async _fetchTranslations() {
        console.log('[i18n] Fetching translations from server...');
        
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
                    this.translations = this.fallback;
                    this.loaded = true;
                    console.log('[i18n] ✅ Fetched translations from server');
                    
                    // Cache for future visits
                    try {
                        localStorage.setItem(`translations_${this.locale}`, JSON.stringify(this.translations));
                        localStorage.setItem('translations_cached_at', Date.now().toString());
                        console.log('[i18n] Cached translations in localStorage');
                    } catch (e) {
                        console.warn('[i18n] Failed to cache translations:', e);
                    }
                    
                    this._logSuccess();
                    return;
                } else {
                    console.error(`[i18n] Failed to fetch en.json: ${res.status}`);
                    retries--;
                    if (retries > 0) {
                        console.log(`[i18n] Retrying in 500ms...`);
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                }
            } catch (e) {
                console.error('[i18n] Failed to load translations:', e);
                retries--;
                if (retries > 0) {
                    console.log(`[i18n] Retrying in 500ms...`);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }
        }
        
        console.error('[i18n] ❌ Failed to load translations after 3 attempts!');
    }

    async _fetchAndCacheInBackground() {
        // Silently fetch fresh translations for next visit
        try {
            const res = await fetch('/static/locales/en.json', { cache: 'no-cache' });
            if (res.ok) {
                const fresh = await res.json();
                localStorage.setItem(`translations_${this.locale}`, JSON.stringify(fresh));
                localStorage.setItem('translations_cached_at', Date.now().toString());
                console.log('[i18n] Updated cache in background');
            }
        } catch (e) {
            // Silently fail
        }
    }

    _logSuccess() {
        console.log('[i18n] Translations loaded:', Object.keys(this.translations).length, 'top-level keys');
        
        // Test a few translations
        const testKeys = ['dashboard.title', 'common.dashboard', 'tiers.current_plan'];
        testKeys.forEach(key => {
            const value = this.t(key);
            console.log(`[i18n] Test: ${key} = "${value}"`);
        });
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
