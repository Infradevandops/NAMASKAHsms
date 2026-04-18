"""Provider settlement and payout service."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.provider_settlement import (
    PayoutSchedule,
    ProviderAgreement,
    ProviderCostTracking,
    ProviderReconciliation,
    ProviderSettlement,
)
from app.models.transaction import Transaction

logger = get_logger(__name__)


class ProviderSettlementService:
    """Service for provider settlements and payouts."""

    def __init__(self, db: Session):
        self.db = db

    async def create_settlement(
        self,
        provider_id: str,
        period: str,
        total_messages: int,
        successful_messages: int,
        per_message_cost: float,
    ) -> Dict:
        """Create settlement for provider.

        Args:
            provider_id: Provider ID
            period: Period (YYYY-MM)
            total_messages: Total messages sent
            successful_messages: Successful messages
            per_message_cost: Cost per message

        Returns:
            Settlement record
        """
        try:
            # Parse period
            year, month = map(int, period.split("-"))
            settlement_start = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                settlement_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(
                    seconds=1
                )
            else:
                settlement_end = datetime(
                    year, month + 1, 1, tzinfo=timezone.utc
                ) - timedelta(seconds=1)

            # Calculate costs
            message_cost = total_messages * per_message_cost
            other_fees = message_cost * 0.05  # 5% in other fees
            total_cost = message_cost + other_fees
            delivery_rate = (successful_messages / total_messages * 100) if total_messages > 0 else 0

            # Create settlement
            settlement = ProviderSettlement(
                provider_id=provider_id,
                settlement_period=period,
                settlement_start=settlement_start,
                settlement_end=settlement_end,
                total_messages_sent=total_messages,
                successful_messages=successful_messages,
                failed_messages=total_messages - successful_messages,
                delivery_rate=delivery_rate,
                per_message_cost=per_message_cost,
                total_message_cost=message_cost,
                other_fees=other_fees,
                total_cost=total_cost,
                currency="USD",
                invoice_date=datetime.now(timezone.utc),
                due_date=datetime.now(timezone.utc) + timedelta(days=30),
                status="open",
                remaining_balance=total_cost,
            )

            self.db.add(settlement)
            self.db.commit()

            logger.info(
                f"Settlement created for {provider_id} {period}: ${total_cost:.2f}"
            )

            return {
                "status": "success",
                "settlement_id": settlement.id,
                "provider_id": provider_id,
                "period": period,
                "total_messages": total_messages,
                "total_cost": total_cost,
                "due_date": settlement.due_date.date().isoformat(),
            }

        except Exception as e:
            logger.error(f"Settlement creation failed: {str(e)}")
            self.db.rollback()
            raise

    async def record_settlement_payment(
        self,
        settlement_id: str,
        paid_amount: float,
        payment_method: str,
        payment_reference: str,
    ) -> Dict:
        """Record payment against settlement.

        Args:
            settlement_id: Settlement ID
            paid_amount: Amount paid
            payment_method: Payment method
            payment_reference: Payment reference

        Returns:
            Updated settlement
        """
        try:
            settlement = (
                self.db.query(ProviderSettlement)
                .filter(ProviderSettlement.id == settlement_id)
                .first()
            )
            if not settlement:
                raise ValueError(f"Settlement {settlement_id} not found")

            settlement.paid_amount += paid_amount
            settlement.remaining_balance = settlement.total_cost - settlement.paid_amount
            settlement.paid_date = datetime.now(timezone.utc)
            settlement.payment_method = payment_method
            settlement.payment_reference = payment_reference

            # Update status
            if settlement.remaining_balance <= 0:
                settlement.status = "paid"
            elif settlement.remaining_balance < settlement.total_cost:
                settlement.status = "due"
            else:
                settlement.status = "open"

            self.db.commit()

            logger.info(
                f"Settlement payment recorded: ${paid_amount:.2f} for settlement {settlement_id}"
            )

            return {
                "status": "success",
                "settlement_id": settlement_id,
                "paid_amount": settlement.paid_amount,
                "remaining_balance": settlement.remaining_balance,
                "payment_status": settlement.status,
            }

        except Exception as e:
            logger.error(f"Settlement payment recording failed: {str(e)}")
            self.db.rollback()
            raise

    async def track_daily_costs(
        self,
        provider_id: str,
        messages_sent: int,
        successful_sends: int,
        per_message_rate: float,
    ) -> Dict:
        """Track daily costs for provider.

        Args:
            provider_id: Provider ID
            messages_sent: Messages sent today
            successful_sends: Successful sends
            per_message_rate: Rate per message

        Returns:
            Cost tracking record
        """
        try:
            daily_cost = messages_sent * per_message_rate
            success_rate = (successful_sends / messages_sent * 100) if messages_sent > 0 else 0

            tracking = ProviderCostTracking(
                provider_id=provider_id,
                tracking_date=datetime.now(timezone.utc),
                messages_sent=messages_sent,
                successful_sends=successful_sends,
                failed_sends=messages_sent - successful_sends,
                success_rate=success_rate,
                per_message_rate=per_message_rate,
                daily_message_cost=daily_cost,
            )

            self.db.add(tracking)
            self.db.commit()

            logger.info(
                f"Daily costs tracked for {provider_id}: ${daily_cost:.2f}"
            )

            return {
                "status": "success",
                "provider_id": provider_id,
                "daily_cost": daily_cost,
                "messages": messages_sent,
                "success_rate": success_rate,
            }

        except Exception as e:
            logger.error(f"Cost tracking failed: {str(e)}")
            self.db.rollback()
            raise

    async def schedule_payout(
        self,
        settlement_id: str,
        payout_amount: float,
        bank_account: str,
        scheduled_date: datetime,
    ) -> Dict:
        """Schedule payout to provider.

        Args:
            settlement_id: Settlement ID
            payout_amount: Payout amount
            bank_account: Bank account
            scheduled_date: Scheduled date

        Returns:
            Payout schedule
        """
        try:
            settlement = (
                self.db.query(ProviderSettlement)
                .filter(ProviderSettlement.id == settlement_id)
                .first()
            )
            if not settlement:
                raise ValueError(f"Settlement {settlement_id} not found")

            payout_id = f"PAYOUT-{settlement.provider_id}-{datetime.now(timezone.utc).timestamp()}"

            payout = PayoutSchedule(
                provider_id=settlement.provider_id,
                payout_id=payout_id,
                settlement_id=settlement_id,
                payout_amount=payout_amount,
                scheduled_date=scheduled_date,
                bank_account=bank_account,
                status="scheduled",
                net_payout=payout_amount,
            )

            self.db.add(payout)
            self.db.commit()

            logger.info(
                f"Payout scheduled: ${payout_amount:.2f} for settlement {settlement_id}"
            )

            return {
                "status": "success",
                "payout_id": payout_id,
                "amount": payout_amount,
                "scheduled_date": scheduled_date.date().isoformat(),
            }

        except Exception as e:
            logger.error(f"Payout scheduling failed: {str(e)}")
            self.db.rollback()
            raise

    async def reconcile_settlement(
        self,
        settlement_id: str,
        provider_invoice_count: int,
        provider_invoice_cost: float,
    ) -> Dict:
        """Reconcile settlement against provider invoice.

        Args:
            settlement_id: Settlement ID
            provider_invoice_count: Message count on invoice
            provider_invoice_cost: Cost on invoice

        Returns:
            Reconciliation result
        """
        try:
            settlement = (
                self.db.query(ProviderSettlement)
                .filter(ProviderSettlement.id == settlement_id)
                .first()
            )
            if not settlement:
                raise ValueError(f"Settlement {settlement_id} not found")

            # Calculate variance
            message_variance = int(settlement.total_messages_sent) - provider_invoice_count
            cost_variance = settlement.total_cost - provider_invoice_cost
            variance_percent = (abs(cost_variance) / settlement.total_cost * 100) if settlement.total_cost > 0 else 0

            # Create reconciliation
            reconciliation = ProviderReconciliation(
                provider_id=settlement.provider_id,
                settlement_period=settlement.settlement_period,
                reconciliation_date=datetime.now(timezone.utc),
                our_message_count=int(settlement.total_messages_sent),
                our_total_cost=settlement.total_cost,
                our_success_rate=settlement.delivery_rate,
                invoice_message_count=provider_invoice_count,
                invoice_total_cost=provider_invoice_cost,
                invoice_success_rate=settlement.delivery_rate,
                message_count_variance=message_variance,
                cost_variance=cost_variance,
                variance_percentage=variance_percent,
                status="reconciled" if variance_percent < 2 else "disputed",
            )

            self.db.add(reconciliation)
            self.db.commit()

            logger.info(
                f"Settlement reconciled: Variance ${cost_variance:.2f} ({variance_percent:.1f}%)"
            )

            return {
                "status": "success",
                "reconciliation_id": reconciliation.id,
                "message_variance": message_variance,
                "cost_variance": cost_variance,
                "variance_percent": variance_percent,
                "reconciliation_status": reconciliation.status,
            }

        except Exception as e:
            logger.error(f"Settlement reconciliation failed: {str(e)}")
            self.db.rollback()
            raise

    async def get_settlement_summary(self, provider_id: str, year: int) -> Dict:
        """Get settlement summary for provider for year.

        Args:
            provider_id: Provider ID
            year: Year

        Returns:
            Summary
        """
        settlements = (
            self.db.query(ProviderSettlement)
            .filter(
                and_(
                    ProviderSettlement.provider_id == provider_id,
                    ProviderSettlement.settlement_period.like(f"{year}-%"),
                )
            )
            .all()
        )

        total_messages = sum(int(s.total_messages_sent) for s in settlements)
        total_cost = sum(s.total_cost for s in settlements)
        total_paid = sum(s.paid_amount for s in settlements)
        avg_delivery_rate = (
            sum(s.delivery_rate for s in settlements) / len(settlements)
            if settlements
            else 0
        )

        return {
            "provider_id": provider_id,
            "year": year,
            "periods": len(settlements),
            "total_messages": total_messages,
            "total_cost": total_cost,
            "total_paid": total_paid,
            "outstanding_balance": total_cost - total_paid,
            "avg_delivery_rate": avg_delivery_rate,
        }

    async def create_provider_agreement(
        self,
        provider_id: str,
        provider_name: str,
        base_rate: float,
        sla_uptime: float = 99.9,
        effective_from: Optional[datetime] = None,
    ) -> Dict:
        """Create provider agreement.

        Args:
            provider_id: Provider ID
            provider_name: Provider name
            base_rate: Base rate per message
            sla_uptime: SLA uptime %
            effective_from: Effective from date

        Returns:
            Agreement
        """
        try:
            if effective_from is None:
                effective_from = datetime.now(timezone.utc)

            agreement = ProviderAgreement(
                provider_id=provider_id,
                provider_name=provider_name,
                agreement_type="master_service",
                effective_from=effective_from,
                base_rate_per_message=base_rate,
                sla_uptime=sla_uptime,
                payment_frequency="monthly",
                net_days=30,
                is_active=True,
            )

            self.db.add(agreement)
            self.db.commit()

            logger.info(
                f"Provider agreement created: {provider_name} @ ${base_rate:.4f}/msg"
            )

            return {
                "status": "success",
                "agreement_id": agreement.id,
                "provider_id": provider_id,
                "base_rate": base_rate,
                "effective_from": effective_from.date().isoformat(),
            }

        except Exception as e:
            logger.error(f"Agreement creation failed: {str(e)}")
            self.db.rollback()
            raise
