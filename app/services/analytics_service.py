from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification


class AnalyticsService:

    def __init__(self, db: Session):

        self.db = db

    async def get_overview(self):
        """Get dashboard overview metrics"""
        # Users
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        active_users = (
            self.db.query(func.count(User.id)).filter(User.credits > 0).scalar() or 0
        )

        # Verifications
        total_verifications = self.db.query(func.count(Verification.id)).scalar() or 0
        success_verifications = (
            self.db.query(func.count(Verification.id))
            .filter(Verification.status == "completed")
            .scalar()
            or 0
        )
        success_rate = (
            (success_verifications / total_verifications * 100)
            if total_verifications > 0
            else 0
        )

        # Revenue
        total_revenue = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.type == "credit")
            .scalar()
            or 0
        )

        # Refunds
        total_refunds = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.type == "verification_refund")
            .scalar()
            or 0
        )
        total_refunds = abs(float(total_refunds))

        # Net Revenue
        net_revenue = float(total_revenue) - total_refunds

        # Monthly revenue (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        monthly_revenue = (
            self.db.query(func.sum(Transaction.amount))
            .filter(
                and_(
                    Transaction.type == "credit",
                    Transaction.created_at >= thirty_days_ago,
                )
            )
            .scalar()
            or 0
        )

        # Calculate changes (mock for now - would need historical data)
        return {
            "users": {"total": total_users, "active": active_users, "change": "+12%"},
            "verifications": {
                "total": total_verifications,
                "success": success_verifications,
                "rate": round(success_rate, 1),
            },
            "revenue": {
                "gross": float(total_revenue),
                "refunds": total_refunds,
                "net": net_revenue,
                "monthly": float(monthly_revenue),
                "change": "+8%",
            },
        }

    async def get_timeseries(self, days: int = 30):
        """Get daily verification timeseries data"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        results = (
            self.db.query(
                func.date(Verification.created_at).label("date"),
                func.count(Verification.id).label("verifications"),
                func.sum(
                    func.case([(Verification.status == "completed", 1)], else_=0)
                ).label("success"),
            )
            .filter(Verification.created_at >= start_date)
            .group_by(func.date(Verification.created_at))
            .order_by("date")
            .all()
        )

        return [
            {
                "date": str(row.date),
                "verifications": row.verifications,
                "success": row.success or 0,
            }
            for row in results
        ]

    async def get_services_stats(self):
        """Get top services by usage"""
        results = (
            self.db.query(
                Verification.service_name,
                func.count(Verification.id).label("count"),
                (
                    func.sum(
                        func.case([(Verification.status == "completed", 1)], else_=0)
                    )
                    * 100.0
                    / func.count(Verification.id)
                ).label("success_rate"),
            )
            .group_by(Verification.service_name)
            .order_by(func.count(Verification.id).desc())
            .limit(10)
            .all()
        )

        return [
            {
                "name": row.service_name,
                "count": row.count,
                "success_rate": round(row.success_rate, 1) if row.success_rate else 0,
            }
            for row in results
        ]

    def calculate_summary(self, verifications: list) -> dict:
        total = len(verifications)
        completed = sum(1 for v in verifications if v.get("status") == "completed")
        failed = sum(1 for v in verifications if v.get("status") == "failed")
        pending = sum(1 for v in verifications if v.get("status") == "pending")
        total_spent = sum(float(v.get("cost", 0) or 0) for v in verifications)
        return {
            "total_verifications": total,
            "successful_verifications": completed,
            "failed_verifications": failed,
            "pending_verifications": pending,
            "success_rate": round(completed / total * 100, 1) if total else 0.0,
            "total_spent": total_spent,
        }

    def group_by_service(self, verifications: list) -> dict:
        groups = {}
        for v in verifications:
            svc = v.get("service_name") or v.get("service", "unknown")
            if svc not in groups:
                groups[svc] = {"count": 0, "total_cost": 0.0}
            groups[svc]["count"] += 1
            groups[svc]["total_cost"] += float(v.get("cost", 0) or 0)
        return groups

    def calculate_daily_stats(self, verifications: list, days: int = 30) -> list:
        from collections import defaultdict
        from datetime import datetime, timedelta

        buckets = defaultdict(int)
        for v in verifications:
            created = v.get("created_at")
            if isinstance(created, datetime):
                buckets[created.date()] += 1
        cutoff = (datetime.now() - timedelta(days=days)).date()
        return [
            {"date": str(d), "count": c}
            for d, c in sorted(buckets.items())
            if d >= cutoff
        ]

    def get_top_services(self, verifications: list, limit: int = 5) -> list:
        grouped = self.group_by_service(verifications)
        sorted_svcs = sorted(grouped.items(), key=lambda x: x[1]["count"], reverse=True)
        return [{"name": name, **stats} for name, stats in sorted_svcs[:limit]]

    async def get_refund_metrics(self, days: int = 30):
        """Get comprehensive refund analytics."""
        from datetime import datetime, timedelta, timezone

        from app.models.balance_transaction import BalanceTransaction

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Total refunds from balance_transactions
        total_refunds = (
            self.db.query(func.sum(BalanceTransaction.amount))
            .filter(
                BalanceTransaction.type == "refund",
                BalanceTransaction.created_at >= start_date,
            )
            .scalar()
            or 0
        )

        refund_count = (
            self.db.query(func.count(BalanceTransaction.id))
            .filter(
                BalanceTransaction.type == "refund",
                BalanceTransaction.created_at >= start_date,
            )
            .scalar()
            or 0
        )

        # Total revenue (credits)
        total_revenue = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.type == "credit", Transaction.created_at >= start_date)
            .scalar()
            or 0
        )

        # Total debits
        total_debits = (
            self.db.query(func.sum(BalanceTransaction.amount))
            .filter(
                BalanceTransaction.type == "debit",
                BalanceTransaction.created_at >= start_date,
            )
            .scalar()
            or 0
        )

        # Refund by reason from verifications
        refund_by_reason = (
            self.db.query(
                Verification.refund_reason,
                func.count(Verification.id).label("count"),
                func.sum(Verification.refund_amount).label("amount"),
            )
            .filter(
                Verification.refunded == True, Verification.created_at >= start_date
            )
            .group_by(Verification.refund_reason)
            .all()
        )

        # Calculate metrics
        total_verifications = (
            self.db.query(func.count(Verification.id))
            .filter(Verification.created_at >= start_date)
            .scalar()
            or 0
        )

        refund_rate = (
            (refund_count / total_verifications * 100) if total_verifications > 0 else 0
        )
        net_revenue = float(total_revenue) - float(total_refunds)

        return {
            "period_days": days,
            "total_refunds": float(total_refunds),
            "refund_count": refund_count,
            "avg_refund": (
                float(total_refunds / refund_count) if refund_count > 0 else 0
            ),
            "total_revenue": float(total_revenue),
            "total_debits": abs(float(total_debits)),
            "net_revenue": net_revenue,
            "refund_rate": round(refund_rate, 2),
            "total_verifications": total_verifications,
            "refund_by_reason": [
                {"reason": r[0] or "unknown", "count": r[1], "amount": float(r[2] or 0)}
                for r in refund_by_reason
            ],
        }

    async def get_net_revenue_by_service(self, limit: int = 10):
        """Get net revenue breakdown per service using hardened telemetry."""
        from app.models.purchase_outcome import PurchaseOutcome

        results = (
            self.db.query(
                PurchaseOutcome.service,
                func.count(PurchaseOutcome.id).label("total_attempts"),
                func.sum(PurchaseOutcome.user_price).label("gross_revenue"),
                func.sum(PurchaseOutcome.refund_amount).label("total_refunds"),
                (
                    func.sum(PurchaseOutcome.user_price)
                    - func.sum(PurchaseOutcome.refund_amount)
                ).label("net_revenue"),
            )
            .group_by(PurchaseOutcome.service)
            .order_by(text("net_revenue DESC"))
            .limit(limit)
            .all()
        )

        return [
            {
                "service": row.service,
                "total_attempts": row.total_attempts,
                "gross_revenue": float(row.gross_revenue or 0),
                "total_refunds": float(row.total_refunds or 0),
                "net_revenue": float(row.net_revenue or 0),
            }
            for row in results
        ]

    async def get_refund_stats(self):
        """Get comprehensive refund analytics (Institutional Grade)"""
        # 1. Total Refunds
        total_refunded = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.type == "verification_refund")
            .scalar()
            or 0.0
        )
        total_refunded = abs(float(total_refunded))

        # 2. Refund Rate
        total_v = self.db.query(func.count(Verification.id)).scalar() or 0
        refunded_v = (
            self.db.query(func.count(Verification.id))
            .filter(Verification.refunded == True)
            .scalar()
            or 0
        )
        refund_rate = (refunded_v / total_v * 100) if total_v > 0 else 0.0

        # 3. Refunds by Reason
        from app.models.purchase_outcome import PurchaseOutcome

        reason_stats = (
            self.db.query(
                PurchaseOutcome.refund_reason,
                func.count(PurchaseOutcome.id).label("count"),
                func.sum(PurchaseOutcome.refund_amount).label("amount"),
            )
            .filter(PurchaseOutcome.is_refunded == True)
            .group_by(PurchaseOutcome.refund_reason)
            .all()
        )

        # 4. Net Revenue Breakdown
        gross_rev = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.type == "credit")
            .scalar()
            or 0.0
        )

        return {
            "total_refunded": total_refunded,
            "refund_rate": round(refund_rate, 2),
            "refund_count": refunded_v,
            "net_revenue": float(gross_rev) - total_refunded,
            "by_reason": [
                {
                    "reason": row.refund_reason or "Unknown",
                    "count": row.count,
                    "amount": float(row.amount or 0),
                }
                for row in reason_stats
            ],
        }
