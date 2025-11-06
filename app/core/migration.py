"""Database migration utilities."""

import logging
import os
import subprocess
from typing import Optional

from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine

logger = logging.getLogger(__name__)


class MigrationManager:
    """Database migration management."""

    def __init__(self):
        self.settings = get_settings()

    @staticmethod
    def run_migrations() -> bool:
        """Run pending migrations."""
        try:
            import shutil

            # Verify alembic is available
            alembic_path = shutil.which("alembic")
            if not alembic_path:
                print("Alembic not found in PATH")
                return False

            result = subprocess.run(
                [alembic_path, "upgrade", "head"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                timeout=300,  # 5 minute timeout
                check=False,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            migration_logger = logging.getLogger(__name__)
            migration_logger.error("Migration timed out")
            return False
        except Exception as e:
            migration_logger = logging.getLogger(__name__)
            migration_logger.error("Migration failed: %s", e)
            return False

    @staticmethod
    def create_migration(message: str) -> bool:
        """Create new migration."""
        try:
            import shutil

            # Verify alembic is available
            alembic_path = shutil.which("alembic")
            if not alembic_path:
                print("Alembic not found in PATH")
                return False

            # Sanitize message to prevent injection
            safe_message = "".join(c for c in message if c.isalnum() or c in " _-")[
                :100
            ]

            result = subprocess.run(
                [alembic_path, "revision", "--autogenerate", "-m", safe_message],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                timeout=60,
                check=False,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Migration creation timed out")
            return False
        except Exception as e:
            logger.error("Migration creation failed: %s", e)
            return False

    @staticmethod
    def rollback_migration(revision: Optional[str] = None) -> bool:
        """Rollback to specific revision or previous."""
        try:
            import shutil

            # Verify alembic is available
            alembic_path = shutil.which("alembic")
            if not alembic_path:
                print("Alembic not found in PATH")
                return False

            # Sanitize revision input
            target = revision or "-1"
            if revision and not revision.replace("-", "").replace("_", "").isalnum():
                print("Invalid revision format")
                return False

            result = subprocess.run(
                [alembic_path, "downgrade", target],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                timeout=300,
                check=False,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Rollback timed out")
            return False
        except Exception as e:
            logger.error("Rollback failed: %s", e)
            return False

    @staticmethod
    def get_current_revision() -> Optional[str]:
        """Get current database revision."""
        try:
            import shutil

            # Verify alembic is available
            alembic_path = shutil.which("alembic")
            if not alembic_path:
                return None

            result = subprocess.run(
                [alembic_path, "current"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except subprocess.TimeoutExpired:
            return None
        except (subprocess.SubprocessError, OSError, ValueError):
            return None

    def backup_database(self) -> bool:
        """Create database backup (SQLite only)."""
        if "sqlite" not in self.settings.database_url:
            logger.warning("Backup only supported for SQLite")
            return False

        try:
            import shutil
            from datetime import datetime

            db_path = self.settings.database_url.replace("sqlite:///", "")
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            logger.info("Database backed up to: %s", backup_path)
            return True
        except Exception as e:
            logger.error("Backup failed: %s", e)
            return False

    @staticmethod
    def validate_schema() -> bool:
        """Validate database schema integrity."""
        try:
            with engine.connect() as conn:
                # Basic connectivity test
                conn.execute(text("SELECT 1"))

                # Check if all expected tables exist
                expected_tables = [
                    "users",
                    "verifications",
                    "transactions",
                    "api_keys",
                    "webhooks",
                    "service_status",
                    "support_tickets",
                ]

                for table in expected_tables:
                    result = conn.execute(
                        text(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                        ),
                        {"table_name": table},
                    )
                    if not result.fetchone():
                        logger.error("Missing table: %s", table)
                        return False

                return True
        except Exception as e:
            logger.error("Schema validation failed: %s", e)
            return False


# Global migration manager instance
migration_manager = MigrationManager()


def run_startup_migrations():
    """Run migrations on application startup."""
    try:
        if migration_manager.run_migrations():
            logger.info("Database migrations completed")
        else:
            logger.warning("Database migrations failed")
    except Exception as e:
        logger.error("Migration startup error: %s", e)
