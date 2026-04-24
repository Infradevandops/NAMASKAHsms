"""Institutional Operational Intelligence Service.
Handles User Vitality, Margin Drift, and Advanced Revenue Forensics.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, desc, func, text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.price_snapshot import PriceSnapshot
from app.models.pricing_template import PricingHistory, PricingTemplate
from app.models.purchase_outcome import PurchaseOutcome
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification
from app.utils.identity_utils import format_admin_identity, get_short_id

logger = get_logger(__name__)


class OperationalIntelligenceService:
    """Service for advanced institutional analytics and governance."""

    def __init__(self, db: Session):
        self.db = db

    async def get_user_vitality(self, days: int = 30) -> Dict[str, Any]:
        """Calculate DAU, Signup Velocity, and Cohort Retention."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        # 1. Signup Velocity (Log-ins per day)
        signups = (
            self.db.query(
                func.date(User.created_at).label("date"),
                func.count(User.id).label("count"),
            )
            .filter(User.created_at >= start_date)
            .group_by(func.date(User.created_at))
            .order_by("date")
            .all()
        )

        # 2. Daily Active Users (Users who did something in last 24h)
        dau_count = (
            self.db.query(func.count(func.distinct(Verification.user_id)))
            .filter(Verification.created_at >= (now - timedelta(hours=24)))
            .scalar()
            or 0
        )

        # 3. Power User Ranking (Top 10 users by spend and volume)
        power_users = (
            self.db.query(
                User.id,
                User.email,
                func.count(Verification.id).label("total_verifications"),
                func.sum(Verification.cost).label("total_spend"),
            )
            .join(Verification, User.id == Verification.user_id)
            .filter(Verification.created_at >= start_date)
            .group_by(User.id)
            .order_by(desc("total_spend"))
            .limit(10)
            .all()
        )

        # 4. Growth Target Tracking (350 Users/Month)
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        monthly_signups = (
            self.db.query(func.count(User.id))
            .filter(User.created_at >= current_month_start)
            .scalar()
            or 0
        )
        target = 350
        target_percentage = round((monthly_signups / target) * 100, 2)

        # Velocity needed to hit target
        days_in_month = 30  # average
        days_passed = (now - current_month_start).days or 1
        current_velocity = round(monthly_signups / days_passed, 1)
        needed_velocity = round(
            (target - monthly_signups) / max(days_in_month - days_passed, 1), 1
        )

        return {
            "period_days": days,
            "dau": dau_count,
            "signup_velocity": [
                {"date": str(s.date), "count": s.count} for s in signups
            ],
            "power_users": [
                {
                    "identifier": format_admin_identity(u.email, internal_id=u.id),
                    "volume": u.total_verifications,
                    "spend": float(u.total_spend or 0),
                }
                for u in power_users
            ],
            "growth_target": {
                "target": target,
                "current": monthly_signups,
                "percentage": target_percentage,
                "velocity_current": current_velocity,
                "velocity_needed": needed_velocity,
                "status": (
                    "On Track" if current_velocity >= needed_velocity else "At Risk"
                ),
            },
        }

    async def get_margin_audit(self, limit: int = 50) -> Dict[str, Any]:
        """Detect and report Margin Drift (leakage)."""
        # Compare actual Verification.cost (platform price) vs PurchaseOutcome.provider_price * active_template.markup
        # Since templates change, we look for current discrepancies

        # 1. Get active template multiplier
        from app.services.pricing_template_service import PricingTemplateService

        pt_service = PricingTemplateService(self.db)
        active_template = pt_service.get_active_template()
        target_markup = (
            active_template.markup_multiplier if active_template else Decimal("1.1000")
        )

        # 2. Fetch recent verification outcomes
        outcomes = (
            self.db.query(PurchaseOutcome)
            .order_by(desc(PurchaseOutcome.created_at))
            .limit(limit)
            .all()
        )

        drift_incidents = []
        total_drift = Decimal("0")

        for o in outcomes:
            if not o.user_price or not o.provider_price:
                continue

            # Use Decimal to avoid precision drift
            user_price = Decimal(str(o.user_price))
            provider_price = Decimal(str(o.provider_price))

            # Expected price based on current target markup
            expected_price = (provider_price * target_markup).quantize(Decimal("0.01"))

            # If the user paid significantly less than the target markup suggests
            if user_price < expected_price:
                drift = expected_price - user_price
                drift_incidents.append(
                    {
                        "id": o.id,
                        "service": o.service,
                        "user_price": float(user_price),
                        "expected_price": float(expected_price),
                        "drift_amount": float(drift),
                        "created_at": o.created_at.isoformat(),
                    }
                )
                total_drift += drift

        return {
            "target_markup": float(target_markup),
            "incidents_count": len(drift_incidents),
            "total_leakage": float(total_drift),
            "incidents": drift_incidents,
        }

    async def get_system_load_heatmap(self) -> List[Dict[str, Any]]:
        """Calculate verification attempts per hour of day (Global Peak Analysis)."""
        # This works on UTC hours
        heatmap = (
            self.db.query(
                func.extract("hour", Verification.created_at).label("hour"),
                func.count(Verification.id).label("attempts"),
            )
            .group_by(text("hour"))
            .order_by(text("hour"))
            .all()
        )

        return [{"hour": int(h.hour), "count": h.attempts} for h in heatmap]

    async def get_forensic_history(
        self, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """Fetch verification history with integrated margin drift (profit) forensics."""
        # Query verifications joined with their outcomes to get cost/platform price
        # This requires standard pagination as requested

        from app.services.pricing_template_service import PricingTemplateService

        pt_service = PricingTemplateService(self.db)
        active_template = pt_service.get_active_template()
        target_markup = (
            active_template.markup_multiplier if active_template else Decimal("1.1000")
        )

        query = (
            self.db.query(
                Verification.id,
                Verification.user_id,
                Verification.service_name,
                Verification.phone_number,
                Verification.status,
                Verification.cost,
                Verification.created_at,
                PurchaseOutcome.provider_price.label("provider_cost"),
                Verification.cost.label("platform_price"),
                User.email.label("user_email"),
            )
            .outerjoin(
                PurchaseOutcome,
                Verification.activation_id == PurchaseOutcome.activation_id,
            )
            .outerjoin(User, Verification.user_id == User.id)
            .order_by(desc(Verification.created_at))
            .offset(offset)
            .limit(limit)
        )

        results = query.all()
        total_count = self.db.query(func.count(Verification.id)).scalar()

        forensics = []
        for r in results:
            p_cost = Decimal(str(r.provider_cost)) if r.provider_cost else Decimal("0")
            plan_price = (
                Decimal(str(r.platform_price)) if r.platform_price else Decimal("0")
            )

            # Profit = Platform Price - Provider Cost
            profit = plan_price - p_cost

            # Target Profit based on template
            expected_profit = (p_cost * (target_markup - Decimal("1.0"))).quantize(
                Decimal("0.01")
            )

            # Drift = Expected Profit - Actual Profit
            # (If positive, we are leaking margin. If negative, we are making more than target)
            drift = expected_profit - profit

            forensics.append(
                {
                    "audit_id": get_short_id(r.id),
                    "identifier": (
                        format_admin_identity(r.user_email, internal_id=r.user_id)
                        if r.user_email
                        else r.user_id
                    ),
                    "service": r.service_name,
                    "phone": r.phone_number or "N/A",
                    "status": r.status,
                    "profit": float(profit),
                    "drift": float(drift),
                    "platform_price": float(plan_price),
                    "timestamp": r.created_at.isoformat(),
                }
            )

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "history": forensics,
        }

    async def get_audit_trail(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch all template activity and admin changes."""
        history = (
            self.db.query(PricingHistory)
            .order_by(desc(PricingHistory.changed_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": h.id,
                "template_id": h.template_id,
                "action": h.action,
                "changed_by": h.changed_by,
                "notes": h.notes,
                "timestamp": h.changed_at.isoformat(),
            }
            for h in history
        ]
