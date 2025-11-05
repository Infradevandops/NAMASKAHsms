/**
 * JavaScript Error Handling Verification Script
 * Checks that comprehensive error handling is implemented in analytics frontend
 */

const fs = require('fs');
const path = require('path');

function checkJavaScriptErrorHandling() {
    const analyticsFile = path.join(__dirname, 'static/js/enhanced-analytics.js');
    
    if (!fs.existsSync(analyticsFile)) {
        console.log('❌ Analytics JavaScript file not found');
        return false;
    }
    
    const content = fs.readFileSync(analyticsFile, 'utf8');
    
    console.log('🔍 JavaScript Error Handling Check');
    console.log('==================================');
    
    // Check for error handling features
    const features = {
        'Global Error Handler': /addEventListener\('error'/g,
        'Promise Rejection Handler': /addEventListener\('unhandledrejection'/g,
        'Network Status Monitoring': /addEventListener\('online'/g,
        'Try-Catch Blocks': /try\s*\{/g,
        'Error Notifications': /showNotification.*error/g,
        'Retry Mechanism': /fetchWithRetry|showRetryOption/g,
        'Timeout Handling': /AbortController|setTimeout.*abort/g,
        'Loading States': /showLoadingState/g,
        'Chart Error Handling': /showChartError/g,
        'Input Validation': /validateNumeric|validatePeriod/g
    };
    
    const results = {};
    let totalScore = 0;
    
    console.log('\n📊 Error Handling Features');
    console.log('==========================');
    
    Object.entries(features).forEach(([feature, pattern]) => {
        const matches = content.match(pattern);
        const count = matches ? matches.length : 0;
        const hasFeature = count > 0;
        
        results[feature] = { count, hasFeature };
        totalScore += hasFeature ? 1 : 0;
        
        const status = hasFeature ? '✅' : '❌';
        console.log(`   ${status} ${feature}: ${count} implementations`);
    });
    
    // Check for specific error handling patterns
    const errorPatterns = {
        'HTTP Status Handling': /response\.status.*401|response\.status.*403|response\.status.*500/g,
        'Authentication Errors': /Authentication.*failed|Session.*expired/g,
        'Network Errors': /timeout|connection|offline/g,
        'User Feedback': /showError|showNotification/g,
        'Graceful Degradation': /catch.*error.*console\.error/g
    };
    
    console.log('\n🛡️ Error Pattern Analysis');
    console.log('=========================');
    
    Object.entries(errorPatterns).forEach(([pattern, regex]) => {
        const matches = content.match(regex);
        const count = matches ? matches.length : 0;
        const hasPattern = count > 0;
        
        totalScore += hasPattern ? 1 : 0;
        
        const status = hasPattern ? '✅' : '❌';
        console.log(`   ${status} ${pattern}: ${count} occurrences`);
    });
    
    // Check for user experience features
    const uxFeatures = {
        'Loading Indicators': /loading.*indicator|showLoadingState/g,
        'Error Recovery': /retry|reload|refresh/g,
        'Offline Support': /navigator\.onLine|offline/g,
        'Progress Feedback': /notification|progress|status/g
    };
    
    console.log('\n🎯 User Experience Features');
    console.log('===========================');
    
    Object.entries(uxFeatures).forEach(([feature, pattern]) => {
        const matches = content.match(pattern);
        const count = matches ? matches.length : 0;
        const hasFeature = count > 0;
        
        totalScore += hasFeature ? 1 : 0;
        
        const status = hasFeature ? '✅' : '❌';
        console.log(`   ${status} ${feature}: ${count} implementations`);
    });
    
    // Calculate overall score
    const maxScore = Object.keys(features).length + Object.keys(errorPatterns).length + Object.keys(uxFeatures).length;
    const successRate = (totalScore / maxScore) * 100;
    
    console.log('\n📈 Error Handling Statistics');
    console.log('============================');
    console.log(`   Total Features: ${totalScore}/${maxScore}`);
    console.log(`   Success Rate: ${successRate.toFixed(1)}%`);
    
    // Check for critical security features
    const securityFeatures = [
        'sanitizeString',
        'validateNumeric',
        'textContent'
    ];
    
    const securityScore = securityFeatures.filter(feature => 
        content.includes(feature)
    ).length;
    
    console.log(`   Security Features: ${securityScore}/${securityFeatures.length}`);
    
    // Overall assessment
    console.log('\n🎯 Overall Assessment');
    console.log('=====================');
    
    if (successRate >= 90) {
        console.log('✅ JavaScript error handling: EXCELLENT');
        return true;
    } else if (successRate >= 75) {
        console.log('⚠️ JavaScript error handling: GOOD (minor improvements needed)');
        return true;
    } else if (successRate >= 60) {
        console.log('⚠️ JavaScript error handling: ADEQUATE (improvements recommended)');
        return true;
    } else {
        console.log('❌ JavaScript error handling: NEEDS SIGNIFICANT WORK');
        return false;
    }
}

if (require.main === module) {
    const success = checkJavaScriptErrorHandling();
    process.exit(success ? 0 : 1);
}

module.exports = { checkJavaScriptErrorHandling };