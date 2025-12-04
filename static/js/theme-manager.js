/**
 * Theme Manager - Handles light/dark mode switching
 * Supports system preference, localStorage persistence, and manual toggle
 */

class ThemeManager {
  constructor() {
    this.STORAGE_KEY = 'namaskah-theme-preference';
    this.DARK_MODE_CLASS = 'dark-mode';
    this.LIGHT_MODE_CLASS = 'light-mode';
    this.SYSTEM_MODE = 'system';
    this.DARK_MODE = 'dark';
    this.LIGHT_MODE = 'light';
    
    this.init();
  }

  /**
   * Initialize theme manager
   */
  init() {
    this.applyTheme(this.getThemePreference());
    this.setupSystemPreferenceListener();
    this.setupToggleButtons();
  }

  /**
   * Get user's theme preference from storage or system
   */
  getThemePreference() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    
    if (stored) {
      return stored;
    }

    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return this.DARK_MODE;
    }

    return this.LIGHT_MODE;
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme) {
    const html = document.documentElement;
    
    // Remove existing theme classes
    html.classList.remove(this.DARK_MODE_CLASS, this.LIGHT_MODE_CLASS);
    
    // Apply new theme
    if (theme === this.DARK_MODE) {
      html.classList.add(this.DARK_MODE_CLASS);
      localStorage.setItem(this.STORAGE_KEY, this.DARK_MODE);
    } else {
      html.classList.add(this.LIGHT_MODE_CLASS);
      localStorage.setItem(this.STORAGE_KEY, this.LIGHT_MODE);
    }

    // Dispatch custom event for other components to listen
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  /**
   * Toggle between light and dark mode
   */
  toggle() {
    const current = this.getCurrentTheme();
    const newTheme = current === this.DARK_MODE ? this.LIGHT_MODE : this.DARK_MODE;
    this.applyTheme(newTheme);
  }

  /**
   * Get current applied theme
   */
  getCurrentTheme() {
    const html = document.documentElement;
    return html.classList.contains(this.DARK_MODE_CLASS) ? this.DARK_MODE : this.LIGHT_MODE;
  }

  /**
   * Set theme explicitly
   */
  setTheme(theme) {
    if ([this.DARK_MODE, this.LIGHT_MODE].includes(theme)) {
      this.applyTheme(theme);
    }
  }

  /**
   * Setup listener for system preference changes
   */
  setupSystemPreferenceListener() {
    if (!window.matchMedia) return;

    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Modern browsers
    if (darkModeQuery.addEventListener) {
      darkModeQuery.addEventListener('change', (e) => {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        // Only apply if user hasn't set explicit preference
        if (!stored) {
          this.applyTheme(e.matches ? this.DARK_MODE : this.LIGHT_MODE);
        }
      });
    }
  }

  /**
   * Setup theme toggle buttons
   */
  setupToggleButtons() {
    // Find all theme toggle buttons
    const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
    
    toggleButtons.forEach(button => {
      button.addEventListener('click', () => this.toggle());
      this.updateToggleButtonState(button);
    });

    // Listen for theme changes to update button states
    window.addEventListener('themechange', () => {
      toggleButtons.forEach(button => this.updateToggleButtonState(button));
    });
  }

  /**
   * Update toggle button appearance based on current theme
   */
  updateToggleButtonState(button) {
    const currentTheme = this.getCurrentTheme();
    const isDark = currentTheme === this.DARK_MODE;
    
    // Update aria-label
    button.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    
    // Update data attribute for styling
    button.setAttribute('data-theme-current', currentTheme);
    
    // Update icon if present
    const icon = button.querySelector('svg');
    if (icon) {
      // You can add icon switching logic here
      icon.setAttribute('data-theme-icon', isDark ? 'moon' : 'sun');
    }
  }

  /**
   * Get theme preference for API/backend
   */
  getThemeForAPI() {
    return this.getCurrentTheme();
  }
}

// Initialize theme manager when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
  });
} else {
  window.themeManager = new ThemeManager();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeManager;
}
