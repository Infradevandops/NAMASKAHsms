"""Analytics schemas for response validation."""
from typing import List, Dict, Any
from pydantic import BaseModel


class ServiceUsage(BaseModel):
    service: str
    count: int


class DailyUsage(BaseModel):
    date: str
    count: int


class AnalyticsResponse(BaseModel):
    total_verifications: int
    success_rate: float
    total_spent: float
    popular_services: List[ServiceUsage]
    daily_usage: List[DailyUsage]