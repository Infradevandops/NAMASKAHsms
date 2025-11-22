#!/usr/bin/env python3
"""
Remove unused imports from Python files
Uses autoflake to automatically remove unused imports
"""

import subprocess
import sys
from pathlib import Path

def remove_unused_imports():
    """Remove unused imports from all Python files"""
    
    # Install autoflake if not available
    try:
        subprocess.run(["autoflake", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing autoflake...")
        subprocess.run([sys.executable, "-m", "pip", "install", "autoflake"], check=True)
    
    # Find all Python files
    python_files = []
    for pattern in ["app/**/*.py", "scripts/*.py", "*.py"]:
        python_files.extend(Path(".").glob(pattern))
    
    # Remove duplicates and filter out __pycache__
    python_files = [f for f in set(python_files) if "__pycache__" not in str(f)]
    
    print(f"Found {len(python_files)} Python files")
    
    # Run autoflake on each file
    for file_path in python_files:
        try:
            cmd = [
                "autoflake",
                "--remove-all-unused-imports",
                "--remove-unused-variables", 
                "--in-place",
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Cleaned: {file_path}")
            else:
                print(f"❌ Error cleaning {file_path}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Exception cleaning {file_path}: {e}")
    
    print("✅ Unused import cleanup completed")

if __name__ == "__main__":
    remove_unused_imports()