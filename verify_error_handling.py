#!/usr/bin/env python3
"""
Error Handling Verification Script
Tests that comprehensive error handling is implemented in analytics API
"""

import ast
import re
from pathlib import Path

def check_error_handling():
    """Check analytics API for proper error handling implementation."""
    
    analytics_file = Path("app/api/analytics.py")
    if not analytics_file.exists():
        print("❌ Analytics API file not found")
        return False
    
    content = analytics_file.read_text()
    
    print("🔍 Error Handling Implementation Check")
    print("=====================================")
    
    # Check for required imports
    required_imports = [
        "HTTPException",
        "SQLAlchemyError", 
        "logging"
    ]
    
    missing_imports = []
    for imp in required_imports:
        if imp not in content:
            missing_imports.append(imp)
    
    if missing_imports:
        print(f"❌ Missing imports: {', '.join(missing_imports)}")
        return False
    else:
        print("✅ All required imports present")
    
    # Check for try-catch blocks
    try_blocks = len(re.findall(r'\btry\s*:', content))
    except_blocks = len(re.findall(r'\bexcept\s+', content))
    
    print(f"\n📊 Exception Handling Statistics")
    print(f"   Try blocks: {try_blocks}")
    print(f"   Except blocks: {except_blocks}")
    
    if try_blocks < 5 or except_blocks < 5:
        print("❌ Insufficient error handling coverage")
        return False
    else:
        print("✅ Adequate exception handling coverage")
    
    # Check for specific error types
    error_types = [
        "SQLAlchemyError",
        "HTTPException", 
        "ValueError",
        "ZeroDivisionError"
    ]
    
    found_errors = []
    for error_type in error_types:
        if f"except {error_type}" in content or f"except ({error_type}" in content:
            found_errors.append(error_type)
    
    print(f"\n🛡️ Specific Error Types Handled")
    for error_type in error_types:
        status = "✅" if error_type in found_errors else "❌"
        print(f"   {status} {error_type}")
    
    # Check for logging
    logger_usage = len(re.findall(r'logger\.(error|warning|info)', content))
    print(f"\n📝 Logging Implementation")
    print(f"   Logger calls: {logger_usage}")
    
    if logger_usage < 5:
        print("❌ Insufficient logging coverage")
        return False
    else:
        print("✅ Adequate logging coverage")
    
    # Check for input validation
    validation_patterns = [
        r'if.*not in.*\[.*\]',  # Whitelist validation
        r'raise HTTPException.*400',  # Bad request errors
        r'len\(.*\)\s*!=\s*\d+'  # Length validation
    ]
    
    validation_count = 0
    for pattern in validation_patterns:
        validation_count += len(re.findall(pattern, content))
    
    print(f"\n🔒 Input Validation")
    print(f"   Validation checks: {validation_count}")
    
    if validation_count < 3:
        print("❌ Insufficient input validation")
        return False
    else:
        print("✅ Adequate input validation")
    
    # Check for graceful degradation
    fallback_patterns = [
        r'or\s+0',  # Fallback to 0
        r'or\s+\[\]',  # Fallback to empty list
        r'continue',  # Skip on error
    ]
    
    fallback_count = 0
    for pattern in fallback_patterns:
        fallback_count += len(re.findall(pattern, content))
    
    print(f"\n🔄 Graceful Degradation")
    print(f"   Fallback mechanisms: {fallback_count}")
    
    if fallback_count < 3:
        print("❌ Insufficient graceful degradation")
        return False
    else:
        print("✅ Adequate graceful degradation")
    
    # Overall assessment
    all_checks = [
        len(missing_imports) == 0,
        try_blocks >= 5,
        except_blocks >= 5,
        len(found_errors) >= 3,
        logger_usage >= 5,
        validation_count >= 3,
        fallback_count >= 3
    ]
    
    success_rate = sum(all_checks) / len(all_checks) * 100
    
    print(f"\n🎯 Overall Assessment")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 85:
        print("✅ Error handling implementation: EXCELLENT")
        return True
    elif success_rate >= 70:
        print("⚠️ Error handling implementation: GOOD (needs minor improvements)")
        return True
    else:
        print("❌ Error handling implementation: NEEDS WORK")
        return False

if __name__ == "__main__":
    success = check_error_handling()
    exit(0 if success else 1)