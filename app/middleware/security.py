"""Security middleware for authentication and authorization."""
from typing import Optional, List
from fastapi import Request, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.auth_service import AuthService


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware for protected endpoints."""
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", 
            "/", "/app", "/services", "/pricing", "/about", "/contact", "/admin",
            "/auth/login", "/auth/register", "/auth/google",
            "/auth/forgot-password", "/auth/reset-password", "/auth/verify",
            "/services/list", "/services/price", "/services/status",
            "/wallet/paystack/webhook", "/support/submit", "/system/health"
        ]
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with JWT authentication."""
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Extract authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication required", "message": "Missing or invalid authorization header"}
            )
        
        token = auth_header.split(" ")[1]
        
        # Validate token and get user
        db = SessionLocal()
        try:
            auth_service = AuthService(db)
            user = auth_service.get_user_from_token(token)
            
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "Invalid token", "message": "Token is invalid or expired"}
                )
            
            if not user.is_active:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Account disabled", "message": "User account is disabled"}
                )
            
            # Add user info to request state
            request.state.user = user
            request.state.user_id = user.id
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication failed", "message": str(e)}
            )
        finally:
            db.close()
        
        return await call_next(request)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """API key authentication middleware for programmatic access."""
    
    def __init__(self, app, api_key_header: str = "X-API-Key"):
        super().__init__(app)
        self.api_key_header = api_key_header
    
    async def dispatch(self, request: Request, call_next):
        """Process request with API key authentication."""
        # Only check API key if no JWT token is present
        if hasattr(request.state, 'user'):
            return await call_next(request)
        
        api_key = request.headers.get(self.api_key_header)
        if not api_key:
            return await call_next(request)
        
        # Validate API key
        db = SessionLocal()
        try:
            auth_service = AuthService(db)
            user = auth_service.verify_api_key(api_key)
            
            if user:
                request.state.user = user
                request.state.user_id = user.id
                request.state.auth_method = "api_key"
            
        except (ValueError, KeyError, AttributeError):
            pass  # Continue without authentication
        finally:
            db.close()
        
        return await call_next(request)


class AdminRoleMiddleware(BaseHTTPMiddleware):
    """Admin role verification middleware."""
    
    def __init__(self, app, admin_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.admin_paths = admin_paths or ["/admin"]
    
    async def dispatch(self, request: Request, call_next):
        """Check admin role for admin endpoints."""
        # Check if this is an admin path
        is_admin_path = any(request.url.path.startswith(path) for path in self.admin_paths)
        
        if is_admin_path:
            # Ensure user is authenticated
            if not hasattr(request.state, 'user'):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "Authentication required", "message": "Admin access requires authentication"}
                )
            
            # Check admin role
            if not request.state.user.is_admin:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Admin access required", "message": "This endpoint requires admin privileges"}
                )
        
        return await call_next(request)


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware with proper origin validation."""
    
    def __init__(
        self, 
        app, 
        allowed_origins: Optional[List[str]] = None,
        allowed_methods: Optional[List[str]] = None,
        allowed_headers: Optional[List[str]] = None,
        allow_credentials: bool = True
    ):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allowed_headers = allowed_headers or [
            "Accept", "Accept-Language", "Content-Language", "Content-Type",
            "Authorization", "X-API-Key", "X-Requested-With"
        ]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS headers."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = JSONResponse(content={})
        else:
            response = await call_next(request)
        
        # Set CORS headers
        if (origin and ("*" in self.allowed_origins or origin in self.allowed_origins or 
            (settings.environment == "development" and ("localhost" in origin or "127.0.0.1" in origin)))):
            response.headers["Access-Control-Allow-Origin"] = origin
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)
        
        # Enhanced Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://js.paystack.co; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.paystack.co https://www.google-analytics.com; "
            "frame-src https://js.paystack.co; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        
        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS for production
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return response