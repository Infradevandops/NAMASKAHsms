"""Public health check endpoint for database schema."""

from fastapi import APIRouter, Depends
from sqlalchemy import inspect

from app.core.database import get_db

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/db-schema")
async def check_db_schema_health(db=Depends(get_db)):
    """Public endpoint to check if database schema is healthy."""
    try:
        engine = db.get_bind()
        inspector = inspect(engine)

        columns = [col["name"] for col in inspector.get_columns("verifications")]

        has_idempotency = "idempotency_key" in columns

        return {
            "status": "healthy" if has_idempotency else "degraded",
            "database": "connected",
            "schema_version": "4.0.0",
            "critical_features": {
                "idempotency_protection": has_idempotency,
                "verification_creation": has_idempotency,
                "polling_services": has_idempotency,
            },
            "message": (
                "All systems operational"
                if has_idempotency
                else "Database migration pending"
            ),
        }
    except Exception as e:
        return {"status": "error", "database": "error", "message": str(e)[:100]}
