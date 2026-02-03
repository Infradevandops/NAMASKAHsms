"""KYC (Know Your Customer) API endpoints."""


from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_admin_user_id, get_current_user_id
from app.core.logging import get_logger
from app.models.kyc import KYCAuditLog, KYCDocument, KYCProfile
from app.schemas.kyc import (
    KYCDocumentResponse,
    KYCProfileCreate,
    KYCProfileResponse,
    KYCStatsResponse,
    KYCVerificationDecision,
)
from app.services.document_service import get_document_service
from app.services.kyc_service import get_kyc_service

logger = get_logger(__name__)
router = APIRouter(prefix="/kyc", tags=["KYC"])


@router.post("/profile", response_model=KYCProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_kyc_profile(
    profile_data: KYCProfileCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Submit KYC profile for verification."""
try:
        # Check if profile already exists
        existing_profile = db.query(KYCProfile).filter(KYCProfile.user_id == user_id).first()
if existing_profile:
            raise HTTPException(status_code=400, detail="KYC profile already exists")

        kyc_service = get_kyc_service(db)

        # Create KYC profile
        kyc_profile = await kyc_service.create_profile(user_id, profile_data)

        return KYCProfileResponse.from_orm(kyc_profile)

except HTTPException:
        pass
except Exception as e:
        logger.error("KYC profile creation failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Profile creation failed")


@router.get("/profile", response_model=KYCProfileResponse)
def get_kyc_profile(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):

    """Get current user's KYC profile."""
    kyc_profile = db.query(KYCProfile).filter(KYCProfile.user_id == user_id).first()

if not kyc_profile:
        raise HTTPException(status_code=404, detail="KYC profile not found")

    return KYCProfileResponse.from_orm(kyc_profile)


@router.put("/profile", response_model=KYCProfileResponse)
async def update_kyc_profile(
    profile_data: KYCProfileCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update KYC profile (only if not verified)."""
    kyc_profile = db.query(KYCProfile).filter(KYCProfile.user_id == user_id).first()

if not kyc_profile:
        raise HTTPException(status_code=404, detail="KYC profile not found")

if kyc_profile.status == "verified":
        raise HTTPException(status_code=400, detail="Cannot update verified profile")

    kyc_service = get_kyc_service(db)
    updated_profile = await kyc_service.update_profile(kyc_profile.id, profile_data)

    return KYCProfileResponse.from_orm(updated_profile)


@router.post("/documents/upload")
async def upload_kyc_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upload KYC document."""
try:
        # Validate document type
        allowed_types = ["passport", "license", "id_card", "utility_bill", "selfie"]
if document_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type. Allowed: {allowed_types}",
            )

        # Get KYC profile
        kyc_profile = db.query(KYCProfile).filter(KYCProfile.user_id == user_id).first()
if not kyc_profile:
            raise HTTPException(status_code=404, detail="KYC profile not found. Create profile first.")

        document_service = get_document_service(db)

        # Upload and process document
        document = await document_service.upload_document(
            file=file, document_type=document_type, kyc_profile_id=kyc_profile.id
        )

        return {
            "id": document.id,
            "document_type": document.document_type,
            "status": document.verification_status,
            "uploaded_at": document.created_at.isoformat(),
        }

except HTTPException:
        pass
except Exception as e:
        logger.error("Document upload failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.get("/documents", response_model=List[KYCDocumentResponse])
def get_kyc_documents(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):

    """Get user's uploaded KYC documents."""
    kyc_profile = db.query(KYCProfile).filter(KYCProfile.user_id == user_id).first()

if not kyc_profile:
        raise HTTPException(status_code=404, detail="KYC profile not found")

    documents = db.query(KYCDocument).filter(KYCDocument.kyc_profile_id == kyc_profile.id).all()

    return [KYCDocumentResponse.from_orm(doc) for doc in documents]


@router.post("/submit")
async def submit_kyc_for_review(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Submit KYC profile for admin review."""
    kyc_profile = db.query(KYCProfile).filter(KYCProfile.user_id == user_id).first()

if not kyc_profile:
        raise HTTPException(status_code=404, detail="KYC profile not found")

if kyc_profile.status != "unverified":
        raise HTTPException(
            status_code=400,
            detail="Profile already submitted or \
    verified",
        )

    kyc_service = get_kyc_service(db)
    await kyc_service.submit_for_review(kyc_profile.id)

    return {"message": "KYC submitted for review", "status": "pending"}


@router.get("/limits")
def get_kyc_limits(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):

    """Get user's current KYC limits."""
    kyc_service = get_kyc_service(db)
    limits = kyc_service.get_user_limits(user_id)

    return {
        "verification_level": limits.get("level", "unverified"),
        "daily_limit": limits.get("daily_limit", 10.0),
        "monthly_limit": limits.get("monthly_limit", 50.0),
        "allowed_services": limits.get("allowed_services", ["basic"]),
        "current_usage": limits.get("current_usage", 0.0),
    }


# Admin endpoints


@router.get("/admin/pending", response_model=List[KYCProfileResponse])
def get_pending_kyc_reviews(

    admin_id: str = Depends(get_admin_user_id),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get all pending KYC reviews (admin only)."""
    pending_profiles = db.query(KYCProfile).filter(KYCProfile.status == "pending").limit(limit).all()

    return [KYCProfileResponse.from_orm(profile) for profile in pending_profiles]


@router.post("/admin/verify/{kyc_profile_id}")
async def admin_verify_kyc(
    kyc_profile_id: str,
    decision: KYCVerificationDecision,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Admin decision on KYC verification."""
    kyc_profile = db.query(KYCProfile).filter(KYCProfile.id == kyc_profile_id).first()

if not kyc_profile:
        raise HTTPException(status_code=404, detail="KYC profile not found")

    kyc_service = get_kyc_service(db)
    result = await kyc_service.admin_verify(
        kyc_profile_id=kyc_profile_id,
        admin_id=admin_id,
        decision=decision.decision,
        verification_level=decision.verification_level,
        notes=decision.notes,
    )

    return {
        "message": f"KYC {decision.decision}",
        "new_status": result.status,
        "verification_level": result.verification_level,
    }


@router.get("/admin/stats", response_model=KYCStatsResponse)
def get_kyc_statistics(admin_id: str = Depends(get_admin_user_id), db: Session = Depends(get_db)):

    """Get KYC statistics (admin only)."""

    # Basic stats
    total_profiles = db.query(KYCProfile).count()
    verified_profiles = db.query(KYCProfile).filter(KYCProfile.status == "verified").count()
    pending_profiles = db.query(KYCProfile).filter(KYCProfile.status == "pending").count()
    rejected_profiles = db.query(KYCProfile).filter(KYCProfile.status == "rejected").count()

    # Verification levels
    level_stats = (
        db.query(KYCProfile.verification_level, func.count(KYCProfile.id))
        .filter(KYCProfile.status == "verified")
        .group_by(KYCProfile.verification_level)
        .all()
    )

    return KYCStatsResponse(
        total_profiles=total_profiles,
        verified_profiles=verified_profiles,
        pending_profiles=pending_profiles,
        rejected_profiles=rejected_profiles,
        verification_rate=(verified_profiles / total_profiles * 100 if total_profiles > 0 else 0),
        level_distribution={level: count for level, count in level_stats},
    )


@router.get("/admin/audit/{user_id}")
def get_kyc_audit_trail(

    user_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Get KYC audit trail for user (admin only)."""
    audit_logs = (
        db.query(KYCAuditLog).filter(KYCAuditLog.user_id == user_id).order_by(KYCAuditLog.created_at.desc()).all()
    )

    return [
        {
            "id": log.id,
            "action": log.action,
            "old_status": log.old_status,
            "new_status": log.new_status,
            "admin_id": log.admin_id,
            "reason": log.reason,
            "created_at": log.created_at.isoformat(),
        }
for log in audit_logs
    ]


@router.post("/admin/aml - screen/{kyc_profile_id}")
async def trigger_aml_screening(
    kyc_profile_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Trigger AML screening for KYC profile (admin only)."""
    kyc_service = get_kyc_service(db)
    screening_result = await kyc_service.perform_aml_screening(kyc_profile_id)

    return {
        "screening_id": screening_result.id,
        "status": screening_result.status,
        "match_score": screening_result.match_score,
        "requires_review": screening_result.status in ["match", "review"],
    }