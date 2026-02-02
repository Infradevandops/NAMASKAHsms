#!/usr/bin/env python3
"""
import datetime
import logging
import subprocess
from pathlib import Path
from app.core.config import get_settings

Automated Database Backup Script
Backs up PostgreSQL database with rotation and verification
"""


# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def backup_database():

    """Create database backup with timestamp"""
    settings = get_settings()

    # Create backup directory
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"namaskah_backup_{timestamp}.sql"

try:
        # Run pg_dump
        cmd = [
            "pg_dump",
            settings.database_url,
            "-",
            str(backup_file),
            "--verbose",
            "--no-password",
        ]

        logger.info(f"Starting backup to {backup_file}")
        result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
            logger.info(f"Backup completed successfully: {backup_file}")

            # Verify backup file exists and has content
if backup_file.exists() and backup_file.stat().st_size > 0:
                logger.info(f"Backup verified: {backup_file.stat().st_size} bytes")
                cleanup_old_backups(backup_dir)
                return str(backup_file)
else:
                logger.error("Backup file is empty or missing")
                return None
else:
            logger.error(f"Backup failed: {result.stderr}")
            return None

except Exception as e:
        logger.error(f"Backup error: {e}")
        return None


def cleanup_old_backups(backup_dir: Path, keep_days: int = 7):

    """Remove backups older than keep_days"""
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)

for backup_file in backup_dir.glob("namaskah_backup_*.sql"):
if backup_file.stat().st_mtime < cutoff_date.timestamp():
            logger.info(f"Removing old backup: {backup_file}")
            backup_file.unlink()


if __name__ == "__main__":
    backup_file = backup_database()
if backup_file:
        print(f"SUCCESS: Backup created at {backup_file}")
else:
        print("FAILED: Backup creation failed")
        exit(1)