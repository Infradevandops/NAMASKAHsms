#!/usr/bin/env python3
"""
Database backup script — dumps PostgreSQL to S3 (or local fallback).
Usage:
  python scripts/backup_database.py            # backup
  python scripts/backup_database.py --restore <s3-key-or-local-file>
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

DATABASE_URL = os.environ.get("DATABASE_URL", "")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("BACKUP_S3_BUCKET", "")
LOCAL_BACKUP_DIR = Path(os.environ.get("BACKUP_LOCAL_DIR", "backups"))
KEEP_DAYS = int(os.environ.get("BACKUP_KEEP_DAYS", "30"))


def _pg_url_to_env(database_url: str) -> dict:
    """Convert DATABASE_URL to pg env vars for pg_dump/pg_restore."""
    import urllib.parse

    p = urllib.parse.urlparse(database_url)
    return {
        **os.environ,
        "PGHOST": p.hostname or "",
        "PGPORT": str(p.port or 5432),
        "PGUSER": p.username or "",
        "PGPASSWORD": p.password or "",
        "PGDATABASE": (p.path or "").lstrip("/"),
    }


def backup() -> str:
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"namaskah_backup_{timestamp}.sql.gz"
    local_path = LOCAL_BACKUP_DIR / filename

    logger.info(f"Starting backup → {local_path}")
    env = _pg_url_to_env(DATABASE_URL)

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
    logger.info(f"Dump complete: {size:,} bytes")

    if S3_BUCKET:
        s3_key = f"db-backups/{filename}"
        _upload_s3(local_path, s3_key)
        logger.info(f"Uploaded to s3://{S3_BUCKET}/{s3_key}")
    else:
        logger.warning("BACKUP_S3_BUCKET not set — backup stored locally only")

    _cleanup_local(LOCAL_BACKUP_DIR)
    return str(local_path)


def restore(source: str):
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        sys.exit(1)

    local_path = Path(source)

    if source.startswith("s3://") or (S3_BUCKET and not local_path.exists()):
        s3_key = (
            source.replace(f"s3://{S3_BUCKET}/", "")
            if source.startswith("s3://")
            else source
        )
        local_path = LOCAL_BACKUP_DIR / Path(s3_key).name
        LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        _download_s3(s3_key, local_path)

    if not local_path.exists():
        logger.error(f"Backup file not found: {local_path}")
        sys.exit(1)

    logger.warning(f"Restoring from {local_path} — this will overwrite the database!")
    env = _pg_url_to_env(DATABASE_URL)

    gunzip = subprocess.Popen(
        ["gunzip", "-c", str(local_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    psql = subprocess.Popen(
        ["psql", "--no-password"], stdin=gunzip.stdout, stderr=subprocess.PIPE, env=env
    )
    gunzip.stdout.close()
    _, psql_err = psql.communicate()
    gunzip.wait()

    if psql.returncode != 0:
        logger.error(f"Restore failed: {psql_err.decode()}")
        sys.exit(1)

    logger.info("Restore complete")


def _upload_s3(local_path: Path, s3_key: str):
    import boto3

    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY or None,
    )
    s3.upload_file(str(local_path), S3_BUCKET, s3_key)


def _download_s3(s3_key: str, local_path: Path):
    import boto3

    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY or None,
    )
    logger.info(f"Downloading s3://{S3_BUCKET}/{s3_key}")
    s3.download_file(S3_BUCKET, s3_key, str(local_path))


def _cleanup_local(backup_dir: Path):
    cutoff = datetime.datetime.utcnow().timestamp() - (KEEP_DAYS * 86400)
    for f in backup_dir.glob("namaskah_backup_*.sql.gz"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            logger.info(f"Removed old backup: {f.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--restore", metavar="SOURCE", help="Restore from file or s3://bucket/key"
    )
    args = parser.parse_args()

    if args.restore:
        restore(args.restore)
    else:
        path = backup()
        print(f"SUCCESS: {path}")
