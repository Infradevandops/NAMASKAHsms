"""Admin endpoint to check and fix database schema."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, text

from app.core.database import get_db
from app.core.dependencies import require_admin

router = APIRouter(prefix="/admin/db", tags=["Admin - Database"])


@router.get("/schema-check")
async def check_database_schema(db=Depends(get_db)):
    """Check if database schema matches models."""
    try:
        engine = db.get_bind()
        inspector = inspect(engine)

        # Check verifications table
        columns = [col["name"] for col in inspector.get_columns("verifications")]

        issues = []
        fixes_applied = []

        # Check for idempotency_key
        if "idempotency_key" not in columns:
            issues.append("Missing column: verifications.idempotency_key")

        return {
            "status": "healthy" if not issues else "issues_found",
            "issues": issues,
            "columns_found": len(columns),
            "critical_columns_present": {
                "idempotency_key": "idempotency_key" in columns,
                "activation_id": "activation_id" in columns,
                "sms_code": "sms_code" in columns,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fix-schema")
async def fix_database_schema(db=Depends(get_db), _=Depends(require_admin)):
    """Fix database schema issues (Admin only)."""
    try:
        engine = db.get_bind()
        inspector = inspect(engine)

        columns = [col["name"] for col in inspector.get_columns("verifications")]
        fixes_applied = []

        # Fix missing idempotency_key
        if "idempotency_key" not in columns:
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE verifications ADD COLUMN idempotency_key VARCHAR")
                )
                conn.execute(
                    text(
                        "CREATE INDEX ix_verifications_idempotency_key ON verifications (idempotency_key)"
                    )
                )
                conn.commit()
                fixes_applied.append("Added idempotency_key column and index")

        return {
            "status": "success",
            "fixes_applied": fixes_applied if fixes_applied else ["No fixes needed"],
            "message": "Database schema is now up to date",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fix failed: {str(e)}")
