#!/usr/bin/env node
/**
 * Lighthouse Accessibility Audit Script
 * Tests all dashboard pages for accessibility compliance
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');

const BASE_URL = 'http://localhost:8000';

const PAGES = [
  { name: 'Dashboard', url: '/dashboard' },
  { name: 'Analytics', url: '/analytics' },
  { name: 'Wallet', url: '/wallet' },
  { name: 'History', url: '/history' },
  { name: 'Notifications', url: '/notifications' },
  { name: 'Verify', url: '/verify' },
  { name: 'Settings', url: '/settings' },
  { name: 'Webhooks', url: '/webhooks' },
  { name: 'Referrals', url: '/referrals' }
];

async function runLighthouse(url) {
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  const options = {
    logLevel: 'error',
    output: 'json',
    onlyCategories: ['accessibility', 'performance', 'best-practices'],
    port: chrome.port
  };

  const runnerResult = await lighthouse(url, options);
  await chrome.kill();
  
  return runnerResult.lhr;
}

async function auditAllPages() {
  console.log('🔍 Starting Lighthouse Accessibility Audit\n');
  
  const results = [];
  
  for (const page of PAGES) {
    const url = `${BASE_URL}${page.url}`;
    console.log(`Testing: ${page.name}...`);
    
    try {
      const report = await runLighthouse(url);
      
      const result = {
        name: page.name,
        url: page.url,
        accessibility: Math.round(report.categories.accessibility.score * 100),
        performance: Math.round(report.categories.performance.score * 100),
        bestPractices: Math.round(report.categories['best-practices'].score * 100)
      };
      
      results.push(result);
      
      const status = result.accessibility >= 90 ? '✅' : '⚠️';
      console.log(`  ${status} Accessibility: ${result.accessibility}/100`);
      
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
      results.push({ name: page.name, error: error.message });
    }
  }
  
  // Generate report
  console.log('\n' + '='.repeat(60));
  console.log('📊 AUDIT SUMMARY');
  console.log('='.repeat(60));
  
  const passed = results.filter(r => r.accessibility >= 90).length;
  const total = results.filter(r => !r.error).length;
  
  console.log(`\nPages Tested: ${total}`);
  console.log(`Passed (≥90): ${passed}`);
  console.log(`Failed (<90): ${total - passed}`);
  console.log(`Success Rate: ${Math.round((passed / total) * 100)}%\n`);
  
  // Save results
  fs.writeFileSync('accessibility_report.json', JSON.stringify(results, null, 2));
  console.log('📄 Full report saved to: accessibility_report.json\n');
  
  return passed === total;
}

auditAllPages()
  .then(success => process.exit(success ? 0 : 1))
  .catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
