"""Tier validation middleware for feature gating."""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.core.logging import get_logger
from app.core.tier_config import TierConfig

logger = get_logger(__name__)


class TierValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate tier access for premium features."""
    
    # Routes that require specific tiers
    TIER_ROUTES = {
        # Area code selection (Starter+)
        "/api/verification/purchase": {"min_tier": "starter", "check_param": "area_code"},
        "/api/verification/area-codes": {"min_tier": "starter"},
        
        # ISP/Carrier filtering (Turbo only)
        "/api/verification/carriers": {"min_tier": "turbo"},
        "/api/verification/isp-filter": {"min_tier": "turbo"},
        
        # API key management (Starter+)
        "/api/keys": {"min_tier": "starter"},
        "/api/keys/generate": {"min_tier": "starter"},
        
        # Rentals (Starter+)
        "/api/rentals": {"min_tier": "starter", "check_params": ["area_code", "carrier"]},
        "/api/rentals/create": {"min_tier": "starter"},
        "/rental-modal": {"min_tier": "starter"},
    }
    
    TIER_HIERARCHY = {
        "freemium": 0,
        "starter": 1,
        "turbo": 2,
    }
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Check tier access before processing request."""
        path = request.url.path
        
        # Check if this route requires tier validation
        route_config = None
        for route_path, config in self.TIER_ROUTES.items():
            if path.startswith(route_path):
                route_config = config
                break
        
        if not route_config:
            # No tier restriction, continue normally
            return await call_next(request)
        
        # Get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            # No user authenticated, let auth middleware handle it
            return await call_next(request)
        
        user_tier = getattr(user, "subscription_tier", "freemium")
        required_tier = route_config["min_tier"]
        
        # Check if user's tier meets minimum requirement
        user_level = self.TIER_HIERARCHY.get(user_tier, 0)
        required_level = self.TIER_HIERARCHY.get(required_tier, 0)
        
        if user_level < required_level:
            logger.warning(
                f"User {user.id} ({user_tier}) attempted to access {required_tier} feature: {path}"
            )
            
            # Return upgrade required response
            return JSONResponse(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                content={
                    "error": "upgrade_required",
                    "message": f"This feature requires {required_tier.title()} tier or higher",
                    "current_tier": user_tier,
                    "required_tier": required_tier,
                    "upgrade_url": f"/upgrade?to={required_tier}"
                }
            )
        
        # Check specific parameters if configured
        if "check_param" in route_config and request.method in ["POST", "PUT"]:
            try:
                body = await request.json()
                param = route_config["check_param"]
                
                if param in body and body[param] not in [None, "", "any"]:
                    # User is trying to use premium parameter
                    if user_level < required_level:
                        return JSONResponse(
                            status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            content={
                                "error": "feature_locked",
                                "message": f"Parameter '{param}' requires {required_tier.title()} tier",
                                "current_tier": user_tier,
                                "required_tier": required_tier
                            }
                        )
            except Exception as e:
                logger.error(f"Error checking request body: {e}")
                # Continue processing, don't block on parameter check errors
        
        # Check multiple parameters (for rentals)
        if "check_params" in route_config and request.method in ["POST", "PUT"]:
            try:
                body = await request.json()
                for param in route_config["check_params"]:
                    if param in body and body[param] not in [None, "", "any"]:
                        if param == "carrier" and user_tier != "turbo":
                            return JSONResponse(
                                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                                content={
                                    "error": "feature_locked",
                                    "message": "Carrier/ISP filtering requires Turbo tier",
                                    "current_tier": user_tier,
                                    "required_tier": "turbo"
                                }
                            )
            except Exception as e:
                logger.error(f"Error checking params: {e}")
        
        # Tier check passed, continue
        request.state.user_tier = user_tier
        return await call_next(request)
