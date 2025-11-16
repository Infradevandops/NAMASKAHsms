"""Authentication API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.exceptions import AuthenticationError, ValidationError
from app.models.user import User
from app.schemas import (
    APIKeyCreate,
    APIKeyListResponse,
    APIKeyResponse,
    GoogleAuthRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    SuccessResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services import get_auth_service, get_notification_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user account."""
    auth_service = get_auth_service(db)
    notification_service = get_notification_service(db)

    try:
        # Register user
        new_user = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            referral_code=user_data.referral_code,
        )

        # Generate access token
        access_token = auth_service.create_user_token(new_user)

        # Send welcome email (async)
        await notification_service.send_email(
            to_email=new_user.email,
            subject="Welcome to Namaskah SMS!",
            body="<h2>Welcome to Namaskah SMS!</h2>"
            + "<p>Your account has been created successfully.</p>"
            + f"<p>You have {new_user.free_verifications} free verification(s) to get started.</p>"
            + "<p><a href='/app'>Start Using Namaskah SMS</a></p>",
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(new_user),
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Registration failed")


@router.get("/google/config")
def get_google_config():
    """Serve Google OAuth and feature flag config to clients.
    
    Returns configuration including:
    - client_id: Google OAuth client ID
    - claude_haiku_4_5_enabled: Global feature flag for Claude Haiku 4.5 model (2025-11-14)
    """
    from app.core.config import get_settings
    
    settings = get_settings()
    
    return JSONResponse(
        content={
            "client_id": settings.google_client_id or "11893866195-r9q595mc77j5n2c0j1neki1lmr3es3fb.apps.googleusercontent.com",
            "claude_haiku_4_5_enabled": True,
            "features": {
                "websocket_enabled": True,
                "real_time_updates": True,
                "bulk_verification": True,
                "enhanced_security": True,
                "auto_refresh": True,
                "notification_sound": True,
            }
        }
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page with Google OAuth."""
    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Namaskah SMS</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }
            .container { 
                max-width: 400px; width: 90%; background: white; padding: 40px; 
                border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 { text-align: center; margin-bottom: 30px; color: #333; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
            input { 
                width: 100%; padding: 15px; border: 2px solid #e1e5e9; border-radius: 8px;
                font-size: 16px; transition: all 0.3s ease;
            }
            input:focus { outline: none; border-color: #667eea; }
            button { 
                width: 100%; padding: 15px; background: #667eea; color: white; border: none;
                border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;
                transition: all 0.3s ease; margin-bottom: 15px;
            }
            button:hover { background: #5a67d8; }
            .google-btn {
                background: white; color: #333; border: 2px solid #e2e8f0;
                display: flex; align-items: center; justify-content: center;
            }
            .google-btn:hover { border-color: #4285f4; background: #f8f9fa; }
            .google-btn svg { margin-right: 10px; }
            .divider { 
                text-align: center; margin: 20px 0; position: relative; color: #718096;
            }
            .divider::before {
                content: ''; position: absolute; top: 50%; left: 0; right: 0;
                height: 1px; background: #e2e8f0;
            }
            .divider span { background: white; padding: 0 15px; }
            .message { padding: 12px; border-radius: 8px; margin-bottom: 20px; display: none; }
            .error { background: #fed7d7; color: #c53030; border-left: 4px solid #e53e3e; }
            .success { background: #c6f6d5; color: #2d7d32; border-left: 4px solid #38a169; }
            .back-link { text-align: center; margin-top: 20px; }
            .back-link a { color: #667eea; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Login to Namaskah SMS</h1>
            
            <div id="message" class="message"></div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" placeholder="Enter your email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" placeholder="Enter your password" required>
                </div>
                
                <button type="submit" id="loginBtn">Login</button>
            </form>
            
            <div class="divider"><span>or</span></div>
            
            <button class="google-btn" onclick="handleGoogleAuth()">
                <svg width="20" height="20" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
            </button>
            
            <div id="g_id_onload"
                 data-client_id="11893866195-r9q595mc77j5n2c0j1neki1lmr3es3fb.apps.googleusercontent.com"
                 data-context="signin"
                 data-ux_mode="popup"
                 data-callback="handleGoogleSignIn">
            </div>
            
            <div class="g_id_signin" style="display:none;"
                 data-type="standard"
                 data-shape="rectangular"
                 data-theme="outline"
                 data-text="continue_with"
                 data-size="large">
            </div>
            
            <div class="back-link">
                <a href="/app">← Back to Dashboard</a>
            </div>
        </div>
        
        <script src="https://accounts.google.com/gsi/client" async defer></script>
        <script>
            const form = document.getElementById('loginForm');
            const message = document.getElementById('message');
            
            function showMessage(text, type) {
                message.textContent = text;
                message.className = `message ${type}`;
                message.style.display = 'block';
            }
            
            form.onsubmit = async (e) => {
                e.preventDefault();
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        localStorage.setItem('token', data.access_token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        showMessage('Login successful! Redirecting...', 'success');
                        setTimeout(() => window.location.href = '/dashboard-app', 1000);
                    } else {
                        showMessage(data.detail || 'Login failed', 'error');
                    }
                } catch (err) {
                    showMessage('Network error', 'error');
                }
            };
            
            function handleGoogleAuth() {
                if (typeof google !== 'undefined' && google.accounts) {
                    google.accounts.id.prompt();
                } else {
                    showMessage('Google Sign-In loading...', 'success');
                    setTimeout(() => {
                        if (typeof google !== 'undefined') {
                            google.accounts.id.prompt();
                        } else {
                            showMessage('Google Sign-In not available', 'error');
                        }
                    }, 1000);
                }
            }
            
            async function handleGoogleSignIn(response) {
                try {
                    const result = await fetch('/auth/google', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: response.credential })
                    });
                    
                    const data = await result.json();
                    
                    if (result.ok) {
                        localStorage.setItem('token', data.access_token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        showMessage('Google sign-in successful! Redirecting...', 'success');
                        setTimeout(() => window.location.href = '/dashboard-app', 1000);
                    } else {
                        showMessage(data.detail || 'Google sign-in failed', 'error');
                    }
                } catch (err) {
                    showMessage('Google sign-in failed', 'error');
                }
            }
            
            // Initialize Google Sign-In
            window.onload = function() {
                if (typeof google !== 'undefined' && google.accounts) {
                    google.accounts.id.initialize({
                        client_id: '11893866195-r9q595mc77j5n2c0j1neki1lmr3es3fb.apps.googleusercontent.com',
                        callback: handleGoogleSignIn
                    });
                }
            };
        </script>
    </body>
    </html>
    """
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password."""
    try:
        auth_service = get_auth_service(db)

        # Authenticate user
        authenticated_user = auth_service.authenticate_user(
            email=login_data.email, password=login_data.password
        )

        if not authenticated_user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Generate access token
        access_token = auth_service.create_user_token(authenticated_user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(authenticated_user),
        )

    except HTTPException:
        raise
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/google", response_model=TokenResponse)
async def google_auth(google_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth."""
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
        from app.core.config import get_settings

        settings = get_settings()
        auth_service = get_auth_service(db)

        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            google_data.token, google_requests.Request(), settings.google_client_id
        )

        google_id = idinfo["sub"]
        email = idinfo["email"]
        name = idinfo.get("name", "")
        avatar_url = idinfo.get("picture")

        # Create or get user
        user = auth_service.create_or_get_google_user(
            google_id=google_id, email=email, name=name, avatar_url=avatar_url
        )

        # Generate access token
        access_token = auth_service.create_user_token(user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user),
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        print(f"Google auth error: {e}")
        raise HTTPException(status_code=401, detail="Google authentication failed")


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current authenticated user information."""
    current_user = db.query(User).filter(User.id == user_id).first()

    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.from_orm(current_user)


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    request_data: PasswordResetRequest, db: Session = Depends(get_db)
):
    """Request password reset link."""
    auth_service = get_auth_service(db)
    notification_service = get_notification_service(db)

    # Generate reset token
    reset_token = auth_service.reset_password_request(request_data.email)

    if reset_token:
        # Send reset email
        await notification_service.send_email(
            to_email=request_data.email,
            subject="Password Reset - Namaskah SMS",
            body="<h2>Password Reset Request</h2>"
            + "<p>Click the link below to reset your password:</p>"
            + f"<p><a href='/auth/reset-password?token={reset_token}'>Reset Password</a></p>"
            + "<p>This link expires in 1 hour.</p>",
        )

    # Always return success for security
    return SuccessResponse(message="If email exists, reset link sent")


@router.post("/reset-password", response_model=SuccessResponse)
def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token."""
    auth_service = get_auth_service(db)

    success = auth_service.reset_password(reset_data.token, reset_data.new_password)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    return SuccessResponse(message="Password reset successfully")


@router.post("/verify-email", response_model=SuccessResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address using token."""
    auth_service = get_auth_service(db)

    success = auth_service.verify_email(token)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    return SuccessResponse(message="Email verified successfully")


@router.post(
    "/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED
)
def create_api_key(
    api_key_data: APIKeyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create new API key for programmatic access."""
    auth_service = get_auth_service(db)

    api_key = auth_service.create_api_key(user_id, api_key_data.name)

    return APIKeyResponse.from_orm(api_key)


@router.get("/api-keys", response_model=list[APIKeyListResponse])
def list_api_keys(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """List user's API keys (without showing actual keys)."""
    from app.models.user import APIKey

    api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()

    return [
        APIKeyListResponse(
            id=key.id,
            name=key.name,
            key_preview=f"{key.key[:12]}...{key.key[-6:]}",
            is_active=key.is_active,
            created_at=key.created_at,
            last_used=key.last_used,
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}", response_model=SuccessResponse)
def delete_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete API key."""
    from app.models.user import APIKey

    api_key = (
        db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
    )

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(api_key)
    db.commit()

    return SuccessResponse(message="API key deleted successfully")


@router.post("/create-admin", response_model=SuccessResponse)
@router.get("/create-admin", response_model=SuccessResponse)
def create_admin_endpoint(db: Session = Depends(get_db)):
    """Create admin user via API endpoint."""
    from app.utils.security import hash_password
    
    admin_email = "admin@namaskah.app"
    admin_password = "NamaskahAdmin2024!"
    
    # Check if admin exists
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if existing_admin:
        return SuccessResponse(message="Admin user already exists")
    
    # Create admin user
    admin_user = User(
        email=admin_email,
        password_hash=hash_password(admin_password),
        credits=1000.0,
        is_admin=True,
        email_verified=True
    )
    
    db.add(admin_user)
    db.commit()
    
    return SuccessResponse(message="Admin user created successfully")



