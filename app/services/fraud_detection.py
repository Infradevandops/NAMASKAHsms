"""Fraud detection system for verification requests."""
from typing import Dict
from datetime import datetime, timedelta
from app.core.database import get_db


class FraudDetector:
    """AI - powered fraud detection system."""

    def __init__(self):
        self.risk_thresholds = {
            "high_frequency": 10,  # requests per hour
            "suspicious_patterns": 5,  # similar requests
            "cost_threshold": 50.0  # high spending
        }

    async def analyze_request(self, user_id: int,
                              service: str, ip_address: str) -> Dict:
        """Analyze verification request for fraud indicators."""
        db = next(get_db())

        risk_score = 0
        flags = []

        # Check request frequency
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_requests = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= hour_ago
        ).count()

        if recent_requests > self.risk_thresholds["high_frequency"]:
            risk_score += 30
            flags.append("high_frequency")

        # Check for suspicious patterns
        day_ago = datetime.utcnow() - timedelta(days=1)
        same_service_requests = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.service_name == service,
            Verification.created_at >= day_ago
        ).count()

        if same_service_requests > self.risk_thresholds["suspicious_patterns"]:
            risk_score += 20
            flags.append("repeated_service")

        # Determine risk level
        if risk_score >= 40:
            risk_level = "high"
        elif risk_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "flags": flags,
            "action": "block" if risk_level == "high" else "allow"
        }


# Global fraud detector instance
fraud_detector = FraudDetector()
