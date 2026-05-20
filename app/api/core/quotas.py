import logging

logger = logging.getLogger(__name__)
"""Usage quotas endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/api/quotas", tags=["Quotas"])


def get_tier_limits(tier: str):
    """Get quota limits for a tier."""
    limits = {
        "freemium": {
            "sms_monthly": 3000,  # High limit — wallet balance is the natural cap
            "api_daily": 0,
            "api_keys": 0,
            "webhooks": 0,
            "voice_monthly": 0,
            "rentals": 0,
        },
        "payg": {
            "sms_monthly": -1,  # Unlimited
            "api_daily": 0,
            "api_keys": 0,
            "webhooks": 3,
            "voice_monthly": -1,
            "rentals": 0,
        },
        "pro": {
            "sms_monthly": -1,
            "api_daily": 10000,
            "api_keys": 10,
            "webhooks": 10,
            "voice_monthly": -1,
            "rentals": 5,
        },
        "custom": {
            "sms_monthly": -1,
            "api_daily": 50000,
            "api_keys": -1,
            "webhooks": -1,
            "voice_monthly": -1,
            "rentals": 20,
        },
    }
    return limits.get(tier, limits["freemium"])


@router.get("/current")
async def get_current_quotas(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        """Get current usage quotas."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier = getattr(user, "subscription_tier", "freemium") or "freemium"
        limits = get_tier_limits(tier)

        # Calculate usage
        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        sms_used = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id, Verification.created_at >= month_start
            )
            .count()
        )

        # Mock API usage (would track in production)
        api_used = 0

        # Mock API keys count
        api_keys_used = 0

        # Mock webhooks count
        webhooks_used = 0

        # Generate alerts
        alerts = []
        sms_percentage = (
            (sms_used / limits["sms_monthly"] * 100) if limits["sms_monthly"] > 0 else 0
        )
        if sms_percentage >= 90:
            alerts.append(
                {
                    "severity": "danger",
                    "title": "SMS Quota Critical",
                    "message": f"You've used {sms_percentage:.0f}% of your monthly SMS quota. Consider upgrading your plan.",
                }
            )
        elif sms_percentage >= 75:
            alerts.append(
                {
                    "severity": "warning",
                    "title": "SMS Quota Warning",
                    "message": f"You've used {sms_percentage:.0f}% of your monthly SMS quota.",
                }
            )

        # Tier descriptions
        tier_descriptions = {
            "freemium": "Free tier with basic features",
            "payg": "Pay-as-you-go with no monthly commitment",
            "pro": "Professional tier with advanced features",
            "custom": "Custom tier with unlimited resources",
        }

        return {
            "tier": {
                "name": tier.upper(),
                "description": tier_descriptions.get(tier, ""),
            },
            "sms_quota": {
                "used": sms_used,
                "limit": limits["sms_monthly"],
                "reset_date": (month_start + timedelta(days=32))
                .replace(day=1)
                .isoformat(),
            },
            "api_quota": {"used": api_used, "limit": limits["api_daily"]},
            "api_keys": {"used": api_keys_used, "limit": limits["api_keys"]},
            "webhooks": {"used": webhooks_used, "limit": limits["webhooks"]},
            "voice_quota": {"used": 0, "limit": limits["voice_monthly"]},
            "rentals": {"used": 0, "limit": limits["rentals"]},
            "alerts": alerts,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_quotas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history")
async def get_usage_history(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        """Get usage history for the last N days."""
        from sqlalchemy import Date, cast, func

        start_date = datetime.now() - timedelta(days=days)

        # Get daily SMS usage
        sms_usage = (
            db.query(
                cast(Verification.created_at, Date).label("date"),
                func.count(Verification.id).label("count"),
            )
            .filter(
                Verification.user_id == user_id, Verification.created_at >= start_date
            )
            .group_by(cast(Verification.created_at, Date))
            .all()
        )

        # Create date range
        dates = []
        sms_data = []
        api_data = []

        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i - 1)).date()
            dates.append(date.strftime("%m/%d"))

            # Find SMS count for this date
            sms_count = next((item.count for item in sms_usage if item.date == date), 0)
            sms_data.append(sms_count)

            # Mock API data
            api_data.append(0)

        return {"dates": dates, "sms_usage": sms_data, "api_usage": api_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_usage_history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/overage")
async def get_overage_charges(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        """Get estimated overage charges."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier = getattr(user, "subscription_tier", "freemium") or "freemium"
        limits = get_tier_limits(tier)

        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        sms_used = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id, Verification.created_at >= month_start
            )
            .count()
        )

        overage = 0
        overage_cost = 0.0

        if limits["sms_monthly"] > 0 and sms_used > limits["sms_monthly"]:
            overage = sms_used - limits["sms_monthly"]
            # Pro: $1.80/SMS overage (23% margin), Custom: $1.50/SMS (2.7% margin)
            rate = 1.80 if tier == "pro" else 1.50
            overage_cost = round(overage * rate, 2)

        return {
            "has_overage": overage > 0,
            "overage_count": overage,
            "overage_cost": overage_cost,
            "tier": tier,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_overage_charges: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
