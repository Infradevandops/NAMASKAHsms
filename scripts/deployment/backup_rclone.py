#!/usr/bin/env python3
"""
Rclone-based backup script for Vrenum
Supports multiple cloud providers via rclone
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
RCLONE_REMOTE = os.environ.get("RCLONE_REMOTE", "vrenum-backup")
BACKUP_BUCKET = os.environ.get("BACKUP_BUCKET", "vrenum-backups")
LOCAL_BACKUP_DIR = Path(os.environ.get("BACKUP_LOCAL_DIR", "backups"))
KEEP_DAYS = int(os.environ.get("BACKUP_KEEP_DAYS", "30"))

# Backup paths
BACKUP_PATHS = {
    "database": LOCAL_BACKUP_DIR,
    "uploads": Path("uploads/kyc"),
    "logs": Path("logs"),
    "config": Path("config"),
}


def check_rclone():
    """Verify rclone is installed and configured."""
    try:
        result = subprocess.run(
            ["rclone", "version"], capture_output=True, text=True, check=True
        )
        logger.info(f"Rclone version: {result.stdout.split()[1]}")
    except FileNotFoundError:
        logger.error(
            "Rclone not installed. Install: curl https://rclone.org/install.sh | bash"
        )
        sys.exit(1)
    except subprocess.CalledProcessError:
        logger.error("Rclone not working properly")
        sys.exit(1)

    # Check remote exists
    try:
        subprocess.run(
            ["rclone", "lsd", f"{RCLONE_REMOTE}:"],
            capture_output=True,
            check=True,
        )
        logger.info(f"Remote '{RCLONE_REMOTE}' configured")
    except subprocess.CalledProcessError:
        logger.error(f"Remote '{RCLONE_REMOTE}' not configured. Run: rclone config")
        sys.exit(1)


def backup_database() -> Path:
    """Backup PostgreSQL database."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"vrenum_backup_{timestamp}.sql.gz"
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
    logger.info(f"Database backup complete: {size:,} bytes")
    return local_path


def sync_to_cloud(local_path: Path, remote_path: str, sync_type: str = "copy"):
    """Sync files to cloud using rclone."""
    remote_full = f"{RCLONE_REMOTE}:{BACKUP_BUCKET}/{remote_path}"

    logger.info(f"Syncing {local_path} → {remote_full}")

    cmd = [
        "rclone",
        sync_type,  # copy, sync, or move
        str(local_path),
        remote_full,
        "--progress",
        "--stats",
        "1s",
        "--transfers",
        "4",
        "--checkers",
        "8",
    ]

    # Add encryption if configured
    if os.environ.get("RCLONE_ENCRYPT") == "true":
        cmd.extend(["--crypt-password", os.environ.get("RCLONE_PASSWORD", "")])

    try:
        subprocess.run(cmd, check=True)
        logger.info(f"✅ Synced to {remote_full}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Sync failed: {e}")
        sys.exit(1)


def backup_all():
    """Backup all components."""
    check_rclone()

    # 1. Database
    db_backup = backup_database()
    sync_to_cloud(db_backup, "database/")

    # 2. User uploads (KYC)
    if BACKUP_PATHS["uploads"].exists():
        logger.info("Backing up user uploads...")
        sync_to_cloud(BACKUP_PATHS["uploads"], "uploads/", sync_type="sync")

    # 3. Logs (archive old ones)
    if BACKUP_PATHS["logs"].exists():
        logger.info("Archiving logs...")
        month = datetime.datetime.utcnow().strftime("%Y%m")
        sync_to_cloud(BACKUP_PATHS["logs"], f"logs/{month}/", sync_type="copy")

    # 4. Config files
    if BACKUP_PATHS["config"].exists():
        logger.info("Backing up config...")
        sync_to_cloud(BACKUP_PATHS["config"], "config/", sync_type="sync")

    # 5. Cleanup old local backups
    cleanup_old_backups()

    logger.info("✅ Full backup complete")


def cleanup_old_backups():
    """Remove local backups older than KEEP_DAYS."""
    cutoff = datetime.datetime.utcnow().timestamp() - (KEEP_DAYS * 86400)
    for f in LOCAL_BACKUP_DIR.glob("vrenum_backup_*.sql.gz"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            logger.info(f"Removed old backup: {f.name}")


def restore_database(source: str):
    """Restore database from backup."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    check_rclone()

    # Download from cloud if needed
    if source.startswith(f"{RCLONE_REMOTE}:"):
        local_path = LOCAL_BACKUP_DIR / "restore_temp.sql.gz"
        LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {source}...")
        subprocess.run(
            ["rclone", "copy", source, str(LOCAL_BACKUP_DIR), "--progress"],
            check=True,
        )
        source = str(local_path)

    local_path = Path(source)
    if not local_path.exists():
        logger.error(f"Backup file not found: {local_path}")
        sys.exit(1)

    logger.warning(
        f"⚠️  Restoring from {local_path} - this will OVERWRITE the database!"
    )

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


def list_backups():
    """List available backups."""
    check_rclone()

    logger.info("Available backups:")
    subprocess.run(
        [
            "rclone",
            "ls",
            f"{RCLONE_REMOTE}:{BACKUP_BUCKET}/database/",
            "--max-depth",
            "1",
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rclone-based backup for Vrenum")
    parser.add_argument("--restore", metavar="SOURCE", help="Restore from backup")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--db-only", action="store_true", help="Backup database only")
    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.restore:
        restore_database(args.restore)
    elif args.db_only:
        check_rclone()
        db_backup = backup_database()
        sync_to_cloud(db_backup, "database/")
    else:
        backup_all()
