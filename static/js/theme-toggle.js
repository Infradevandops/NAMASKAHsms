/**
 * Theme Toggle - Dark/Light Mode
 * Simple, working implementation
 */

(function() {
    const STORAGE_KEY = 'theme';

    // Get current theme
    function getTheme() {
        return localStorage.getItem(STORAGE_KEY) ||
               (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    }

    // Set theme
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);

        // Update all icons matching theme-icon ID, class, or mobile variant
        const icons = document.querySelectorAll('#theme-icon, .theme-icon-mobile, [id^="theme-icon"]');
        icons.forEach(icon => {
            icon.textContent = theme === 'dark' ? '☀️' : '🌙';
        });
    }

    // Toggle theme
    window.toggleTheme = function() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        setTheme(current === 'dark' ? 'light' : 'dark');
    };

    // Initialize
    setTheme(getTheme());

    // Listen for system changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
})();
