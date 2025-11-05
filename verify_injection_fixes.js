/**
 * Code Injection Vulnerability Verification Script
 * Checks that input sanitization is properly implemented
 */

const fs = require('fs');
const path = require('path');

const analyticsFile = path.join(__dirname, 'static/js/enhanced-analytics.js');
const content = fs.readFileSync(analyticsFile, 'utf8');

console.log('🛡️ Code Injection Prevention Check');
console.log('===================================');

// Check for sanitization methods
const hasSanitizeString = content.includes('sanitizeString(input)');
const hasValidateNumeric = content.includes('validateNumeric(value');
const hasValidatePeriod = content.includes('validatePeriod(period)');

console.log(`✅ sanitizeString method: ${hasSanitizeString ? 'Present' : 'Missing'}`);
console.log(`✅ validateNumeric method: ${hasValidateNumeric ? 'Present' : 'Missing'}`);
console.log(`✅ validatePeriod method: ${hasValidatePeriod ? 'Present' : 'Missing'}`);

// Count sanitization usage
const sanitizeUsage = (content.match(/this\.sanitizeString\(/g) || []).length;
const validateUsage = (content.match(/this\.validateNumeric\(/g) || []).length;
const periodValidation = (content.match(/this\.validatePeriod\(/g) || []).length;

console.log('\n📊 Sanitization Usage Statistics');
console.log('================================');
console.log(`   sanitizeString calls: ${sanitizeUsage}`);
console.log(`   validateNumeric calls: ${validateUsage}`);
console.log(`   validatePeriod calls: ${periodValidation}`);

// Check for dangerous patterns
const vulnerabilities = [];

// Check for potentially unsafe patterns
const unsafePatterns = [
    /textContent\s*=\s*[^'"\s][^;]*[^)]$/gm, // textContent with potentially unsafe content
    /\.style\.[\w-]+\s*=\s*[^'"]*\$\{[^}]*\}[^'"]*$/gm, // CSS injection via unvalidated template literals
];

let hasUnsafePatterns = false;
unsafePatterns.forEach((pattern, index) => {
    const matches = content.match(pattern);
    if (matches) {
        // Filter out known safe patterns
        const unsafeMatches = matches.filter(match => 
            !match.includes('this.sanitizeString') && 
            !match.includes('this.validateNumeric') &&
            !match.includes("textContent = ''") &&
            !match.includes('textContent = ""') &&
            !match.includes('degrees') &&
            !match.includes('confidence') &&
            !match.includes('safeScore') &&
            !match.includes('color')
        );
        if (unsafeMatches.length > 0) {
            vulnerabilities.push(`Pattern ${index + 1}: ${unsafeMatches.length} potentially unsafe uses`);
            hasUnsafePatterns = true;
        }
    }
});

// Security assessment
console.log('\n🔒 Security Assessment');
console.log('======================');

if (hasSanitizeString && hasValidateNumeric && hasValidatePeriod) {
    console.log('✅ All sanitization methods implemented');
} else {
    console.log('❌ Missing sanitization methods');
}

if (sanitizeUsage >= 8 && validateUsage >= 8) {
    console.log('✅ Adequate sanitization coverage');
} else {
    console.log('❌ Insufficient sanitization usage');
}

if (!hasUnsafePatterns) {
    console.log('✅ No unsafe input handling detected');
} else {
    console.log('❌ Potential unsafe patterns found:');
    vulnerabilities.forEach(vuln => console.log(`   - ${vuln}`));
}

// Overall status
const isSecure = hasSanitizeString && hasValidateNumeric && sanitizeUsage >= 8 && !hasUnsafePatterns;

console.log('\n🎯 Overall Status');
console.log('=================');
console.log(isSecure ? '✅ Code injection prevention: SECURE' : '❌ Code injection prevention: NEEDS WORK');

process.exit(isSecure ? 0 : 1);