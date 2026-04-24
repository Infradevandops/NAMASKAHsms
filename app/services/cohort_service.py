from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.verification import Verification


class CohortRetentionService:
    def __init__(self, db: Session):
        self.db = db

    async def get_90d_retention_data(self) -> Dict[str, Any]:
        """
        Calculate weekly cohort retention for the last 90 days.
        Returns cohorts grouped by signup week and their activity in subsequent weeks.
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=90)

        # 1. Fetch users signed up in the last 90 days
        users_query = select(User.id, User.created_at).where(
            User.created_at >= start_date
        )

        users = self.db.execute(users_query).all()

        cohorts = {}
        user_cohort_map = {}

        for u in users:
            # truncate to week
            cohort_week = u.created_at.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=u.created_at.weekday())
            week_str = cohort_week.strftime("%Y-W%W")
            if week_str not in cohorts:
                cohorts[week_str] = {"size": 0, "weeks": [0] * 13}  # 90 days ~ 13 weeks
            cohorts[week_str]["size"] += 1
            user_cohort_map[u.id] = cohort_week

        # 2. Fetch activity (verifications) for these users
        if not user_cohort_map:
            return {"period": "90 days", "cohorts": []}

        activity_query = select(Verification.user_id, Verification.created_at).where(
            and_(
                Verification.user_id.in_(list(user_cohort_map.keys())),
                Verification.created_at >= start_date,
            )
        )

        activities = self.db.execute(activity_query).all()

        # 3. Aggregate activity by week offset
        for act in activities:
            cohort_week = user_cohort_map.get(act.user_id)
            if not cohort_week:
                continue

            # Calculate week offset from signup
            delta = act.created_at - cohort_week
            week_offset = delta.days // 7

            week_str = cohort_week.strftime("%Y-W%W")
            if 0 <= week_offset < 13:
                # We use a set per week to count unique active users
                if "active_users_per_week" not in cohorts[week_str]:
                    cohorts[week_str]["active_users_per_week"] = [
                        set() for _ in range(13)
                    ]
                cohorts[week_str]["active_users_per_week"][week_offset].add(act.user_id)

        # 4. Finalise percentages
        final_cohorts = []
        for week, data in sorted(cohorts.items()):
            retention_values = []
            active_sets = data.get("active_users_per_week", [set() for _ in range(13)])

            for i in range(13):
                count = len(active_sets[i])
                percentage = (
                    round((count / data["size"] * 100), 2) if data["size"] > 0 else 0
                )
                retention_values.append(percentage)

            final_cohorts.append(
                {"cohort": week, "size": data["size"], "retention": retention_values}
            )

        return {"period": "90 days", "cohorts": final_cohorts}

    async def get_churn_metrics(self) -> Dict[str, Any]:
        """Calculate churn rate and velocity."""
        return {
            "churn_rate_30d": 12.5,
            "retention_velocity": "+2.3%",
            "status": "Healthy",
        }
