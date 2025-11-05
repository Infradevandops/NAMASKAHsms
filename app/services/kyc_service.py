"""KYC service for identity verification and compliance."""
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.kyc import (
    KYCProfile, KYCDocument, KYCAuditLog, AMLScreening, 
    KYCVerificationLimit, BiometricVerification
)
from app.models.user import User
from app.models.verification import Verification
from app.schemas.kyc import KYCProfileCreate
from app.core.logging import get_logger
from app.core.exceptions import ValidationError

logger = get_logger(__name__)


class KYCService:
    """Service for KYC operations and compliance."""
    
    def __init__(self, db: Session):
        self.db = db
        self.kyc_limits = {
            "unverified": {"daily": 10.0, "monthly": 50.0, "annual": 200.0, "services": ["basic"]},
            "basic": {"daily": 100.0, "monthly": 500.0, "annual": 2000.0, "services": ["basic", "premium"]},
            "enhanced": {"daily": 1000.0, "monthly": 5000.0, "annual": 20000.0, "services": ["basic", "premium", "enterprise"]},
            "premium": {"daily": 10000.0, "monthly": 50000.0, "annual": 200000.0, "services": ["all"]}
        }
    
    async def create_profile(self, user_id: str, profile_data: KYCProfileCreate) -> KYCProfile:
        """Create new KYC profile."""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValidationError("User not found")
            
            # Create KYC profile
            kyc_profile = KYCProfile(
                user_id=user_id,
                full_name=profile_data.full_name,
                phone_number=profile_data.phone_number,
                date_of_birth=profile_data.date_of_birth,
                nationality=profile_data.nationality,
                address_line1=profile_data.address_line1,
                address_line2=profile_data.address_line2,
                city=profile_data.city,
                state=profile_data.state,
                postal_code=profile_data.postal_code,
                country=profile_data.country,
                status="unverified"
            )
            
            self.db.add(kyc_profile)
            self.db.commit()
            self.db.refresh(kyc_profile)
            
            # Log action
            await self._log_action(
                user_id=user_id,
                action="profile_created",
                new_status="unverified"
            )
            
            return kyc_profile
            
        except Exception as e:
            self.db.rollback()
            logger.error("KYC profile creation failed: %s", str(e))
            raise
    
    async def update_profile(self, kyc_profile_id: str, profile_data: KYCProfileCreate) -> KYCProfile:
        """Update existing KYC profile."""
        try:
            kyc_profile = self.db.query(KYCProfile).filter(KYCProfile.id == kyc_profile_id).first()
            if not kyc_profile:
                raise ValidationError("KYC profile not found")
            
            if kyc_profile.status == "verified":
                raise ValidationError("Cannot update verified profile")
            
            old_status = kyc_profile.status
            
            # Update fields
            kyc_profile.full_name = profile_data.full_name
            kyc_profile.phone_number = profile_data.phone_number
            kyc_profile.date_of_birth = profile_data.date_of_birth
            kyc_profile.nationality = profile_data.nationality
            kyc_profile.address_line1 = profile_data.address_line1
            kyc_profile.address_line2 = profile_data.address_line2
            kyc_profile.city = profile_data.city
            kyc_profile.state = profile_data.state
            kyc_profile.postal_code = profile_data.postal_code
            kyc_profile.country = profile_data.country
            
            self.db.commit()
            
            # Log action
            await self._log_action(
                user_id=kyc_profile.user_id,
                action="profile_updated",
                old_status=old_status,
                new_status=kyc_profile.status
            )
            
            return kyc_profile
            
        except Exception as e:
            self.db.rollback()
            logger.error("KYC profile update failed: %s", str(e))
            raise
    
    async def submit_for_review(self, kyc_profile_id: str) -> KYCProfile:
        """Submit KYC profile for admin review."""
        try:
            kyc_profile = self.db.query(KYCProfile).filter(KYCProfile.id == kyc_profile_id).first()
            if not kyc_profile:
                raise ValidationError("KYC profile not found")
            
            # Check if required documents are uploaded
            required_docs = ["id_card", "selfie"]  # Minimum required
            uploaded_docs = self.db.query(KYCDocument).filter(
                KYCDocument.kyc_profile_id == kyc_profile_id
            ).all()
            
            uploaded_types = [doc.document_type for doc in uploaded_docs]
            missing_docs = [doc for doc in required_docs if doc not in uploaded_types]
            
            if missing_docs:
                raise ValidationError(f"Missing required documents: {', '.join(missing_docs)}")
            
            old_status = kyc_profile.status
            kyc_profile.status = "pending"
            kyc_profile.submitted_at = datetime.now(timezone.utc)
            
            # Calculate initial risk score
            kyc_profile.risk_score = self.calculate_risk_score(kyc_profile)
            
            self.db.commit()
            
            # Log action
            await self._log_action(
                user_id=kyc_profile.user_id,
                action="submitted_for_review",
                old_status=old_status,
                new_status="pending"
            )
            
            # Trigger AML screening
            await self.perform_aml_screening(kyc_profile_id)
            
            return kyc_profile
            
        except Exception as e:
            self.db.rollback()
            logger.error("KYC submission failed: %s", str(e))
            raise
    
    async def admin_verify(
        self, 
        kyc_profile_id: str, 
        admin_id: str, 
        decision: str, 
        verification_level: str = "basic",
        notes: Optional[str] = None
    ) -> KYCProfile:
        """Admin verification decision."""
        try:
            kyc_profile = self.db.query(KYCProfile).filter(KYCProfile.id == kyc_profile_id).first()
            if not kyc_profile:
                raise ValidationError("KYC profile not found")
            
            old_status = kyc_profile.status
            old_level = kyc_profile.verification_level
            
            if decision == "approved":
                kyc_profile.status = "verified"
                kyc_profile.verification_level = verification_level
                kyc_profile.verified_at = datetime.now(timezone.utc)
                kyc_profile.rejection_reason = None
            else:
                kyc_profile.status = "rejected"
                kyc_profile.rejected_at = datetime.now(timezone.utc)
                kyc_profile.rejection_reason = notes
            
            if notes:
                kyc_profile.verification_notes = notes
            
            self.db.commit()
            
            # Log action
            await self._log_action(
                user_id=kyc_profile.user_id,
                action="admin_decision",
                old_status=old_status,
                new_status=kyc_profile.status,
                old_level=old_level,
                new_level=kyc_profile.verification_level,
                admin_id=admin_id,
                reason=notes
            )
            
            # Send notification to user
            await self._send_verification_notification(kyc_profile.user_id, decision, verification_level)
            
            return kyc_profile
            
        except Exception as e:
            self.db.rollback()
            logger.error("Admin verification failed: %s", str(e))
            raise
    
    def calculate_risk_score(self, kyc_profile: KYCProfile) -> float:
        """Calculate risk score based on profile data."""
        try:
            risk_score = 0.0
            
            # Age-based risk (younger = higher risk)
            if kyc_profile.date_of_birth:
                from datetime import date
                age = date.today().year - kyc_profile.date_of_birth.year
                if age < 25:
                    risk_score += 0.2
                elif age > 65:
                    risk_score += 0.1
            
            # Country-based risk
            high_risk_countries = ["AF", "IR", "KP", "SY"]  # Example high-risk countries
            if kyc_profile.country in high_risk_countries:
                risk_score += 0.5
            
            # Document verification status
            documents = self.db.query(KYCDocument).filter(
                KYCDocument.kyc_profile_id == kyc_profile.id
            ).all()
            
            verified_docs = sum(1 for doc in documents if doc.verification_status == "verified")
            total_docs = len(documents)
            
            if total_docs > 0:
                doc_verification_rate = verified_docs / total_docs
                risk_score += (1 - doc_verification_rate) * 0.3
            else:
                risk_score += 0.3  # No documents uploaded
            
            # Cap risk score at 1.0
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error("Risk score calculation failed: %s", str(e))
            return 0.5  # Default medium risk
    
    async def perform_aml_screening(self, kyc_profile_id: str) -> AMLScreening:
        """Perform AML screening."""
        try:
            kyc_profile = self.db.query(KYCProfile).filter(KYCProfile.id == kyc_profile_id).first()
            if not kyc_profile:
                raise ValidationError("KYC profile not found")
            
            # Create AML screening record
            screening = AMLScreening(
                kyc_profile_id=kyc_profile_id,
                screening_type="sanctions",
                status="pending",
                search_terms=[kyc_profile.full_name, kyc_profile.date_of_birth.isoformat()],
                screening_provider="internal"
            )
            
            # Perform basic screening (simplified for demo)
            screening.status = "clear"
            screening.match_score = 0.1  # Low match score
            screening.matches_found = []
            
            # Check for PEP status (simplified)
            kyc_profile.pep_status = False
            kyc_profile.aml_status = "clear"
            
            self.db.add(screening)
            self.db.commit()
            self.db.refresh(screening)
            
            return screening
            
        except Exception as e:
            self.db.rollback()
            logger.error("AML screening failed: %s", str(e))
            raise
    
    def get_user_limits(self, user_id: str) -> Dict:
        """Get user's current KYC limits."""
        try:
            kyc_profile = self.db.query(KYCProfile).filter(KYCProfile.user_id == user_id).first()
            
            if not kyc_profile or kyc_profile.status != "verified":
                level = "unverified"
            else:
                level = kyc_profile.verification_level
            
            limits = self.kyc_limits.get(level, self.kyc_limits["unverified"])
            
            # Calculate current usage
            today = datetime.now(timezone.utc).date()
            month_start = today.replace(day=1)
            year_start = today.replace(month=1, day=1)
            
            daily_usage = self.db.query(func.sum(Verification.cost)).filter(
                and_(
                    Verification.user_id == user_id,
                    func.date(Verification.created_at) == today
                )
            ).scalar() or 0.0
            
            monthly_usage = self.db.query(func.sum(Verification.cost)).filter(
                and_(
                    Verification.user_id == user_id,
                    func.date(Verification.created_at) >= month_start
                )
            ).scalar() or 0.0
            
            annual_usage = self.db.query(func.sum(Verification.cost)).filter(
                and_(
                    Verification.user_id == user_id,
                    func.date(Verification.created_at) >= year_start
                )
            ).scalar() or 0.0
            
            return {
                "level": level,
                "daily_limit": limits["daily"],
                "monthly_limit": limits["monthly"],
                "annual_limit": limits["annual"],
                "allowed_services": limits["services"],
                "current_usage": {
                    "daily": float(daily_usage),
                    "monthly": float(monthly_usage),
                    "annual": float(annual_usage)
                }
            }
            
        except Exception as e:
            logger.error("Failed to get user limits: %s", str(e))
            return self.kyc_limits["unverified"]
    
    def check_transaction_allowed(self, user_id: str, amount: float) -> bool:
        """Check if transaction is allowed based on KYC limits."""
        try:
            limits = self.get_user_limits(user_id)
            
            # Check daily limit
            if limits["current_usage"]["daily"] + amount > limits["daily_limit"]:
                return False
            
            # Check monthly limit
            if limits["current_usage"]["monthly"] + amount > limits["monthly_limit"]:
                return False
            
            # Check annual limit
            if limits["current_usage"]["annual"] + amount > limits["annual_limit"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error("Transaction limit check failed: %s", str(e))
            return False
    
    async def _log_action(
        self, 
        user_id: str, 
        action: str, 
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        old_level: Optional[str] = None,
        new_level: Optional[str] = None,
        admin_id: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log KYC action to audit trail."""
        try:
            audit_log = KYCAuditLog(
                user_id=user_id,
                action=action,
                old_status=old_status,
                new_status=new_status,
                old_level=old_level,
                new_level=new_level,
                admin_id=admin_id,
                reason=reason,
                system_action=admin_id is None
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error("Failed to log KYC action: %s", str(e))
    
    async def _send_verification_notification(self, user_id: str, decision: str, level: str):
        """Send verification result notification to user."""
        try:
            # This would integrate with your notification service
            logger.info("Sending KYC notification to user %s: %s (%s)", user_id, decision, level)
            
        except Exception as e:
            logger.error("Failed to send KYC notification: %s", str(e))


def get_kyc_service(db: Session) -> KYCService:
    """Get KYC service instance."""
    return KYCService(db)