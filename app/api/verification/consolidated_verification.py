"""Consolidated SMS Verification API with unified endpoints."""
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from datetime import datetime, timezone
from app.utils.timezone_utils import utc_now, parse_date_string
from typing import Optional
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

    SuccessResponse,
    VerificationCreate,
    VerificationHistoryResponse,
    VerificationResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])


@router.get("/services")
async def get_available_services():
    """Get popular SMS verification services."""
    services = [
        {"id": "telegram", "name": "Telegram", "category": "messaging", "icon": "💬"},
        {"id": "whatsapp", "name": "WhatsApp", "category": "messaging", "icon": "📱"},
        {"id": "google", "name": "Google", "category": "tech", "icon": "🔍"},
        {"id": "facebook", "name": "Facebook", "category": "social", "icon": "📘"},
        {"id": "instagram", "name": "Instagram", "category": "social", "icon": "📷"},
        {"id": "discord", "name": "Discord", "category": "messaging", "icon": "🎮"},
        {"id": "twitter", "name": "Twitter", "category": "social", "icon": "🐦"},
        {"id": "tiktok", "name": "TikTok", "category": "social", "icon": "🎵"},
        {"id": "microsoft", "name": "Microsoft", "category": "tech", "icon": "🪟"},
        {"id": "amazon", "name": "Amazon", "category": "ecommerce", "icon": "📦"},
        {"id": "uber", "name": "Uber", "category": "transport", "icon": "🚗"},
        {"id": "netflix", "name": "Netflix", "category": "entertainment", "icon": "🎬"},
        {"id": "spotify", "name": "Spotify", "category": "entertainment", "icon": "🎵"},
        {"id": "paypal", "name": "PayPal", "category": "finance", "icon": "💳"}
    ]
    return {
        "success": True,
        "services": services,
        "total": len(services)
    }


@router.post("/create",
             response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create new SMS verification."""
    try:
        if not verification_data.service_name:
            raise HTTPException(status_code=400, detail="Service name is required")

        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check provider availability
        try:
            balance_data = await provider_manager.get_balance()
            balance = balance_data.get("balance", 0.0)
            if balance < 0.50:
                raise HTTPException(
                    status_code=503,
                    detail="SMS service temporarily unavailable"
                )
        except Exception as e:
            logger.error(f"Provider check failed: {create_safe_error_detail(e)}")
            raise HTTPException(
                status_code=503,
                detail="SMS service temporarily unavailable"
            )

        country = getattr(verification_data, "country", "US")
        base_cost = 0.50

        # Handle credits/free verifications
        if current_user.free_verifications > 0:
            current_user.free_verifications -= 1
            actual_cost = 0.0
            db.commit()
        elif current_user.credits >= base_cost:
            current_user.credits -= base_cost
            actual_cost = base_cost
            db.commit()
        else:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Need ${base_cost:.2f}, have ${current_user.credits:.2f}"
            )

        # Purchase number
        try:
            number_data = await provider_manager.buy_number(
                country=country,
                service=verification_data.service_name
            )
            phone_number = number_data["phone_number"]
            activation_id = str(number_data["activation_id"])
        except Exception as e:
            # Refund on failure
            if actual_cost > 0:
                current_user.credits += actual_cost
            else:
                current_user.free_verifications += 1
            db.commit()

            logger.error(f"Number purchase failed: {create_safe_error_detail(e)}")
            raise HTTPException(
                status_code=503,
                detail="Failed to purchase SMS number"
            )

        # Create verification record
        verification = Verification(
            user_id=user_id,
            service_name=verification_data.service_name,
            capability=getattr(verification_data, "capability", "sms"),
            status="pending",
            cost=actual_cost,
            phone_number=phone_number,
            country=country,
            verification_code=activation_id,
        )

        # Set optional fields if they exist
        if hasattr(verification, 'provider'):
            verification.provider = "textverified"
        if hasattr(verification, 'activation_id'):
            verification.activation_id = activation_id

        db.add(verification)
        db.commit()
        db.refresh(verification)

        return {
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": verification.cost,
            "created_at": verification.created_at,
            "completed_at": verification.completed_at
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Verification creation failed: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=500, detail="Failed to create verification")


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(verification_id: str, db: Session = Depends(get_db)):
    """Get verification status with SMS check."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    # Check for SMS updates if still pending
    if verification.status == "pending" and verification.verification_code:
        try:
            sms_result = await provider_manager.check_sms(verification.verification_code)
            if sms_result.get("sms_code"):
                verification.status = "completed"
                verification.completed_at = datetime.now(timezone.utc)
                if hasattr(verification, 'sms_code'):
                    verification.sms_code = sms_result["sms_code"]
                db.commit()
        except Exception as e:
            logger.warning(f"SMS check failed: {create_safe_error_detail(e)}")

    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "capability": verification.capability,
        "status": verification.status,
        "cost": verification.cost,
        "created_at": verification.created_at.isoformat(),
        "provider": getattr(verification, "provider", "textverified"),
        "country": getattr(verification, "country", "US"),
        "completed_at": verification.completed_at.isoformat() if verification.completed_at else None
    }


@router.get("/{verification_id}/messages")
async def get_verification_messages(verification_id: str, db: Session = Depends(get_db)):
    """Get SMS messages for verification."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if not verification.verification_code:
        return {
            "messages": [],
            "status": verification.status,
            "verification_id": verification_id,
            "error": "No activation ID found"
        }

    try:
        sms_result = await provider_manager.check_sms(verification.verification_code)
        messages = []
        sms_code = sms_result.get("sms_code")

        if sms_code:
            messages.append({
                "text": f"Your verification code is: {sms_code}",
                "code": sms_code,
                "date": datetime.now(timezone.utc).isoformat()
            })

            # Update verification status
            if verification.status == "pending":
                verification.status = "completed"
                verification.completed_at = datetime.now(timezone.utc)
                if hasattr(verification, 'sms_code'):
                    verification.sms_code = sms_code
                db.commit()

        return {
            "messages": messages,
            "status": verification.status,
            "verification_id": verification_id,
            "code": sms_code,
            "phone": verification.phone_number,
            "provider": "textverified"
        }

    except Exception as e:
        logger.error(f"Message retrieval failed: {create_safe_error_detail(e)}")
        return {
            "messages": [],
            "status": verification.status,
            "verification_id": verification_id,
            "error": "Failed to retrieve messages"
        }


@router.get("/history", response_model=VerificationHistoryResponse)
def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    service: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    limit: int = Query(50, le=100),
    skip: int = Query(0),
    db: Session = Depends(get_db),
):
    """Get user's verification history with filtering and sorting."""
    query = db.query(Verification).filter(Verification.user_id == user_id)

    # Apply filters
    if service:
        query = query.filter(Verification.service_name == service)
    if verification_status:
        query = query.filter(Verification.status == verification_status)
    if country:
        query = query.filter(Verification.country == country.lower())

    # Date range filters
    if start_date:
        try:
            start_dt = parse_date_string(start_date, "%Y-%m-%d")
            query = query.filter(Verification.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = parse_date_string(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Verification.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Verification.phone_number.like(search_term))
            | (Verification.verification_code.like(search_term))
        )

    # Sorting
    sort_field = sort_by.lower()
    order_column = {
        "created_at": Verification.created_at,
        "cost": Verification.cost,
        "status": Verification.status,
    }.get(sort_field, Verification.created_at)

    if sort_order.lower() == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    total = query.count()
    verifications = query.offset(skip).limit(limit).all()

    return VerificationHistoryResponse(
        verifications=[VerificationResponse.from_orm(v) for v in verifications],
        total_count=total,
    )


@router.get("/history/export")
async def export_verification_history(
    user_id: str = Depends(get_current_user_id),
    service: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export verification history as CSV."""
    query = db.query(Verification).filter(Verification.user_id == user_id)

    # Apply filters
    if service:
        query = query.filter(Verification.service_name == service)
    if verification_status:
        query = query.filter(Verification.status == verification_status)

    # Date filters
    if start_date:
        try:
            start_dt = parse_date_string(start_date, "%Y-%m-%d")
            query = query.filter(Verification.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = parse_date_string(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Verification.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # Limit export size
    MAX_EXPORT = 10000
    total = query.count()

    if total > MAX_EXPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Export limited to {MAX_EXPORT} records. Found {total} records."
        )

    if total == 0:
        raise HTTPException(status_code=404, detail="No verifications found")

    verifications = query.order_by(Verification.created_at.desc()).all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Service', 'Phone Number', 'Country', 'Status',
        'Cost', 'Provider', 'Created At', 'Completed At', 'SMS Code'
    ])

    for v in verifications:
        writer.writerow([
            v.id, v.service_name, v.phone_number or '', v.country or '',
            v.status, f"${v.cost:.2f}",
            getattr(v, 'provider', 'textverified'),
            v.created_at.strftime('%Y-%m-%d %H:%M:%S') if v.created_at else '',
            v.completed_at.strftime('%Y-%m-%d %H:%M:%S') if v.completed_at else '',
            getattr(v, 'sms_code', '') or ''
        ])

    output.seek(0)
    filename = f"verifications_{utc_now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content - Disposition": f"attachment; filename={filename}"}
    )


@router.get("/analytics")
async def get_verification_analytics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's verification analytics and success rates."""
    verifications = db.query(Verification).filter(
        Verification.user_id == user_id
    ).all()

    if not verifications:
        return {
            "success": True,
            "overall_rate": 0.0,
            "total_verifications": 0,
            "successful": 0,
            "failed": 0,
            "by_service": {},
            "by_country": {}
        }

    total = len(verifications)
    successful = sum(1 for v in verifications if v.status == "completed")
    failed = sum(1 for v in verifications if v.status in ["failed",
                                                          "timeout", "cancelled"])
    overall_rate = (successful / total * 100) if total > 0 else 0.0

    # Analytics by service
    by_service = {}
    for v in verifications:
        service = v.service_name
        if service not in by_service:
            by_service[service] = {"total": 0, "successful": 0, "rate": 0.0}
        by_service[service]["total"] += 1
        if v.status == "completed":
            by_service[service]["successful"] += 1

    for service in by_service:
        total_s = by_service[service]["total"]
        successful_s = by_service[service]["successful"]
        by_service[service]["rate"] = (successful_s / total_s * 100) if total_s > 0 else 0.0

    # Analytics by country
    by_country = {}
    for v in verifications:
        country = v.country or "unknown"
        if country not in by_country:
            by_country[country] = {"total": 0, "successful": 0, "rate": 0.0}
        by_country[country]["total"] += 1
        if v.status == "completed":
            by_country[country]["successful"] += 1

    for country in by_country:
        total_c = by_country[country]["total"]
        successful_c = by_country[country]["successful"]
        by_country[country]["rate"] = (successful_c / total_c * 100) if total_c > 0 else 0.0

    return {
        "success": True,
        "overall_rate": round(overall_rate, 1),
        "total_verifications": total,
        "successful": successful,
        "failed": failed,
        "pending": total - successful - failed,
        "by_service": dict(sorted(by_service.items(),
                                  key=lambda x: x[1]["total"], reverse=True)[:10]),
        "by_country": dict(sorted(by_country.items(),
                                  key=lambda x: x[1]["total"], reverse=True)[:10])
    }


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification and refund credits."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status in ["cancelled", "completed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel {verification.status} verification"
        )

    # Refund credits
    current_user = db.query(User).filter(User.id == user_id).first()
    if verification.cost > 0:
        current_user.credits += verification.cost
    else:
        current_user.free_verifications += 1

    verification.status = "cancelled"
    db.commit()

    return SuccessResponse(
        message="Verification cancelled and refunded",
        data={"refunded": verification.cost, "new_balance": current_user.credits},
    )
