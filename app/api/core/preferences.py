"""Service preferences API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.preferences import ServicePreference
from app.utils.exception_handling import safe_int_conversion

logger = get_logger(__name__)

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.post("/save")
async def save_preference(
    service_name: str,
    preferred_country: str,
    preferred_operator: str = "any",
    preferred_tier: str = "standard",
    preferred_capability: str = "sms",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Save or update service preference."""
    try:
        # Check if preference exists
        preference = db.query(ServicePreference).filter(
            ServicePreference.user_id == user_id,
            ServicePreference.service_name == service_name
        ).first()

        if preference:
            # Update existing
            preference.preferred_country = preferred_country
            preference.preferred_operator = preferred_operator
            preference.preferred_tier = preferred_tier
            preference.preferred_capability = preferred_capability
        else:
            # Create new
            preference = ServicePreference(
                user_id=user_id,
                service_name=service_name,
                preferred_country=preferred_country,
                preferred_operator=preferred_operator,
                preferred_tier=preferred_tier,
                preferred_capability=preferred_capability,
                use_count="0"
            )
            db.add(preference)

        db.commit()
        db.refresh(preference)

        return {
            "success": True,
            "message": f"Preference saved for {service_name}",
            "preference": {
                "service_name": preference.service_name,
                "preferred_country": preference.preferred_country,
                "preferred_operator": preference.preferred_operator,
                "preferred_tier": preference.preferred_tier,
                "preferred_capability": preference.preferred_capability
            }
        }

    except IntegrityError as e:
        logger.error(f"Database integrity error saving preference: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid preference data or \
    duplicate entry")
    except SQLAlchemyError as e:
        logger.error(f"Database error saving preference: {str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.get("")
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get all user preferences."""
    try:
        preferences = db.query(ServicePreference).filter(
            ServicePreference.user_id == user_id
        ).all()

        return {
            "success": True,
            "preferences": [
                {
                    "id": p.id,
                    "service_name": p.service_name,
                    "preferred_country": p.preferred_country,
                    "preferred_operator": p.preferred_operator,
                    "preferred_tier": p.preferred_tier,
                    "preferred_capability": p.preferred_capability,
                    "use_count": p.use_count,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in preferences
            ]
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error getting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.get("/{service_name}")
async def get_service_preference(
    service_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get preference for specific service."""
    try:
        preference = db.query(ServicePreference).filter(
            ServicePreference.user_id == user_id,
            ServicePreference.service_name == service_name
        ).first()

        if not preference:
            return {
                "success": False,
                "message": f"No preference found for {service_name}"
            }

        # Increment use count
        try:
            use_count = safe_int_conversion(preference.use_count or "0", 0, "use_count")
            preference.use_count = str(use_count + 1)
            db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Failed to update use count: {e}")
            # Continue without failing the request

        return {
            "success": True,
            "preference": {
                "service_name": preference.service_name,
                "preferred_country": preference.preferred_country,
                "preferred_operator": preference.preferred_operator,
                "preferred_tier": preference.preferred_tier,
                "preferred_capability": preference.preferred_capability,
                "use_count": preference.use_count
            }
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error getting preference: {str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.delete("/{service_name}")
async def delete_preference(
    service_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete service preference."""
    try:
        preference = db.query(ServicePreference).filter(
            ServicePreference.user_id == user_id,
            ServicePreference.service_name == service_name
        ).first()

        if not preference:
            raise HTTPException(status_code=404, detail="Preference not found")

        db.delete(preference)
        db.commit()

        return {
            "success": True,
            "message": f"Preference deleted for {service_name}"
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting preference: {str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")


@router.post("/quick - select/{service_name}")
async def quick_select_with_preference(
    service_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Quick - select: Get preference and return ready - to-use settings.
    This endpoint returns the saved preference for immediate use in verification.
    """
    try:
        preference = db.query(ServicePreference).filter(
            ServicePreference.user_id == user_id,
            ServicePreference.service_name == service_name
        ).first()

        if not preference:
            return {
                "success": False,
                "message": f"No saved preference for {service_name}. Please configure and \
    save first."
            }

        # Increment use count
        try:
            use_count = safe_int_conversion(preference.use_count or "0", 0, "use_count")
            preference.use_count = str(use_count + 1)
            db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Failed to update use count: {e}")
            # Continue without failing the request

        return {
            "success": True,
            "message": f"Using saved settings for {service_name}",
            "settings": {
                "service_name": service_name,
                "country": preference.preferred_country,
                "operator": preference.preferred_operator,
                "pricing_tier": preference.preferred_tier,
                "capability": preference.preferred_capability
            }
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error in quick - select: {str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
