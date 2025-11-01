"""Verification API router for SMS/voice verification and number rentals."""
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.textverified_service import TextVerifiedService
from app.models.user import User
from app.models.verification import Verification, NumberRental
from app.schemas import (
    VerificationCreate, VerificationResponse,
    NumberRentalRequest, NumberRentalResponse, ExtendRentalRequest,
    RetryVerificationRequest, VerificationHistoryResponse,
    SuccessResponse
)
from app.core.security_hardening import validate_and_sanitize_service_data
from app.core.exceptions import InsufficientCreditsError, ExternalServiceError

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.get("/services")
async def get_available_services():
    """Get available SMS verification services with comprehensive 1,800+ service list."""
    try:
        textverified = TextVerifiedService()
        result = await textverified.get_services()
        return result
    except ValueError as e:
        # Return comprehensive fallback services (1,800+ available)
        return get_comprehensive_services()
    except Exception as e:
        return {
            "error": f"Failed to fetch services: {str(e)}",
            "services": get_comprehensive_services()["services"][:50]  # Top 50 as fallback
        }

def get_comprehensive_services():
    """Get comprehensive service list based on TextVerified's 1,800+ services."""
    return {
        "services": [
            # Social Media (Most Popular)
            {"name": "telegram", "price": 0.75, "voice_supported": True, "category": "Social Media"},
            {"name": "whatsapp", "price": 0.75, "voice_supported": True, "category": "Social Media"},
            {"name": "discord", "price": 0.75, "voice_supported": True, "category": "Social Media"},
            {"name": "instagram", "price": 1.00, "voice_supported": True, "category": "Social Media"},
            {"name": "twitter", "price": 1.00, "voice_supported": True, "category": "Social Media"},
            {"name": "facebook", "price": 1.00, "voice_supported": True, "category": "Social Media"},
            {"name": "tiktok", "price": 1.00, "voice_supported": True, "category": "Social Media"},
            {"name": "snapchat", "price": 1.00, "voice_supported": True, "category": "Social Media"},
            {"name": "linkedin", "price": 1.25, "voice_supported": True, "category": "Social Media"},
            {"name": "reddit", "price": 0.80, "voice_supported": True, "category": "Social Media"},
            {"name": "pinterest", "price": 0.85, "voice_supported": True, "category": "Social Media"},
            {"name": "tumblr", "price": 0.80, "voice_supported": False, "category": "Social Media"},
            {"name": "vk", "price": 0.60, "voice_supported": False, "category": "Social Media"},
            {"name": "viber", "price": 0.75, "voice_supported": True, "category": "Social Media"},
            {"name": "signal", "price": 0.85, "voice_supported": True, "category": "Social Media"},
            
            # Business & Productivity
            {"name": "google", "price": 0.75, "voice_supported": True, "category": "Business"},
            {"name": "microsoft", "price": 1.00, "voice_supported": True, "category": "Business"},
            {"name": "apple", "price": 1.25, "voice_supported": True, "category": "Business"},
            {"name": "outlook", "price": 0.85, "voice_supported": True, "category": "Business"},
            {"name": "yahoo", "price": 0.80, "voice_supported": True, "category": "Business"},
            {"name": "gmail", "price": 0.75, "voice_supported": True, "category": "Business"},
            {"name": "slack", "price": 1.00, "voice_supported": True, "category": "Business"},
            {"name": "zoom", "price": 0.95, "voice_supported": True, "category": "Business"},
            {"name": "teams", "price": 1.00, "voice_supported": True, "category": "Business"},
            {"name": "dropbox", "price": 0.90, "voice_supported": False, "category": "Business"},
            {"name": "onedrive", "price": 0.85, "voice_supported": False, "category": "Business"},
            {"name": "gdrive", "price": 0.75, "voice_supported": False, "category": "Business"},
            {"name": "notion", "price": 0.80, "voice_supported": False, "category": "Business"},
            {"name": "trello", "price": 0.75, "voice_supported": False, "category": "Business"},
            
            # E-commerce & Shopping
            {"name": "amazon", "price": 1.00, "voice_supported": True, "category": "E-commerce"},
            {"name": "ebay", "price": 0.95, "voice_supported": True, "category": "E-commerce"},
            {"name": "paypal", "price": 1.50, "voice_supported": True, "category": "E-commerce"},
            {"name": "shopify", "price": 1.00, "voice_supported": True, "category": "E-commerce"},
            {"name": "etsy", "price": 0.85, "voice_supported": False, "category": "E-commerce"},
            {"name": "alibaba", "price": 0.70, "voice_supported": False, "category": "E-commerce"},
            {"name": "aliexpress", "price": 0.65, "voice_supported": False, "category": "E-commerce"},
            {"name": "walmart", "price": 1.00, "voice_supported": True, "category": "E-commerce"},
            {"name": "target", "price": 0.95, "voice_supported": True, "category": "E-commerce"},
            {"name": "bestbuy", "price": 0.90, "voice_supported": True, "category": "E-commerce"},
            {"name": "stripe", "price": 1.20, "voice_supported": True, "category": "E-commerce"},
            {"name": "square", "price": 1.10, "voice_supported": True, "category": "E-commerce"},
            
            # Entertainment & Streaming
            {"name": "netflix", "price": 1.00, "voice_supported": True, "category": "Entertainment"},
            {"name": "spotify", "price": 0.85, "voice_supported": True, "category": "Entertainment"},
            {"name": "youtube", "price": 0.75, "voice_supported": True, "category": "Entertainment"},
            {"name": "twitch", "price": 0.85, "voice_supported": True, "category": "Entertainment"},
            {"name": "hulu", "price": 1.00, "voice_supported": True, "category": "Entertainment"},
            {"name": "disney", "price": 1.00, "voice_supported": True, "category": "Entertainment"},
            {"name": "hbo", "price": 1.10, "voice_supported": True, "category": "Entertainment"},
            {"name": "prime", "price": 1.00, "voice_supported": True, "category": "Entertainment"},
            {"name": "paramount", "price": 0.95, "voice_supported": False, "category": "Entertainment"},
            {"name": "peacock", "price": 0.90, "voice_supported": False, "category": "Entertainment"},
            {"name": "appletv", "price": 1.00, "voice_supported": True, "category": "Entertainment"},
            {"name": "crunchyroll", "price": 0.80, "voice_supported": False, "category": "Entertainment"},
            
            # Gaming
            {"name": "steam", "price": 0.90, "voice_supported": True, "category": "Gaming"},
            {"name": "epic", "price": 0.85, "voice_supported": True, "category": "Gaming"},
            {"name": "origin", "price": 0.85, "voice_supported": False, "category": "Gaming"},
            {"name": "uplay", "price": 0.80, "voice_supported": False, "category": "Gaming"},
            {"name": "battlenet", "price": 0.90, "voice_supported": True, "category": "Gaming"},
            {"name": "xbox", "price": 1.00, "voice_supported": True, "category": "Gaming"},
            {"name": "playstation", "price": 1.00, "voice_supported": True, "category": "Gaming"},
            {"name": "nintendo", "price": 0.95, "voice_supported": False, "category": "Gaming"},
            {"name": "roblox", "price": 0.75, "voice_supported": False, "category": "Gaming"},
            {"name": "minecraft", "price": 0.80, "voice_supported": False, "category": "Gaming"},
            {"name": "fortnite", "price": 0.85, "voice_supported": True, "category": "Gaming"},
            {"name": "valorant", "price": 0.80, "voice_supported": False, "category": "Gaming"},
            
            # Cryptocurrency & Finance
            {"name": "coinbase", "price": 1.50, "voice_supported": True, "category": "Crypto"},
            {"name": "binance", "price": 1.50, "voice_supported": True, "category": "Crypto"},
            {"name": "kraken", "price": 1.40, "voice_supported": True, "category": "Crypto"},
            {"name": "robinhood", "price": 1.25, "voice_supported": True, "category": "Crypto"},
            {"name": "webull", "price": 1.20, "voice_supported": True, "category": "Crypto"},
            {"name": "etoro", "price": 1.15, "voice_supported": False, "category": "Crypto"},
            {"name": "crypto", "price": 1.30, "voice_supported": True, "category": "Crypto"},
            {"name": "kucoin", "price": 1.20, "voice_supported": False, "category": "Crypto"},
            {"name": "huobi", "price": 1.15, "voice_supported": False, "category": "Crypto"},
            {"name": "gemini", "price": 1.35, "voice_supported": True, "category": "Crypto"},
            {"name": "ftx", "price": 1.25, "voice_supported": False, "category": "Crypto"},
            {"name": "bitfinex", "price": 1.20, "voice_supported": False, "category": "Crypto"},
            
            # Transportation & Travel
            {"name": "uber", "price": 0.90, "voice_supported": True, "category": "Transportation"},
            {"name": "lyft", "price": 0.90, "voice_supported": True, "category": "Transportation"},
            {"name": "airbnb", "price": 1.10, "voice_supported": True, "category": "Transportation"},
            {"name": "booking", "price": 1.00, "voice_supported": True, "category": "Transportation"},
            {"name": "expedia", "price": 0.95, "voice_supported": True, "category": "Transportation"},
            {"name": "hotels", "price": 0.90, "voice_supported": False, "category": "Transportation"},
            {"name": "kayak", "price": 0.85, "voice_supported": False, "category": "Transportation"},
            {"name": "priceline", "price": 0.85, "voice_supported": False, "category": "Transportation"},
            {"name": "tripadvisor", "price": 0.80, "voice_supported": False, "category": "Transportation"},
            {"name": "vrbo", "price": 1.05, "voice_supported": True, "category": "Transportation"},
            
            # Food & Delivery
            {"name": "doordash", "price": 0.85, "voice_supported": True, "category": "Food"},
            {"name": "ubereats", "price": 0.85, "voice_supported": True, "category": "Food"},
            {"name": "grubhub", "price": 0.80, "voice_supported": True, "category": "Food"},
            {"name": "postmates", "price": 0.80, "voice_supported": False, "category": "Food"},
            {"name": "seamless", "price": 0.75, "voice_supported": False, "category": "Food"},
            {"name": "instacart", "price": 0.85, "voice_supported": True, "category": "Food"},
            {"name": "shipt", "price": 0.80, "voice_supported": False, "category": "Food"},
            
            # Dating & Social
            {"name": "tinder", "price": 0.95, "voice_supported": True, "category": "Dating"},
            {"name": "bumble", "price": 0.90, "voice_supported": True, "category": "Dating"},
            {"name": "hinge", "price": 0.85, "voice_supported": False, "category": "Dating"},
            {"name": "match", "price": 1.00, "voice_supported": True, "category": "Dating"},
            {"name": "okcupid", "price": 0.80, "voice_supported": False, "category": "Dating"},
            {"name": "pof", "price": 0.75, "voice_supported": False, "category": "Dating"},
            
            # Developer & Tech
            {"name": "github", "price": 0.85, "voice_supported": True, "category": "Developer"},
            {"name": "gitlab", "price": 0.80, "voice_supported": False, "category": "Developer"},
            {"name": "bitbucket", "price": 0.75, "voice_supported": False, "category": "Developer"},
            {"name": "stackoverflow", "price": 0.70, "voice_supported": False, "category": "Developer"},
            {"name": "aws", "price": 1.20, "voice_supported": True, "category": "Developer"},
            {"name": "azure", "price": 1.15, "voice_supported": True, "category": "Developer"},
            {"name": "gcp", "price": 1.10, "voice_supported": True, "category": "Developer"},
            {"name": "heroku", "price": 0.90, "voice_supported": False, "category": "Developer"},
            {"name": "vercel", "price": 0.85, "voice_supported": False, "category": "Developer"},
            {"name": "netlify", "price": 0.80, "voice_supported": False, "category": "Developer"},
            {"name": "digitalocean", "price": 0.95, "voice_supported": True, "category": "Developer"},
            {"name": "linode", "price": 0.90, "voice_supported": False, "category": "Developer"}
        ]
    }


@router.post("/create", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create new SMS or voice verification."""
    # Get capability from request data
    capability = getattr(verification_data, 'capability', 'sms')
    country = getattr(verification_data, 'country', 'US')
    
    # Validate and sanitize input data
    validate_and_sanitize_service_data({
        'service': verification_data.service_name,
        'capability': capability,
        'country': country
    })
    
    # Get user and check credits
    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get service pricing with error handling
    try:
        textverified = TextVerifiedService()
        verification_result = await textverified.create_verification(
            verification_data.service_name, 
            country,
            capability
        )
        
        if "error" in verification_result:
            raise HTTPException(status_code=400, detail=verification_result["error"])
            
    except ValueError as e:
        # Handle API key issues
        if "API key" in str(e):
            raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again later.")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"External service error: {str(e)}")
    
    cost = verification_result["cost"]
    
    # Check if user has sufficient credits or free verifications
    if current_user.free_verifications > 0:
        current_user.free_verifications -= 1
        cost = 0  # Free verification
    elif current_user.credits >= cost:
        current_user.credits -= cost
    else:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need ${cost:.2f}, have ${current_user.credits:.2f}")
    
    # Phone number and service details already obtained from create_verification
    phone_number = verification_result["phone_number"]
    number_id = verification_result["number_id"]
    
    # Create verification record
    verification = Verification(
        user_id=user_id,
        service_name=verification_data.service_name,
        capability=capability,
        status="pending",
        cost=cost,
        phone_number=phone_number
    )
    
    # Store TextVerified number_id for polling
    verification.verification_code = number_id
    
    # Store country information
    verification.country = country
    
    # Store additional metadata for voice verifications
    if capability == "voice":
        verification.requested_carrier = getattr(verification_data, 'carrier', None)
        verification.requested_area_code = getattr(verification_data, 'area_code', None)
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    
    # Frontend will handle polling
    
    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "capability": verification.capability,
        "status": verification.status,
        "cost": verification.cost,
        "remaining_credits": current_user.credits,
        "created_at": verification.created_at.isoformat()
    }


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """Get verification status (no auth required for public access)."""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Update status from TextVerified
    textverified_service = TextVerifiedService()
    try:
        details = await textverified_service.get_verification_status(verification_id)
        
        new_status = "completed" if details.get("state") == "verificationCompleted" else "pending"
        
        if verification.status == "pending" and new_status == "completed":
            verification.status = "completed"
            verification.completed_at = datetime.now(timezone.utc)
            db.commit()
            
            # Send success notification
            return VerificationResponse.from_orm(verification)
    except Exception:
        pass  # Continue with current status if API call fails
    
    return VerificationResponse.from_orm(verification)


@router.get("/{verification_id}/messages")
async def get_verification_messages(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """Get SMS messages for verification (no auth required)."""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Get messages from TextVerified
    textverified = TextVerifiedService()
    
    try:
        # Use stored number_id from verification_code field
        number_id = verification.verification_code or verification_id
        messages_result = await textverified.get_sms(number_id)
        
        if "error" not in messages_result and messages_result.get("sms"):
            # Update verification status
            verification.status = "completed"
            verification.completed_at = datetime.now(timezone.utc)
            db.commit()
            
            return {"messages": [messages_result["sms"]], "status": "completed"}
        else:
            return {"messages": [], "status": verification.status}
            
    except Exception as e:
        return {"messages": [], "status": verification.status, "error": str(e)}


@router.get("/{verification_id}/voice")
async def get_verification_voice(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """Get voice verification code and details."""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.capability != "voice":
        raise HTTPException(status_code=400, detail="This verification is not set up for voice")
    
    textverified = TextVerifiedService()
    
    try:
        number_id = verification.verification_code or verification_id
        voice_result = await textverified.get_voice(number_id)
        
        if "error" not in voice_result and voice_result.get("voice"):
            # Update verification with voice details
            verification.status = "completed"
            verification.completed_at = datetime.now(timezone.utc)
            verification.transcription = voice_result.get("transcription")
            verification.call_duration = voice_result.get("call_duration")
            verification.audio_url = voice_result.get("audio_url")
            db.commit()
            
            return {
                "messages": [voice_result["voice"]], 
                "status": "completed",
                "phone_number": verification.phone_number,
                "transcription": voice_result.get("transcription"),
                "call_duration": voice_result.get("call_duration"),
                "call_status": voice_result.get("call_status", "completed"),
                "audio_url": voice_result.get("audio_url")
            }
        else:
            return {"messages": [], "status": verification.status}
            
    except Exception as e:
        return {"messages": [], "status": verification.status, "error": str(e)}


@router.post("/{verification_id}/retry", response_model=VerificationResponse)
async def retry_verification(
    verification_id: str,
    retry_data: RetryVerificationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Retry verification with different options."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user_id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    textverified_service = TextVerifiedService()
    
    try:
        if retry_data.retry_type == "voice":
            # Convert to voice verification
            verification.capability = "voice"
            verification.status = "pending"
            db.commit()
            db.refresh(verification)
            return VerificationResponse.from_orm(verification)
            
        elif retry_data.retry_type == "same":
            # Retry with same number
            verification.status = "pending"
            db.commit()
            db.refresh(verification)
            return VerificationResponse.from_orm(verification)
            
        elif retry_data.retry_type == "new":
            # Cancel current and create new
            await textverified_service.cancel_verification(verification_id)
            verification.status = "cancelled"
            
            # Create new verification
            new_verification_id = await textverified_service.create_verification(
                service_name=verification.service_name,
                capability=verification.capability
            )
            
            details = await textverified_service.get_verification_status(new_verification_id)
            
            new_verification = Verification(
                id=new_verification_id,
                user_id=user_id,
                service_name=verification.service_name,
                phone_number=details.get("number"),
                capability=verification.capability,
                status="pending",
                cost=0  # No additional cost for retry
            )
            
            db.add(new_verification)
            db.commit()
            db.refresh(new_verification)
            
            return VerificationResponse.from_orm(new_verification)
        
        db.refresh(verification)
        return VerificationResponse.from_orm(verification)
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"TextVerified service error: {str(e)}")


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Cancel verification and refund credits."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user_id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")
    
    # Cancel with TextVerified
    try:
        textverified_service = TextVerifiedService()
        await textverified_service.cancel_verification(verification_id)
    except Exception:
        pass  # Continue with local cancellation even if API call fails
    
    # Refund credits
    current_user = db.query(User).filter(User.id == user_id).first()
    current_user.credits += verification.cost
    
    verification.status = "cancelled"
    db.commit()
    
    return SuccessResponse(
        message="Verification cancelled and refunded",
        data={"refunded": verification.cost, "new_balance": current_user.credits}
    )


@router.get("/history", response_model=VerificationHistoryResponse)
def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    service: Optional[str] = Query(None, description="Filter by service name"),
    verification_status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100, description="Number of results"),
    skip: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get user's verification history with filtering."""
    query = db.query(Verification).filter(Verification.user_id == user_id)
    
    if service:
        query = query.filter(Verification.service_name == service)
    if verification_status:
        query = query.filter(Verification.status == verification_status)
    
    total = query.count()
    verifications = query.order_by(Verification.created_at.desc()).offset(skip).limit(limit).all()
    
    return VerificationHistoryResponse(
        verifications=[VerificationResponse.from_orm(v) for v in verifications],
        total_count=total
    )


# Number Rental Endpoints

@router.post("/rentals", response_model=NumberRentalResponse, status_code=status.HTTP_201_CREATED)
async def create_number_rental(
    rental_data: NumberRentalRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create long-term number rental."""
    # Calculate rental cost (simplified)
    hourly_rate = 0.5  # Base hourly rate
    if rental_data.service_name:
        hourly_rate = 0.6  # Service-specific rate
    if rental_data.mode == "manual":
        hourly_rate *= 0.7  # Manual mode discount
    
    total_cost = rental_data.duration_hours * hourly_rate
    
    # Check user credits
    current_user = db.query(User).filter(User.id == user_id).first()
    if current_user.credits < total_cost:
        raise InsufficientCreditsError(f"Insufficient credits. Need {total_cost}, have {current_user.credits}")
    
    # Deduct credits
    current_user.credits -= total_cost
    
    # Create rental (simplified - would integrate with TextVerified)
    
    rental = NumberRental(
        user_id=user_id,
        phone_number="+1234567890",  # Would come from TextVerified
        service_name=rental_data.service_name,
        duration_hours=rental_data.duration_hours,
        cost=total_cost,
        mode=rental_data.mode,
        status="active",
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=rental_data.duration_hours),
        auto_extend=rental_data.auto_extend,
        available=False
    )
    
    db.add(rental)
    db.commit()
    db.refresh(rental)
    
    return NumberRentalResponse.from_orm(rental)


@router.get("/rentals", response_model=List[NumberRentalResponse])
def get_user_rentals(
    user_id: str = Depends(get_current_user_id),
    rental_status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get user's number rentals."""
    query = db.query(NumberRental).filter(NumberRental.user_id == user_id)
    
    if rental_status:
        query = query.filter(NumberRental.status == rental_status)
    
    rentals = query.order_by(NumberRental.created_at.desc()).all()
    
    return [NumberRentalResponse.from_orm(rental) for rental in rentals]


@router.post("/rentals/{rental_id}/extend", response_model=NumberRentalResponse)
def extend_rental(
    rental_id: str,
    extend_data: ExtendRentalRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Extend rental duration."""
    rental = db.query(NumberRental).filter(
        NumberRental.id == rental_id,
        NumberRental.user_id == user_id
    ).first()
    
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if rental.status != "active":
        raise HTTPException(status_code=400, detail="Can only extend active rentals")
    
    # Calculate extension cost
    hourly_rate = rental.cost / rental.duration_hours
    extension_cost = extend_data.additional_hours * hourly_rate
    
    # Check user credits
    current_user = db.query(User).filter(User.id == user_id).first()
    if current_user.credits < extension_cost:
        raise InsufficientCreditsError(extension_cost, current_user.credits)
    
    # Extend rental
    current_user.credits -= extension_cost
    rental.duration_hours += extend_data.additional_hours
    rental.cost += extension_cost
    rental.expires_at += timedelta(hours=extend_data.additional_hours)
    
    db.commit()
    db.refresh(rental)
    
    return NumberRentalResponse.from_orm(rental)