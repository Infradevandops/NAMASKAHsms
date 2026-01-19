"""Enterprise SLA and account management service."""

from typing import Dict, Optional

from app.core.database import get_db
from app.models.enterprise import EnterpriseAccount, EnterpriseTier


class EnterpriseService:
    """Enterprise account and SLA management."""

    async def get_user_tier(self, user_id: int) -> Optional[Dict]:
        """Get enterprise tier for user."""
        db = next(get_db())

        account = (
            db.query(EnterpriseAccount)
            .filter(EnterpriseAccount.user_id == user_id)
            .first()
        )

        if not account:
            return None

        return {
            "tier_name": account.tier.name,
            "sla_uptime": account.tier.sla_uptime,
            "max_response_time": account.tier.max_response_time,
            "priority_support": account.tier.priority_support,
            "dedicated_manager": account.tier.dedicated_manager,
            "account_manager": account.account_manager_email,
            "features": account.tier.features,
            "sla_credits": account.sla_credits,
        }

    async def upgrade_to_enterprise(self, user_id: int, tier_name: str) -> Dict:
        """Upgrade user to enterprise tier."""
        db = next(get_db())

        tier = db.query(EnterpriseTier).filter(EnterpriseTier.name == tier_name).first()

        if not tier:
            raise ValueError(f"Tier {tier_name} not found")

        # Check if account already exists
        existing = (
            db.query(EnterpriseAccount)
            .filter(EnterpriseAccount.user_id == user_id)
            .first()
        )

        if existing:
            existing.tier_id = tier.id
        else:
            account = EnterpriseAccount(user_id=user_id, tier_id=tier.id)
            db.add(account)

        db.commit()
        return {"success": True, "tier": tier_name}

    async def check_sla_compliance(self, response_time: int, tier_name: str) -> Dict:
        """Check if response time meets SLA."""
        db = next(get_db())

        tier = db.query(EnterpriseTier).filter(EnterpriseTier.name == tier_name).first()

        if not tier:
            return {"compliant": True}

        compliant = response_time <= tier.max_response_time

        return {
            "compliant": compliant,
            "response_time": response_time,
            "sla_limit": tier.max_response_time,
            "violation": not compliant,
        }


# Global service instance
enterprise_service = EnterpriseService()
