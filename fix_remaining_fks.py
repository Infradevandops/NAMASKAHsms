#!/usr/bin/env python3
"""Fix all remaining String foreign keys to UUID."""

import re
from pathlib import Path

files_to_fix = [
    "app/models/whitelabel_enhanced.py",
    "app/models/reseller.py",
    "app/models/sms_message.py",
    "app/models/sms_forwarding.py",
]

for file_path in files_to_fix:
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
    
    # Replace all String foreign keys with UUID (including String(36))
    content = re.sub(
        r'Column\(String(?:\(\d+\))?, ForeignKey\(',
        'Column(UUID(as_uuid=False), ForeignKey(',
        content
    )
    
    path.write_text(content)
    print(f"✅ Fixed {file_path}")

print("\n✅ All foreign keys fixed")
