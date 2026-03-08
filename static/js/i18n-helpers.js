/**
 * i18n Helper Utilities
 * 
 * Provides helper functions for i18n-aware DOM manipulation
 * Use these instead of direct textContent/innerHTML assignments
 * to prevent translation key regression issues.
 * 
 * Usage:
 *   import { setI18nContent, updateI18nHTML } from '/static/js/i18n-helpers.js';
 *   setI18nContent('my-element-id', 'Hello World');
 *   updateI18nHTML('container', '<div>Dynamic content</div>');
 */

/**
 * Wait for i18n to be ready
 * @returns {Promise<void>}
 */
export async function waitForI18n() {
    if (window.i18nReady) {
        await window.i18nReady;
    }
    return Promise.resolve();
}

/**
 * Set element content while preserving i18n system
 * Removes data-i18n attribute to indicate this is dynamic content
 * 
 * @param {string|HTMLElement} elementOrId - Element or element ID
 * @param {string} content - Content to set
 */
export function setI18nContent(elementOrId, content) {
    const el = typeof elementOrId === 'string' 
        ? document.getElementById(elementOrId) 
        : elementOrId;
    
    if (!el) {
        console.warn(`[i18n-helpers] Element not found:`, elementOrId);
        return;
    }

    // Remove translation key to indicate dynamic content
    el.removeAttribute('data-i18n');
    el.textContent = content;
}

/**
 * Set element HTML while preserving i18n for child elements
 * 
 * @param {string|HTMLElement} elementOrId - Element or element ID
 * @param {string} html - HTML content to set
 */
export function updateI18nHTML(elementOrId, html) {
    const el = typeof elementOrId === 'string' 
        ? document.getElementById(elementOrId) 
        : elementOrId;
    
    if (!el) {
        console.warn(`[i18n-helpers] Element not found:`, elementOrId);
        return;
    }

    el.innerHTML = html;
    
    // Re-translate any new elements with data-i18n
    if (window.i18n && window.i18n.loaded) {
        el.querySelectorAll('[data-i18n]').forEach(child => {
            const key = child.getAttribute('data-i18n');
            const params = child.getAttribute('data-i18n-params')
                ? JSON.parse(child.getAttribute('data-i18n-params'))
                : {};
            child.textContent = window.i18n.t(key, params);
        });
    }
}

/**
 * Update multiple elements at once
 * 
 * @param {Object} updates - Map of element IDs to content
 * @example
 *   updateMultiple({
 *     'tier-name': 'Pro',
 *     'tier-price': '$25/month',
 *     'tier-features': 'All features included'
 *   });
 */
export function updateMultiple(updates) {
    for (const [elementId, content] of Object.entries(updates)) {
        setI18nContent(elementId, content);
    }
}

/**
 * Safely update element with translation key
 * If element has data-i18n, it will be translated
 * Otherwise, content is set directly
 * 
 * @param {string|HTMLElement} elementOrId - Element or element ID
 * @param {string} translationKey - Translation key (e.g., 'dashboard.title')
 */
export function setTranslatedContent(elementOrId, translationKey) {
    const el = typeof elementOrId === 'string' 
        ? document.getElementById(elementOrId) 
        : elementOrId;
    
    if (!el) {
        console.warn(`[i18n-helpers] Element not found:`, elementOrId);
        return;
    }

    if (window.i18n && window.i18n.loaded) {
        el.setAttribute('data-i18n', translationKey);
        el.textContent = window.i18n.t(translationKey);
    } else {
        // i18n not ready, set key as placeholder
        el.setAttribute('data-i18n', translationKey);
        el.textContent = translationKey;
    }
}

/**
 * Create element with i18n support
 * 
 * @param {string} tag - HTML tag name
 * @param {Object} options - Element options
 * @param {string} options.translationKey - Translation key
 * @param {string} options.content - Direct content (if no translation key)
 * @param {string} options.className - CSS class
 * @param {Object} options.attributes - Additional attributes
 * @returns {HTMLElement}
 */
export function createI18nElement(tag, options = {}) {
    const el = document.createElement(tag);
    
    if (options.className) {
        el.className = options.className;
    }
    
    if (options.attributes) {
        for (const [key, value] of Object.entries(options.attributes)) {
            el.setAttribute(key, value);
        }
    }
    
    if (options.translationKey) {
        setTranslatedContent(el, options.translationKey);
    } else if (options.content) {
        el.textContent = options.content;
    }
    
    return el;
}

/**
 * Batch update with i18n awareness
 * Useful for updating multiple elements after API calls
 * 
 * @param {Array<Object>} updates - Array of update objects
 * @example
 *   batchUpdate([
 *     { id: 'tier-name', content: 'Pro', removeI18n: true },
 *     { id: 'tier-price', content: '$25/month', removeI18n: true },
 *     { id: 'welcome-msg', translationKey: 'dashboard.welcome' }
 *   ]);
 */
export function batchUpdate(updates) {
    for (const update of updates) {
        const el = document.getElementById(update.id);
        if (!el) continue;
        
        if (update.removeI18n) {
            el.removeAttribute('data-i18n');
        }
        
        if (update.translationKey) {
            setTranslatedContent(el, update.translationKey);
        } else if (update.content !== undefined) {
            el.textContent = update.content;
        }
        
        if (update.html !== undefined) {
            updateI18nHTML(el, update.html);
        }
    }
}

/**
 * Debug helper: Log all elements with data-i18n
 */
export function debugI18nElements() {
    const elements = document.querySelectorAll('[data-i18n]');
    console.group('🌐 i18n Elements');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        const content = el.textContent.trim();
        console.log(`${key} → "${content}"`);
    });
    console.groupEnd();
}

// Export for non-module usage
if (typeof window !== 'undefined') {
    window.i18nHelpers = {
        waitForI18n,
        setI18nContent,
        updateI18nHTML,
        updateMultiple,
        setTranslatedContent,
        createI18nElement,
        batchUpdate,
        debugI18nElements
    };
}
