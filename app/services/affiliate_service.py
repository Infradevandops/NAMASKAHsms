"""Affiliate program service."""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.affiliate import AffiliateApplication
from datetime import datetime


class AffiliateService:
    """Affiliate program management service."""

    async def create_application(
        self,
        email: str,
        program_type: str,
        program_options: List[str],
        message: Optional[str],
        db: Session,
    ) -> Dict:
        """Create new affiliate application."""

        # Check for existing application
        existing = (
            db.query(AffiliateApplication)
            .filter(AffiliateApplication.email == email, AffiliateApplication.status == "pending")
            .first()
        )

        if existing:
            raise ValueError("You already have a pending application")

        application = AffiliateApplication(
            email=email,
            program_type=program_type,
            program_options={"selected_options": program_options},
            message=message,
            status="pending",
        )

        db.add(application)
        db.commit()
        db.refresh(application)

        return {"id": application.id, "status": "pending"}

    async def get_available_programs(self, db: Session) -> Dict:
        """Get available affiliate programs."""
        return {
            "referral_program": {
                "name": "Individual Referral Program",
                "commission_rate": "10%",
                "options": [
                    "SMS Verification Services",
                    "WhatsApp Business Integration",
                    "Payment Processing",
                    "API Access",
                ],
                "benefits": [
                    "Earn 10% commission on referrals",
                    "Real - time tracking dashboard",
                    "Monthly payouts",
                    "Marketing materials provided",
                ],
            },
            "enterprise_program": {
                "name": "Enterprise Affiliate Program",
                "commission_rate": "15 - 30%",
                "options": [
                    "White - label Solutions",
                    "Reseller Programs",
                    "Custom Integration Support",
                    "Dedicated Account Manager",
                    "Volume Discounts",
                    "Priority Support",
                    "Custom Branding",
                    "Multi - domain Management",
                ],
                "benefits": [
                    "Up to 30% commission rates",
                    "Dedicated account manager",
                    "Custom pricing negotiations",
                    "White - label opportunities",
                    "Priority technical support",
                    "Quarterly business reviews",
                ],
            },
        }

    async def get_all_applications(self, db: Session) -> List[Dict]:
        """Get all affiliate applications."""
        applications = (
            db.query(AffiliateApplication).order_by(AffiliateApplication.created_at.desc()).all()
        )

        return [
            {
                "id": app.id,
                "email": app.email,
                "program_type": app.program_type,
                "program_options": app.program_options,
                "message": app.message,
                "status": app.status,
                "admin_notes": app.admin_notes,
                "created_at": app.created_at,
                "updated_at": app.updated_at,
            }
            for app in applications
        ]

    async def update_application_status(
        self, application_id: int, status: str, admin_notes: Optional[str], db: Session
    ) -> Dict:
        """Update affiliate application status."""
        application = (
            db.query(AffiliateApplication).filter(AffiliateApplication.id == application_id).first()
        )

        if not application:
            raise ValueError("Application not found")

        application.status = status
        if admin_notes:
            application.admin_notes = admin_notes
        application.updated_at = datetime.utcnow()

        db.commit()

        return {"success": True, "status": status}


# Global service instance
affiliate_service = AffiliateService()
