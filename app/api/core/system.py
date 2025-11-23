"""System API router for health checks and service status."""
from app.core.dependencies import get_current_user_id, get_current_admin_user, get_admin_user_id
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings

router = APIRouter(prefix="/system", tags=["System"])

# Add a root router for landing page
root_router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check with external service monitoring."""

    try:
        system_health = await health_monitor.get_system_health()
        health_data = check_system_health(db)

        return {
            "status": system_health["status"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.4.0",
            "environment": settings.environment,
            "database": health_data.get("database", "connected"),
            "services": system_health["services"],
            "summary": system_health["summary"],
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


@router.get("/health/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe."""

    try:
        db_health = check_database_health(db)
        is_ready = db_health["status"] == "healthy"
    except Exception:
        is_ready = False

    status_code = 200 if is_ready else 503
    return JSONResponse(status_code=status_code, content={"ready": is_ready})


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""

    # Simple liveness check - if we can respond, we're alive
    is_alive = True

    status_code = 200 if is_alive else 503
    return JSONResponse(status_code=status_code, content={"alive": is_alive})


@router.get("/status", response_model=ServiceStatusSummary)
def get_service_status(db: Session = Depends(get_db)):
    """Get comprehensive service status."""

    # Get service statuses from database
    services = db.query(ServiceStatusModel).all()

    # Convert to response format
    service_statuses = [
        ServiceStatus(
            service_name=service.service_name,
            status=service.status,
            success_rate=service.success_rate,
            last_checked=service.last_checked,
        )
        for service in services
    ]

    # Calculate overall status
    if not service_statuses:
        overall_status = "unknown"
        stats = {"operational": 0, "degraded": 0, "down": 0}
    else:
        status_counts = {}
        for service in service_statuses:
            status_counts[service.status] = status_counts.get(service.status, 0) + 1

        if status_counts.get("down", 0) > 0:
            overall_status = "down"
        elif status_counts.get("degraded", 0) > 0:
            overall_status = "degraded"
        else:
            overall_status = "operational"

        stats = {
            "operational": status_counts.get("operational", 0),
            "degraded": status_counts.get("degraded", 0),
            "down": status_counts.get("down", 0),
        }

    return ServiceStatusSummary(
        overall_status=overall_status,
        services=service_statuses,
        stats=stats,
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/info")
def get_system_info():
    """Get basic system information."""
    return {
        "service_name": "Namaskah SMS",
        "version": "2.3.0",
        "environment": getattr(settings, "environment", "production"),
        "features": {
            "sms_verification": True,
            "payment_processing": True,
            "admin_panel": True,
            "analytics": True,
        },
        "limits": {
            "max_concurrent_verifications": 100,
            "rate_limit_per_minute": 60,
            "max_api_keys_per_user": 5,
        },
    }


@router.get("/config")
def get_public_config():
    """Get public configuration settings."""
    return {
        "supported_services": [
            "telegram",
            "whatsapp",
            "discord",
            "instagram",
            "twitter",
            "facebook",
            "google",
            "microsoft",
        ],
        "payment_methods": ["paystack"],
        "currencies": ["NGN"],
        "min_credit_amount": 100.0,
        "verification_timeout_minutes": 10,
        "api_version": "v1",
    }


@router.get("/metrics")
async def get_system_metrics():
    """Get system performance metrics with service health."""

    try:
        system_health = await health_monitor.get_system_health()
        dashboard_data = await dashboard_metrics.get_system_health()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": f"{system_health['summary']['uptime_percentage']:.1f}%",
            "response_time": dashboard_data.get(
                "response_time", {"p50": "150ms", "p95": "500ms", "p99": "1000ms"}
            ),
            "requests": dashboard_data.get(
                "requests",
                {"total": 10000, "success_rate": "99.5%", "error_rate": "0.5%"},
            ),
            "services": {
                name: {
                    "status": service["status"],
                    "response_time": f"{service['response_time']*1000:.0f}ms",
                }
                for name, service in system_health["services"].items()
            },
            "database": dashboard_data.get(
                "database", {"connections": 5, "query_time": "50ms"}
            ),
        }
    except Exception:
        return {
            "error": "Metrics unavailable",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/metrics/business")
async def get_business_metrics():
    """Get business metrics."""
    return await dashboard_metrics.get_business_metrics()


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get Prometheus - formatted metrics."""


    metrics_data = get_prom_metrics()
    return Response(content=metrics_data, media_type=get_metrics_content_type())


@router.get("/metrics/application")
async def get_application_metrics():
    """Get application - specific metrics."""

    app_metrics = metrics_collector.get_application_metrics()
    health_score = metrics_collector.get_health_score()

    return {
        "application": app_metrics,
        "health": health_score,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@root_router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page with service information."""
    try:
        # Initialize templates
        templates = Jinja2Templates(directory="templates")

        # Context data for the template
        context = {
            "request": request,
            "service_name": "Namaskah SMS",
            "version": "2.4.0",
            "description": "SMS Verification Service API",
            "status": "operational",
            "total_services": 1807,
            "success_rate": 95,
            "active_users": 5247,
            "verifications_today": 15234,
        }

        # Render the landing page template
        return templates.TemplateResponse("landing.html", context)

    except Exception as e:
        # Fallback to JSON response if template fails
        import logging

        logger = logging.getLogger(__name__)
        logger.error("Landing page template error: %s", str(e), exc_info=True)

        # Return simple HTML as fallback
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Namaskah SMS</title>
            <meta charset="UTF - 8">
            <meta name="viewport" content="width = device - width, initial - scale = 1.0">
            <style>
                body {{ font - family: Arial, sans - serif; margin: 0; padding: 40px; background: #f5f5f5; }}
                .container {{ max - width: 800px; margin: 0 auto; background: white; padding: 40px; border - radius: 10px; box - shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #667eea; margin - bottom: 20px; }}
                .status {{ color: #10b981; font - weight: bold; }}
                .endpoints {{ background: #f8f9fa; padding: 20px; border - radius: 8px; margin: 20px 0; }}
                .endpoints a {{ color: #667eea; text - decoration: none; display: block; margin: 5px 0; }}
                .endpoints a:hover {{ text - decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Namaskah SMS</h1>
                <p><strong>Version:</strong> 2.4.0</p>
                <p><strong>Description:</strong> SMS Verification Service API</p>
                <p><strong>Status:</strong> <span class="status">Operational</span></p>

                <div class="endpoints">
                    <h3>Available Endpoints:</h3>
                    <a href="/app">📱 Main Dashboard</a>
                    <a href="/system/health">🏥 Health Check</a>
                    <a href="/auth">🔐 Authentication</a>
                    <a href="/verify">📱 SMS Verification</a>
                    <a href="/docs">📚 API Documentation</a>
                    <a href="/redoc">📖 ReDoc Documentation</a>
                </div>

                <p><em>Welcome to Namaskah SMS API - Your reliable SMS verification service!</em></p>
            </div>
        </body>
        </html>
        """,
            status_code=200,
        )

# Removed conflicting /app route - handled in main.py


@root_router.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    """Services listing page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {
            "request": request,
            "service_name": "Namaskah SMS",
            "total_services": 1807,
        }
        return templates.TemplateResponse("services.html", context)
    except Exception:
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head><title>Services - Namaskah SMS</title></head>
        <body>
            <h1>📱 Supported Services</h1>
            <p>We support 1,807+ services including:</p>
            <ul>
                <li>WhatsApp</li>
                <li>Telegram</li>
                <li>Google</li>
                <li>Discord</li>
                <li>Instagram</li>
                <li>And 1,800+ more...</li>
            </ul>
            <a href="/app">← Back to Dashboard</a>
        </body>
        </html>
        """
        )


@root_router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pricing - Namaskah SMS</title>
        <style>
            body { font - family: Arial, sans - serif; margin: 0; padding: 20px; background: #f5f7fa; }
            .container { max - width: 800px; margin: 0 auto; background: white; padding: 40px; border - radius: 10px; }
            .price { font - size: 3rem; color: #667eea; font - weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Simple Pricing</h1>
            <div class="price">₦1</div>
            <p>Per SMS verification</p>
            <ul>
                <li>✅ 1 Free verification on signup</li>
                <li>✅ Pay as you go - no subscriptions</li>
                <li>✅ Auto - refund if SMS not received</li>
                <li>✅ 95%+ success rate</li>
                <li>✅ 1,807+ supported services</li>
            </ul>
            <a href="/app" style="background: #667eea; color: white; padding: 12px 24px; text - decoration: none; border - radius: 6px;">Get Started</a>
        </div>
    </body>
    </html>
    """
    )


@root_router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request, "service_name": "Namaskah SMS"}
        return templates.TemplateResponse("about.html", context)
    except Exception:
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head><title>About - Namaskah SMS</title></head>
        <body>
            <h1>About Namaskah SMS</h1>
            <p>Reliable SMS verification service for 1,807+ platforms.</p>
            <p>Fast, secure, and affordable SMS verification solutions.</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """
        )


@root_router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Contact page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request, "service_name": "Namaskah SMS"}
        return templates.TemplateResponse("contact.html", context)
    except Exception:
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head><title>Contact - Namaskah SMS</title></head>
        <body>
            <h1>Contact Us</h1>
            <p>Need help? We're here for you!</p>
            <ul>
                <li>📧 Email: support@namaskah.app</li>
                <li>💬 Live Chat: Available 24/7</li>
                <li>📚 Documentation: <a href="/docs">/docs</a></li>
            </ul>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """
        )


@root_router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    """FAQ page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request, "service_name": "Namaskah SMS"}
        return templates.TemplateResponse("faq.html", context)
    except Exception:
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head><title>FAQ - Namaskah SMS</title></head>
        <body>
            <h1>Frequently Asked Questions</h1>
            <p>Find answers to common questions about Namaskah SMS.</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """
        )


@root_router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, admin_user=Depends(get_current_admin_user)):
    """Admin dashboard page (requires admin authentication)."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {
            "request": request,
            "service_name": "Namaskah SMS",
            "version": "2.4.0",
        }
        return templates.TemplateResponse("admin.html", context)
    except Exception:
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Dashboard - Namaskah SMS</title>
            <meta charset="UTF - 8">
            <meta name="viewport" content="width = device - width, initial - scale = 1.0">
            <style>
                body { font - family: Arial, sans - serif; margin: 0; padding: 0; background: #f5f7fa; }
                .header { background: linear - gradient(135deg,
                .container { max - width: 1200px; margin: 0 auto; padding: 20px; }
                .card { background: white; padding: 20px; border - radius: 10px; box - shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }
                .admin - grid { display: grid; grid - template-columns: repeat(auto - fit,
    minmax(250px, 1fr)); gap: 20px; }
                .admin - card { background: white; padding: 20px; border - radius: 8px; text - align: center; box - shadow: 0 2px 8px rgba(0,0,0,0.1); border - left: 4px solid #dc2626; }
                .admin - number { font - size: 2rem; font - weight: bold; color: #dc2626; }
                .cta - button { background: #dc2626; color: white; padding: 12px 24px; border: none; border - radius: 6px; cursor: pointer; font - size: 16px; text - decoration: none; display: inline - block; margin: 5px; }
                .cta - button:hover { background: #b91c1c; }
                .warning { background: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border - radius: 8px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>🛡️ Admin Dashboard</h1>
                    <p>Namaskah SMS Administration Panel</p>
                </div>
            </div>

            <div class="container">
                <div class="warning">
                    <h3>⚠️ Authentication Required</h3>
                    <p>This is the admin dashboard. Please log in with admin credentials to access admin features.</p>
                </div>

                <div class="card">
                    <h2>🔐 Admin Access</h2>
                    <p>To access admin features, you need to:</p>
                    <ol>
                        <li>Log in with an admin account</li>
                        <li>Have admin privileges enabled</li>
                        <li>Use proper authentication headers for API access</li>
                    </ol>

                    <div style="margin: 20px 0;">
                        <a href="/auth/login" class="cta - button">Admin Login</a>
                        <a href="/docs" class="cta - button" style="background: #6b7280;">API Docs</a>
                        <a href="/" class="cta - button" style="background: #10b981;">← Back Home</a>
                    </div>
                </div>

                <div class="card">
                    <h3>📋 Admin API Endpoints</h3>
                    <p>Available admin endpoints (require authentication):</p>
                    <ul>
                        <li><code>GET /admin/users</code> - List all users</li>
                        <li><code>GET /admin/stats</code> - System statistics</li>
                        <li><code>GET /admin/support/tickets</code> - Support tickets</li>
                        <li><code>PUT /admin/users/{user_id}</code> - Update user</li>
                        <li><code>DELETE /admin/users/{user_id}</code> - Delete user</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        )


@root_router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Service status page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request}
        return templates.TemplateResponse("status.html", context)
    except Exception:
        return HTMLResponse(content="<h1>Status page unavailable</h1>")


@root_router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Privacy policy page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request}
        return templates.TemplateResponse("privacy.html", context)
    except Exception:
        return HTMLResponse(content="<h1>Privacy policy unavailable</h1>")


@root_router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Terms of service page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request}
        return templates.TemplateResponse("terms.html", context)
    except Exception:
        return HTMLResponse(content="<h1>Terms of service unavailable</h1>")


@root_router.get("/refund", response_class=HTMLResponse)
async def refund_page(request: Request):
    """Refund policy page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request}
        return templates.TemplateResponse("refund.html", context)
    except Exception:
        return HTMLResponse(content="<h1>Refund policy unavailable</h1>")


@root_router.get("/cookies", response_class=HTMLResponse)
async def cookies_page(request: Request):
    """Cookie policy page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request}
        return templates.TemplateResponse("cookies.html", context)
    except Exception:
        return HTMLResponse(content="<h1>Cookie policy unavailable</h1>")
