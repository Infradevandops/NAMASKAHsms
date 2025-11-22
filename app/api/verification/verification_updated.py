"""SMS Verification API with TextVerified API Integration - Updated Error Handling"""
from datetime import timedelta
from app.utils.timezone_utils import utc_now, parse_date_string, get_timestamp_filename
from typing import Optional
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.unified_error_handling import (
    ExternalServiceError as TextVerifiedAPIError,
    InsufficientCreditsError,
    ValidationError as InvalidInputError,
    VerificationError,
    ValidationError as ResourceNotFoundError,
)
from app.models.user import User
from app.models.verification import Verification
from app.schemas import (
    SuccessResponse,
    VerificationCreate,
    VerificationHistoryResponse,
    VerificationResponse,
)
from app.services.provider_factory import provider_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])


@router.get("/services")
async def get_available_services():
    """Get popular SMS verification services"""
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
        "total": len(services),
        "note": "For full service list, select a country first"
    }


@router.post("/create",
             response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create new SMS verification using TextVerified API"""
    try:
        if not verification_data.service_name:
            raise InvalidInputError("Service name is required")

        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise ResourceNotFoundError("User not found")

        provider = provider_manager.get_primary_provider()
        if not provider:
            raise TextVerifiedAPIError("TextVerified provider not available")

        country = getattr(verification_data, "country", "US")
        pricing_tier = getattr(verification_data, "pricing_tier", "standard")

        try:
            balance_data = await provider.get_balance()
            balance = balance_data.get("balance", 0.0)
            if balance < 0.50:
                raise TextVerifiedAPIError(f"TextVerified balance too low: ${balance}")
        except TextVerifiedAPIError:
            raise
        except Exception as e:
            raise TextVerifiedAPIError(f"API authentication failed: {str(e)}")

        base_cost = 0.50
        final_cost = base_cost

        if current_user.free_verifications > 0:
            current_user.free_verifications -= 1
            actual_cost = 0.0
            db.commit()
        elif current_user.credits >= final_cost:
            current_user.credits -= final_cost
            actual_cost = final_cost
            db.commit()
        else:
            raise InsufficientCreditsError(
                f"Need ${final_cost:.2f}, have ${current_user.credits:.2f}"
            )

        try:
            number_data = await provider.buy_number(
                country=country,
                service=verification_data.service_name
            )
            phone_number = number_data["phone_number"]
            activation_id = str(number_data["activation_id"])
            if "cost" in number_data:
                final_cost = number_data["cost"]
        except Exception as e:
            if actual_cost > 0:
                current_user.credits += actual_cost
            else:
                current_user.free_verifications += 1
            db.commit()
            raise TextVerifiedAPIError(f"Purchase failed: {str(e)}")

        verification = Verification(
            user_id=user_id,
            service_name=verification_data.service_name,
            capability=getattr(verification_data, "capability", "sms"),
            status="pending",
            cost=actual_cost,
            phone_number=phone_number,
            country=country,
            verification_code=str(activation_id),
        )

        if hasattr(verification, 'provider'):
            verification.provider = "textverified"
        if hasattr(verification, 'pricing_tier'):
            verification.pricing_tier = pricing_tier
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
            "requested_carrier": getattr(verification, 'requested_carrier', None),
            "requested_area_code": getattr(verification, 'requested_area_code', None),
            "created_at": verification.created_at,
            "completed_at": verification.completed_at
        }

    except InvalidInputError as e:
        logger.warning(f"Invalid input: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientCreditsError as e:
        logger.warning(f"Insufficient credits: {str(e)}")
        raise HTTPException(status_code=402, detail=str(e))
    except TextVerifiedAPIError as e:
        logger.error(f"TextVerified API error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Verification creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(verification_id: str, db: Session = Depends(get_db)):
    """Get verification status"""
    try:
        verification = db.query(Verification).filter(Verification.id == verification_id).first()
        if not verification:
            raise ResourceNotFoundError("Verification not found")

        if verification.status == "pending" and verification.verification_code:
            try:
                provider = provider_manager.get_primary_provider()
                sms_code = await provider.get_sms(verification.verification_code)
                if sms_code:
                    verification.status = "completed"
                    verification.completed_at = utc_now()
                    if hasattr(verification, 'sms_code'):
                        verification.sms_code = sms_code
                    db.commit()
            except Exception as e:
                logger.error(f"SMS provider check failed: {e}")

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

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get verification status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve verification")


@router.get("/{verification_id}/messages")
async def get_verification_messages(verification_id: str, db: Session = Depends(get_db)):
    """Get SMS messages for verification"""
    try:
        verification = db.query(Verification).filter(Verification.id == verification_id).first()
        if not verification:
            raise ResourceNotFoundError("Verification not found")

        if not verification.verification_code:
            return {
                "messages": [],
                "status": verification.status,
                "verification_id": verification_id,
                "error": "No activation ID found"
            }

        try:
            provider = provider_manager.get_primary_provider()
            sms_code = await provider.get_sms(verification.verification_code)
            messages = []

            if sms_code:
                messages.append({
                    "text": f"Your verification code is: {sms_code}",
                    "code": sms_code,
                    "date": utc_now().isoformat()
                })

                if verification.status == "pending":
                    verification.status = "completed"
                    verification.completed_at = utc_now()
                    if hasattr(verification, 'sms_text'):
                        verification.sms_text = messages[-1]["text"]
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
            logger.error(f"SMS provider failed: {e}")
            return {
                "messages": [],
                "status": verification.status,
                "verification_id": verification_id,
                "error": str(e)
            }

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


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
    """Get user's verification history"""
    try:
        query = db.query(Verification).filter(Verification.user_id == user_id)

        if service:
            query = query.filter(Verification.service_name == service)
        if verification_status:
            query = query.filter(Verification.status == verification_status)
        if country:
            query = query.filter(Verification.country == country.lower())

        if start_date:
            try:
                start_dt = parse_date_string(start_date, "%Y-%m-%d")
                query = query.filter(Verification.created_at >= start_dt)
            except ValueError:
                raise InvalidInputError("Invalid start_date format. Use YYYY - MM-DD")

        if end_date:
            try:
                end_dt = parse_date_string(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Verification.created_at <= end_dt)
            except ValueError:
                raise InvalidInputError("Invalid end_date format. Use YYYY - MM-DD")

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Verification.phone_number.like(search_term))
                | (Verification.verification_code.like(search_term))
            )

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

    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.get("/history/export")
async def export_verification_history(
    user_id: str = Depends(get_current_user_id),
    service: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export verification history as CSV"""
    try:
        query = db.query(Verification).filter(Verification.user_id == user_id)

        if service:
            query = query.filter(Verification.service_name == service)
        if verification_status:
            query = query.filter(Verification.status == verification_status)

        if start_date:
            try:
                start_dt = parse_date_string(start_date, "%Y-%m-%d")
                query = query.filter(Verification.created_at >= start_dt)
            except ValueError:
                raise InvalidInputError("Invalid start_date format. Use YYYY - MM-DD")

        if end_date:
            try:
                end_dt = parse_date_string(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Verification.created_at <= end_dt)
            except ValueError:
                raise InvalidInputError("Invalid end_date format. Use YYYY - MM-DD")

        MAX_EXPORT = 10000
        total = query.count()

        if total > MAX_EXPORT:
            raise VerificationError(
                f"Export limited to {MAX_EXPORT} records. Found {total} records."
            )

        if total == 0:
            raise ResourceNotFoundError("No verifications found for export")

        verifications = query.order_by(Verification.created_at.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'ID', 'Service', 'Phone Number', 'Country', 'Operator', 'Status',
            'Cost', 'Pricing Tier', 'Provider', 'Created At', 'Completed At',
            'SMS Code', 'Area Code'
        ])

        for v in verifications:
            writer.writerow([
                v.id, v.service_name, v.phone_number or '', v.country or '',
                getattr(v, 'operator', '') or '', v.status, f"${v.cost:.2f}",
                getattr(v, 'pricing_tier', 'standard') or 'standard',
                getattr(v, 'provider', '5sim') or '5sim',
                v.created_at.strftime('%Y-%m-%d %H:%M:%S') if v.created_at else '',
                v.completed_at.strftime('%Y-%m-%d %H:%M:%S') if v.completed_at else '',
                getattr(v, 'sms_code', '') or '', v.requested_area_code or ''
            ])

        output.seek(0)
        filename = f"namaskah_verifications_{get_timestamp_filename()}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content - Disposition": f"attachment; filename={filename}"}
        )

    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VerificationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/analytics")
async def get_verification_analytics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's verification analytics"""
    try:
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
                "by_country": {},
                "recent_trend": []
            }

        total = len(verifications)
        successful = sum(1 for v in verifications if v.status == "completed")
        failed = sum(1 for v in verifications if v.status in ["failed",
                                                              "timeout", "cancelled"])
        overall_rate = (successful / total * 100) if total > 0 else 0.0

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

        by_service = dict(sorted(by_service.items(),
                                 key=lambda x: x[1]["total"], reverse=True)[:10])

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

        by_country = dict(sorted(by_country.items(),
                                 key=lambda x: x[1]["total"], reverse=True)[:10])

        thirty_days_ago = utc_now() - timedelta(days=30)
        recent_verifications = [v for v in verifications if v.created_at >= thirty_days_ago]

        trend = {}
        for v in recent_verifications:
            date_key = v.created_at.strftime("%Y-%m-%d")
            if date_key not in trend:
                trend[date_key] = {"total": 0, "successful": 0}
            trend[date_key]["total"] += 1
            if v.status == "completed":
                trend[date_key]["successful"] += 1

        recent_trend = []
        for date_key in sorted(trend.keys()):
            total_t = trend[date_key]["total"]
            successful_t = trend[date_key]["successful"]
            rate = (successful_t / total_t * 100) if total_t > 0 else 0.0
            recent_trend.append({
                "date": date_key,
                "total": total_t,
                "successful": successful_t,
                "rate": round(rate, 1)
            })

        return {
            "success": True,
            "overall_rate": round(overall_rate, 1),
            "total_verifications": total,
            "successful": successful,
            "failed": failed,
            "pending": total - successful - failed,
            "by_service": by_service,
            "by_country": by_country,
            "recent_trend": recent_trend
        }

    except Exception as e:
        logger.error(f"Analytics calculation failed: {str(e)}")
        return {
            "success": False,
            "overall_rate": 0.0,
            "total_verifications": 0,
            "successful": 0,
            "failed": 0,
            "by_service": {},
            "by_country": {},
            "recent_trend": [],
            "error": "Failed to calculate analytics"
        }


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification and refund credits"""
    try:
        verification = db.query(Verification).filter(
            Verification.id == verification_id,
            Verification.user_id == user_id
        ).first()

        if not verification:
            raise ResourceNotFoundError("Verification not found")

        if verification.status in ["cancelled", "completed"]:
            raise VerificationError(f"Cannot cancel {verification.status} verification")

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

    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VerificationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cancel verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel verification")
