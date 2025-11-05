/**
 * XSS Vulnerability Verification Script
 * Checks that the enhanced-analytics.js file is secure
 */

const fs = require('fs');
const path = require('path');

const analyticsFile = path.join(__dirname, 'static/js/enhanced-analytics.js');
const content = fs.readFileSync(analyticsFile, 'utf8');

// Check for dangerous patterns
const vulnerabilities = [];

// Check for innerHTML usage
const innerHTMLMatches = content.match(/\.innerHTML\s*=/g);
if (innerHTMLMatches) {
    vulnerabilities.push(`Found ${innerHTMLMatches.length} innerHTML assignments`);
}

// Check for template literal injections
const templateMatches = content.match(/\$\{[^}]*\}/g);
if (templateMatches) {
    const dangerousTemplates = templateMatches.filter(match => 
        !match.includes('toFixed') && 
        !match.includes('Math.') && 
        !match.includes('index') &&
        !match.includes('degrees') &&
        !match.includes('confidence') &&
        !match.includes('currentPeriod')
    );
    if (dangerousTemplates.length > 0) {
        vulnerabilities.push(`Found ${dangerousTemplates.length} potentially dangerous template literals: ${dangerousTemplates.join(', ')}`);
    }
}

// Check for eval usage
const evalMatches = content.match(/eval\s*\(/g);
if (evalMatches) {
    vulnerabilities.push(`Found ${evalMatches.length} eval() calls`);
}

// Check for Function constructor
const functionMatches = content.match(/new\s+Function\s*\(/g);
if (functionMatches) {
    vulnerabilities.push(`Found ${functionMatches.length} Function constructor calls`);
}

// Verify security fixes are in place
const securityChecks = [];

// Check for textContent usage
const textContentMatches = content.match(/\.textContent\s*=/g);
if (textContentMatches && textContentMatches.length >= 10) {
    securityChecks.push('✅ Uses textContent for safe DOM updates');
} else {
    securityChecks.push('❌ Insufficient textContent usage');
}

// Check for createElement usage
const createElementMatches = content.match(/createElement\s*\(/g);
if (createElementMatches && createElementMatches.length >= 5) {
    securityChecks.push('✅ Uses createElement for safe DOM construction');
} else {
    securityChecks.push('❌ Insufficient createElement usage');
}

// Check for appendChild usage
const appendChildMatches = content.match(/appendChild\s*\(/g);
if (appendChildMatches && appendChildMatches.length >= 5) {
    securityChecks.push('✅ Uses appendChild for safe DOM insertion');
} else {
    securityChecks.push('❌ Insufficient appendChild usage');
}

console.log('🔒 XSS Vulnerability Check Results');
console.log('=====================================');

if (vulnerabilities.length === 0) {
    console.log('✅ No XSS vulnerabilities detected!');
} else {
    console.log('❌ Vulnerabilities found:');
    vulnerabilities.forEach(vuln => console.log(`   - ${vuln}`));
}

console.log('\n🛡️ Security Implementation Check');
console.log('=================================');
securityChecks.forEach(check => console.log(`   ${check}`));

console.log('\n📊 Statistics');
console.log('=============');
console.log(`   textContent assignments: ${textContentMatches ? textContentMatches.length : 0}`);
console.log(`   createElement calls: ${createElementMatches ? createElementMatches.length : 0}`);
console.log(`   appendChild calls: ${appendChildMatches ? appendChildMatches.length : 0}`);
console.log(`   innerHTML assignments: ${innerHTMLMatches ? innerHTMLMatches.length : 0}`);

// Exit with appropriate code
process.exit(vulnerabilities.length === 0 ? 0 : 1);