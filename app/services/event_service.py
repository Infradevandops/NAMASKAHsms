"""Event tracking and analytics service."""

from datetime import datetime
from typing import Dict, Any, List
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventService:
    """Tracks user events for analytics."""

    def __init__(self):
        self.events = []

    async def track_event(self, user_id: str, event_type: str, properties: Dict[str, Any] = None):
        """Track user event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "event_type": event_type,
            "properties": properties or {},
        }
        self.events.append(event)
        logger.debug(f"Event tracked: {event_type} for {user_id}")

    async def get_events(self, user_id: str, event_type: str = None) -> List[Dict]:
        """Get user events."""
        events = [e for e in self.events if e["user_id"] == user_id]
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        return events

    async def get_funnel_data(self, steps: List[str]) -> Dict[str, int]:
        """Get conversion funnel data."""
        funnel = {}
        for step in steps:
            count = len([e for e in self.events if e["event_type"] == step])
            funnel[step] = count
        return funnel

    async def export_events(self, user_id: str = None) -> List[Dict]:
        """Export events for data warehouse."""
        if user_id:
            return [e for e in self.events if e["user_id"] == user_id]
        return self.events


event_service = EventService()
