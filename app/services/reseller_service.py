"""Reseller service for managing reseller accounts and sub-accounts."""

from sqlalchemy.orm import Session

from app.models.reseller import (
    BulkOperation,
    ResellerAccount,
    SubAccount,
    SubAccountTransaction,
)
from app.models.user import User

TIER_DISCOUNTS = {"bronze": 0.10, "silver": 0.15, "gold": 0.20, "platinum": 0.25}
TIER_CREDIT_LIMITS = {
    "bronze": 5000.0,
    "silver": 10000.0,
    "gold": 25000.0,
    "platinum": 100000.0,
}


class ResellerService:
    def __init__(self, db: Session):
        self.db = db

    async def create_reseller_account(self, user_id: str, tier: str = "bronze") -> dict:
        existing = (
            self.db.query(ResellerAccount)
            .filter(ResellerAccount.user_id == user_id)
            .first()
        )
        if existing:
            return {"error": "User already has reseller account"}

        account = ResellerAccount(
            user_id=user_id,
            tier=tier,
            volume_discount=TIER_DISCOUNTS.get(tier, 0.10),
            credit_limit=TIER_CREDIT_LIMITS.get(tier, 5000.0),
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return {
            "success": True,
            "reseller_id": account.id,
            "tier": account.tier,
            "discount": account.volume_discount,
        }

    async def create_sub_account(
        self,
        reseller_id: str,
        name: str,
        email: str,
        initial_credits: float = 0.0,
    ) -> dict:
        reseller = (
            self.db.query(ResellerAccount)
            .filter(ResellerAccount.id == reseller_id)
            .first()
        )
        if not reseller:
            return {"error": "Reseller account not found"}

        existing = (
            self.db.query(SubAccount).filter(SubAccount.email == email).first()
        )
        if existing:
            return {"error": "Email already exists"}

        sub = SubAccount(
            reseller_id=reseller_id,
            name=name,
            email=email,
            credits=initial_credits,
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        return {"success": True, "sub_account_id": sub.id}

    async def allocate_credits(
        self, reseller_id: str, sub_account_id: str, amount: float
    ) -> dict:
        reseller = (
            self.db.query(ResellerAccount)
            .filter(ResellerAccount.id == reseller_id)
            .first()
        )
        sub = (
            self.db.query(SubAccount)
            .filter(SubAccount.id == sub_account_id)
            .first()
        )
        if not reseller or not sub:
            return {"error": "Invalid reseller or sub - account"}

        user = self.db.query(User).filter(User.id == reseller.user_id).first()
        if not user or float(user.credits) < amount:
            return {"error": "Insufficient reseller credits"}

        user.credits = type(user.credits)(float(user.credits) - amount)
        sub.credits += amount

        tx = SubAccountTransaction(
            sub_account_id=sub.id,
            transaction_type="credit",
            amount=amount,
            description=f"Credit allocation from reseller {reseller_id}",
            balance_after=sub.credits,
        )
        self.db.add(tx)
        self.db.commit()
        return {"success": True, "allocated_amount": amount}

    async def bulk_credit_topup(
        self, reseller_id: str, sub_account_ids: list, amount_each: float
    ) -> dict:
        processed, failed, errors = 0, 0, []
        for sub_id in sub_account_ids:
            result = await self.allocate_credits(reseller_id, sub_id, amount_each)
            if result.get("success"):
                processed += 1
            else:
                failed += 1
                errors.append({"sub_account_id": sub_id, "error": result.get("error")})

        if failed == 0:
            op = BulkOperation(
                reseller_id=reseller_id,
                operation_type="credit_topup",
                total_accounts=len(sub_account_ids),
                processed_accounts=processed,
                failed_accounts=failed,
                status="completed",
            )
            self.db.add(op)
            self.db.commit()

        return {
            "success": failed == 0,
            "processed": processed,
            "failed": failed,
            "errors": errors,
        }

    async def get_usage_report(self, reseller_id: str, days: int = 30) -> dict:
        subs = (
            self.db.query(SubAccount)
            .filter(SubAccount.reseller_id == reseller_id)
            .all()
        )
        sub_ids = [s.id for s in subs]

        txs = (
            self.db.query(SubAccountTransaction)
            .filter(SubAccountTransaction.sub_account_id.in_(sub_ids))
            .all()
        )

        total_allocated = sum(
            t.amount for t in txs if t.transaction_type == "credit"
        )
        total_usage = sum(t.amount for t in txs if t.transaction_type == "debit")

        return {
            "total_sub_accounts": len(subs),
            "total_credits_allocated": total_allocated,
            "total_usage": total_usage,
            "transactions": [
                {
                    "id": t.id,
                    "type": t.transaction_type,
                    "amount": t.amount,
                    "description": t.description,
                }
                for t in txs
            ],
        }


def get_reseller_service(db: Session) -> ResellerService:
    return ResellerService(db)
