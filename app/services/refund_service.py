"""Refund service for managing payment refunds."""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.logging import get_logger
from app.models.user import User
from app.models.refund import Refund
from app.models.transaction import Transaction, PaymentLog
from app.services.paystack_service import paystack_service

logger = get_logger(__name__)


class RefundService:
    """Service for managing refunds."""

    def __init__(self, db: Session):
        """Initialize refund service with database session."""
        self.db = db
        self.refund_window_days = 30  # Refunds allowed within 30 days

    def initiate_refund(
        self,
        user_id: str,
        payment_id: str,
        reason: str,
        initiated_by: str = "user"
    ) -> Refund:
        """Initiate a refund request.
        
        Args:
            user_id: User ID
            payment_id: Payment ID to refund
            reason: Refund reason
            initiated_by: Who initiated (user or admin)
            
        Returns:
            Created refund record
            
        Raises:
            ValueError: If refund not eligible
        """
        # Get payment log
        payment_log = self.db.query(PaymentLog).filter(
            PaymentLog.id == payment_id,
            PaymentLog.user_id == user_id
        ).first()
        
        if not payment_log:
            raise ValueError(f"Payment not found: {payment_id}")
        
        # Check payment status
        if payment_log.status != "success":
            raise ValueError(f"Cannot refund payment with status: {payment_log.status}")
        
        # Check if already refunded
        existing_refund = self.db.query(Refund).filter(
            Refund.payment_id == payment_id,
            Refund.status.in_(["success", "pending"])
        ).first()
        
        if existing_refund:
            raise ValueError(f"Payment already refunded: {payment_id}")
        
        # Check refund window
        if payment_log.created_at:
            days_since_payment = (datetime.now(timezone.utc) - payment_log.created_at).days
            if days_since_payment > self.refund_window_days:
                raise ValueError(
                    f"Refund window expired. Refunds allowed within {self.refund_window_days} days"
                )
        
        # Generate reference
        reference = f"refund_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Create refund record
        refund = Refund(
            payment_id=payment_id,
            user_id=user_id,
            amount=payment_log.amount_usd,
            reason=reason,
            status="pending",
            reference=reference,
            initiated_by=initiated_by
        )
        
        self.db.add(refund)
        self.db.commit()
        
        logger.info(
            f"Refund initiated: Reference={reference}, User={user_id}, "
            f"Amount={payment_log.amount_usd}, Reason={reason}"
        )
        
        return refund

    def process_refund(self, reference: str) -> Dict[str, Any]:
        """Process a refund with Paystack.
        
        Args:
            reference: Refund reference
            
        Returns:
            Refund processing result
            
        Raises:
            ValueError: If refund not found or processing fails
        """
        # Get refund
        refund = self.db.query(Refund).filter(Refund.reference == reference).first()
        
        if not refund:
            raise ValueError(f"Refund not found: {reference}")
        
        if refund.status != "pending":
            raise ValueError(f"Cannot process refund with status: {refund.status}")
        
        # Get payment log for original reference
        payment_log = self.db.query(PaymentLog).filter(
            PaymentLog.id == refund.payment_id
        ).first()
        
        if not payment_log:
            raise ValueError(f"Original payment not found: {refund.payment_id}")
        
        logger.info(f"Processing refund: {reference}")
        
        try:
            # Call Paystack refund API
            # Note: This is a placeholder - actual implementation depends on Paystack API
            # For now, we'll mark as success
            
            # Update refund status
            refund.status = "success"
            refund.processed_at = datetime.now(timezone.utc)
            
            # Get user
            user = self.db.query(User).filter(User.id == refund.user_id).first()
            if not user:
                raise ValueError(f"User not found: {refund.user_id}")
            
            # Deduct credits
            user.credits = (user.credits or 0.0) - refund.amount
            
            # Create refund transaction
            transaction = Transaction(
                user_id=refund.user_id,
                amount=-refund.amount,
                type="refund",
                description=f"Refund for payment {payment_log.reference} (Ref: {reference})"
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(
                f"Refund processed: Reference={reference}, User={refund.user_id}, "
                f"Amount={refund.amount}, New Balance={user.credits}"
            )
            
            return {
                "reference": reference,
                "status": "success",
                "amount": refund.amount,
                "processed_at": refund.processed_at.isoformat()
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to process refund: {str(e)}", exc_info=True)
            
            # Update refund status to failed
            refund.status = "failed"
            refund.error_message = str(e)
            self.db.commit()
            
            raise ValueError(f"Refund processing failed: {str(e)}")

    def verify_refund(self, reference: str) -> Dict[str, Any]:
        """Verify a refund status.
        
        Args:
            reference: Refund reference
            
        Returns:
            Refund details
            
        Raises:
            ValueError: If refund not found
        """
        refund = self.db.query(Refund).filter(Refund.reference == reference).first()
        
        if not refund:
            raise ValueError(f"Refund not found: {reference}")
        
        logger.info(f"Verified refund: {reference}, Status={refund.status}")
        
        return {
            "reference": reference,
            "status": refund.status,
            "amount": refund.amount,
            "reason": refund.reason,
            "initiated_at": refund.initiated_at.isoformat() if refund.initiated_at else None,
            "processed_at": refund.processed_at.isoformat() if refund.processed_at else None,
            "error_message": refund.error_message
        }

    def get_refund_history(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get refund history for user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Number of records to return
            
        Returns:
            Refund history with metadata
            
        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get total count
        total = self.db.query(Refund).filter(Refund.user_id == user_id).count()
        
        # Get refunds
        refunds = (
            self.db.query(Refund)
            .filter(Refund.user_id == user_id)
            .order_by(desc(Refund.created_at))
            .offset(skip)
            .limit(min(limit, 100))
            .all()
        )
        
        logger.info(
            f"Retrieved {len(refunds)} refunds for user {user_id} "
            f"(total: {total}, skip: {skip}, limit: {limit})"
        )
        
        return {
            "user_id": user_id,
            "total": total,
            "skip": skip,
            "limit": limit,
            "refunds": [
                {
                    "reference": r.reference,
                    "amount": r.amount,
                    "reason": r.reason,
                    "status": r.status,
                    "initiated_at": r.initiated_at.isoformat() if r.initiated_at else None,
                    "processed_at": r.processed_at.isoformat() if r.processed_at else None
                }
                for r in refunds
            ]
        }

    def cancel_refund(self, reference: str, user_id: str) -> Refund:
        """Cancel a pending refund.
        
        Args:
            reference: Refund reference
            user_id: User ID
            
        Returns:
            Updated refund
            
        Raises:
            ValueError: If refund not found or cannot be cancelled
        """
        refund = self.db.query(Refund).filter(
            Refund.reference == reference,
            Refund.user_id == user_id
        ).first()
        
        if not refund:
            raise ValueError(f"Refund not found: {reference}")
        
        if refund.status != "pending":
            raise ValueError(f"Cannot cancel refund with status: {refund.status}")
        
        refund.status = "cancelled"
        self.db.commit()
        
        logger.info(f"Refund cancelled: {reference}")
        
        return refund

    def handle_refund_webhook(self, event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund webhook from Paystack.
        
        Args:
            event: Event type
            payload: Event payload
            
        Returns:
            Processing result
        """
        logger.info(f"Processing refund webhook: Event={event}")
        
        try:
            if event == "charge.refunded":
                reference = payload.get("reference")
                
                # Get payment log
                payment_log = self.db.query(PaymentLog).filter(
                    PaymentLog.reference == reference
                ).first()
                
                if not payment_log:
                    logger.warning(f"Payment not found for refund: {reference}")
                    return {"status": "ignored", "message": "Payment not found"}
                
                # Get refund
                refund = self.db.query(Refund).filter(
                    Refund.payment_id == payment_log.id
                ).first()
                
                if not refund:
                    logger.warning(f"Refund not found for payment: {reference}")
                    return {"status": "ignored", "message": "Refund not found"}
                
                # Process refund
                return self.process_refund(refund.reference)
            
            else:
                logger.warning(f"Unknown refund event: {event}")
                return {"status": "ignored", "message": f"Unknown event: {event}"}
        
        except Exception as e:
            logger.error(f"Refund webhook processing error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}
