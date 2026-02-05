#!/usr/bin/env python3
"""Fix all schema files with indentation issues."""

import os
import subprocess

def fix_schema_files():
    """Fix all schema files using autopep8."""
    schema_files = [
        "app/schemas/auth.py",
        "app/schemas/payment.py", 
        "app/schemas/validators.py",
        "app/schemas/verification.py",
        "app/schemas/analytics.py",
        "app/schemas/system.py"
    ]
    
    print("🔧 COMPREHENSIVE SCHEMA FIX")
    print("=" * 50)
    
    for file_path in schema_files:
        if os.path.exists(file_path):
            print(f"🔧 Fixing {file_path}")
            try:
                # Run autopep8 with aggressive fixes
                result = subprocess.run([
                    "python3", "-m", "autopep8",
                    "--in-place",
                    "--aggressive",
                    "--aggressive", 
                    "--max-line-length=100",
                    file_path
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Fixed {file_path}")
                else:
                    print(f"⚠️  Warning for {file_path}: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n✅ Schema fix complete!")

if __name__ == '__main__':
    fix_schema_files()
