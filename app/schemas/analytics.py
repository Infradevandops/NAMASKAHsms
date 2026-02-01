"""Analytics schemas for response validation."""


from typing import Dict, List, Optional
from pydantic import BaseModel

class ServiceUsage(BaseModel):

    service: str
    count: int
    success_rate: float
    avg_cost: float
    total_cost: float


class DailyUsage(BaseModel):

    date: str
    count: int
    cost: float
    success_rate: float


class CountryAnalytics(BaseModel):

    country: str
    count: int
    success_rate: float
    avg_cost: float


class TrendData(BaseModel):

    period: str
    value: float
    change_percent: Optional[float] = None


class PredictiveInsight(BaseModel):

    metric: str
    prediction: float
    confidence: float
    timeframe: str


class AnalyticsResponse(BaseModel):

    total_verifications: int
    success_rate: float
    total_spent: float
    popular_services: List[ServiceUsage]
    daily_usage: List[DailyUsage]
    country_performance: List[CountryAnalytics]
    cost_trends: List[TrendData]
    predictions: List[PredictiveInsight]
    efficiency_score: float
    recommendations: List[str]


class BusinessMetrics(BaseModel):

    revenue: float
    profit_margin: float
    customer_lifetime_value: float
    churn_rate: float
    growth_rate: float


class CompetitiveAnalysis(BaseModel):

    market_position: str
    cost_comparison: Dict[str, float]
    service_availability: Dict[str, bool]
    performance_benchmark: float