"""Tier verification middleware for all requests.

This middleware verifies the user's tier on every request and attaches it to the
request state for use in endpoints and decorators. It ensures that tier information
is always fresh and available throughout the request lifecycle.
"""

from fastapi import Request
from app.services.tier_manager import TierManager
from app.core.logging import get_logger

logger = get_logger(__name__)


async def tier_verification_middleware(request: Request, call_next):
    """Verify and attach tier to every request.
    
    This middleware:
    1. Skips public endpoints (auth, health, docs)
    2. Gets user_id from request state (set by auth middleware)
    3. Creates TierManager instance
    4. Calls get_user_tier() to get fresh tier from database
    5. Attaches tier and tier_manager to request state
    6. Handles errors gracefully (defaults to freemium)
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint in chain
        
    Returns:
        Response from next middleware/endpoint
    """
    
    # Skip public endpoints
    public_paths = ['/auth/', '/health', '/docs', '/openapi.json', '/static/']
    if any(request.url.path.startswith(p) for p in public_paths):
        return await call_next(request)
    
    # Get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        # No authenticated user - skip tier verification
        return await call_next(request)
    
    try:
        # Get database session from request state
        db = getattr(request.state, 'db', None)
        if not db:
            # No database session - skip tier verification
            logger.warning(f"No database session for user {user_id}")
            return await call_next(request)
        
        # Create TierManager and get fresh tier from database
        tier_manager = TierManager(db)
        tier = tier_manager.get_user_tier(user_id)
        
        # Attach to request state for use in endpoints
        request.state.user_tier = tier
        request.state.tier_manager = tier_manager
        
        # Log tier verification (debug level to avoid log spam)
        logger.debug(f"Tier verified: user={user_id}, tier={tier}")
        
    except Exception as e:
        # Error during tier verification - default to freemium
        logger.error(f"Tier verification failed for user {user_id}: {e}")
        request.state.user_tier = 'freemium'
        request.state.tier_manager = None
    
    # Continue to next middleware/endpoint
    return await call_next(request)
