"""Service for tracking user events and interactions."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user_event import UserEvent


class EventTrackingService:
    """Track user events for analytics and monitoring."""

    def __init__(self, db: Session):
        self.db = db

    def track_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserEvent:
        """Track a user event synchronously."""
        try:
            event = UserEvent.create(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(event)
            self.db.commit()
            return event
        except Exception as e:
            self.db.rollback()
            print(f"Error tracking event: {e}")
            return None

    async def track_event_async(
        self,
        user_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserEvent:
        """Track a user event asynchronously."""
        return await asyncio.to_thread(
            self.track_event,
            user_id,
            event_type,
            event_data,
            ip_address,
            user_agent,
        )

    def track_signup(
        self, user_id: str, event_data: Optional[Dict] = None
    ) -> UserEvent:
        """Track user signup event."""
        return self.track_event(
            user_id=user_id,
            event_type=UserEvent.SIGNUP,
            event_data=event_data or {},
        )

    def track_login(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserEvent:
        """Track user login event."""
        return self.track_event(
            user_id=user_id,
            event_type=UserEvent.LOGIN,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def track_verification(
        self,
        user_id: str,
        service_name: str,
        success: bool,
        cost: float,
        event_data: Optional[Dict] = None,
    ) -> UserEvent:
        """Track verification event."""
        event_type = (
            UserEvent.VERIFICATION_SUCCESS if success else UserEvent.VERIFICATION_FAILED
        )
        return self.track_event(
            user_id=user_id,
            event_type=event_type,
            event_data={
                "service": service_name,
                "cost": cost,
                **(event_data or {}),
            },
        )

    def track_tier_change(
        self,
        user_id: str,
        from_tier: str,
        to_tier: str,
        event_data: Optional[Dict] = None,
    ) -> UserEvent:
        """Track tier upgrade/downgrade event."""
        event_type = (
            UserEvent.TIER_UPGRADE if to_tier > from_tier else UserEvent.TIER_DOWNGRADE
        )
        return self.track_event(
            user_id=user_id,
            event_type=event_type,
            event_data={
                "from_tier": from_tier,
                "to_tier": to_tier,
                **(event_data or {}),
            },
        )

    def track_payment(
        self,
        user_id: str,
        amount: float,
        success: bool,
        event_data: Optional[Dict] = None,
    ) -> UserEvent:
        """Track payment event."""
        event_type = (
            UserEvent.PAYMENT_COMPLETED if success else UserEvent.PAYMENT_FAILED
        )
        return self.track_event(
            user_id=user_id,
            event_type=event_type,
            event_data={
                "amount": amount,
                **(event_data or {}),
            },
        )

    def track_feature_usage(
        self,
        user_id: str,
        feature_name: str,
        event_data: Optional[Dict] = None,
    ) -> UserEvent:
        """Track feature usage event."""
        return self.track_event(
            user_id=user_id,
            event_type=UserEvent.FEATURE_USED,
            event_data={
                "feature": feature_name,
                **(event_data or {}),
            },
        )

    def track_support_ticket(
        self,
        user_id: str,
        category: str,
        event_data: Optional[Dict] = None,
    ) -> UserEvent:
        """Track support ticket creation."""
        return self.track_event(
            user_id=user_id,
            event_type=UserEvent.SUPPORT_TICKET_CREATED,
            event_data={
                "category": category,
                **(event_data or {}),
            },
        )

    def get_user_events(
        self,
        user_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """Get user events."""
        query = self.db.query(UserEvent).filter(UserEvent.user_id == user_id)

        if event_type:
            query = query.filter(UserEvent.event_type == event_type)

        return query.order_by(UserEvent.created_at.desc()).limit(limit).all()

    def get_recent_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """Get recent events across all users."""
        query = self.db.query(UserEvent)

        if event_type:
            query = query.filter(UserEvent.event_type == event_type)

        return query.order_by(UserEvent.created_at.desc()).limit(limit).all()

    def get_event_count(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> int:
        """Get count of events."""
        query = self.db.query(UserEvent)

        if user_id:
            query = query.filter(UserEvent.user_id == user_id)

        if event_type:
            query = query.filter(UserEvent.event_type == event_type)

        return query.count()

    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics."""
        try:
            total_events = self.db.query(UserEvent).count()
            unique_users = self.db.query(UserEvent.user_id).distinct().count()

            # Get event type breakdown
            event_types = (
                self.db.query(
                    UserEvent.event_type, __import__("sqlalchemy").func.count()
                )
                .group_by(UserEvent.event_type)
                .all()
            )

            return {
                "total_events": total_events,
                "unique_users": unique_users,
                "event_types": {et[0]: et[1] for et in event_types},
            }
        except Exception as e:
            print(f"Error getting event stats: {e}")
            return {
                "total_events": 0,
                "unique_users": 0,
                "event_types": {},
            }
