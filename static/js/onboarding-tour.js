/**
 * Onboarding Tour - Driver.js Implementation
 * Version: 4.8.2
 * Status: Production Ready
 *
 * Auto-starts on first dashboard visit for new users
 * Guides users through currency, language, and key features
 * Dismissible at any point, marks completion in backend
 */

(function() {
    'use strict';

    class OnboardingTour {
        constructor() {
            this.driver = null;
            this.isRunning = false;
            this.completionEndpoint = '/api/auth/onboarding-complete';
            this.statusEndpoint = '/api/auth/onboarding-status';
        }

        /**
         * Initialize tour - checks backend completion status
         */
        async init() {
            console.log('[OnboardingTour] Initializing...');

            // Only run on dashboard page
            if (!this.isDashboardPage()) {
                console.log('[OnboardingTour] Not on dashboard, skipping');
                return;
            }

            // Check if user is authenticated
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('[OnboardingTour] No auth token, skipping');
                return;
            }

            // Check completion status from backend
            const shouldRun = await this.shouldRunTour();
            if (!shouldRun) {
                console.log('[OnboardingTour] Already completed, skipping');
                return;
            }

            // Wait for page to fully load, then start
            console.log('[OnboardingTour] Scheduling tour start...');
            if (document.readyState === 'complete') {
                console.log('[OnboardingTour] Page already loaded, starting in 1.5s');
                setTimeout(() => this.start(), 1500); // 1.5s delay for smooth UX
            } else {
                console.log('[OnboardingTour] Waiting for page load...');
                window.addEventListener('load', () => {
                    console.log('[OnboardingTour] Page loaded, starting in 1.5s');
                    setTimeout(() => this.start(), 1500);
                });
            }
        }

        /**
         * Check if we're on the dashboard page
         */
        isDashboardPage() {
            const path = window.location.pathname;
            const isDash = path === '/dashboard' || path === '/'
            console.log('[OnboardingTour] Path check:', path, '→', isDash);
            return isDash;
        }

        /**
         * Check backend if tour should run
         */
        async shouldRunTour() {
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('[OnboardingTour] No token found');
                return false;
            }

            // ONE-TIME RESET: Clear old flags for v4.8.2 rollout (MUST happen FIRST)
            const tourVersion = localStorage.getItem('tour_version');
            if (tourVersion !== '4.8.2') {
                console.log('[OnboardingTour] Resetting for v4.8.2 rollout');
                localStorage.removeItem('onboarding_tour_completed');
                localStorage.setItem('tour_version', '4.8.2');
            }

            // Check localStorage cache (AFTER version reset)
            const cachedCompletion = localStorage.getItem('onboarding_tour_completed');
            console.log('[OnboardingTour] Cache check:', cachedCompletion);
            if (cachedCompletion === 'true') {
                console.log('[OnboardingTour] Tour already completed (cached)');
                return false;
            }

            try {
                const response = await fetch(this.statusEndpoint, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    console.warn('[OnboardingTour] Status check failed, assuming not completed');
                    return true; // Default to showing tour on error
                }

                const data = await response.json();
                const completed = data.completed || false;
                console.log('[OnboardingTour] Backend status:', data);

                // Cache result
                if (completed) {
                    localStorage.setItem('onboarding_tour_completed', 'true');
                    console.log('[OnboardingTour] Tour already completed (backend)');
                }

                return !completed;
            } catch (error) {
                console.error('[OnboardingTour] Error checking status:', error);
                // On network error, check if we've run tour in this session
                return !sessionStorage.getItem('tour_attempted_this_session');
            }
        }

        /**
         * Start the tour
         */
        start() {
            if (this.isRunning) {
                console.log('[OnboardingTour] Already running');
                return;
            }

            console.log('[OnboardingTour] Starting tour...');

            // Mark as attempted this session (prevent loops on error)
            sessionStorage.setItem('tour_attempted_this_session', 'true');

            // Verify driver.js is loaded
            if (typeof window.driver === 'undefined') {
                console.error('[OnboardingTour] driver.js not loaded!');
                return;
            }

            // Build tour steps dynamically (skip missing elements)
            const steps = this.buildTourSteps();
            if (steps.length === 0) {
                console.error('[OnboardingTour] No valid tour steps found');
                return;
            }

            try {
                this.driver = window.driver({
                    showProgress: true,
                    showButtons: ['next', 'previous', 'close'],
                    nextBtnText: 'Next →',
                    prevBtnText: '← Back',
                    doneBtnText: 'Done ✓',
                    closeBtnText: 'Skip',
                    progressText: 'Step {{current}} of {{total}}',

                    // Styling
                    popoverClass: 'onboarding-tour-popover',
                    animate: true,
                    overlayOpacity: 0.75,

                    // Callbacks
                    onDestroyStarted: () => {
                        console.log('[OnboardingTour] Tour ended by user');
                        this.handleTourEnd();
                    },

                    onDestroyed: () => {
                        this.isRunning = false;
                        console.log('[OnboardingTour] Tour destroyed');
                    },

                    steps: steps
                });

                this.driver.drive();
                this.isRunning = true;

                console.log('[OnboardingTour] Tour started successfully');
            } catch (error) {
                console.error('[OnboardingTour] Error starting tour:', error);
                this.isRunning = false;
            }
        }

        /**
         * Build tour steps - only include elements that exist
         */
        buildTourSteps() {
            const allSteps = [
                // Step 1: Welcome
                {
                    popover: {
                        title: '👋 Welcome to VRENUM SMS',
                        description: 'Let\'s take a quick tour to help you get started. This will only take 30 seconds!',
                        side: 'over', // Full screen popover
                        align: 'center'
                    }
                },

                // Step 2: Currency Selector
                {
                    element: '#currency-selector-btn',
                    popover: {
                        title: '🌍 Choose Your Currency',
                        description: 'Click here to select your preferred currency. All prices throughout the platform will be automatically converted.',
                        side: 'bottom',
                        align: 'start'
                    }
                },

                // Step 3: Tier Badge
                {
                    element: '#header-tier-badge',
                    popover: {
                        title: '⚡ Your Current Plan',
                        description: 'You\'re currently on the Freemium plan. Click here anytime to see upgrade options for API access, webhooks, and lower SMS rates.',
                        side: 'left',
                        align: 'start'
                    }
                },

                // Step 4: Verify Button (sidebar link)
                {
                    element: 'a[href="/verify"]',
                    popover: {
                        title: '📱 Start Verifying',
                        description: 'Click here to get a temporary phone number and receive SMS verification codes instantly.',
                        side: 'right',
                        align: 'start'
                    }
                },

                // Step 5: History
                {
                    element: 'a[href="/history"]',
                    popover: {
                        title: '📋 View Your History',
                        description: 'All your past verifications, received codes, and spending are logged here for easy reference.',
                        side: 'right',
                        align: 'start'
                    }
                },

                // Step 6: Wallet
                {
                    element: 'a[href="/wallet"]',
                    popover: {
                        title: '💰 Manage Your Wallet',
                        description: 'Add credits here to pay for verifications. We support multiple payment methods based on your location.',
                        side: 'right',
                        align: 'start'
                    }
                },

                // Step 7: Completion
                {
                    popover: {
                        title: '🎉 You\'re All Set!',
                        description: 'You can restart this tour anytime from your Settings page. Happy verifying!',
                        side: 'over',
                        align: 'center'
                    }
                }
            ];

            // Filter out steps where element doesn't exist
            const validSteps = allSteps.filter(step => {
                if (!step.element) return true; // No element = full screen popover

                const element = document.querySelector(step.element);
                if (!element) {
                    console.warn(`[OnboardingTour] Element not found: ${step.element}`);
                    return false;
                }

                return true;
            });

            console.log(`[OnboardingTour] Built ${validSteps.length}/${allSteps.length} steps`);
            return validSteps;
        }

        /**
         * Handle tour end - mark as completed in backend
         */
        async handleTourEnd() {
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('[OnboardingTour] No token, skipping backend update');
                return;
            }

            try {
                const response = await fetch(this.completionEndpoint, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    console.log('[OnboardingTour] Marked as completed in backend');
                    localStorage.setItem('onboarding_tour_completed', 'true');
                } else {
                    console.warn('[OnboardingTour] Failed to mark completed:', response.status);
                }
            } catch (error) {
                console.error('[OnboardingTour] Error marking completed:', error);
            }
        }

        /**
         * Manual restart (for settings page button)
         */
        restart() {
            console.log('[OnboardingTour] Manual restart requested');

            // Clear completion flags
            localStorage.removeItem('onboarding_tour_completed');
            sessionStorage.removeItem('tour_attempted_this_session');

            // Start tour
            this.start();
        }

        /**
         * Destroy tour instance
         */
        destroy() {
            if (this.driver) {
                this.driver.destroy();
                this.driver = null;
            }
            this.isRunning = false;
        }
    }

    // Initialize tour when DOM is ready
    function initTour() {
        console.log('[OnboardingTour] initTour() called, readyState:', document.readyState);
        window.onboardingTour = new OnboardingTour();
        window.onboardingTour.init();
    }

    console.log('[OnboardingTour] Module loaded, readyState:', document.readyState);

    if (document.readyState === 'loading') {
        console.log('[OnboardingTour] Waiting for DOMContentLoaded...');
        document.addEventListener('DOMContentLoaded', initTour);
    } else {
        console.log('[OnboardingTour] DOM already ready, calling initTour()...');
        initTour();
    }
})();
