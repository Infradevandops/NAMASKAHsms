"""
STRICT REFUND POLICY ENFORCEMENT
Ensures 100% automatic refunds for failed SMS verifications
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.verification import Verification
from app.services.auto_refund_service import AutoRefundService

logger = get_logger(__name__)


class RefundPolicyEnforcer:
    """
    STRICT REFUND POLICY:
    - Any verification pending >10 minutes = AUTOMATIC REFUND
    - Any verification with status timeout/failed/cancelled = AUTOMATIC REFUND
    - No exceptions, no manual intervention required
    - Runs every 5 minutes as backup to real-time polling
    """

    def __init__(self):
        self.is_running = False
        self.enforcement_interval = 300  # 5 minutes
        self.timeout_threshold = 600  # 10 minutes

    async def start_enforcement(self):
        """Start the refund policy enforcement background service."""
        self.is_running = True
        logger.info("🛡️  REFUND POLICY ENFORCER STARTED")
        logger.info(f"   - Enforcement interval: {self.enforcement_interval}s (5 min)")
        logger.info(f"   - Timeout threshold: {self.timeout_threshold}s (10 min)")
        logger.info("   - Policy: 100% automatic refunds for failed/timeout SMS")

        while self.is_running:
            try:
                await self._enforce_refund_policy()
                await asyncio.sleep(self.enforcement_interval)
            except Exception as e:
                logger.error(f"Refund enforcement error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 min on error

    async def stop_enforcement(self):
        """Stop the refund policy enforcement service."""
        self.is_running = False
        logger.info("🛡️  REFUND POLICY ENFORCER STOPPED")

    async def _enforce_refund_policy(self):
        """Enforce refund policy - find and refund all eligible verifications."""
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            # Find verifications that need refunds
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                seconds=self.timeout_threshold
            )

            # Criteria for refund:
            # 1. Status is pending but created >10 minutes ago (stuck)
            # 2. Status is timeout/failed/cancelled but not refunded yet
            eligible = (
                db.query(Verification)
                .filter(
                    or_(
                        # Stuck pending verifications
                        and_(
                            Verification.status == "pending",
                            Verification.created_at < cutoff_time,
                        ),
                        # Failed/timeout/cancelled not yet refunded
                        and_(
                            Verification.status.in_(["timeout", "failed", "cancelled"]),
                            or_(
                                Verification.refunded == False,
                                Verification.refunded.is_(None),
                            ),
                        ),
                    )
                )
                .all()
            )

            if not eligible:
                logger.debug("✅ No verifications need refunds")
                return

            logger.warning(
                f"🚨 REFUND POLICY VIOLATION: {len(eligible)} verifications need refunds"
            )

            refund_service = AutoRefundService(db)
            refunded_count = 0
            refunded_amount = 0.0
            failed_count = 0

            for verification in eligible:
                try:
                    # Update status if still pending
                    if verification.status == "pending":
                        verification.status = "timeout"
                        verification.outcome = "timeout"
                        db.commit()
                        logger.info(
                            f"Updated stuck verification {verification.id} to timeout"
                        )

                    # Process refund
                    reason = verification.status
                    result = await refund_service.process_verification_refund(
                        verification.id, reason
                    )

                    if result:
                        refunded_count += 1
                        refunded_amount += result["refund_amount"]
                        logger.info(
                            f"✅ ENFORCED REFUND: {verification.id} - "
                            f"${result['refund_amount']:.2f} - {reason}"
                        )
                    else:
                        failed_count += 1
                        logger.error(
                            f"❌ REFUND FAILED: {verification.id} - {reason}"
                        )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"❌ REFUND ERROR: {verification.id} - {str(e)}", exc_info=True
                    )

            # Summary
            logger.warning(
                f"🛡️  REFUND ENFORCEMENT COMPLETE: "
                f"Refunded={refunded_count}, "
                f"Failed={failed_count}, "
                f"Amount=${refunded_amount:.2f}"
            )

            # Alert if any refunds failed
            if failed_count > 0:
                logger.critical(
                    f"🚨 CRITICAL: {failed_count} refunds FAILED - Manual intervention required"
                )

        except Exception as e:
            logger.error(f"Refund enforcement failed: {e}", exc_info=True)
        finally:
            db.close()

    async def enforce_single_verification(
        self, verification_id: str, db: Session
    ) -> Optional[dict]:
        """
        Enforce refund policy for a single verification.
        Called immediately when verification fails/times out.
        """
        try:
            verification = (
                db.query(Verification)
                .filter(Verification.id == verification_id)
                .first()
            )

            if not verification:
                logger.error(f"Verification {verification_id} not found")
                return None

            # Check if refund needed
            if verification.status not in ["timeout", "failed", "cancelled"]:
                logger.debug(
                    f"Verification {verification_id} status={verification.status} - no refund needed"
                )
                return None

            # Check if already refunded
            if verification.refunded:
                logger.debug(f"Verification {verification_id} already refunded")
                return None

            # Process refund
            refund_service = AutoRefundService(db)
            result = await refund_service.process_verification_refund(
                verification_id, verification.status
            )

            if result:
                logger.info(
                    f"✅ IMMEDIATE REFUND: {verification_id} - "
                    f"${result['refund_amount']:.2f} - {verification.status}"
                )
            else:
                logger.error(f"❌ IMMEDIATE REFUND FAILED: {verification_id}")

            return result

        except Exception as e:
            logger.error(
                f"Single verification refund failed: {verification_id} - {e}",
                exc_info=True,
            )
            return None


# Global instance
refund_policy_enforcer = RefundPolicyEnforcer()
