"""SMS Verification API with TextVerified API Integration"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.schemas import (SuccessResponse, VerificationCreate,
                         VerificationHistoryResponse, VerificationResponse)
from app.services.provider_factory import provider_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.get("/services")
async def get_available_services():
    """Get popular SMS verification services"""
    # Return curated list of most popular services
    # These are guaranteed to work well across most countries
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


@router.post("/create", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create new SMS verification using 5SIM API v1"""
    try:
        logger.info(f"Creating verification for user {user_id} with data: {verification_data.dict()}")
        # Validate input
        logger.info(f"Validating service_name: {verification_data.service_name}")
        if not verification_data.service_name:
            raise HTTPException(status_code=400, detail="Service name is required")

        # Get user and check credits
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get TextVerified provider
        provider = provider_manager.get_primary_provider()
        if not provider:
            raise HTTPException(status_code=503, detail="TextVerified provider not available")

        # Extract parameters with defaults
        country = getattr(verification_data, "country", "US")
        pricing_tier = getattr(verification_data, "pricing_tier", "standard")

        # Get balance and check if provider has funds
        try:
            balance_data = await provider.get_balance()
            balance = balance_data.get("balance", 0.0)
            if balance < 0.50:
                logger.warning(f"TextVerified balance low: ${balance}")
                raise HTTPException(
                    status_code=503,
                    detail=f"TextVerified balance too low: ${balance}. Please add funds to your TextVerified account."
                )
            logger.info(f"TextVerified balance: ${balance}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"TextVerified API failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="TextVerified API authentication failed. Please check API key configuration."
            )

        # TextVerified pricing is fixed, typically $0.50-$2.00 per verification
        base_cost = 0.50  # Default cost
        final_cost = base_cost

        # Check user credits/free verifications
        if current_user.free_verifications > 0:
            current_user.free_verifications -= 1
            actual_cost = 0.0
            db.commit()  # Commit credit deduction first
        elif current_user.credits >= final_cost:
            current_user.credits -= final_cost
            actual_cost = final_cost
            db.commit()  # Commit credit deduction first
        else:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Need ${final_cost:.2f}, have ${current_user.credits:.2f}"
            )

        # Purchase number from TextVerified
        try:
            number_data = await provider.buy_number(
                country=country,
                service=verification_data.service_name
            )

            phone_number = number_data["phone_number"]
            activation_id = str(number_data["activation_id"])

            # Update cost if TextVerified returned different price
            if "cost" in number_data:
                final_cost = number_data["cost"]

        except HTTPException:
            raise
        except Exception as e:
            # Refund credits on purchase failure
            if actual_cost > 0:
                current_user.credits += actual_cost
            else:
                current_user.free_verifications += 1
            db.commit()

            logger.error(f"TextVerified purchase failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="SMS service temporarily unavailable. Please try again."
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
            verification_code=str(activation_id),  # Store TextVerified activation ID
        )

        # Add optional fields if they exist in model
        if hasattr(verification, 'provider'):
            verification.provider = "textverified"
        if hasattr(verification, 'pricing_tier'):
            verification.pricing_tier = pricing_tier
        if hasattr(verification, 'activation_id'):
            verification.activation_id = activation_id

        db.add(verification)
        db.commit()
        db.refresh(verification)

        # SMS polling handled by background service
        logger.info(f"Verification {verification.id} created, SMS polling will check for codes")

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Verification creation failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(verification_id: str, db: Session = Depends(get_db)):
    """Get verification status with real-time 5SIM check"""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    # Check SMS provider for updates
    if verification.status == "pending" and verification.verification_code:
        try:
            provider = provider_manager.get_primary_provider()
            activation_id = verification.verification_code

            # Get SMS from provider
            sms_code = await provider.get_sms(activation_id)

            if sms_code:
                verification.status = "completed"
                verification.completed_at = datetime.now(timezone.utc)

                if hasattr(verification, 'sms_code'):
                    verification.sms_code = sms_code

                db.commit()
                logger.info(f"SMS code received: {sms_code} for {verification_id}")

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


@router.get("/{verification_id}/messages")
async def get_verification_messages(verification_id: str, db: Session = Depends(get_db)):
    """Get SMS messages for verification from TextVerified"""
    try:
        verification = db.query(Verification).filter(Verification.id == verification_id).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Check TextVerified for SMS messages
        if not verification.verification_code:
            return {
                "messages": [],
                "status": verification.status,
                "verification_id": verification_id,
                "error": "No activation ID found"
            }

        provider = provider_manager.get_primary_provider()
        activation_id = verification.verification_code

        # Get SMS messages from provider
        try:
            provider = provider_manager.get_primary_provider()
            activation_id = verification.verification_code

            # Get SMS code from provider
            sms_code = await provider.get_sms(activation_id)

            messages = []
            extracted_code = sms_code

            if sms_code:
                messages.append({
                    "text": f"Your verification code is: {sms_code}",
                    "code": sms_code,
                    "date": datetime.now(timezone.utc).isoformat()
                })

                # Update verification if SMS received
                if verification.status == "pending":
                    verification.status = "completed"
                    verification.completed_at = datetime.now(timezone.utc)

                    if hasattr(verification, 'sms_text'):
                        verification.sms_text = messages[-1]["text"]
                    if hasattr(verification, 'sms_code'):
                        verification.sms_code = extracted_code

                    db.commit()

            return {
                "messages": messages,
                "status": verification.status,
                "verification_id": verification_id,
                "code": extracted_code,
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get messages for %s: %s", verification_id, str(e))
        return {
            "messages": [],
            "status": "error",
            "error": "Failed to retrieve messages",
        }


@router.get("/history", response_model=VerificationHistoryResponse)
def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    service: Optional[str] = Query(None, description="Filter by service name"),
    verification_status: Optional[str] = Query(None, description="Filter by status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search by phone number or code"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at, cost, status"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(50, le=100, description="Number of results"),
    skip: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Get user's verification history with advanced filtering, sorting, and search"""
    query = db.query(Verification).filter(Verification.user_id == user_id)

    # Service filter
    if service:
        query = query.filter(Verification.service_name == service)

    # Status filter
    if verification_status:
        query = query.filter(Verification.status == verification_status)

    # Country filter
    if country:
        query = query.filter(Verification.country == country.lower())

    # Date range filter
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Verification.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            # Add 1 day to include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Verification.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    # Search by phone number or verification code
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Verification.phone_number.like(search_term))
            | (Verification.verification_code.like(search_term))
        )

    # Sorting
    sort_field = sort_by.lower()
    sort_direction = sort_order.lower()

    if sort_field == "created_at":
        order_column = Verification.created_at
    elif sort_field == "cost":
        order_column = Verification.cost
    elif sort_field == "status":
        order_column = Verification.status
    else:
        order_column = Verification.created_at  # Default

    if sort_direction == "asc":
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
    service: Optional[str] = Query(None, description="Filter by service name"),
    verification_status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Export verification history as CSV"""
    import csv
    import io

    from fastapi.responses import StreamingResponse

    try:
        # Build query
        query = db.query(Verification).filter(Verification.user_id == user_id)

        if service:
            query = query.filter(Verification.service_name == service)
        if verification_status:
            query = query.filter(Verification.status == verification_status)

        # Date range filtering
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(Verification.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # Add 1 day to include the entire end date
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Verification.created_at <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

        # Limit to prevent abuse
        MAX_EXPORT = 10000
        total = query.count()

        if total > MAX_EXPORT:
            raise HTTPException(
                status_code=400,
                detail=f"Export limited to {MAX_EXPORT} records. Please narrow your date range. Found {total} records."
            )

        if total == 0:
            raise HTTPException(status_code=404, detail="No verifications found for export")

        # Get all verifications
        verifications = query.order_by(Verification.created_at.desc()).all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID',
            'Service',
            'Phone Number',
            'Country',
            'Operator',
            'Status',
            'Cost',
            'Pricing Tier',
            'Provider',
            'Created At',
            'Completed At',
            'SMS Code',
            'Area Code'
        ])

        # Write data
        for v in verifications:
            writer.writerow([
                v.id,
                v.service_name,
                v.phone_number or '',
                v.country or '',
                getattr(v, 'operator', '') or '',
                v.status,
                f"${v.cost:.2f}",
                getattr(v, 'pricing_tier', 'standard') or 'standard',
                getattr(v, 'provider', '5sim') or '5sim',
                v.created_at.strftime('%Y-%m-%d %H:%M:%S') if v.created_at else '',
                v.completed_at.strftime('%Y-%m-%d %H:%M:%S') if v.completed_at else '',
                getattr(v, 'sms_code', '') or '',
                v.requested_area_code or ''
            ])

        # Prepare response
        output.seek(0)

        # Generate filename
        filename = f"namaskah_verifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Export failed. Please try again.")


@router.get("/analytics")
async def get_verification_analytics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's verification analytics and success rates"""
    try:
        # Get all user verifications
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

        # Calculate overall success rate
        total = len(verifications)
        successful = sum(1 for v in verifications if v.status == "completed")
        failed = sum(1 for v in verifications if v.status in ["failed", "timeout", "cancelled"])
        overall_rate = (successful / total * 100) if total > 0 else 0.0

        # Success rate by service
        by_service = {}
        for v in verifications:
            service = v.service_name
            if service not in by_service:
                by_service[service] = {"total": 0, "successful": 0, "rate": 0.0}

            by_service[service]["total"] += 1
            if v.status == "completed":
                by_service[service]["successful"] += 1

        # Calculate rates
        for service in by_service:
            total_s = by_service[service]["total"]
            successful_s = by_service[service]["successful"]
            by_service[service]["rate"] = (successful_s / total_s * 100) if total_s > 0 else 0.0

        # Sort by total usage
        by_service = dict(sorted(by_service.items(), key=lambda x: x[1]["total"], reverse=True)[:10])

        # Success rate by country
        by_country = {}
        for v in verifications:
            country = v.country or "unknown"
            if country not in by_country:
                by_country[country] = {"total": 0, "successful": 0, "rate": 0.0}

            by_country[country]["total"] += 1
            if v.status == "completed":
                by_country[country]["successful"] += 1

        # Calculate rates
        for country in by_country:
            total_c = by_country[country]["total"]
            successful_c = by_country[country]["successful"]
            by_country[country]["rate"] = (successful_c / total_c * 100) if total_c > 0 else 0.0

        # Sort by total usage
        by_country = dict(sorted(by_country.items(), key=lambda x: x[1]["total"], reverse=True)[:10])

        # Recent trend (last 30 days, grouped by day)
        from datetime import timedelta
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_verifications = [v for v in verifications if v.created_at >= thirty_days_ago]

        # Group by date
        trend = {}
        for v in recent_verifications:
            date_key = v.created_at.strftime("%Y-%m-%d")
            if date_key not in trend:
                trend[date_key] = {"total": 0, "successful": 0}

            trend[date_key]["total"] += 1
            if v.status == "completed":
                trend[date_key]["successful"] += 1

        # Convert to list and calculate rates
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
        # Return empty analytics instead of crashing
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


@router.get("/history")
async def get_sms_history(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get SMS history for user"""
    try:
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.status == "completed"
        ).order_by(Verification.created_at.desc()).all()

        history = []
        for v in verifications:
            history.append({
                "id": v.id,
                "type": "verification",
                "to": v.phone_number or "N/A",
                "from": v.service_name or "Unknown",
                "body": f"Your {v.service_name} verification code is ready",
                "code": getattr(v, 'sms_code', None) or getattr(v, 'verification_code', None),
                "service": v.service_name,
                "country": v.country,
                "created_at": v.created_at.isoformat() if v.created_at else None
            })

        return {
            "success": True,
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get SMS history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve SMS history")


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification and refund credits"""
    verification = (
        db.query(Verification)
        .filter(Verification.id == verification_id, Verification.user_id == user_id)
        .first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status in ["cancelled", "completed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel {verification.status} verification"
        )

    # Cancel on 5SIM if activation ID exists
    if verification.verification_code:
        try:
            fivesim = FiveSimService()
            activation_id = int(verification.verification_code)
            await fivesim.cancel_activation(activation_id)
        except ExternalServiceError as e:
            logger.warning(f"5SIM cancel failed for {activation_id}: {str(e)}")
            # Continue with local cancellation even if 5SIM fails
        except Exception as e:
            logger.warning(f"Unexpected cancel error for {activation_id}: {str(e)}")

    # Refund credits
    current_user = db.query(User).filter(User.id == user_id).first()
    if verification.cost > 0:
        current_user.credits += verification.cost
    else:
        # Restore free verification if it was used
        current_user.free_verifications += 1

    verification.status = "cancelled"
    db.commit()

    # Stop polling for this verification
    from app.services.sms_polling_service import sms_polling_service
    await sms_polling_service.stop_polling(verification_id)

    return SuccessResponse(
        message="Verification cancelled and refunded",
        data={"refunded": verification.cost, "new_balance": current_user.credits},
    )
