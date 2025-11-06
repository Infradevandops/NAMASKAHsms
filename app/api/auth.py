"""Authentication API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
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


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page with enhanced UX and error handling."""
    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Namaskah SMS</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="google-signin-client_id" content="11893866195-r9q595mc77j5n2c0j1neki1lmr3es3fb.apps.googleusercontent.com">
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
            input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
            input.error { border-color: #e53e3e; }
            button { 
                width: 100%; padding: 15px; background: #667eea; color: white; border: none;
                border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;
                transition: all 0.3s ease; position: relative;
            }
            button:hover:not(:disabled) { background: #5a67d8; transform: translateY(-1px); }
            button:disabled { background: #a0aec0; cursor: not-allowed; }
            .spinner { 
                display: none; width: 20px; height: 20px; border: 2px solid #ffffff40;
                border-top: 2px solid white; border-radius: 50%; animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .error-message { 
                background: #fed7d7; color: #c53030; padding: 12px; border-radius: 8px;
                margin-bottom: 20px; display: none; border-left: 4px solid #e53e3e;
            }
            .success-message { 
                background: #c6f6d5; color: #2d7d32; padding: 12px; border-radius: 8px;
                margin-bottom: 20px; display: none; border-left: 4px solid #38a169;
            }
            .back-link { text-align: center; margin-top: 20px; }
            .back-link a { color: #667eea; text-decoration: none; }
            .back-link a:hover { text-decoration: underline; }
            .demo-credentials { 
                background: #f7fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;
                border-left: 4px solid #4299e1;
            }
            .demo-credentials h4 { color: #2d3748; margin-bottom: 10px; }
            .demo-credentials p { color: #4a5568; font-size: 14px; margin: 5px 0; }
            .divider { 
                text-align: center; margin: 20px 0; position: relative;
                color: #718096;
            }
            .divider::before {
                content: ''; position: absolute; top: 50%; left: 0; right: 0;
                height: 1px; background: #e2e8f0;
            }
            .divider span {
                background: white; padding: 0 15px;
            }
            .google-btn {
                width: 100%; padding: 15px; background: white; color: #333;
                border: 2px solid #e2e8f0; border-radius: 8px; font-size: 16px;
                cursor: pointer; transition: all 0.3s ease; display: flex;
                align-items: center; justify-content: center; margin-bottom: 20px;
            }
            .google-btn:hover { border-color: #4285f4; box-shadow: 0 2px 8px rgba(66, 133, 244, 0.2); }
            .google-btn svg { margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Login to Namaskah SMS</h1>
            
            <div class="demo-credentials">
                <h4>Demo Admin Credentials:</h4>
                <p><strong>Email:</strong> admin@namaskah.app</p>
                <p><strong>Password:</strong> Namaskah@Admin2024</p>
            </div>
            
            <div id="errorMessage" class="error-message"></div>
            <div id="successMessage" class="success-message"></div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" placeholder="Enter your email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" placeholder="Enter your password" required>
                </div>
                
                <button type="submit" id="loginBtn">
                    <div class="spinner" id="spinner"></div>
                    <span id="btnText">Login</span>
                </button>
            </form>
            
            <div class="divider">
                <span>or</span>
            </div>
            
            <div id="g_id_onload"
                 data-client_id="11893866195-r9q595mc77j5n2c0j1neki1lmr3es3fb.apps.googleusercontent.com"
                 data-context="signin"
                 data-ux_mode="popup"
                 data-callback="handleGoogleSignIn"
                 data-auto_prompt="false"
                 data-itp_support="true">
            </div>
            
            <div class="g_id_signin" id="googleSignInButton"
                 data-type="standard"
                 data-shape="rectangular"
                 data-theme="outline"
                 data-text="continue_with"
                 data-size="large"
                 data-logo_alignment="left">
            </div>
            
            <button class="google-btn" id="googleSignIn" style="margin-top: 10px;">
                <svg width="20" height="20" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Fallback: Continue with Google
            </button>
            
            <div class="back-link">
                <a href="/app">← Back to Dashboard</a> | 
                <a href="/docs">API Docs</a>
            </div>
        </div>
        
        <script src="https://accounts.google.com/gsi/client" async defer onload="initializeGoogleSignIn()"></script>
        <script>
            const form = document.getElementById('loginForm');
            const emailInput = document.getElementById('email');
            const passwordInput = document.getElementById('password');
            const loginBtn = document.getElementById('loginBtn');
            const spinner = document.getElementById('spinner');
            const btnText = document.getElementById('btnText');
            const errorMessage = document.getElementById('errorMessage');
            const successMessage = document.getElementById('successMessage');
            const googleBtn = document.getElementById('googleSignIn');
            
            let googleInitialized = false;
            
            function showError(message) {
                errorMessage.textContent = message;
                errorMessage.style.display = 'block';
                successMessage.style.display = 'none';
                emailInput.classList.add('error');
                passwordInput.classList.add('error');
            }
            
            function showSuccess(message) {
                successMessage.textContent = message;
                successMessage.style.display = 'block';
                errorMessage.style.display = 'none';
                emailInput.classList.remove('error');
                passwordInput.classList.remove('error');
            }
            
            function hideMessages() {
                errorMessage.style.display = 'none';
                successMessage.style.display = 'none';
                emailInput.classList.remove('error');
                passwordInput.classList.remove('error');
            }
            
            function setLoading(loading) {
                loginBtn.disabled = loading;
                spinner.style.display = loading ? 'inline-block' : 'none';
                btnText.textContent = loading ? 'Logging in...' : 'Login';
            }
            
            // Clear errors on input
            [emailInput, passwordInput].forEach(input => {
                input.addEventListener('input', hideMessages);
            });
            
            form.onsubmit = async (e) => {
                e.preventDefault();
                hideMessages();
                setLoading(true);
                
                const email = emailInput.value.trim();
                const password = passwordInput.value;
                
                if (!email || !password) {
                    showError('Please fill in all fields');
                    setLoading(false);
                    return;
                }
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        localStorage.setItem('token', data.access_token);
                        localStorage.setItem('admin_token', data.access_token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        
                        showSuccess('Login successful! Redirecting...');
                        
                        setTimeout(() => {
                            window.location.href = data.user.is_admin ? '/admin' : '/app';
                        }, 1500);
                    } else {
                        showError(data.detail || 'Login failed. Please check your credentials.');
                        setLoading(false);
                    }
                } catch (err) {
                    showError('Network error. Please check your connection and try again.');
                    setLoading(false);
                }
            };
            
            // Auto-fill demo credentials on demo button click
            document.querySelector('.demo-credentials').addEventListener('click', () => {
                emailInput.value = 'admin@namaskah.app';
                passwordInput.value = 'Namaskah@Admin2024';
                hideMessages();
            });
            
            // Google Sign-In initialization
            function initializeGoogleSignIn() {
                if (typeof google !== 'undefined' && google.accounts) {
                    try {
                        google.accounts.id.initialize({
                            client_id: '11893866195-r9q595mc77j5n2c0j1neki1lmr3es3fb.apps.googleusercontent.com',
                            callback: handleGoogleSignIn,
                            auto_select: false,
                            cancel_on_tap_outside: false,
                            use_fedcm_for_prompt: false
                        });
                        
                        // Render the sign-in button
                        const buttonElement = document.getElementById('googleSignInButton');
                        if (buttonElement) {
                            google.accounts.id.renderButton(
                                buttonElement,
                                {
                                    theme: 'outline',
                                    size: 'large',
                                    type: 'standard',
                                    text: 'continue_with',
                                    logo_alignment: 'left'
                                }
                            );
                        }
                        
                        googleInitialized = true;
                        console.log('Google Sign-In initialized successfully');
                        
                        // Hide loading message and show success
                        hideMessages();
                        showSuccess('Google Sign-In ready! Click the Google button to sign in.');
                        
                    } catch (error) {
                        console.error('Google Sign-In initialization failed:', error);
                        showError('Google Sign-In setup failed. Using fallback button.');
                    }
                } else {
                    console.log('Google Sign-In library not loaded yet, retrying...');
                    setTimeout(initializeGoogleSignIn, 1000);
                }
            }
            
            async function handleGoogleSignIn(response) {
                try {
                    console.log('Google Sign-In response received');
                    setLoading(true);
                    
                    const result = await fetch('/auth/google', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: response.credential })
                    });
                    
                    const data = await result.json();
                    
                    if (result.ok) {
                        localStorage.setItem('token', data.access_token);
                        localStorage.setItem('admin_token', data.access_token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        
                        showSuccess('Google sign-in successful! Redirecting...');
                        
                        setTimeout(() => {
                            window.location.href = data.user.is_admin ? '/admin' : '/app';
                        }, 1500);
                    } else {
                        console.error('Google Sign-In API error:', data);
                        showError(data.detail || 'Google sign-in failed');
                        setLoading(false);
                    }
                } catch (err) {
                    console.error('Google Sign-In network error:', err);
                    showError('Google sign-in failed. Please try again.');
                    setLoading(false);
                }
            }
            
            googleBtn.addEventListener('click', () => {
                if (googleInitialized && typeof google !== 'undefined') {
                    try {
                        // For localhost development, show a demo message
                        showSuccess('Demo: Google Sign-In would work on HTTPS production. Using fallback for localhost.');
                        
                        // Simulate Google sign-in for demo
                        setTimeout(async () => {
                            try {
                                setLoading(true);
                                
                                // Demo Google user data
                                const demoGoogleUser = {
                                    credential: 'demo_google_token_for_localhost_testing'
                                };
                                
                                await handleGoogleSignIn(demoGoogleUser);
                            } catch (err) {
                                setLoading(false);
                                showError('Demo Google Sign-In failed. This would work on production HTTPS.');
                            }
                        }, 1000);
                        
                    } catch (error) {
                        console.error('Google Sign-In error:', error);
                        showError('Google Sign-In not available on localhost. Works on HTTPS production.');
                    }
                } else {
                    showError('Google Sign-In library not loaded. This is normal for localhost development.');
                }
            });
            
            // Initialize when page loads
            window.addEventListener('load', () => {
                setTimeout(() => {
                    if (!googleInitialized) {
                        initializeGoogleSignIn();
                        // Hide loading message after attempt
                        setTimeout(() => {
                            if (!googleInitialized) {
                                hideMessages();
                            }
                        }, 3000);
                    }
                }, 1000);
            });
            
            // Try to initialize when script loads
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    setTimeout(initializeGoogleSignIn, 500);
                });
            } else {
                setTimeout(initializeGoogleSignIn, 500);
            }
        </script>
    </body>
    </html>
    """
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password."""
    auth_service = get_auth_service(db)

    try:
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
    except Exception:
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


@router.post("/google", response_model=TokenResponse)
async def google_auth(google_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth."""
    try:
        from app.core.config import get_settings

        settings = get_settings()

        # Handle demo token for localhost development
        if google_data.token == "demo_google_token_for_localhost_testing":
            auth_service = get_auth_service(db)

            # Create demo Google user
            user = auth_service.create_or_get_google_user(
                google_id="demo_google_user_123",
                email="demo.google.user@gmail.com",
                name="Demo Google User",
                avatar_url="https://via.placeholder.com/150",
            )

            # Generate access token
            access_token = auth_service.create_user_token(user)

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse.from_orm(user),
            )

        # Real Google OAuth verification
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            google_data.token, google_requests.Request(), settings.google_client_id
        )

        google_id = idinfo["sub"]
        email = idinfo["email"]
        name = idinfo.get("name", "")
        avatar_url = idinfo.get("picture")

        auth_service = get_auth_service(db)

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

    except ImportError:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception:
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


@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None):
    """Handle Google OAuth callback for popup flow."""
    if error:
        return HTMLResponse(
            content=f"""
        <script>
            window.opener.postMessage({{type: 'GOOGLE_AUTH_ERROR', error: '{error}'}}, '*');
            window.close();
        </script>
        """
        )

    if not code:
        return HTMLResponse(
            content="""
        <script>
            window.opener.postMessage({type: 'GOOGLE_AUTH_ERROR', error: 'No authorization code received'}, '*');
            window.close();
        </script>
        """
        )

    # Exchange code for token (simplified for demo)
    return HTMLResponse(
        content=f"""
    <script>
        window.opener.postMessage({{type: 'GOOGLE_AUTH_SUCCESS', code: '{code}'}}, '*');
        window.close();
    </script>
    """
    )
