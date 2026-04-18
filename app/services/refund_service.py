"""
Refund Service - Tier-Aware Automatic Refunds
Handles refunds when area code or carrier filters don't match
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RefundService:
    """Service for processing tier-aware refunds"""

    def __init__(self):
        """Initialize refund service"""
        pass

    async def process_refund(
        self, verification: Any, user: Any, db: Session
    ) -> Dict[str, Any]:
        """
        Process automatic refund based on filter mismatches and user tier.

        Refund Logic:
        - PAYG/Freemium: Refund surcharges ($0.25 area code + $0.30 carrier)
        - Pro/Custom: Refund overage cost (filters included in quota)
        - Freemium: No refund (no filters available)

        Args:
            verification: Verification object with match status
            user: User object with tier and credits
            db: Database session

        Returns:
            {
                "refund_issued": bool,
                "refund_amount": float,
                "refund_type": str,  # "surcharge", "overage", "none"
                "reason": str,
                "timestamp": str
            }
        """
        # Check if any mismatch occurred
        area_code_mismatch = not verification.area_code_matched
        carrier_mismatch = not verification.carrier_matched

        if not area_code_mismatch and not carrier_mismatch:
            return {
                "refund_issued": False,
                "refund_amount": 0.0,
                "refund_type": "none",
                "reason": "no_mismatch",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Determine refund based on tier
        tier = user.subscription_tier.lower()

        # Freemium: No refunds (no filters available)
        if tier == "freemium":
            logger.info(
                f"No refund for freemium user {user.id} (filters not available)"
            )
            return {
                "refund_issued": False,
                "refund_amount": 0.0,
                "refund_type": "none",
                "reason": "freemium_no_filters",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # PAYG: Refund surcharges
        if tier == "payg":
            refund_amount = 0.0
            reasons = []

            if area_code_mismatch and verification.area_code_surcharge > 0:
                refund_amount += verification.area_code_surcharge
                reasons.append("area_code_mismatch")

            if carrier_mismatch and verification.carrier_surcharge > 0:
                refund_amount += verification.carrier_surcharge
                reasons.append("carrier_mismatch")

            if refund_amount > 0:
                # Issue refund
                user.credits = type(user.credits)(
                    float(user.credits or 0) + float(refund_amount)
                )

                # Create Transaction (Analytics)
                await self._create_refund_transaction(
                    db, user, verification, refund_amount, "surcharge", reasons
                )

                # Create BalanceTransaction (Strict Audit)
                from datetime import datetime, timezone

                from app.core.constants import TransactionType
                from app.models.balance_transaction import BalanceTransaction

                balance_tx = BalanceTransaction(
                    user_id=user.id,
                    amount=refund_amount,
                    type=TransactionType.REFUND,
                    description=f"Surcharge refund: {', '.join(reasons)}",
                    balance_after=float(user.credits),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(balance_tx)

                if hasattr(db, "commit"):
                    db.commit()

                logger.info(
                    f"PAYG refund issued: user={user.id}, amount=${refund_amount:.2f}, "
                    f"reasons={reasons}"
                )

                return {
                    "refund_issued": True,
                    "refund_amount": round(refund_amount, 2),
                    "refund_type": "surcharge",
                    "reason": ", ".join(reasons),
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # Pro/Custom: Refund overage cost (filters included in quota)
        if tier in ["pro", "custom"]:
            refund_amount = verification.cost
            reasons = []

            if area_code_mismatch:
                reasons.append("area_code_mismatch")
            if carrier_mismatch:
                reasons.append("carrier_mismatch")

            # Issue refund
            user.credits = type(user.credits)(
                float(user.credits or 0) + float(refund_amount)
            )

            # Create Transaction (Analytics)
            await self._create_refund_transaction(
                db, user, verification, refund_amount, "overage", reasons
            )

            # Create BalanceTransaction (Strict Audit)
            from datetime import datetime, timezone

            from app.core.constants import TransactionType
            from app.models.balance_transaction import BalanceTransaction

            balance_tx = BalanceTransaction(
                user_id=user.id,
                amount=refund_amount,
                type=TransactionType.REFUND,
                description=f"Overage refund: {', '.join(reasons)}",
                balance_after=float(user.credits),
                created_at=datetime.now(timezone.utc),
            )
            db.add(balance_tx)

            if hasattr(db, "commit"):
                db.commit()

            logger.info(
                f"{tier.upper()} refund issued: user={user.id}, amount=${refund_amount:.2f}, "
                f"reasons={reasons}"
            )

            return {
                "refund_issued": True,
                "refund_amount": round(refund_amount, 2),
                "refund_type": "overage",
                "reason": ", ".join(reasons),
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Unknown tier - no refund
        logger.warning(f"Unknown tier {tier} for user {user.id} - no refund issued")
        return {
            "refund_issued": False,
            "refund_amount": 0.0,
            "refund_type": "none",
            "reason": f"unknown_tier_{tier}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _create_refund_transaction(
        self,
        db: Session,
        user: Any,
        verification: Any,
        amount: float,
        refund_type: str,
        reasons: list,
    ):
        """Create transaction record for refund and link to telemetry"""
        from sqlalchemy import update

        from app.models.purchase_outcome import PurchaseOutcome
        from app.models.transaction import Transaction

        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            type="refund",
            status="completed",
            description=f"Automatic {refund_type} refund: {', '.join(reasons)}",
            tier=user.subscription_tier,
        )

        db.add(transaction)

        # Update PurchaseOutcome telemetry
        if hasattr(verification, "id") and verification.id:
            reason_str = ", ".join(reasons) if reasons else refund_type
            try:
                stmt = (
                    update(PurchaseOutcome)
                    .where(PurchaseOutcome.verification_id == str(verification.id))
                    .values(
                        is_refunded=True,
                        refund_amount=amount,
                        refund_reason=reason_str,
                        outcome_category="PRODUCT",
                        provider_refunded=True,  # Cancellation at purchase-time always refunds on provider side
                    )
                )
                db.execute(stmt)
            except Exception as e:
                logger.error(f"Failed to update PurchaseOutcome refund status: {e}")

        # Commit logic
        if hasattr(db, "commit"):
            import inspect

            if inspect.iscoroutinefunction(db.commit):
                await db.commit()
            else:
                db.commit()

        logger.debug(f"Refund transaction created: {transaction.id}")
