#!/usr/bin/env python3
"""Fix all foreign key references to use UUID type."""

import re
from pathlib import Path

# Files to update
model_files = [
    "app/models/whitelabel_enhanced.py",
    "app/models/commission.py",
    "app/models/reseller.py",
    "app/models/pricing_template.py",
    "app/models/notification.py",
    "app/models/sms_message.py",
    "app/models/activity.py",
    "app/models/sms_forwarding.py",
    "app/models/notification_preference.py",
    "app/models/device_token.py",
    "app/models/api_key.py",
    "app/models/balance_transaction.py",
    "app/models/enterprise.py",
    "app/models/notification_analytics.py",
    "app/models/user_quota.py",
    "app/models/refund.py",
]

for file_path in model_files:
    path = Path(file_path)
    if not path.exists():
        continue
    
    content = path.read_text()
    
    # Add UUID import if not present
    if "from sqlalchemy.dialects.postgresql import UUID" not in content:
        content = content.replace(
            "from sqlalchemy import",
            "from sqlalchemy.dialects.postgresql import UUID\nfrom sqlalchemy import"
        )
    
    # Replace String foreign keys with UUID
    content = re.sub(
        r'Column\(String(?:\(\d+\))?, ForeignKey\("users\.id"',
        'Column(UUID(as_uuid=False), ForeignKey("users.id"',
        content
    )
    
    path.write_text(content)
    print(f"✅ Fixed {file_path}")

print("\n✅ All foreign keys updated to UUID type")
