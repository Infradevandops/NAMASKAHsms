"""Analytics service for rental monitoring."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Dict, Any
from app.models.rental import Rental
from app.utils.performance import async_cache

class RentalAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @async_cache(ttl=300)
    async def get_rental_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get rental usage statistics."""
        query = select(
            func.count(Rental.id).label('total_rentals'),
            func.sum(Rental.cost).label('total_spent'),
            func.avg(Rental.duration_hours).label('avg_duration')
        )
        
        if user_id:
            query = query.where(Rental.user_id == user_id)
        
        result = await self.db.execute(query)
        stats = result.first()
        
        return {
            'total_rentals': stats.total_rentals or 0,
            'total_spent': float(stats.total_spent or 0),
            'avg_duration': float(stats.avg_duration or 0)
        }
    
    @async_cache(ttl=600)
    async def get_provider_performance(self) -> Dict[str, Any]:
        """Get provider performance metrics."""
        query = select(
            Rental.provider,
            func.count(Rental.id).label('count'),
            func.avg(Rental.cost).label('avg_cost')
        ).group_by(Rental.provider)
        
        result = await self.db.execute(query)
        providers = result.all()
        
        return {
            provider.provider: {
                'rental_count': provider.count,
                'avg_cost': float(provider.avg_cost)
            }
            for provider in providers
        }