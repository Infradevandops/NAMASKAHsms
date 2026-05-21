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

    // Unified Toggle function
    window.toggleSidebar = function() {
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            // On mobile, toggle the 'open' and 'active' classes to slide the drawer in/out from left
            const isOpen = sidebar.classList.toggle('open');
            sidebar.classList.toggle('active', isOpen);
            if (toggleBtn) {
                toggleBtn.setAttribute('aria-expanded', isOpen);
            }
        } else {
            // On desktop, toggle the 'collapsed' state
            const isCollapsed = sidebar.classList.toggle('collapsed');
            if (mainContent) mainContent.classList.toggle('sidebar-collapsed');

            // Save state
            localStorage.setItem('sidebar-collapsed', isCollapsed);

            // Update aria-expanded
            if (toggleBtn) {
                toggleBtn.setAttribute('aria-expanded', !isCollapsed);
            }
        }
    };

    // Alias for compatibility
    window.toggleSidebarCollapse = window.toggleSidebar;

    // Add toggle button if it doesn't exist
    if (!toggleBtn && isDesktop) {
        const btn = document.createElement('button');
        btn.className = 'sidebar-collapse-btn';
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"></polyline></svg>';
        btn.setAttribute('aria-label', 'Toggle sidebar');
        btn.setAttribute('aria-expanded', !shouldCollapse);
        btn.onclick = window.toggleSidebar;

        const sidebarHeader = sidebar.querySelector('.sidebar-header');
        if (sidebarHeader) {
            sidebarHeader.appendChild(btn);
        }
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(event) {
        const isMobile = window.innerWidth <= 768;
        if (!isMobile) return;

        const mobileToggleBtn = document.querySelector('.mobile-sidebar-toggle-btn');
        const sidebarToggleBtn = document.querySelector('.sidebar-toggle');

        if ((sidebar.classList.contains('open') || sidebar.classList.contains('active')) &&
            !sidebar.contains(event.target) &&
            (!mobileToggleBtn || !mobileToggleBtn.contains(event.target)) &&
            (!sidebarToggleBtn || !sidebarToggleBtn.contains(event.target))) {
            sidebar.classList.remove('open');
            sidebar.classList.remove('active');
        }
    });

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            const isNowDesktop = window.innerWidth >= 1024;
            if (isNowDesktop) {
                // Ensure mobile open state is cleaned up
                sidebar.classList.remove('open');
                sidebar.classList.remove('active');

                // Auto-collapse on desktop if not explicitly expanded
                if (!sidebar.classList.contains('collapsed')) {
                    const userExpanded = localStorage.getItem('sidebar-collapsed') === 'false';
                    if (!userExpanded) {
                        sidebar.classList.add('collapsed');
                        if (mainContent) mainContent.classList.add('sidebar-collapsed');
                    }
                }
            }
        }, 250);
    });
})();
