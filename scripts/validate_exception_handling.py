#!/usr/bin/env python3
"""Validation script for exception handling fixes."""
import re
import sys
from pathlib import Path

def check_generic_exceptions(file_path):
    """Check for remaining generic exception handling."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for bare except:
        if re.search(r'^\s*except\s*:', line):
            issues.append(f"Line {i}: Bare except clause found")
        
        # Check for generic Exception catching (with some exceptions)
        if re.search(r'except\s+Exception\s+as\s+\w+:', line):
            # Allow in middleware, exception handlers, and startup (for critical errors)
            if ('middleware' not in str(file_path) and 
                'exception' not in str(file_path) and 
                'startup' not in str(file_path)):
                issues.append(f"Line {i}: Generic Exception catching found")
            # In startup, only allow if it re-raises or logs as critical
            elif 'startup' in str(file_path):
                # Check next few lines for re-raise or critical logging
                next_lines = lines[i:i+3] if i < len(lines) - 2 else lines[i:]
                has_reraise = any('raise' in next_line for next_line in next_lines)
                has_critical = any('critical' in next_line for next_line in next_lines)
                if not (has_reraise or has_critical):
                    issues.append(f"Line {i}: Generic Exception catching without re-raise or critical logging")
    
    return issues

def check_specific_improvements(file_path):
    """Check for specific improvements made."""
    improvements = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for specific exception imports
    if 'SQLAlchemyError' in content or 'IntegrityError' in content:
        improvements.append("Database-specific exceptions imported")
    
    if 'ClientError' in content or 'BotoCoreError' in content:
        improvements.append("AWS-specific exceptions imported")
    
    if 'InvalidToken' in content:
        improvements.append("Encryption-specific exceptions imported")
    
    if 'safe_int_conversion' in content or 'safe_json_parse' in content:
        improvements.append("Safe conversion utilities used")
    
    return improvements

def main():
    """Main validation function."""
    app_dir = Path(__file__).parent.parent / 'app'
    
    if not app_dir.exists():
        print("❌ App directory not found")
        return 1
    
    print("🔍 Validating Exception Handling Fixes")
    print("=" * 50)
    
    # Files we specifically fixed
    fixed_files = [
        'api/core/preferences.py',
        'core/secrets_manager.py',
        'core/encryption.py',
        'core/startup.py',
        'middleware/monitoring.py'
    ]
    
    total_issues = 0
    total_improvements = 0
    
    for file_rel_path in fixed_files:
        file_path = app_dir / file_rel_path
        
        if not file_path.exists():
            print(f"⚠️  {file_rel_path}: File not found")
            continue
        
        print(f"\n📁 {file_rel_path}")
        
        # Check for remaining issues
        issues = check_generic_exceptions(file_path)
        if issues:
            print("  ❌ Issues found:")
            for issue in issues:
                print(f"    - {issue}")
            total_issues += len(issues)
        else:
            print("  ✅ No generic exception handling found")
        
        # Check for improvements
        improvements = check_specific_improvements(file_path)
        if improvements:
            print("  ✅ Improvements made:")
            for improvement in improvements:
                print(f"    - {improvement}")
            total_improvements += len(improvements)
    
    # Check if utility file was created
    util_file = app_dir / 'utils' / 'exception_handling.py'
    if util_file.exists():
        print(f"\n📁 utils/exception_handling.py")
        print("  ✅ Exception handling utilities created")
        total_improvements += 1
    else:
        print(f"\n📁 utils/exception_handling.py")
        print("  ❌ Exception handling utilities not found")
        total_issues += 1
    
    # Check if tests were created
    test_file = app_dir / 'tests' / 'test_exception_handling.py'
    if test_file.exists():
        print(f"\n📁 tests/test_exception_handling.py")
        print("  ✅ Exception handling tests created")
        total_improvements += 1
    else:
        print(f"\n📁 tests/test_exception_handling.py")
        print("  ❌ Exception handling tests not found")
        total_issues += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Summary:")
    print(f"  ✅ Improvements: {total_improvements}")
    print(f"  ❌ Issues: {total_issues}")
    
    if total_issues == 0:
        print("\n🎉 All exception handling fixes validated successfully!")
        return 0
    else:
        print(f"\n⚠️  {total_issues} issues found that need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())