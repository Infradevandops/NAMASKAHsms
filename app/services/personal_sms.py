"""Personal SMS verification service using your own phone numbers."""
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import Verification
from app.schemas.verification import VerificationCreate
from app.services.sms_gateway import SMSGateway

class PersonalSMSService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sms_gateway = SMSGateway()
    
    async def create_verification(self, user_id: int, verification: VerificationCreate):
        """Create verification using personal phone number."""
        verification_id = str(uuid.uuid4())
        
        # Create verification record
        db_verification = Verification(
            id=verification_id,
            user_id=user_id,
            service_id=verification.service_id,
            country=verification.country,
            phone_number="YOUR_PERSONAL_NUMBER",  # Replace with actual number
            status="active",
            created_at=datetime.utcnow()
        )
        
        self.db.add(db_verification)
        await self.db.commit()
        
        return {
            "verification_id": verification_id,
            "phone_number": "YOUR_PERSONAL_NUMBER",
            "status": "active",
            "message": "Use this number to receive SMS codes"
        }
    
    async def get_messages(self, verification_id: str, user_id: int):
        """Get messages for verification (manual input required)."""
        return {
            "verification_id": verification_id,
            "messages": [],
            "note": "Manually enter SMS codes received on your personal number"
        }
    
    async def add_personal_number(self, user_id: int, phone_number: str):
        """Add personal phone number to user account."""
        # Store in user preferences or separate table
        return {
            "phone_number": phone_number,
            "status": "added",
            "message": "Personal number added successfully"
        }