"""Health check utilities for system monitoring."""
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def check_database_health(db: Session) -> Dict[str, Any]:
    """Check database connectivity and health."""
    try:
        # Simple connectivity test
        result = db.execute(text("SELECT 1")).fetchone()
        if result and result[0] == 1:
            return {"status": "healthy", "message": "Database connection successful"}
        else:
            return {
                "status": "unhealthy",
                "error": "Database query returned unexpected result",
            }
    except SQLAlchemyError as e:
        return {"status": "unhealthy", "error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"status": "unhealthy", "error": f"Unexpected error: {str(e)}"}


def check_system_health(db: Session) -> Dict[str, Any]:
    """Comprehensive system health check."""
    health_status = {"status": "healthy", "timestamp": None, "services": {}}

    # Check database
    db_health = check_database_health(db)
    health_status["services"]["database"] = db_health

    # Overall status
    if db_health["status"] != "healthy":
        health_status["status"] = "unhealthy"

    return health_status
