#!/usr/bin/env python3
"""Fix remaining syntax and import issues."""

import os

def fix_file(file_path, fixes):
    """Apply fixes to a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original = content
        for old, new in fixes:
            content = content.replace(old, new)
        
        if content != original:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    return False

def main():
    """Fix critical issues."""
    fixes = {
        "app/api/admin/admin.py": [
            ('+ f"<p>{sanitize_email_content(response_text)}</p><p>If you need further assistance, please reply to this email.</p><p>Best regards,<br>Namaskah Support Team</p>"<p>Best regards,<br>Namaskah Support Team</p>"",',
             '+ f"<p>{sanitize_email_content(response_text)}</p><p>If you need further assistance, please reply to this email.</p><p>Best regards,<br>Namaskah Support Team</p>",')
        ],
        
        "app/api/admin/support.py": [
            ('Google, Facebook, "', 'Google, Facebook, and more."')
        ],
        
        "app/api/verification/verification.py": [
            ('sort_by: Optional[str] = Query("created_at", description="Sort field: created_at,',
             'sort_by: Optional[str] = Query("created_at", description="Sort field: created_at"')
        ],
        
        "app/services/reseller_service.py": [
            ('    SubAccountTransaction, CreditAllocation, BulkOperation',
             'SubAccountTransaction, CreditAllocation, BulkOperation')
        ],
        
        "app/services/whitelabel_enhanced.py": [
            ('WhiteLabelTheme, WhiteLabelAsset',
             'from app.models.whitelabel_enhanced import WhiteLabelTheme, WhiteLabelAsset')
        ],
        
        "app/tests/test_provider_consolidation.py": [
            ('    ProviderHealth, ProviderStatus',
             'ProviderHealth, ProviderStatus')
        ],
        
        "app/tests/test_provider_integration.py": [
            ('UnifiedSMSProvider, ProviderStatus',
             'from app.services.provider_system import UnifiedSMSProvider, ProviderStatus')
        ],
        
        "app/tests/test_exception_handling.py": [
            ("'Message': 'Secrets Manager can\\\\'t find the specified secret.'",
             "'Message': 'Secrets Manager cannot find the specified secret.'")
        ]
    }
    
    fixed = 0
    for file_path, file_fixes in fixes.items():
        if os.path.exists(file_path):
            if fix_file(file_path, file_fixes):
                fixed += 1
    
    print(f"Fixed {fixed} files")

if __name__ == "__main__":
    main()