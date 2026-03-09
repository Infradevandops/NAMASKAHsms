import { readFileSync } from 'fs';
const html = readFileSync('/Users/machine/My Drive/Github Projects/Namaskah. app/templates/verify_modern.html', 'utf8');

let passed = 0, failed = 0;
function check(name, condition) {
    if (condition) { console.log(`  ✅ ${name}`); passed++; }
    else { console.log(`  ❌ ${name}`); failed++; }
}

console.log('\n── DOM Elements present in HTML ──');
['service-search-input','service-inline-dropdown','service-selected-display',
 'service-loading-spinner','area-code-search-input','carrier-select-inline',
 'continue-btn','advanced-options-section','freemium-upsell'].forEach(id =>
    check(`#${id} exists`, html.includes(`id="${id}"`)));

console.log('\n── Removed elements must NOT exist ──');
['service-picker-btn','area-code-picker-btn','carrier-picker-btn'].forEach(id =>
    check(`#${id} removed`, !html.includes(`id="${id}"`)));

console.log('\n── No broken getElementById calls ──');
['service-picker-btn','area-code-display','carrier-display'].forEach(id =>
    check(`getElementById('${id}') absent`, !new RegExp(`getElementById\\(['"]${id}['"]\\)`).test(html)));

console.log('\n── Key JS functions defined ──');
['loadServices','loadTier','loadCarriers','loadAreaCodes','selectServiceInline',
 'filterServicesInline','showServiceDropdown','_renderServiceDropdown',
 'filterAreaCodesInline','selectAreaCodeInline','startScanning',
 'toggleAdvanced','clearServiceSelection','_refreshPricedCache','_buildServiceItems'
].forEach(fn => check(`${fn}()`, html.includes(`function ${fn}`) || html.includes(`async function ${fn}`)));

console.log('\n── Backoff correctness ──');
check('backoffMs in ms', html.includes('backoffMs = [2000, 3000, 5000, 8000, 10000]'));
check('elapsed uses ms/1000', html.includes('backoffMs[Math.max(0, stepIdx - 1)] / 1000'));
check('clearTimeout used for scanInterval', html.includes('clearTimeout(scanInterval)'));

console.log('\n── Tier caching ──');
check('nsk_tier_cache key', html.includes("'nsk_tier_cache'"));
check('1h TTL', html.includes('3600000'));
check('loadAreaCodes called before await fetch tiers', 
    html.indexOf('loadAreaCodes()') < html.indexOf("await fetch('/api/tiers/current'"));

console.log('\n── Carrier caching + pricing ──');
check('nsk_carriers_cache key', html.includes("'nsk_carriers_cache'"));
check('24h TTL', html.includes('24 * 60 * 60 * 1000'));
check('price_impact in carrier render', html.includes('price_impact'));

console.log('\n── Favorites integration ──');
check('favoriteServices.getAll() called', html.includes('favoriteServices.getAll()'));
check('favIds.includes used', html.includes('favIds.includes'));

console.log('\n── DOMContentLoaded init ──');
check('loadServices() fires', html.includes('loadServices();'));
check('loadTier() fires', html.includes('loadTier();'));
check('loadBalance() fires', html.includes('loadBalance();'));

console.log(`\n${passed + failed} checks: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
