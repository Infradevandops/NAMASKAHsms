"""Advanced commission calculation engine."""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.commission import CommissionTier, RevenueShare
from app.models.user import User
from datetime import datetime, timedelta
import json

class CommissionEngine:
    """Advanced commission calculation and revenue sharing engine."""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def calculate_commission(
        self, 
        partner_id: int, 
        transaction_amount: float,
        transaction_id: str,
        service_type: str = "sms"
    ) -> Dict:
        """Calculate commission for a transaction."""
        
        # Get partner details
        partner = self.db.query(User).filter(User.id == partner_id).first()
        if not partner or not partner.is_affiliate:
            return {"error": "Invalid partner"}
        
        # Get partner's commission tier
        tier = await self._get_partner_tier(partner_id)
        if not tier:
            return {"error": "No commission tier found"}
        
        # Calculate base commission
        base_commission = transaction_amount * tier["base_rate"]
        
        # Calculate performance bonus
        bonus_commission = await self._calculate_bonus(partner_id, tier, transaction_amount)
        
        total_commission = base_commission + bonus_commission
        
        # Create revenue share record
        revenue_share = RevenueShare(
            partner_id=partner_id,
            transaction_id=transaction_id,
            revenue_amount=transaction_amount,
            commission_rate=tier["base_rate"] + (bonus_commission / transaction_amount if transaction_amount > 0 else 0),
            commission_amount=total_commission,
            tier_name=tier["name"],
            status="pending"
        )
        
        self.db.add(revenue_share)
        self.db.commit()
        
        return {
            "commission_amount": total_commission,
            "base_commission": base_commission,
            "bonus_commission": bonus_commission,
            "commission_rate": revenue_share.commission_rate,
            "tier": tier["name"]
        }
    
    async def _get_partner_tier(self, partner_id: int) -> Optional[Dict]:
        """Get partner's current commission tier."""
        partner = self.db.query(User).filter(User.id == partner_id).first()
        
        # Get partner's performance metrics
        total_volume = await self._get_partner_volume(partner_id)
        total_referrals = await self._get_partner_referrals(partner_id)
        
        # Find appropriate tier
        tiers = self.db.query(CommissionTier).filter(
            CommissionTier.is_active == True
        ).order_by(CommissionTier.min_volume.desc()).all()
        
        for tier in tiers:
            if (total_volume >= tier.min_volume and 
                total_referrals >= tier.min_referrals):
                return {
                    "name": tier.name,
                    "base_rate": tier.base_rate,
                    "bonus_rate": tier.bonus_rate,
                    "benefits": tier.benefits
                }
        
        # Default tier
        return {
            "name": "starter",
            "base_rate": 0.05,
            "bonus_rate": 0.0,
            "benefits": {}
        }
    
    async def _calculate_bonus(self, partner_id: int, tier: Dict, transaction_amount: float) -> float:
        """Calculate performance-based bonus."""
        if tier.get("bonus_rate", 0) == 0:
            return 0.0
        
        # Monthly volume bonus
        monthly_volume = await self._get_monthly_volume(partner_id)
        
        bonus_thresholds = {
            1000: 0.02,   # 2% bonus for 1K+ monthly volume
            5000: 0.05,   # 5% bonus for 5K+ monthly volume
            25000: 0.10   # 10% bonus for 25K+ monthly volume
        }
        
        bonus_rate = 0.0
        for threshold, rate in sorted(bonus_thresholds.items(), reverse=True):
            if monthly_volume >= threshold:
                bonus_rate = rate
                break
        
        return transaction_amount * bonus_rate
    
    async def _get_partner_volume(self, partner_id: int) -> float:
        """Get partner's total transaction volume."""
        result = self.db.query(
            self.db.func.sum(RevenueShare.revenue_amount)
        ).filter(
            RevenueShare.partner_id == partner_id,
            RevenueShare.status == "completed"
        ).scalar()
        
        return result or 0.0
    
    async def _get_partner_referrals(self, partner_id: int) -> int:
        """Get partner's total referral count."""
        partner = self.db.query(User).filter(User.id == partner_id).first()
        if not partner or not partner.referral_code:
            return 0
        
        result = self.db.query(User).filter(
            User.referred_by == partner.referral_code
        ).count()
        
        return result
    
    async def _get_monthly_volume(self, partner_id: int) -> float:
        """Get partner's current month volume."""
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = self.db.query(
            self.db.func.sum(RevenueShare.revenue_amount)
        ).filter(
            RevenueShare.partner_id == partner_id,
            RevenueShare.created_at >= start_of_month,
            RevenueShare.status == "completed"
        ).scalar()
        
        return result or 0.0
    
    async def process_payouts(self) -> Dict:
        """Process pending commission payouts."""
        # Get all pending revenue shares
        pending_shares = self.db.query(RevenueShare).filter(
            RevenueShare.status == "pending"
        ).all()
        
        processed_count = 0
        total_amount = 0.0
        
        for share in pending_shares:
            # Update partner's earnings
            partner = share.partner
            partner.referral_earnings += share.commission_amount
            
            # Mark as processed
            share.status = "completed"
            share.processed_at = datetime.utcnow()
            
            processed_count += 1
            total_amount += share.commission_amount
        
        self.db.commit()
        
        return {
            "processed_count": processed_count,
            "total_amount": total_amount
        }

# Global service instance
commission_engine = None

def get_commission_engine(db: Session) -> CommissionEngine:
    """Get commission engine instance."""
    return CommissionEngine(db)