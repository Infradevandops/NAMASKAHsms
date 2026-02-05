/**
 * Tier Card Widget Tests
 * 
 * Tests for the dashboard tier card component including:
 * - State management (loading, error, loaded, etc.)
 * - Authentication handling
 * - Timeout behavior
 * - CTA button visibility by tier
 * - Retry functionality
 */

describe('Tier Card Widget', () => {
    
    beforeEach(() => {
        cy.visit('/dashboard');
    });

    describe('Authentication States', () => {
        
        it('shows login prompt when no auth token exists', () => {
            cy.clearLocalStorage();
            cy.reload();
            
            cy.get('#tier-name').should('contain', 'Not logged in');
            cy.get('#tier-features-list a[href="/auth/login"]').should('exist');
            cy.get('#tier-features-list a').should('contain', 'Log in');
        });

        it('shows session expired when 401 returned', () => {
            cy.window().then(win => {
                win.localStorage.setItem('access_token', 'invalid-expired-token');
            });
            cy.reload();
            
            cy.get('#tier-name', { timeout: 12000 }).should('contain', 'Session expired');
            cy.get('#tier-features-list a[href="/auth/login"]').should('exist');
        });

        it('loads tier info when authenticated', () => {
            cy.login(); // Custom command - implement in cypress/support/commands.js
            
            cy.get('#tier-name', { timeout: 10000 }).should('not.contain', 'Loading');
            cy.get('#tier-name').should('match', /Freemium|Pay-As-You-Go|Pro|Custom/);
        });
    });

    describe('Timeout Handling', () => {
        
        it('shows timeout message after 10 seconds on slow response', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                delay: 15000,
                body: {}
            }).as('slowTier');
            
            cy.reload();
            cy.get('#tier-name', { timeout: 12000 }).should('contain', 'timed out');
            cy.get('#tier-features-list button').should('contain', 'Try again');
        });

        it('failsafe triggers after 15 seconds if still loading', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                delay: 20000,
                body: {}
            }).as('verySlowTier');
            
            cy.reload();
            cy.get('#tier-name', { timeout: 17000 }).should('not.contain', 'Loading');
        });
    });

    describe('Error Handling', () => {
        
        it('shows error state on 500 response', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                statusCode: 500,
                body: { detail: 'Internal server error' }
            }).as('serverError');
            
            cy.reload();
            cy.get('#tier-name', { timeout: 5000 }).should('contain', 'Error');
            cy.get('#tier-features-list button').should('contain', 'Retry');
        });

        it('shows error state on network failure', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                forceNetworkError: true
            }).as('networkError');
            
            cy.reload();
            cy.get('#tier-name', { timeout: 12000 }).should('contain', 'Error');
        });

        it('retry button triggers new API call', () => {
            cy.login();
            let callCount = 0;
            cy.intercept('GET', '/api/tiers/current', (req) => {
                callCount++;
                if (callCount === 1) {
                    req.reply({ statusCode: 500 });
                } else {
                    req.reply({
                        statusCode: 200,
                        body: {
                            current_tier: 'freemium',
                            tier_name: 'Freemium',
                            price_monthly: 0,
                            quota_usd: 0,
                            quota_used_usd: 0,
                            quota_remaining_usd: 0,
                            sms_count: 0,
                            within_quota: true,
                            overage_rate: 2.22,
                            features: {}
                        }
                    });
                }
            }).as('tierApi');
            
            cy.reload();
            cy.get('#tier-features-list button').contains('Retry').click();
            cy.get('#tier-name').should('contain', 'Freemium');
        });

        it('uses cached data as fallback on error', () => {
            // First, load successfully to cache data
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                body: {
                    current_tier: 'pro',
                    tier_name: 'Pro',
                    price_monthly: 25,
                    quota_usd: 30,
                    quota_used_usd: 5,
                    quota_remaining_usd: 25,
                    sms_count: 10,
                    within_quota: true,
                    overage_rate: 2.20,
                    features: { api_access: true }
                }
            }).as('successTier');
            
            cy.reload();
            cy.get('#tier-name').should('contain', 'Pro');
            
            // Now simulate error - should show cached data
            cy.intercept('GET', '/api/tiers/current', {
                statusCode: 500
            }).as('failTier');
            
            cy.reload();
            cy.get('#tier-name').should('contain', 'Pro');
            cy.get('#tier-features-list').should('contain', 'cached data');
        });
    });

    describe('CTA Button Visibility', () => {
        
        const tierCTATests = [
            {
                tier: 'freemium',
                visible: ['upgrade-btn', 'compare-plans-btn'],
                hidden: ['add-credits-btn', 'usage-btn', 'manage-btn', 'contact-btn']
            },
            {
                tier: 'payg',
                visible: ['add-credits-btn', 'upgrade-btn', 'compare-plans-btn'],
                hidden: ['usage-btn', 'manage-btn', 'contact-btn']
            },
            {
                tier: 'pro',
                visible: ['usage-btn', 'compare-plans-btn', 'manage-btn'],
                hidden: ['add-credits-btn', 'upgrade-btn', 'contact-btn']
            },
            {
                tier: 'custom',
                visible: ['usage-btn', 'contact-btn', 'manage-btn'],
                hidden: ['add-credits-btn', 'upgrade-btn', 'compare-plans-btn']
            }
        ];

        tierCTATests.forEach(({ tier, visible, hidden }) => {
            it(`shows correct CTAs for ${tier} tier`, () => {
                cy.login();
                cy.intercept('GET', '/api/tiers/current', {
                    body: {
                        current_tier: tier,
                        tier_name: tier.charAt(0).toUpperCase() + tier.slice(1),
                        price_monthly: tier === 'freemium' ? 0 : 25,
                        quota_usd: tier === 'freemium' ? 0 : 30,
                        quota_used_usd: 0,
                        quota_remaining_usd: 30,
                        sms_count: 0,
                        within_quota: true,
                        overage_rate: 2.22,
                        features: {}
                    }
                });
                
                cy.reload();
                cy.get('#tier-name', { timeout: 5000 }).should('not.contain', 'Loading');
                
                visible.forEach(btnId => {
                    cy.get(`#${btnId}`).should('be.visible');
                });
                
                hidden.forEach(btnId => {
                    cy.get(`#${btnId}`).should('not.be.visible');
                });
            });
        });
    });

    describe('CTA Button Actions', () => {
        
        it('Upgrade button navigates to pricing page', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                body: { current_tier: 'freemium', tier_name: 'Freemium', price_monthly: 0, quota_usd: 0, quota_used_usd: 0, quota_remaining_usd: 0, sms_count: 0, within_quota: true, overage_rate: 2.22, features: {} }
            });
            
            cy.reload();
            cy.get('#upgrade-btn').click();
            cy.url().should('include', '/pricing');
        });

        it('Compare Plans button opens modal', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                body: { current_tier: 'freemium', tier_name: 'Freemium', price_monthly: 0, quota_usd: 0, quota_used_usd: 0, quota_remaining_usd: 0, sms_count: 0, within_quota: true, overage_rate: 2.22, features: {} }
            });
            
            cy.reload();
            cy.get('#compare-plans-btn').click();
            cy.get('#tier-compare-modal').should('be.visible');
        });

        it('Add Credits button navigates to wallet', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                body: { current_tier: 'payg', tier_name: 'Pay-As-You-Go', price_monthly: 0, quota_usd: 100, quota_used_usd: 0, quota_remaining_usd: 100, sms_count: 0, within_quota: true, overage_rate: 2.50, features: {} }
            });
            
            cy.reload();
            cy.get('#add-credits-btn').click();
            cy.url().should('include', '/wallet');
        });
    });

    describe('Tier Badge Styling', () => {
        
        const tierBadgeClasses = {
            freemium: 'tier-badge-freemium',
            payg: 'tier-badge-payg',
            pro: 'tier-badge-pro',
            custom: 'tier-badge-custom'
        };

        Object.entries(tierBadgeClasses).forEach(([tier, badgeClass]) => {
            it(`applies ${badgeClass} class for ${tier} tier`, () => {
                cy.login();
                cy.intercept('GET', '/api/tiers/current', {
                    body: { current_tier: tier, tier_name: tier, price_monthly: 0, quota_usd: 0, quota_used_usd: 0, quota_remaining_usd: 0, sms_count: 0, within_quota: true, overage_rate: 2.22, features: {} }
                });
                
                cy.reload();
                cy.get('#tier-name .tier-badge').should('have.class', badgeClass);
            });
        });
    });

    describe('Responsive Layout', () => {
        
        it('stacks CTA buttons vertically on mobile', () => {
            cy.login();
            cy.intercept('GET', '/api/tiers/current', {
                body: { current_tier: 'freemium', tier_name: 'Freemium', price_monthly: 0, quota_usd: 0, quota_used_usd: 0, quota_remaining_usd: 0, sms_count: 0, within_quota: true, overage_rate: 2.22, features: {} }
            });
            
            cy.viewport(375, 667); // iPhone SE
            cy.reload();
            
            cy.get('.tier-cta-container').should('have.css', 'flex-direction', 'column');
        });
    });
});
