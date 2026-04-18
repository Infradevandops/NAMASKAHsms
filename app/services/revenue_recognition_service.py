"""Revenue recognition service for GAAP compliance."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.revenue_recognition import (
    AccrualTrackingLog,
    DeferredRevenueSchedule,
    RevenueAdjustment,
    RevenueRecognition,
)
from app.models.transaction import Transaction
from app.models.user import User

logger = get_logger(__name__)


class RevenueRecognitionService:
    """Service for revenue recognition under GAAP standards."""

    def __init__(self, db: Session):
        self.db = db

    async def recognize_revenue(
        self,
        transaction_id: str,
        gross_amount: float,
        provider_cost: float,
        tax_jurisdiction: str,
    ) -> Dict:
        """Recognize revenue for a completed transaction.

        Args:
            transaction_id: Transaction ID
            gross_amount: Total revenue amount
            provider_cost: Cost paid to provider
            tax_jurisdiction: Tax jurisdiction code

        Returns:
            Revenue recognition record
        """
        try:
            transaction = (
                self.db.query(Transaction)
                .filter(Transaction.id == transaction_id)
                .first()
            )
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            now = datetime.now(timezone.utc)
            revenue_period = now.strftime("%Y-%m")

            # Create revenue recognition record
            recognition = RevenueRecognition(
                transaction_id=transaction_id,
                user_id=transaction.user_id,
                gross_amount=gross_amount,
                net_amount=gross_amount - provider_cost,
                provider_cost=provider_cost,
                transaction_date=transaction.created_at,
                revenue_recognized_date=now,
                revenue_period=revenue_period,
                status="recognized",
                service_type=transaction.service or "general",
                transaction_category=transaction.type,
                tax_jurisdiction=tax_jurisdiction,
                is_cash_basis=True,
                is_accrual_basis=False,
                matches_expected_revenue=True,
            )

            self.db.add(recognition)
            self.db.commit()

            logger.info(
                f"Revenue recognized for transaction {transaction_id}: ${gross_amount:.2f}"
            )

            return {
                "status": "success",
                "revenue_id": recognition.id,
                "transaction_id": transaction_id,
                "gross_amount": gross_amount,
                "net_amount": recognition.net_amount,
                "recognized_at": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Revenue recognition failed for {transaction_id}: {str(e)}")
            self.db.rollback()
            raise

    async def recognize_deferred_revenue(
        self,
        user_id: str,
        contract_id: str,
        contract_start: datetime,
        contract_end: datetime,
        total_contract_value: float,
    ) -> Dict:
        """Create deferred revenue schedule for long-term contracts.

        Args:
            user_id: User ID
            contract_id: Contract ID
            contract_start: Contract start date
            contract_end: Contract end date
            total_contract_value: Total contract value

        Returns:
            Deferred revenue schedule
        """
        try:
            # Calculate monthly recognition
            months_count = (
                (contract_end.year - contract_start.year) * 12
                + (contract_end.month - contract_start.month)
                + 1
            )
            monthly_amount = total_contract_value / months_count

            # Create schedule array
            schedule = []
            current_date = contract_start
            while current_date <= contract_end:
                month_key = current_date.strftime("%Y-%m")
                schedule.append(
                    {
                        "month": month_key,
                        "amount": monthly_amount,
                        "recognized": False,
                        "recognition_date": None,
                    }
                )
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

            # Create deferred revenue record
            deferred = DeferredRevenueSchedule(
                user_id=user_id,
                contract_id=contract_id,
                contract_start_date=contract_start,
                contract_end_date=contract_end,
                total_contract_value=total_contract_value,
                monthly_recognition_amount=monthly_amount,
                months_remaining=months_count,
                schedule=schedule,
                total_recognized=0.0,
                total_remaining=total_contract_value,
                status="active",
            )

            self.db.add(deferred)
            self.db.commit()

            logger.info(
                f"Deferred revenue created for contract {contract_id}: ${total_contract_value:.2f}"
            )

            return {
                "status": "success",
                "deferred_id": deferred.id,
                "contract_id": contract_id,
                "total_value": total_contract_value,
                "monthly_amount": monthly_amount,
                "months": months_count,
            }

        except Exception as e:
            logger.error(f"Deferred revenue creation failed: {str(e)}")
            self.db.rollback()
            raise

    async def process_revenue_adjustment(
        self,
        revenue_id: str,
        adjustment_type: str,
        adjustment_amount: float,
        reason: str,
        initiated_by: str,
    ) -> Dict:
        """Process revenue adjustment (refund, dispute, correction).

        Args:
            revenue_id: Original revenue recognition ID
            adjustment_type: Type of adjustment
            adjustment_amount: Amount of adjustment
            reason: Reason for adjustment
            initiated_by: User who initiated adjustment

        Returns:
            Adjustment record
        """
        try:
            # Get original revenue
            original = (
                self.db.query(RevenueRecognition)
                .filter(RevenueRecognition.id == revenue_id)
                .first()
            )
            if not original:
                raise ValueError(f"Revenue record {revenue_id} not found")

            # Determine impact
            impact = "decrease"
            if adjustment_type in ["correction", "reversal"]:
                impact = "decrease"

            # Create adjustment
            adjustment = RevenueAdjustment(
                original_revenue_id=revenue_id,
                user_id=original.user_id,
                transaction_id=original.transaction_id,
                adjustment_type=adjustment_type,
                adjustment_reason=reason,
                original_amount=original.gross_amount,
                adjusted_amount=original.gross_amount - adjustment_amount,
                adjustment_delta=adjustment_amount,
                adjustment_date=datetime.now(timezone.utc),
                adjustment_period=datetime.now(timezone.utc).strftime("%Y-%m"),
                revenue_impact=impact,
                initiated_by=initiated_by,
                approval_status="pending",
            )

            self.db.add(adjustment)

            # Update original revenue status
            original.status = "adjusted"
            original.variance_amount = adjustment_amount
            original.variance_reason = reason

            self.db.commit()

            logger.info(
                f"Revenue adjustment created for {revenue_id}: ${adjustment_amount:.2f} ({adjustment_type})"
            )

            return {
                "status": "success",
                "adjustment_id": adjustment.id,
                "adjustment_type": adjustment_type,
                "amount": adjustment_amount,
                "approval_status": "pending",
            }

        except Exception as e:
            logger.error(f"Revenue adjustment failed: {str(e)}")
            self.db.rollback()
            raise

    async def record_accrual(
        self,
        user_id: Optional[str],
        period: str,
        accrual_type: str,
        accrued_amount: float,
        actual_amount: float,
    ) -> Dict:
        """Record accrual for accounting purposes.

        Args:
            user_id: Optional user ID
            period: Period (YYYY-MM)
            accrual_type: Type of accrual
            accrued_amount: Accrued amount
            actual_amount: Actual amount

        Returns:
            Accrual record
        """
        try:
            variance = actual_amount - accrued_amount

            accrual = AccrualTrackingLog(
                user_id=user_id,
                account_type="revenue",
                period=period,
                accrual_date=datetime.now(timezone.utc),
                accrual_type=accrual_type,
                accrued_amount=accrued_amount,
                actual_amount=actual_amount,
                variance=variance,
                status="open",
            )

            self.db.add(accrual)
            self.db.commit()

            logger.info(
                f"Accrual recorded for {period}: ${accrued_amount:.2f} (actual: ${actual_amount:.2f})"
            )

            return {
                "status": "success",
                "accrual_id": accrual.id,
                "period": period,
                "variance": variance,
            }

        except Exception as e:
            logger.error(f"Accrual recording failed: {str(e)}")
            self.db.rollback()
            raise

    async def get_revenue_by_period(
        self, period: str, user_id: Optional[str] = None
    ) -> Dict:
        """Get revenue summary for a period.

        Args:
            period: Period (YYYY-MM)
            user_id: Optional filter by user

        Returns:
            Revenue summary
        """
        query = self.db.query(RevenueRecognition).filter(
            RevenueRecognition.revenue_period == period
        )

        if user_id:
            query = query.filter(RevenueRecognition.user_id == user_id)

        recognitions = query.all()

        total_gross = sum(r.gross_amount for r in recognitions)
        total_net = sum(r.net_amount for r in recognitions)
        total_costs = sum(r.provider_cost for r in recognitions)

        return {
            "period": period,
            "count": len(recognitions),
            "gross_revenue": total_gross,
            "net_revenue": total_net,
            "provider_costs": total_costs,
            "margin_percent": (
                ((total_net / total_gross) * 100) if total_gross > 0 else 0
            ),
        }

    async def get_deferred_revenue_summary(self, user_id: Optional[str] = None) -> Dict:
        """Get deferred revenue summary.

        Args:
            user_id: Optional filter by user

        Returns:
            Deferred revenue summary
        """
        query = self.db.query(DeferredRevenueSchedule).filter(
            DeferredRevenueSchedule.status == "active"
        )

        if user_id:
            query = query.filter(DeferredRevenueSchedule.user_id == user_id)

        schedules = query.all()

        total_deferred = sum(s.total_remaining for s in schedules)
        total_value = sum(s.total_contract_value for s in schedules)
        recognized = sum(s.total_recognized for s in schedules)

        return {
            "active_contracts": len(schedules),
            "total_contract_value": total_value,
            "total_recognized": recognized,
            "total_deferred": total_deferred,
            "avg_monthly_recognition": ((total_value / 12) if total_value > 0 else 0),
        }
