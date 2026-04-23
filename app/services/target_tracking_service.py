from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.daily_user_snapshot import DailyUserSnapshot
from app.models.monthly_target import MonthlyTarget
from app.models.user import User
from app.models.verification import Verification


class TargetTrackingService:
    def __init__(self, db: Session):
        self.db = db

    async def get_active_target(self, month_str: Optional[str] = None) -> MonthlyTarget:
        """Fetch the active growth target for a specific month (YYYY-MM)."""
        if not month_str:
            month_str = datetime.now(timezone.utc).strftime("%Y-%m")

        query = select(MonthlyTarget).where(
            MonthlyTarget.month == month_str,
            MonthlyTarget.is_active == True
        )
        target = self.db.execute(query).scalar_one_or_none()

        if not target:
            # Create default institutional target if none exists
            target = MonthlyTarget(
                month=month_str,
                target_count=350,
                revenue_target=Decimal("4000.00"),
                is_active=True,
                notes="Auto-generated institutional break-even target."
            )
            self.db.add(target)
            self.db.commit()
            self.db.refresh(target)

        return target

    async def record_daily_snapshot(self) -> DailyUserSnapshot:
        """Capture platform growth metrics and persist to database."""
        today = date.today()
        
        # 1. Check if already exists
        existing_query = select(DailyUserSnapshot).where(DailyUserSnapshot.snapshot_date == today)
        if self.db.execute(existing_query).scalar_one_or_none():
            return None

        # 2. Gather metrics
        total_users = self.db.query(func.count(User.id)).scalar()
        
        # New users today
        midnight = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        new_users = self.db.query(func.count(User.id)).filter(User.created_at >= midnight).scalar()

        # Active users (24h)
        active_users = self.db.query(func.count(func.distinct(Verification.user_id))).filter(
            Verification.created_at >= (datetime.now(timezone.utc) - timedelta(hours=24))
        ).scalar()

        # Tier breakdown
        def tier_count(tier_name):
            return self.db.query(func.count(User.id)).filter(User.subscription_tier == tier_name).scalar()
        
        snapshot = DailyUserSnapshot(
            snapshot_date=today,
            total_users=total_users or 0,
            new_users=new_users or 0,
            active_users_24h=active_users or 0,
            freemium_count=tier_count("freemium") or 0,
            payg_count=tier_count("payg") or 0,
            pro_count=tier_count("pro") or 0,
            custom_count=tier_count("custom") or 0
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        return snapshot

    async def get_growth_projections(self) -> Dict[str, Any]:
        """Calculate progress and projections based on persistent snapshots."""
        target = await self.get_active_target()
        
        # Get latest 30 snapshots for velocity
        snapshots = self.db.query(DailyUserSnapshot).order_by(desc(DailyUserSnapshot.snapshot_date)).limit(30).all()
        
        current_users = self.db.query(func.count(User.id)).scalar() or 0
        
        # Calculate velocity (avg new users per day over last 14 days)
        recent_snapshots = snapshots[:14]
        if len(recent_snapshots) > 1:
            total_new = sum(s.new_users for s in recent_snapshots)
            daily_velocity = total_new / len(recent_snapshots)
        else:
            daily_velocity = 0.0

        target_count = target.target_count
        remaining = max(0, target_count - current_users)
        
        days_to_target = 999
        projected_date = None
        
        if daily_velocity > 0:
            days_to_target = remaining / daily_velocity
            projected_date = (datetime.now(timezone.utc) + timedelta(days=days_to_target)).strftime("%Y-%m-%d")

        return {
            "month": target.month,
            "target": target_count,
            "current": current_users,
            "percentage": round((current_users / target_count * 100), 2) if target_count > 0 else 0,
            "velocity": round(daily_velocity, 1),
            "projected_date": projected_date,
            "status": "On Track" if daily_velocity >= 12.0 else "Behind"
        }
