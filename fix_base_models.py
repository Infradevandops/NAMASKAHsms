#!/usr/bin/env python3
"""Convert all models from Base to BaseModel."""

from pathlib import Path

files = [
    "app/models/pricing_template.py",
    "app/models/sms_message.py",
    "app/models/sms_forwarding.py",
    "app/models/api_key.py",
]

for file_path in files:
    path = Path(file_path)
    if not path.exists():
        continue
    
    content = path.read_text()
    
    # Replace Base import with BaseModel
    content = content.replace("from .base import Base", "from .base import BaseModel")
    content = content.replace("from app.models.base import Base", "from app.models.base import BaseModel")
    
    # Replace class inheritance
    content = content.replace("(Base):", "(BaseModel):")
    
    # Remove manual id column definitions (BaseModel provides it)
    lines = content.split('\n')
    new_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        if 'id = Column(String' in line and 'primary_key=True' in line:
            # Skip this line - BaseModel provides id
            continue
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    path.write_text(content)
    print(f"✅ Fixed {file_path}")

print("\n✅ All models converted to BaseModel")
