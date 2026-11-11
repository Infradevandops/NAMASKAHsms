"""Verification reuse endpoint — $0.25 convenience fee to reuse a completed number."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.services.balance_service import BalanceService
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)
router = APIRouter(prefix="/verification", tags=["Verification"])

REUSE_FEE = 0.25
_tv_service = TextVerifiedService()


class ReuseRequest(BaseModel):
    service_name: str


@router.post("/{verification_id}/reuse")
async def reuse_verification(
    verification_id: str,
    body: ReuseRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Reuse a completed verification number for a different service.

    Charges $0.25 convenience fee. Only available while reusable_until is in the future.
    TV charges less than a fresh purchase — platform keeps the margin difference.
    """
    verification = (
        db.query(Verification)
        .filter(Verification.id == verification_id, Verification.user_id == user_id)
        .first()
    )
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found.")

    if not verification.reusable_until:
        raise HTTPException(status_code=410, detail="This number is not available for reuse.")

    reusable_until = verification.reusable_until
    if reusable_until.tzinfo is None:
        reusable_until = reusable_until.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > reusable_until:
        raise HTTPException(status_code=410, detail="Reuse window has expired.")

    balance_check = await BalanceService.check_sufficient_balance(user_id, REUSE_FEE, db)
    if not balance_check["sufficient"]:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient balance. Need ${REUSE_FEE:.2f}, have ${balance_check['current_balance']:.2f}.",
        )

    # Deduct fee before calling TV
    user = db.query(User).filter(User.id == user_id).first()
    success, error = await BalanceService.deduct_credits_for_verification(
        db=db,
        user=user,
        verification=verification,
        cost=REUSE_FEE,
        service_name=f"reuse:{body.service_name}",
        country_code="US",
    )
    if not success:
        raise HTTPException(status_code=402, detail=error or "Failed to deduct reuse fee.")

    try:
        result = await _tv_service.reuse_verification(verification.activation_id)
    except Exception as e:
        # Refund the fee on TV failure
        user.credits = type(user.credits)(float(user.credits) + REUSE_FEE)
        db.commit()
        logger.error(f"TV reuse failed for {verification_id}: {e}")
        raise HTTPException(status_code=503, detail="Reuse failed — fee refunded.")

    # Create new verification record
    new_v = Verification(
        user_id=user_id,
        service_name=body.service_name,
        phone_number=verification.phone_number,
        country=verification.country,
        capability=verification.capability,
        cost=REUSE_FEE,
        provider=verification.provider,
        activation_id=result["id"],
        status="pending",
        reused_from_id=str(verification.id),
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_v)
    db.commit()
    db.refresh(new_v)

    logger.info(f"Reuse: user={user_id} old={verification_id} new={new_v.id} service={body.service_name}")

    from app.services.sms_polling_service import sms_polling_service
    import asyncio
    asyncio.create_task(sms_polling_service.start_polling(str(new_v.id)))

    return {
        "verification_id": str(new_v.id),
        "phone_number": verification.phone_number,
        "service_name": body.service_name,
        "cost": REUSE_FEE,
        "ends_at": result.get("ends_at"),
    }
