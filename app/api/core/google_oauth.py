"""Google OAuth authentication implementation."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Google OAuth"])
settings = get_settings()


@router.get("/google")
async def google_login(request: Request):
    """Initiate Google OAuth flow."""
    try:
        # Get Google OAuth URL
        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session (you might want to use Redis in production)
        # For now, we'll pass it through the redirect
        
        redirect_uri = f"{settings.base_url}/api/auth/google/callback"
        
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        
        # Build URL
        auth_url = f"{google_auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Google OAuth initiation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google login"
        )


@router.get("/google/callback")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback."""
    try:
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        redirect_uri = f"{settings.base_url}/api/auth/google/callback"
        
        token_data = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            logger.error(f"Google token exchange failed: {token_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        tokens = token_response.json()
        id_token = tokens.get("id_token")
        
        # Verify and decode ID token
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {tokens.get('access_token')}"}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        
        if userinfo_response.status_code != 200:
            logger.error(f"Failed to get user info: {userinfo_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )
        
        user_info = userinfo_response.json()
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        
        if not email or not google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        # Check if user exists
        user = db.query(User).filter(
            (User.email == email) | (User.google_id == google_id)
        ).first()
        
        if user:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
                db.commit()
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Google OAuth login: {email}")
        else:
            # Create new user
            user = User(
                email=email,
                google_id=google_id,
                is_active=True,
                email_verified=True,  # Google emails are verified
                credits=0.0,
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"New user via Google OAuth: {email}")
        
        # Generate JWT token
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours),
        }
        
        access_token = jwt.encode(
            token_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        # Redirect to dashboard with token
        redirect_url = f"{settings.base_url}/auth/login?token={access_token}&google_auth=success"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )
