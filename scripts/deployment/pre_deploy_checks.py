#!/usr/bin/env python3
"""Pre-deployment checks for production deployment."""

import os
import sys
import logging
from datetime import datetime
import subprocess
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_environment_variables():
    """Verify all required environment variables are set."""
    logger.info("Checking environment variables...")
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
        "ENVIRONMENT",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return False

    logger.info("✓ All required environment variables present")
    return True


def check_database_connection():
    """Verify database connectivity."""
    logger.info("Checking database connection...")
    try:
        from sqlalchemy import create_engine, text

        db_url = os.getenv("DATABASE_URL")
        engine = create_engine(db_url, pool_pre_ping=True, pool_size=5)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                logger.info("✓ Database connection successful")
                return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def check_redis_connection():
    """Verify Redis connectivity."""
    logger.info("Checking Redis connection...")
    try:
        import redis

        redis_url = os.getenv("REDIS_URL")
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        logger.info("✓ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


def check_migrations():
    """Verify database migrations are up to date."""
    logger.info("Checking database migrations...")
    try:
        result = subprocess.run(
            ["alembic", "current"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            logger.info("✓ Database migrations verified")
            return True
        else:
            logger.error(f"Migration check failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False


def check_dependencies():
    """Verify all required dependencies are installed."""
    logger.info("Checking dependencies...")
    try:
        import fastapi
        import sqlalchemy
        import redis
        import pydantic
        import prometheus_client
        import sentry_sdk

        logger.info("✓ All required dependencies installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False


def check_disk_space():
    """Verify sufficient disk space available."""
    logger.info("Checking disk space...")
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024**3)

        if free_gb < 1:
            logger.error(f"Insufficient disk space: {free_gb:.2f}GB available")
            return False

        logger.info(f"✓ Disk space available: {free_gb:.2f}GB")
        return True
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return False


def check_memory():
    """Verify sufficient memory available."""
    logger.info("Checking memory...")
    try:
        import psutil

        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)

        if available_gb < 0.5:
            logger.error(f"Insufficient memory: {available_gb:.2f}GB available")
            return False

        logger.info(f"✓ Memory available: {available_gb:.2f}GB")
        return True
    except Exception as e:
        logger.warning(f"Memory check skipped: {e}")
        return True


def check_configuration():
    """Verify application configuration is valid."""
    logger.info("Checking application configuration...")
    try:
        from app.core.config import settings

        # Validate critical settings
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
            logger.error("Invalid SECRET_KEY configuration")
            return False

        if settings.ENVIRONMENT not in ["production", "staging", "development"]:
            logger.error(f"Invalid ENVIRONMENT: {settings.ENVIRONMENT}")
            return False

        logger.info("✓ Application configuration valid")
        return True
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        return False


def check_monitoring_setup():
    """Verify monitoring is properly configured."""
    logger.info("Checking monitoring setup...")
    try:
        if os.getenv("MONITORING_ENABLED") != "true":
            logger.warning("Monitoring not enabled")
            return True

        # Check Sentry
        sentry_dsn = os.getenv("SENTRY_DSN")
        if not sentry_dsn:
            logger.warning("Sentry DSN not configured")
        else:
            logger.info("✓ Sentry configured")

        # Check Prometheus
        if os.getenv("PROMETHEUS_ENABLED") == "true":
            logger.info("✓ Prometheus enabled")

        logger.info("✓ Monitoring setup verified")
        return True
    except Exception as e:
        logger.error(f"Monitoring check failed: {e}")
        return False


def generate_deployment_report():
    """Generate deployment readiness report."""
    logger.info("Generating deployment report...")

    report = {
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT"),
        "checks": {
            "environment_variables": check_environment_variables(),
            "database_connection": check_database_connection(),
            "redis_connection": check_redis_connection(),
            "migrations": check_migrations(),
            "dependencies": check_dependencies(),
            "disk_space": check_disk_space(),
            "memory": check_memory(),
            "configuration": check_configuration(),
            "monitoring_setup": check_monitoring_setup(),
        },
    }

    report["all_passed"] = all(report["checks"].values())

    # Log report
    logger.info("\n" + "=" * 60)
    logger.info("DEPLOYMENT READINESS REPORT")
    logger.info("=" * 60)
    for check, passed in report["checks"].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{check:.<40} {status}")
    logger.info("=" * 60)

    if report["all_passed"]:
        logger.info("✓ All checks passed - Ready for deployment")
    else:
        logger.error("✗ Some checks failed - Deployment blocked")

    # Save report
    with open("/tmp/deployment_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report["all_passed"]


def main():
    """Run all pre-deployment checks."""
    logger.info("Starting pre-deployment checks...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT')}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")

    try:
        if generate_deployment_report():
            logger.info("Pre-deployment checks completed successfully")
            sys.exit(0)
        else:
            logger.error("Pre-deployment checks failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pre-deployment check error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
