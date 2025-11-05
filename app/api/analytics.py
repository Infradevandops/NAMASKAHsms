"""Enhanced Analytics API router with advanced insights and predictions."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from sqlalchemy.exc import SQLAlchemyError, DatabaseError, OperationalError
import statistics
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.schemas import (
    AnalyticsResponse, BusinessMetrics, CompetitiveAnalysis,
    ServiceUsage, DailyUsage, CountryAnalytics, TrendData, PredictiveInsight
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/usage", response_model=AnalyticsResponse)
def get_user_analytics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get enhanced user analytics with predictions and insights."""
    try:
        # Validate period parameter
        if period not in [7, 30, 90]:
            raise HTTPException(status_code=400, detail="Period must be 7, 30, or 90 days")
        
        start_date = datetime.now(timezone.utc) - timedelta(days=period)
    
        # Optimized basic metrics - single query with aggregations
        try:
            basic_stats = db.query(
                func.count(Verification.id).label('total_verifications'),
                func.sum(func.case([(Verification.status == 'completed', 1)], else_=0)).label('completed_verifications'),
                func.sum(Verification.cost).label('total_cost')
            ).filter(
                Verification.user_id == user_id,
                Verification.created_at >= start_date
            ).first()
            
            total_verifications = basic_stats.total_verifications or 0
            completed_verifications = basic_stats.completed_verifications or 0
            verification_costs = basic_stats.total_cost or 0
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to query basic metrics for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error retrieving basic metrics")
        
        success_rate = (completed_verifications / total_verifications * 100) if total_verifications > 0 else 0
        
        # Get transaction spending separately (different table)
        try:
            total_spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == "debit",
                Transaction.created_at >= start_date
            ).scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to query total spent for user {user_id}: {e}")
            total_spent = 0
    
        # Optimized service metrics - single query with all aggregations
        try:
            service_stats = db.query(
                Verification.service_name,
                func.count(Verification.id).label('count'),
                func.sum(func.case([(Verification.status == 'completed', 1)], else_=0)).label('completed'),
                func.sum(Verification.cost).label('total_cost'),
                func.avg(Verification.cost).label('avg_cost')
            ).filter(
                Verification.user_id == user_id,
                Verification.created_at >= start_date
            ).group_by(Verification.service_name).order_by(
                func.count(Verification.id).desc()
            ).limit(10).all()
            
            enhanced_services = []
            for service, count, completed, total_cost, avg_cost in service_stats:
                try:
                    enhanced_services.append(ServiceUsage(
                        service=service or "unknown",
                        count=count,
                        success_rate=round((completed / count * 100) if count > 0 else 0, 1),
                        avg_cost=round(float(avg_cost or 0), 2),
                        total_cost=float(total_cost or 0)
                    ))
                except (ZeroDivisionError, ValueError) as e:
                    logger.warning(f"Failed to process service {service} for user {user_id}: {e}")
                    continue
                    
        except SQLAlchemyError as e:
            logger.error(f"Failed to query service metrics for user {user_id}: {e}")
            enhanced_services = []
    
        # Optimized daily usage - single query with date grouping
        try:
            daily_stats = db.query(
                func.date(Verification.created_at).label('date'),
                func.count(Verification.id).label('count'),
                func.sum(func.case([(Verification.status == 'completed', 1)], else_=0)).label('completed'),
                func.sum(Verification.cost).label('cost')
            ).filter(
                Verification.user_id == user_id,
                Verification.created_at >= start_date
            ).group_by(func.date(Verification.created_at)).all()
            
            # Create lookup dict for daily stats
            daily_lookup = {str(stat.date): stat for stat in daily_stats}
            
            daily_usage = []
            for i in range(period):
                day = datetime.now(timezone.utc) - timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                
                if day_str in daily_lookup:
                    stat = daily_lookup[day_str]
                    count = stat.count
                    completed = stat.completed or 0
                    cost = float(stat.cost or 0)
                    success_rate = round((completed / count * 100) if count > 0 else 0, 1)
                else:
                    count = 0
                    cost = 0.0
                    success_rate = 0.0
                
                daily_usage.append(DailyUsage(
                    date=day_str,
                    count=count,
                    cost=cost,
                    success_rate=success_rate
                ))
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to query daily usage for user {user_id}: {e}")
            daily_usage = []
    
        # Country performance (already optimized)
        try:
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
                    country=country or "unknown",
                    count=count,
                    success_rate=round((completed / count * 100) if count > 0 else 0, 1),
                    avg_cost=round(float(avg_cost or 0), 2)
                ))
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to query country performance for user {user_id}: {e}")
            country_analytics = []
    
        # Optimized cost trends - single query with week grouping
        try:
            four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
            
            weekly_costs = db.query(
                func.extract('week', Verification.created_at).label('week'),
                func.extract('year', Verification.created_at).label('year'),
                func.sum(Verification.cost).label('cost')
            ).filter(
                Verification.user_id == user_id,
                Verification.created_at >= four_weeks_ago
            ).group_by(
                func.extract('week', Verification.created_at),
                func.extract('year', Verification.created_at)
            ).order_by(
                func.extract('year', Verification.created_at).desc(),
                func.extract('week', Verification.created_at).desc()
            ).limit(4).all()
            
            cost_trends = []
            for i, (week, year, cost) in enumerate(weekly_costs):
                cost_trends.append(TrendData(
                    period=f"Week {i+1}",
                    value=float(cost or 0)
                ))
                
            # Fill missing weeks with zero
            while len(cost_trends) < 4:
                cost_trends.append(TrendData(
                    period=f"Week {len(cost_trends)+1}",
                    value=0.0
                ))
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to query cost trends for user {user_id}: {e}")
            cost_trends = [TrendData(period=f"Week {i+1}", value=0.0) for i in range(4)]
    
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_analytics for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing analytics")


@router.get("/business-metrics", response_model=BusinessMetrics)
def get_business_metrics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(90, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get business intelligence metrics."""
    try:
        if period not in [30, 60, 90, 180, 365]:
            raise HTTPException(status_code=400, detail="Period must be 30, 60, 90, 180, or 365 days")
        
        start_date = datetime.now(timezone.utc) - timedelta(days=period)
    
        # Optimized business metrics - combined queries
        try:
            # Combined revenue and cost calculation
            current_month_start = datetime.now(timezone.utc).replace(day=1)
            last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            
            # Single query for all transaction metrics
            transaction_metrics = db.query(
                func.sum(func.case([
                    (and_(Transaction.type == "credit", Transaction.created_at >= start_date), Transaction.amount)
                ], else_=0)).label('period_revenue'),
                func.sum(func.case([
                    (Transaction.type == "credit", Transaction.amount)
                ], else_=0)).label('total_revenue'),
                func.sum(func.case([
                    (and_(Transaction.type == "credit", Transaction.created_at >= current_month_start), Transaction.amount)
                ], else_=0)).label('current_month_revenue'),
                func.sum(func.case([
                    (and_(Transaction.type == "credit", 
                          Transaction.created_at >= last_month_start,
                          Transaction.created_at < current_month_start), Transaction.amount)
                ], else_=0)).label('last_month_revenue')
            ).filter(Transaction.user_id == user_id).first()
            
            revenue = transaction_metrics.period_revenue or 0
            total_user_spent = transaction_metrics.total_revenue or 0
            current_month_revenue = transaction_metrics.current_month_revenue or 0
            last_month_revenue = transaction_metrics.last_month_revenue or 0
            
            # Get costs from verification table
            costs = db.query(func.sum(Verification.cost)).filter(
                Verification.user_id == user_id,
                Verification.created_at >= start_date
            ).scalar() or 0
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to calculate business metrics for user {user_id}: {e}")
            revenue = costs = total_user_spent = current_month_revenue = last_month_revenue = 0
        
        profit_margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0
        growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
    
        return BusinessMetrics(
            revenue=float(revenue),
            profit_margin=round(profit_margin, 2),
            customer_lifetime_value=float(total_user_spent),
            churn_rate=0.0,  # Would need user activity tracking
            growth_rate=round(growth_rate, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_business_metrics for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing business metrics")


@router.get("/competitive-analysis", response_model=CompetitiveAnalysis)
def get_competitive_analysis(
    country: Optional[str] = Query(None, description="Country code"),
    db: Session = Depends(get_db)
):
    """Get competitive analysis and market positioning."""
    try:
        # Validate country code if provided
        if country and len(country) != 2:
            raise HTTPException(status_code=400, detail="Country code must be 2 characters")
        
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
        try:
            available_services = sum(1 for available in service_availability.values() if available)
            total_services = len(service_availability)
            performance_benchmark = (available_services / total_services) * 100
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Failed to calculate performance benchmark: {e}")
            performance_benchmark = 0.0
        
        return CompetitiveAnalysis(
            market_position="competitive",
            cost_comparison=cost_comparison,
            service_availability=service_availability,
            performance_benchmark=round(performance_benchmark, 1)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_competitive_analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing competitive analysis")


@router.get("/real-time-insights")
def get_real_time_insights(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get real-time analytics insights."""
    try:
        now = datetime.now(timezone.utc)
        
        # Optimized real-time insights - combined time-based queries
        last_24h = now - timedelta(hours=24)
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        try:
            # Single query for all time-based metrics
            time_metrics = db.query(
                func.sum(func.case([
                    (Verification.created_at >= last_24h, 1)
                ], else_=0)).label('recent_verifications'),
                func.sum(func.case([
                    (and_(Verification.created_at >= last_24h, Verification.status == 'completed'), 1)
                ], else_=0)).label('recent_success'),
                func.sum(func.case([
                    (Verification.created_at >= current_hour, 1)
                ], else_=0)).label('hourly_verifications')
            ).filter(Verification.user_id == user_id).first()
            
            recent_verifications = time_metrics.recent_verifications or 0
            recent_success = time_metrics.recent_success or 0
            hourly_verifications = time_metrics.hourly_verifications or 0
            
            # Separate query for hourly services (needs grouping)
            hourly_services = db.query(
                Verification.service_name,
                func.count(Verification.id).label('count')
            ).filter(
                Verification.user_id == user_id,
                Verification.created_at >= current_hour
            ).group_by(Verification.service_name).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to query real-time insights for user {user_id}: {e}")
            recent_verifications = recent_success = hourly_verifications = 0
            hourly_services = []
        
        return {
            "timestamp": now.isoformat(),
            "last_24h": {
                "verifications": recent_verifications,
                "success_rate": round((recent_success / recent_verifications * 100) if recent_verifications > 0 else 0, 1)
            },
            "current_hour": {
                "verifications": hourly_verifications,
                "services": [{"service": s[0] or "unknown", "count": s[1]} for s in hourly_services]
            },
            "system_status": "operational",
            "alerts": []
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in get_real_time_insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing real-time insights")