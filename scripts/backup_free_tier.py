#!/usr/bin/env python3
"""
Free Tier Backup Strategy for Namaskah
Uses Google Drive (15GB free) + OneDrive (5GB free)
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "")
LOCAL_BACKUP_DIR = Path("backups")
KEEP_LOCAL_DAYS = 7  # Keep 7 days locally

# Free tier remotes
GDRIVE_REMOTE = "gdrive"  # 15GB free
ONEDRIVE_REMOTE = "onedrive"  # 5GB free
MEGA_REMOTE = "mega"  # 20GB free


def backup_database() -> Path:
    """Backup PostgreSQL database."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"namaskah_backup_{timestamp}.sql.gz"
    local_path = LOCAL_BACKUP_DIR / filename

    logger.info(f"Backing up database → {local_path}")

    # Parse DATABASE_URL
    import urllib.parse

    p = urllib.parse.urlparse(DATABASE_URL)
    env = {
        **os.environ,
        "PGHOST": p.hostname or "",
        "PGPORT": str(p.port or 5432),
        "PGUSER": p.username or "",
        "PGPASSWORD": p.password or "",
        "PGDATABASE": (p.path or "").lstrip("/"),
    }

    # Dump and compress
    dump = subprocess.Popen(
        ["pg_dump", "--no-password", "--format=plain"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    gzip = subprocess.Popen(
        ["gzip", "-c"],
        stdin=dump.stdout,
        stdout=open(local_path, "wb"),
        stderr=subprocess.PIPE,
    )
    dump.stdout.close()
    gzip.communicate()
    dump.wait()

    if dump.returncode != 0:
        logger.error(f"pg_dump failed: {dump.stderr.read().decode()}")
        sys.exit(1)

    size = local_path.stat().st_size
    logger.info(
        f"✅ Database backup complete: {size:,} bytes ({size/1024/1024:.2f} MB)"
    )
    return local_path


def sync_to_gdrive(local_path: Path):
    """Sync to Google Drive (15GB free)."""
    logger.info("Syncing to Google Drive (15GB free)...")

    try:
        subprocess.run(
            [
                "rclone",
                "copy",
                str(local_path),
                f"{GDRIVE_REMOTE}:Namaskah-Backups/database/",
                "--progress",
            ],
            check=True,
        )
        logger.info("✅ Synced to Google Drive")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Google Drive sync failed: {e}")


def sync_to_onedrive(local_path: Path):
    """Sync to OneDrive (5GB free) - Weekly only."""
    day_of_week = datetime.datetime.utcnow().weekday()
    if day_of_week != 6:  # Only on Sunday
        logger.info("⏭️  Skipping OneDrive (weekly backup on Sundays)")
        return

    logger.info("Syncing to OneDrive (5GB free)...")

    try:
        subprocess.run(
            [
                "rclone",
                "copy",
                str(local_path),
                f"{ONEDRIVE_REMOTE}:Namaskah-Backups/database/",
                "--progress",
            ],
            check=True,
        )
        logger.info("✅ Synced to OneDrive")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ OneDrive sync failed: {e}")


def sync_to_mega(local_path: Path):
    """Sync to MEGA (20GB free) - Monthly only."""
    day_of_month = datetime.datetime.utcnow().day
    if day_of_month != 1:  # Only on 1st of month
        logger.info("⏭️  Skipping MEGA (monthly backup on 1st)")
        return

    logger.info("Syncing to MEGA (20GB free)...")

    try:
        subprocess.run(
            [
                "rclone",
                "copy",
                str(local_path),
                f"{MEGA_REMOTE}:Namaskah-Backups/database/",
                "--progress",
            ],
            check=True,
        )
        logger.info("✅ Synced to MEGA")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ MEGA sync failed: {e}")


def cleanup_old_backups():
    """Remove local backups older than KEEP_LOCAL_DAYS."""
    cutoff = datetime.datetime.utcnow().timestamp() - (KEEP_LOCAL_DAYS * 86400)
    removed = 0

    for f in LOCAL_BACKUP_DIR.glob("namaskah_backup_*.sql.gz"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
            logger.info(f"🗑️  Removed old backup: {f.name}")

    if removed == 0:
        logger.info("✅ No old backups to remove")


def cleanup_cloud_backups():
    """Keep only last 30 backups in cloud (free tier space management)."""
    logger.info("Cleaning up old cloud backups...")

    # Google Drive: Keep last 30 backups
    try:
        result = subprocess.run(
            [
                "rclone",
                "lsf",
                f"{GDRIVE_REMOTE}:Namaskah-Backups/database/",
                "--files-only",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        files = sorted(result.stdout.strip().split("\n"))
        if len(files) > 30:
            old_files = files[:-30]  # Keep last 30
            for old_file in old_files:
                subprocess.run(
                    [
                        "rclone",
                        "delete",
                        f"{GDRIVE_REMOTE}:Namaskah-Backups/database/{old_file}",
                    ],
                    check=True,
                )
                logger.info(f"🗑️  Removed from Google Drive: {old_file}")
    except subprocess.CalledProcessError:
        logger.warning("⚠️  Could not cleanup Google Drive")


def backup_all():
    """Full backup workflow."""
    logger.info("🚀 Starting free tier backup...")

    # 1. Backup database locally
    db_backup = backup_database()

    # 2. Sync to Google Drive (daily)
    sync_to_gdrive(db_backup)

    # 3. Sync to OneDrive (weekly)
    sync_to_onedrive(db_backup)

    # 4. Sync to MEGA (monthly)
    sync_to_mega(db_backup)

    # 5. Cleanup old local backups
    cleanup_old_backups()

    # 6. Cleanup old cloud backups (space management)
    cleanup_cloud_backups()

    logger.info("✅ Backup complete!")
    logger.info(f"📊 Storage used:")
    logger.info(f"   - Google Drive: Daily backups (last 30 days)")
    logger.info(f"   - OneDrive: Weekly backups")
    logger.info(f"   - MEGA: Monthly archives")


def list_backups():
    """List available backups from all remotes."""
    logger.info("📋 Available backups:\n")

    # Google Drive
    logger.info("Google Drive (15GB free):")
    subprocess.run(
        [
            "rclone",
            "ls",
            f"{GDRIVE_REMOTE}:Namaskah-Backups/database/",
        ]
    )

    # OneDrive
    logger.info("\nOneDrive (5GB free):")
    subprocess.run(
        [
            "rclone",
            "ls",
            f"{ONEDRIVE_REMOTE}:Namaskah-Backups/database/",
        ]
    )

    # MEGA
    logger.info("\nMEGA (20GB free):")
    subprocess.run(
        [
            "rclone",
            "ls",
            f"{MEGA_REMOTE}:Namaskah-Backups/database/",
        ]
    )


def restore_database(source: str):
    """Restore database from backup."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    # Download from cloud if needed
    if ":" in source:  # Remote path
        local_path = LOCAL_BACKUP_DIR / "restore_temp.sql.gz"
        LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {source}...")
        subprocess.run(
            [
                "rclone",
                "copy",
                source,
                str(LOCAL_BACKUP_DIR),
                "--progress",
            ],
            check=True,
        )

        # Find the downloaded file
        local_path = max(
            LOCAL_BACKUP_DIR.glob("namaskah_backup_*.sql.gz"),
            key=lambda p: p.stat().st_mtime,
        )
    else:
        local_path = Path(source)

    if not local_path.exists():
        logger.error(f"Backup file not found: {local_path}")
        sys.exit(1)

    logger.warning(
        f"⚠️  Restoring from {local_path} - this will OVERWRITE the database!"
    )
    input("Press Enter to continue or Ctrl+C to cancel...")

    # Parse DATABASE_URL
    import urllib.parse

    p = urllib.parse.urlparse(DATABASE_URL)
    env = {
        **os.environ,
        "PGHOST": p.hostname or "",
        "PGPORT": str(p.port or 5432),
        "PGUSER": p.username or "",
        "PGPASSWORD": p.password or "",
        "PGDATABASE": (p.path or "").lstrip("/"),
    }

    # Restore
    gunzip = subprocess.Popen(
        ["gunzip", "-c", str(local_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    psql = subprocess.Popen(
        ["psql", "--no-password"],
        stdin=gunzip.stdout,
        stderr=subprocess.PIPE,
        env=env,
    )
    gunzip.stdout.close()
    _, psql_err = psql.communicate()
    gunzip.wait()

    if psql.returncode != 0:
        logger.error(f"Restore failed: {psql_err.decode()}")
        sys.exit(1)

    logger.info("✅ Database restored successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Free tier backup for Namaskah")
    parser.add_argument(
        "--restore",
        metavar="SOURCE",
        help="Restore from backup (e.g., gdrive:Namaskah-Backups/database/file.sql.gz)",
    )
    parser.add_argument("--list", action="store_true", help="List available backups")
    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.restore:
        restore_database(args.restore)
    else:
        backup_all()
