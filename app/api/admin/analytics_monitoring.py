"""Analytics monitoring endpoints for tracking verification metrics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Note: Analytics endpoints removed - implement AnalyticsService first
# See roadmap for planned analytics features
