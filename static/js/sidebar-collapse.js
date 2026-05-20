/**
 * Collapsible Sidebar - Auto-collapse on desktop, toggle on mobile
 * Saves state to localStorage
 */

(function() {
    const sidebar = document.getElementById('app-sidebar');
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    if (!sidebar) return;

    // Check saved state or default to collapsed on desktop
    const savedState = localStorage.getItem('sidebar-collapsed');
    const isDesktop = window.innerWidth >= 1024;
    const shouldCollapse = savedState === 'true' || (savedState === null && isDesktop);

    // Apply initial state
    if (shouldCollapse) {
        sidebar.classList.add('collapsed');
        if (mainContent) mainContent.classList.add('sidebar-collapsed');
    }

    // Toggle function
    window.toggleSidebarCollapse = function() {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        if (mainContent) mainContent.classList.toggle('sidebar-collapsed');
        
        // Save state
        localStorage.setItem('sidebar-collapsed', isCollapsed);
        
        // Update aria-expanded
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-expanded', !isCollapsed);
        }
    };

    // Add toggle button if it doesn't exist
    if (!toggleBtn && isDesktop) {
        const btn = document.createElement('button');
        btn.className = 'sidebar-collapse-btn';
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"></polyline></svg>';
        btn.setAttribute('aria-label', 'Toggle sidebar');
        btn.setAttribute('aria-expanded', !shouldCollapse);
        btn.onclick = window.toggleSidebarCollapse;
        
        const sidebarHeader = sidebar.querySelector('.sidebar-header');
        if (sidebarHeader) {
            sidebarHeader.appendChild(btn);
        }
    }

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            const isNowDesktop = window.innerWidth >= 1024;
            if (isNowDesktop && !sidebar.classList.contains('collapsed')) {
                // Auto-collapse on desktop if not explicitly expanded
                const userExpanded = localStorage.getItem('sidebar-collapsed') === 'false';
                if (!userExpanded) {
                    sidebar.classList.add('collapsed');
                    if (mainContent) mainContent.classList.add('sidebar-collapsed');
                }
            }
        }, 250);
    });
})();
