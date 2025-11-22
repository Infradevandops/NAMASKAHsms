#!/usr/bin/env python3
"""Run database migrations on Render."""
import subprocess
import sys
import os
from pathlib import Path

def run_migrations():
    """Execute alembic migrations."""
    try:
        print("Running database migrations...")
        alembic_path = Path("alembic")
        if not alembic_path.exists():
            print("Error: alembic directory not found")
            return False
        
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            print(f"Migration failed with code {result.returncode}")
            return False
        
        print("Migrations completed successfully")
        return True
    except subprocess.TimeoutExpired:
        print("Error: Migration process timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
