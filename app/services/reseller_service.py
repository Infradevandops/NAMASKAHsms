"""Reseller management service."""


from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.reseller import (

    BulkOperation,
    CreditAllocation,
    ResellerAccount,
    SubAccount,
    SubAccountTransaction,
)


class ResellerService:

    """Reseller account and sub - account management."""

    def __init__(self, db: Session):

        self.db = db

    async def create_reseller_account(self, user_id: int, tier: str = "bronze") -> Dict:
        """Create new reseller account."""

        # Check if user already has reseller account
        existing = self.db.query(ResellerAccount).filter(ResellerAccount.user_id == user_id).first()

        if existing:
        return {"error": "User already has reseller account"}

        # Get tier configuration
        tier_config = self._get_tier_config(tier)

        reseller = ResellerAccount(
            user_id=user_id,
            tier=tier,
            volume_discount=tier_config["discount"],
            custom_rates=tier_config["rates"],
            credit_limit=tier_config["credit_limit"],
        )

        self.db.add(reseller)
        self.db.commit()

        return {
            "success": True,
            "reseller_id": reseller.id,
            "tier": tier,
            "discount": tier_config["discount"],
        }

    async def create_sub_account(
        self,
        reseller_id: int,
        name: str,
        email: str,
        initial_credits: float = 0.0,
        features: Dict = None,
        ) -> Dict:
        """Create new sub - account."""

        reseller = self.db.query(ResellerAccount).filter(ResellerAccount.id == reseller_id).first()

        if not reseller:
        return {"error": "Reseller account not found"}

        # Check if email already exists
        existing = self.db.query(SubAccount).filter(SubAccount.email == email).first()

        if existing:
        return {"error": "Email already exists"}

        sub_account = SubAccount(
            reseller_id=reseller_id,
            name=name,
            email=email,
            credits=initial_credits,
            features=features or {},
        )

        self.db.add(sub_account)
        self.db.flush()  # Get ID

        # Create initial credit transaction if credits > 0
        if initial_credits > 0:
            transaction = SubAccountTransaction(
                sub_account_id=sub_account.id,
                transaction_type="credit",
                amount=initial_credits,
                description="Initial credit allocation",
                balance_after=initial_credits,
            )
            self.db.add(transaction)

        self.db.commit()

        return {
            "success": True,
            "sub_account_id": sub_account.id,
            "name": name,
            "email": email,
            "credits": initial_credits,
        }

    async def allocate_credits(
        self,
        reseller_id: int,
        sub_account_id: int,
        amount: float,
        allocation_type: str = "manual",
        notes: str = None,
        ) -> Dict:
        """Allocate credits to sub - account."""

        reseller = self.db.query(ResellerAccount).filter(ResellerAccount.id == reseller_id).first()

        sub_account = (
            self.db.query(SubAccount)
            .filter(SubAccount.id == sub_account_id, SubAccount.reseller_id == reseller_id)
            .first()
        )

        if not reseller or not sub_account:
        return {"error": "Invalid reseller or sub - account"}

        # Check reseller balance (if applicable)
        reseller_user = reseller.user
        if reseller_user.credits < amount:
        return {"error": "Insufficient reseller credits"}

        # Deduct from reseller
        reseller_user.credits -= amount

        # Add to sub - account
        old_balance = sub_account.credits
        sub_account.credits += amount

        # Create transaction record
        transaction = SubAccountTransaction(
            sub_account_id=sub_account_id,
            transaction_type="credit",
            amount=amount,
            description=f"Credit allocation from reseller ({allocation_type})",
            balance_after=sub_account.credits,
        )

        # Create allocation record
        allocation = CreditAllocation(
            reseller_id=reseller_id,
            sub_account_id=sub_account_id,
            amount=amount,
            allocation_type=allocation_type,
            notes=notes,
        )

        self.db.add(transaction)
        self.db.add(allocation)
        self.db.commit()

        return {
            "success": True,
            "allocated_amount": amount,
            "old_balance": old_balance,
            "new_balance": sub_account.credits,
        }

    async def get_sub_accounts(self, reseller_id: int) -> List[Dict]:
        """Get all sub - accounts for reseller."""

        sub_accounts = (
            self.db.query(SubAccount)
            .filter(SubAccount.reseller_id == reseller_id)
            .order_by(SubAccount.created_at.desc())
            .all()
        )

        return [
            {
                "id": account.id,
                "name": account.name,
                "email": account.email,
                "credits": account.credits,
                "usage_limit": account.usage_limit,
                "is_active": account.is_active,
                "last_activity": account.last_activity,
                "created_at": account.created_at,
            }
        for account in sub_accounts
        ]

    async def bulk_credit_topup(self, reseller_id: int, account_ids: List[int], amount_per_account: float) -> Dict:
        """Bulk credit top - up for multiple accounts."""

        # Create bulk operation record
        bulk_op = BulkOperation(
            reseller_id=reseller_id,
            operation_type="credit_topup",
            total_accounts=len(account_ids),
            operation_data={
                "amount_per_account": amount_per_account,
                "account_ids": account_ids,
            },
        )

        self.db.add(bulk_op)
        self.db.flush()

        processed = 0
        failed = 0
        errors = []

        for account_id in account_ids:
        try:
                result = await self.allocate_credits(
                    reseller_id=reseller_id,
                    sub_account_id=account_id,
                    amount=amount_per_account,
                    allocation_type="bulk",
                )

        if result.get("success"):
                    processed += 1
        else:
                    failed += 1
                    errors.append(f"Account {account_id}: {result.get('error')}")

        except Exception as e:
                failed += 1
                errors.append(f"Account {account_id}: {str(e)}")

        # Update bulk operation
        bulk_op.processed_accounts = processed
        bulk_op.failed_accounts = failed
        bulk_op.status = "completed" if failed == 0 else "partial"
        bulk_op.error_log = {"errors": errors}

        self.db.commit()

        return {
            "success": True,
            "bulk_operation_id": bulk_op.id,
            "processed": processed,
            "failed": failed,
            "errors": errors,
        }

    async def get_usage_report(self, reseller_id: int, days: int = 30) -> Dict:
        """Get usage analytics for reseller."""

        start_date = datetime.utcnow() - timedelta(days=days)

        # Get sub - accounts
        sub_accounts = await self.get_sub_accounts(reseller_id)

        # Get transactions
        transactions = (
            self.db.query(SubAccountTransaction)
            .join(SubAccount)
            .filter(
                SubAccount.reseller_id == reseller_id,
                SubAccountTransaction.created_at >= start_date,
            )
            .all()
        )

        # Calculate metrics
        total_usage = sum(t.amount for t in transactions if t.transaction_type == "debit")
        total_credits_allocated = sum(t.amount for t in transactions if t.transaction_type == "credit")

        # Usage by sub - account
        usage_by_account = {}
        for transaction in transactions:
            account_id = transaction.sub_account_id
        if account_id not in usage_by_account:
                usage_by_account[account_id] = {"credits": 0, "debits": 0}

        if transaction.transaction_type == "credit":
                usage_by_account[account_id]["credits"] += transaction.amount
        else:
                usage_by_account[account_id]["debits"] += transaction.amount

        return {
            "period_days": days,
            "total_sub_accounts": len(sub_accounts),
            "active_accounts": len([a for a in sub_accounts if a["is_active"]]),
            "total_usage": total_usage,
            "total_credits_allocated": total_credits_allocated,
            "usage_by_account": usage_by_account,
            "transactions": [
                {
                    "date": t.created_at,
                    "type": t.transaction_type,
                    "amount": t.amount,
                    "description": t.description,
                }
        for t in transactions[-50:]  # Last 50 transactions
            ],
        }

    def _get_tier_config(self, tier: str) -> Dict:

        """Get configuration for reseller tier."""

        tiers = {
            "bronze": {
                "discount": 0.05,
                "credit_limit": 1000.0,
                "rates": {"sms": 0.45, "whatsapp": 0.55},
            },
            "silver": {
                "discount": 0.10,
                "credit_limit": 5000.0,
                "rates": {"sms": 0.40, "whatsapp": 0.50},
            },
            "gold": {
                "discount": 0.20,
                "credit_limit": 25000.0,
                "rates": {"sms": 0.35, "whatsapp": 0.45},
            },
            "platinum": {
                "discount": 0.35,
                "credit_limit": 100000.0,
                "rates": {"sms": 0.30, "whatsapp": 0.40},
            },
        }

        return tiers.get(tier, tiers["bronze"])


# Global service instance


    def get_reseller_service(db: Session) -> ResellerService:

        """Get reseller service instance."""
        return ResellerService(db)