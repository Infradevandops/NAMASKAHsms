#!/usr/bin/env python3
"""Fix critical syntax errors preventing tests from running."""

import os
import re

def fix_file_syntax_errors(file_path, fixes):
    """Apply syntax fixes to a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_text, new_text in fixes:
            content = content.replace(old_text, new_text)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False
    
    return False

def main():
    """Fix critical syntax errors."""
    print("🔧 Fixing critical syntax errors...")
    
    # Define fixes for specific files
    fixes = {
        "app/services/reseller_service.py": [
            ("from app.models.reseller import ResellerAccount, SubAccount,", 
             "from app.models.reseller import ResellerAccount, SubAccount")
        ],
        
        "app/services/whitelabel_enhanced.py": [
            ("    WhiteLabelTheme, WhiteLabelAsset", 
             "WhiteLabelTheme, WhiteLabelAsset")
        ],
        
        "app/tests/test_provider_consolidation.py": [
            ("from app.services.provider_system import SMSProvider, ProviderManager,",
             "from app.services.provider_system import SMSProvider, ProviderManager")
        ],
        
        "app/tests/test_provider_integration.py": [
            ("    UnifiedSMSProvider, ProviderStatus",
             "UnifiedSMSProvider, ProviderStatus")
        ],
        
        "app/api/verification/verification.py": [
            ("    sanitize_service_name, safe_log_format",
             "sanitize_service_name, safe_log_format")
        ]
    }
    
    fixed_count = 0
    
    for file_path, file_fixes in fixes.items():
        if os.path.exists(file_path):
            if fix_file_syntax_errors(file_path, file_fixes):
                fixed_count += 1
        else:
            print(f"File not found: {file_path}")
    
    # Fix f-string issues in admin.py
    admin_file = "app/api/admin/admin.py"
    if os.path.exists(admin_file):
        try:
            with open(admin_file, 'r') as f:
                content = f.read()
            
            # Fix malformed f-string
            content = re.sub(
                r'\+ ff""<p>\{sanitize_email_content\(response_text\)\}</p>""<p>.*?</p>""',
                '+ f"<p>{sanitize_email_content(response_text)}</p><p>If you need further assistance, please reply to this email.</p><p>Best regards,<br>Namaskah Support Team</p>"',
                content,
                flags=re.DOTALL
            )
            
            with open(admin_file, 'w') as f:
                f.write(content)
            print(f"Fixed f-string in: {admin_file}")
            fixed_count += 1
            
        except Exception as e:
            print(f"Error fixing {admin_file}: {e}")
    
    # Fix string literal in support.py
    support_file = "app/api/admin/support.py"
    if os.path.exists(support_file):
        try:
            with open(support_file, 'r') as f:
                content = f.read()
            
            # Fix incomplete string literal
            content = content.replace(
                '"We support 1,800+ services including Telegram, WhatsApp,',
                '"We support 1,800+ services including Telegram, WhatsApp, and more."'
            )
            
            with open(support_file, 'w') as f:
                f.write(content)
            print(f"Fixed string literal in: {support_file}")
            fixed_count += 1
            
        except Exception as e:
            print(f"Error fixing {support_file}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} files with syntax errors")

if __name__ == "__main__":
    main()