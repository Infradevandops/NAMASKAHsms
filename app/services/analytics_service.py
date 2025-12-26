from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_overview(self):
        """Get dashboard overview metrics"""
        # Users
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        active_users = self.db.query(func.count(User.id)).filter(User.credits > 0).scalar() or 0
        
        # Verifications
        total_verifications = self.db.query(func.count(Verification.id)).scalar() or 0
        success_verifications = self.db.query(func.count(Verification.id)).filter(
            Verification.status == 'completed'
        ).scalar() or 0
        success_rate = (success_verifications / total_verifications * 100) if total_verifications > 0 else 0
        
        # Revenue
        total_revenue = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'credit'
        ).scalar() or 0
        
        # Monthly revenue (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        monthly_revenue = self.db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.type == 'credit',
                Transaction.created_at >= thirty_days_ago
            )
        ).scalar() or 0
        
        # Calculate changes (mock for now - would need historical data)
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "change": "+12%"
            },
            "verifications": {
                "total": total_verifications,
                "success": success_verifications,
                "rate": round(success_rate, 1)
            },
            "revenue": {
                "total": float(total_revenue),
                "monthly": float(monthly_revenue),
                "change": "+8%"
            }
        }
    
    async def get_timeseries(self, days: int = 30):
        """Get daily verification timeseries data"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            func.date(Verification.created_at).label('date'),
            func.count(Verification.id).label('verifications'),
            func.sum(func.case([(Verification.status == 'completed', 1)], else_=0)).label('success')
        ).filter(
            Verification.created_at >= start_date
        ).group_by(
            func.date(Verification.created_at)
        ).order_by('date').all()
        
        return [
            {
                "date": str(row.date),
                "verifications": row.verifications,
                "success": row.success or 0
            }
            for row in results
        ]
    
    async def get_services_stats(self):
        """Get top services by usage"""
        results = self.db.query(
            Verification.service_name,
            func.count(Verification.id).label('count'),
            (func.sum(func.case([(Verification.status == 'completed', 1)], else_=0)) * 100.0 / func.count(Verification.id)).label('success_rate')
        ).group_by(
            Verification.service_name
        ).order_by(
            func.count(Verification.id).desc()
        ).limit(10).all()
        
        return [
            {
                "name": row.service_name,
                "count": row.count,
                "success_rate": round(row.success_rate, 1) if row.success_rate else 0
            }
            for row in results
        ]
