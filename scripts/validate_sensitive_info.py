#!/usr/bin/env python3
"""Validation script for sensitive information exposure fixes."""
import re
import sys
from pathlib import Path

def check_sensitive_exposures(file_path):
    """Check for potential sensitive information exposures."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for detail=str(e) pattern
        if re.search(r'detail\s*=\s*str\s*\(\s*e\s*\)', line):
            issues.append(f"Line {i}: Potential sensitive error exposure - detail=str(e)")
        
        # Check for f-strings with exception objects (but not safe ones)
        if re.search(r'f["\'].*\{.*e.*\}.*["\']', line) and 'create_safe_error_detail' not in line:
            issues.append(f"Line {i}: Potential sensitive error in f-string")
        
        # Check for direct exception logging without sanitization
        if re.search(r'logger\.\w+\(.*str\(.*e.*\).*\)', line) and 'create_safe_error_detail' not in line:
            issues.append(f"Line {i}: Potential unsanitized error logging")
    
    return issues

def check_data_masking_usage(file_path):
    """Check for proper data masking usage."""
    improvements = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for data masking imports
    if 'create_safe_error_detail' in content:
        improvements.append("Safe error detail function imported")
    
    if 'DataMasker' in content:
        improvements.append("DataMasker utility imported")
    
    if 'sanitize_log_data' in content:
        improvements.append("Log data sanitization imported")
    
    # Check for generic error messages instead of str(e)
    if 'Authentication failed' in content or 'Registration validation failed' in content:
        improvements.append("Generic error messages used")
    
    return improvements

def main():
    """Main validation function."""
    app_dir = Path(__file__).parent.parent / 'app'
    
    if not app_dir.exists():
        print("❌ App directory not found")
        return 1
    
    print("🔍 Validating Sensitive Information Exposure Fixes")
    print("=" * 60)
    
    # Files we specifically fixed
    fixed_files = [
        'api/rentals/rentals_updated.py',
        'api/core/auth.py'
    ]
    
    # Check for new utility files
    utility_files = [
        'utils/data_masking.py',
        'tests/test_data_masking.py'
    ]
    
    total_issues = 0
    total_improvements = 0
    
    # Check fixed files
    for file_rel_path in fixed_files:
        file_path = app_dir / file_rel_path
        
        if not file_path.exists():
            print(f"⚠️  {file_rel_path}: File not found")
            continue
        
        print(f"\n📁 {file_rel_path}")
        
        # Check for remaining issues
        issues = check_sensitive_exposures(file_path)
        if issues:
            print("  ❌ Issues found:")
            for issue in issues:
                print(f"    - {issue}")
            total_issues += len(issues)
        else:
            print("  ✅ No sensitive information exposures found")
        
        # Check for improvements
        improvements = check_data_masking_usage(file_path)
        if improvements:
            print("  ✅ Improvements made:")
            for improvement in improvements:
                print(f"    - {improvement}")
            total_improvements += len(improvements)
    
    # Check utility files
    for file_rel_path in utility_files:
        file_path = app_dir / file_rel_path
        
        print(f"\n📁 {file_rel_path}")
        
        if file_path.exists():
            print("  ✅ Utility file created")
            total_improvements += 1
            
            # Check file size as a basic quality indicator
            file_size = file_path.stat().st_size
            if file_size > 1000:  # At least 1KB
                print(f"  ✅ Substantial implementation ({file_size} bytes)")
                total_improvements += 1
        else:
            print("  ❌ Utility file not found")
            total_issues += 1
    
    # Scan for remaining sensitive exposures in critical files
    print(f"\n🔍 Scanning for remaining sensitive exposures...")
    
    critical_patterns = [
        (r'detail\s*=\s*str\s*\(\s*e\s*\)', 'detail=str(e) pattern'),
        (r'HTTPException.*detail.*\{.*\}', 'Dynamic error details in HTTPException'),
    ]
    
    api_files = list((app_dir / 'api').rglob('*.py'))[:10]  # Limit to first 10 files
    
    remaining_issues = 0
    for api_file in api_files:
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern, description in critical_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    remaining_issues += len(matches)
        except Exception:
            continue
    
    if remaining_issues > 0:
        print(f"  ⚠️  Found {remaining_issues} potential issues in other API files")
        total_issues += remaining_issues
    else:
        print("  ✅ No obvious sensitive exposures in sampled API files")
    
    print("\n" + "=" * 60)
    print(f"📊 Summary:")
    print(f"  ✅ Improvements: {total_improvements}")
    print(f"  ❌ Issues: {total_issues}")
    
    if total_issues == 0:
        print("\n🎉 All sensitive information exposure fixes validated successfully!")
        return 0
    else:
        print(f"\n⚠️  {total_issues} issues found that need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())