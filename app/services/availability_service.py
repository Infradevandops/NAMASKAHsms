"""Service availability tracking for SMS verification success rates."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.verification import Verification

logger = get_logger(__name__)


class AvailabilityService:
    """Track and report SMS verification success rates."""

    def __init__(self, db: Session):
        self.db = db

    def get_service_availability(self, service: str, country: str = None, hours: int = 24) -> Dict:
        """Get availability stats for a service.

        Returns:
            success_rate: 0-100%
            avg_delivery_time: seconds
            total_attempts: count
            status: excellent/good/fair/poor
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = self.db.query(Verification).filter(
            Verification.service_name == service, Verification.created_at >= cutoff
        )

        if country:
            query = query.filter(Verification.country == country)

        verifications = query.all()

        if not verifications:
            return {
                "success_rate": 0,
                "avg_delivery_time": 0,
                "total_attempts": 0,
                "status": "unknown",
                "confidence": "low",
            }

        total = len(verifications)
        completed = sum(1 for v in verifications if v.status == "completed")
        success_rate = (completed / total * 100) if total > 0 else 0

        # Calculate avg delivery time for completed
        delivery_times = []
        for v in verifications:
            if v.status == "completed" and v.completed_at and v.created_at:
                delta = (v.completed_at - v.created_at).total_seconds()
                delivery_times.append(delta)

        avg_delivery = sum(delivery_times) / len(delivery_times) if delivery_times else 0

        # Determine status
        if success_rate >= 90:
            status = "excellent"
        elif success_rate >= 75:
            status = "good"
        elif success_rate >= 50:
            status = "fair"
        else:
            status = "poor"

        # Confidence based on sample size
        if total >= 50:
            confidence = "high"
        elif total >= 20:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "success_rate": round(success_rate, 1),
            "avg_delivery_time": round(avg_delivery, 1),
            "total_attempts": total,
            "status": status,
            "confidence": confidence,
        }

    def get_country_availability(self, country: str, hours: int = 24) -> Dict:
        """Get availability stats for a country."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        verifications = (
            self.db.query(Verification).filter(Verification.country == country, Verification.created_at >= cutoff).all()
        )

        if not verifications:
            return {"success_rate": 0, "status": "unknown"}

        total = len(verifications)
        completed = sum(1 for v in verifications if v.status == "completed")
        success_rate = (completed / total * 100) if total > 0 else 0

        if success_rate >= 85:
            status = "excellent"
        elif success_rate >= 70:
            status = "good"
        elif success_rate >= 50:
            status = "fair"
        else:
            status = "poor"

        return {
            "success_rate": round(success_rate, 1),
            "total_attempts": total,
            "status": status,
        }

    def get_carrier_availability(self, carrier: str, country: str = None, hours: int = 24) -> Dict:
        """Get availability stats for a carrier."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = self.db.query(Verification).filter(Verification.operator == carrier, Verification.created_at >= cutoff)

        if country:
            query = query.filter(Verification.country == country)

        verifications = query.all()

        if not verifications:
            return {"success_rate": 90, "total": 0, "status": "unknown"}

        total = len(verifications)
        completed = sum(1 for v in verifications if v.status == "completed")
        success_rate = (completed / total * 100) if total > 0 else 0

        if success_rate >= 85:
            status = "excellent"
        elif success_rate >= 70:
            status = "good"
        else:
            status = "poor"

        return {
            "success_rate": round(success_rate, 1),
            "total": total,
            "status": status,
        }

    def get_area_code_availability(self, area_code: str, country: str = None, hours: int = 24) -> Dict:
        """Get availability stats for an area code."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = self.db.query(Verification).filter(
            Verification.requested_area_code == area_code,
            Verification.created_at >= cutoff,
        )

        if country:
            query = query.filter(Verification.country == country)

        verifications = query.all()

        if not verifications:
            return {"success_rate": 90, "total": 0, "status": "unknown"}

        total = len(verifications)
        completed = sum(1 for v in verifications if v.status == "completed")
        success_rate = (completed / total * 100) if total > 0 else 0

        if success_rate >= 85:
            status = "excellent"
        elif success_rate >= 70:
            status = "good"
        else:
            status = "poor"

        return {
            "success_rate": round(success_rate, 1),
            "total": total,
            "status": status,
        }

    def get_top_services(self, country: str = None, limit: int = 10) -> List[Dict]:
        """Get top performing services by success rate."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        query = self.db.query(
            Verification.service_name,
            func.count(Verification.id).label("total"),
            func.sum(func.case((Verification.status == "completed", 1), else_=0)).label("completed"),
        ).filter(Verification.created_at >= cutoff)

        if country:
            query = query.filter(Verification.country == country)

        results = (
            query.group_by(Verification.service_name).having(func.count(Verification.id) >= 5).all()  # Min 5 attempts
        )

        services = []
        for service_name, total, completed in results:
            success_rate = (completed / total * 100) if total > 0 else 0
            services.append(
                {
                    "service": service_name,
                    "success_rate": round(success_rate, 1),
                    "total_attempts": total,
                }
            )

        # Sort by success rate
        services.sort(key=lambda x: x["success_rate"], reverse=True)
        return services[:limit]

    def get_availability_summary(self, service: str, country: str, carrier: str = None) -> Dict:
        """Get comprehensive availability summary for UI display."""
        service_stats = self.get_service_availability(service, country)
        country_stats = self.get_country_availability(country)

        carrier_stats = None
        if carrier and carrier != "Any Carrier":
            carrier_stats = self.get_carrier_availability(carrier, country)

        # Overall recommendation
        min_success = min(
            service_stats["success_rate"],
            country_stats["success_rate"],
            carrier_stats["success_rate"] if carrier_stats else 100,
        )

        if min_success >= 85:
            recommendation = "excellent"
            message = "High success rate - Recommended"
        elif min_success >= 70:
            recommendation = "good"
            message = "Good success rate"
        elif min_success >= 50:
            recommendation = "fair"
            message = "Moderate success rate - May experience delays"
        else:
            recommendation = "poor"
            message = "Low success rate - Consider alternative"

        return {
            "service": service_stats,
            "country": country_stats,
            "carrier": carrier_stats,
            "overall": {
                "recommendation": recommendation,
                "message": message,
                "min_success_rate": round(min_success, 1),
            },
        }
