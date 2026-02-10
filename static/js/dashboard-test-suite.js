// Dashboard Functionality Test Suite
// Run in browser console: copy and paste this entire script

(function() {
    'use strict';
    
    const results = {
        passed: [],
        failed: [],
        warnings: []
    };

    function test(name, fn) {
        try {
            const result = fn();
            if (result === true || result === undefined) {
                results.passed.push(name);
                console.log(`✅ ${name}`);
            } else {
                results.failed.push(name);
                console.error(`❌ ${name}: ${result}`);
            }
        } catch (e) {
            results.failed.push(name);
            console.error(`❌ ${name}: ${e.message}`);
        }
    }

    function warn(name, message) {
        results.warnings.push(`${name}: ${message}`);
        console.warn(`⚠️ ${name}: ${message}`);
    }

    console.log('🔍 Starting Dashboard Functionality Test...\n');

    // ===== SIDEBAR TESTS =====
    console.log('📊 Testing Sidebar Navigation...');
    
    test('Sidebar exists', () => {
        return document.getElementById('app-sidebar') !== null;
    });

    test('Sidebar has navigation items', () => {
        const items = document.querySelectorAll('.nav-item');
        return items.length > 0 || 'No navigation items found';
    });

    test('Active page is highlighted', () => {
        const active = document.querySelector('.nav-item.active');
        return active !== null || 'No active nav item';
    });

    test('Notification badge exists', () => {
        const badge = document.getElementById('sidebar-notif-badge');
        return badge !== null;
    });

    test('Language switcher exists', () => {
        const switcher = document.getElementById('lang-switcher');
        return switcher !== null;
    });

    test('Logout function exists', () => {
        return typeof window.logout === 'function' || typeof logout === 'function';
    });

    // ===== SETTINGS PAGE TESTS =====
    if (window.location.pathname.includes('settings')) {
        console.log('\n⚙️ Testing Settings Page...');
        
        test('Settings tabs exist', () => {
            const tabs = document.querySelectorAll('.settings-nav-item');
            return tabs.length >= 4 || `Only ${tabs.length} tabs found`;
        });

        test('switchTab function exists', () => {
            return typeof window.switchTab === 'function';
        });

        test('Account tab exists', () => {
            return document.getElementById('account-tab') !== null;
        });

        test('Security tab exists', () => {
            return document.getElementById('security-tab') !== null;
        });

        test('Notifications tab exists', () => {
            return document.getElementById('notifications-tab') !== null;
        });

        test('Billing tab exists', () => {
            return document.getElementById('billing-tab') !== null;
        });

        // Settings functions
        test('requestPasswordReset exists', () => {
            return typeof window.requestPasswordReset === 'function';
        });

        test('updateSettings exists', () => {
            return typeof window.updateSettings === 'function';
        });

        test('generateApiKey exists', () => {
            return typeof window.generateApiKey === 'function';
        });

        test('deleteApiKey exists', () => {
            return typeof window.deleteApiKey === 'function';
        });

        test('showRefundModal exists', () => {
            return typeof window.showRefundModal === 'function';
        });

        test('toggleForwardingOption exists', () => {
            return typeof window.toggleForwardingOption === 'function';
        });

        test('addToBlacklist exists', () => {
            return typeof window.addToBlacklist === 'function';
        });
    }

    // ===== WALLET PAGE TESTS =====
    if (window.location.pathname.includes('wallet')) {
        console.log('\n💰 Testing Wallet Page...');
        
        test('Wallet balance display exists', () => {
            return document.getElementById('wallet-balance') !== null;
        });

        test('Payment buttons exist', () => {
            const buttons = document.querySelectorAll('button[onclick*="addCredits"]');
            return buttons.length >= 4 || `Only ${buttons.length} payment buttons`;
        });

        test('addCredits function exists', () => {
            return typeof window.addCredits === 'function';
        });

        test('switchPaymentMethod exists', () => {
            return typeof window.switchPaymentMethod === 'function';
        });

        test('exportCreditHistory exists', () => {
            return typeof window.exportCreditHistory === 'function';
        });

        test('Transactions table exists', () => {
            return document.getElementById('transactions-body') !== null;
        });

        test('Pagination exists', () => {
            return document.getElementById('transactions-pagination') !== null;
        });

        test('Auto-reload settings exist', () => {
            const container = document.getElementById('auto-reload-settings');
            if (!container) warn('Auto-reload', 'Container not found');
            return container !== null;
        });

        test('Pending transactions exist', () => {
            const container = document.getElementById('pending-transactions');
            if (!container) warn('Pending transactions', 'Container not found');
            return container !== null;
        });
    }

    // ===== VERIFY PAGE TESTS =====
    if (window.location.pathname.includes('verify')) {
        console.log('\n📱 Testing Verify Page...');
        
        test('Service search exists', () => {
            return document.getElementById('service-search') !== null;
        });

        test('Purchase button exists', () => {
            return document.getElementById('purchase-btn') !== null;
        });

        test('selectService function exists', () => {
            return typeof window.selectService === 'function';
        });

        test('purchaseVerification exists', () => {
            return typeof window.purchaseVerification === 'function';
        });

        test('Favorites list exists', () => {
            return document.getElementById('favorites-list') !== null;
        });

        test('Templates list exists', () => {
            return document.getElementById('templates-list') !== null;
        });

        test('favoriteServices exists', () => {
            return typeof window.favoriteServices === 'object';
        });

        test('verificationTemplates exists', () => {
            return typeof window.verificationTemplates === 'object';
        });

        test('toggleFavorite exists', () => {
            return typeof window.toggleFavorite === 'function';
        });
    }

    // ===== DASHBOARD PAGE TESTS =====
    if (window.location.pathname === '/dashboard' || window.location.pathname === '/') {
        console.log('\n📊 Testing Dashboard Page...');
        
        test('Stat cards exist', () => {
            const cards = document.querySelectorAll('.card');
            return cards.length >= 4 || `Only ${cards.length} cards found`;
        });

        test('Activity table exists', () => {
            const table = document.querySelector('table');
            return table !== null;
        });
    }

    // ===== ANALYTICS PAGE TESTS =====
    if (window.location.pathname.includes('analytics')) {
        console.log('\n📈 Testing Analytics Page...');
        
        test('Date range picker exists', () => {
            const startDate = document.querySelector('input[type="date"]');
            return startDate !== null;
        });

        test('Export button exists', () => {
            const exportBtn = document.querySelector('button[onclick*="export"]');
            return exportBtn !== null;
        });

        test('Charts container exists', () => {
            const charts = document.querySelectorAll('[id*="chart"]');
            return charts.length > 0 || 'No charts found';
        });
    }

    // ===== GLOBAL TESTS =====
    console.log('\n🌐 Testing Global Features...');
    
    test('Error handler exists', () => {
        return typeof window.errorHandler === 'object' || typeof window.ErrorHandler === 'function';
    });

    test('Notification system exists', () => {
        return typeof window.notificationSystem === 'object';
    });

    test('Loading skeleton exists', () => {
        return typeof window.LoadingSkeleton === 'function';
    });

    test('Pagination component exists', () => {
        return typeof window.Pagination === 'function';
    });

    test('i18n exists', () => {
        return typeof window.i18n === 'object';
    });

    test('Notification bell exists', () => {
        const bell = document.querySelector('.notification-bell-btn');
        return bell !== null;
    });

    test('Balance widget exists', () => {
        const balance = document.querySelector('[id*="balance"]');
        return balance !== null;
    });

    // ===== SUMMARY =====
    console.log('\n' + '='.repeat(50));
    console.log('📊 TEST SUMMARY');
    console.log('='.repeat(50));
    console.log(`✅ Passed: ${results.passed.length}`);
    console.log(`❌ Failed: ${results.failed.length}`);
    console.log(`⚠️  Warnings: ${results.warnings.length}`);
    console.log('='.repeat(50));

    if (results.failed.length > 0) {
        console.log('\n❌ FAILED TESTS:');
        results.failed.forEach(f => console.log(`  - ${f}`));
    }

    if (results.warnings.length > 0) {
        console.log('\n⚠️  WARNINGS:');
        results.warnings.forEach(w => console.log(`  - ${w}`));
    }

    if (results.failed.length === 0) {
        console.log('\n🎉 ALL TESTS PASSED!');
    } else {
        console.log(`\n⚠️  ${results.failed.length} tests failed. Check console for details.`);
    }

    // Return results for programmatic access
    return {
        passed: results.passed.length,
        failed: results.failed.length,
        warnings: results.warnings.length,
        details: results
    };
})();
