"""Enhanced Analytics API router with advanced insights and predictions."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
import statistics

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.schemas import (
    AnalyticsResponse, BusinessMetrics, CompetitiveAnalysis,
    ServiceUsage, DailyUsage, CountryAnalytics, TrendData, PredictiveInsight
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/usage", response_model=AnalyticsResponse)
def get_user_analytics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get enhanced user analytics with predictions and insights."""
    start_date = datetime.now(timezone.utc) - timedelta(days=period)
    
    # Basic metrics
    total_verifications = db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date
    ).count()
    
    completed_verifications = db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date,
        Verification.status == "completed"
    ).count()
    
    success_rate = (completed_verifications / total_verifications * 100) if total_verifications > 0 else 0
    
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "debit",
        Transaction.created_at >= start_date
    ).scalar() or 0
    
    # Popular services with enhanced metrics
    popular_services = db.query(
        Verification.service_name,
        func.count(Verification.id).label('count')
    ).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date
    ).group_by(Verification.service_name).order_by(
        func.count(Verification.id).desc()
    ).limit(10).all()
    
    enhanced_services = []
    for service, count in popular_services:
        service_success = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.service_name == service,
            Verification.created_at >= start_date,
            Verification.status == "completed"
        ).count()
        
        service_cost = db.query(func.sum(Verification.cost)).filter(
            Verification.user_id == user_id,
            Verification.service_name == service,
            Verification.created_at >= start_date
        ).scalar() or 0
        
        enhanced_services.append(ServiceUsage(
            service=service,
            count=count,
            success_rate=round((service_success / count * 100) if count > 0 else 0, 1),
            avg_cost=round(float(service_cost / count) if count > 0 else 0, 2),
            total_cost=float(service_cost)
        ))
    
    # Daily usage with enhanced metrics
    daily_usage = []
    for i in range(period):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_verifications = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= day_start,
            Verification.created_at < day_end
        ).count()
        
        day_cost = db.query(func.sum(Verification.cost)).filter(
            Verification.user_id == user_id,
            Verification.created_at >= day_start,
            Verification.created_at < day_end
        ).scalar() or 0
        
        day_success = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= day_start,
            Verification.created_at < day_end,
            Verification.status == "completed"
        ).count()
        
        daily_usage.append(DailyUsage(
            date=day_start.strftime("%Y-%m-%d"),
            count=day_verifications,
            cost=float(day_cost),
            success_rate=round((day_success / day_verifications * 100) if day_verifications > 0 else 0, 1)
        ))
    
    # Country performance
    country_stats = db.query(
        Verification.country,
        func.count(Verification.id).label('count'),
        func.sum(func.case([(Verification.status == 'completed', 1)], else_=0)).label('completed'),
        func.avg(Verification.cost).label('avg_cost')
    ).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date
    ).group_by(Verification.country).all()
    
    country_analytics = []
    for country, count, completed, avg_cost in country_stats:
        country_analytics.append(CountryAnalytics(
            country=country,
            count=count,
            success_rate=round((completed / count * 100) if count > 0 else 0, 1),
            avg_cost=round(float(avg_cost or 0), 2)
        ))
    
    # Cost trends (weekly)
    cost_trends = []
    for i in range(4):
        week_start = datetime.now(timezone.utc) - timedelta(weeks=i+1)
        week_end = week_start + timedelta(weeks=1)
        
        week_cost = db.query(func.sum(Verification.cost)).filter(
            Verification.user_id == user_id,
            Verification.created_at >= week_start,
            Verification.created_at < week_end
        ).scalar() or 0
        
        cost_trends.append(TrendData(
            period=f"Week {i+1}",
            value=float(week_cost)
        ))
    
    # Calculate trend changes
    for i in range(len(cost_trends) - 1):
        if cost_trends[i+1].value > 0:
            change = ((cost_trends[i].value - cost_trends[i+1].value) / cost_trends[i+1].value) * 100
            cost_trends[i].change_percent = round(change, 1)
    
    # Predictive insights
    predictions = []
    if len(daily_usage) >= 7:
        recent_usage = [day.count for day in daily_usage[-7:]]
        avg_daily = statistics.mean(recent_usage)
        
        predictions.append(PredictiveInsight(
            metric="daily_usage",
            prediction=round(avg_daily * 1.1, 1),
            confidence=0.75,
            timeframe="next_week"
        ))
        
        # Cost prediction
        recent_costs = [day.cost for day in daily_usage[-7:]]
        avg_cost = statistics.mean(recent_costs)
        
        predictions.append(PredictiveInsight(
            metric="weekly_cost",
            prediction=round(avg_cost * 7 * 1.05, 2),
            confidence=0.70,
            timeframe="next_week"
        ))
    
    # Efficiency score (0-100)
    efficiency_factors = [
        success_rate / 100,  # Success rate factor
        min(1.0, 50 / (total_spent / total_verifications if total_verifications > 0 else 50)),  # Cost efficiency
        min(1.0, total_verifications / 30)  # Usage frequency
    ]
    efficiency_score = round(statistics.mean(efficiency_factors) * 100, 1)
    
    # Smart recommendations
    recommendations = []
    if success_rate < 80:
        recommendations.append("Consider switching to higher-success-rate services")
    if total_spent / total_verifications > 1.0 if total_verifications > 0 else False:
        recommendations.append("Look for more cost-effective service options")
    if total_verifications < 10:
        recommendations.append("Increase usage to get better insights")
    if len(enhanced_services) > 0:
        best_service = max(enhanced_services, key=lambda x: x.success_rate)
        recommendations.append(f"Consider using {best_service.service} more (highest success rate: {best_service.success_rate}%)")
    
    return AnalyticsResponse(
        total_verifications=total_verifications,
        success_rate=round(success_rate, 1),
        total_spent=abs(total_spent),
        popular_services=enhanced_services,
        daily_usage=list(reversed(daily_usage)),
        country_performance=country_analytics,
        cost_trends=cost_trends,
        predictions=predictions,
        efficiency_score=efficiency_score,
        recommendations=recommendations
    )


@router.get("/business-metrics", response_model=BusinessMetrics)
def get_business_metrics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(90, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get business intelligence metrics."""
    start_date = datetime.now(timezone.utc) - timedelta(days=period)
    
    # Revenue calculation
    revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "credit",
        Transaction.created_at >= start_date
    ).scalar() or 0
    
    # Cost calculation
    costs = db.query(func.sum(Verification.cost)).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date
    ).scalar() or 0
    
    profit_margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0
    
    # Customer lifetime value (simplified)
    total_user_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "credit"
    ).scalar() or 0
    
    # Growth rate (month over month)
    current_month_start = datetime.now(timezone.utc).replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    current_month_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "credit",
        Transaction.created_at >= current_month_start
    ).scalar() or 0
    
    last_month_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "credit",
        Transaction.created_at >= last_month_start,
        Transaction.created_at < current_month_start
    ).scalar() or 0
    
    growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
    
    return BusinessMetrics(
        revenue=float(revenue),
        profit_margin=round(profit_margin, 2),
        customer_lifetime_value=float(total_user_spent),
        churn_rate=0.0,  # Would need user activity tracking
        growth_rate=round(growth_rate, 2)
    )


@router.get("/competitive-analysis", response_model=CompetitiveAnalysis)
def get_competitive_analysis(
    country: Optional[str] = Query(None, description="Country code"),
    db: Session = Depends(get_db)
):
    """Get competitive analysis and market positioning."""
    
    # Mock competitive data (would be real-time in production)
    cost_comparison = {
        "telegram": 0.75,
        "whatsapp": 0.80,
        "google": 0.65,
        "discord": 0.70,
        "instagram": 1.20,
        "facebook": 1.10
    }
    
    service_availability = {
        "telegram": True,
        "whatsapp": True,
        "google": True,
        "discord": True,
        "instagram": False,
        "facebook": True,
        "twitter": False,
        "tiktok": True
    }
    
    # Calculate performance benchmark
    available_services = sum(1 for available in service_availability.values() if available)
    total_services = len(service_availability)
    performance_benchmark = (available_services / total_services) * 100
    
    return CompetitiveAnalysis(
        market_position="competitive",
        cost_comparison=cost_comparison,
        service_availability=service_availability,
        performance_benchmark=round(performance_benchmark, 1)
    )


@router.get("/real-time-insights")
def get_real_time_insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get real-time analytics insights."""
    now = datetime.now(timezone.utc)
    
    # Last 24 hours activity
    last_24h = now - timedelta(hours=24)
    
    recent_verifications = db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= last_24h
    ).count()
    
    recent_success = db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= last_24h,
        Verification.status == "completed"
    ).count()
    
    # Current hour activity
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    
    hourly_verifications = db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= current_hour
    ).count()
    
    # Service performance in last hour
    hourly_services = db.query(
        Verification.service_name,
        func.count(Verification.id).label('count')
    ).filter(
        Verification.user_id == user_id,
        Verification.created_at >= current_hour
    ).group_by(Verification.service_name).all()
    
    return {
        "timestamp": now.isoformat(),
        "last_24h": {
            "verifications": recent_verifications,
            "success_rate": round((recent_success / recent_verifications * 100) if recent_verifications > 0 else 0, 1)
        },
        "current_hour": {
            "verifications": hourly_verifications,
            "services": [{"service": s[0], "count": s[1]} for s in hourly_services]
        },
        "system_status": "operational",
        "alerts": []
    }