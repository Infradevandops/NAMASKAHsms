from fastapi import FastAPI

from app.api.core.router import router as core_router


def test_core_router_inclusion():
    """Test that all expected sub-routers are included in the core router."""
    app = FastAPI()
    app.include_router(core_router)

    # Get all registered routes
    routes = [route.path for route in app.routes]

    # Check for representative routes from various domains
    expected_prefixes = [
        "/api/keys",
        "/api/webhooks",
        "/api/user/me",
        "/api/user/preferences",
        "/system/health",
        "/api/countries",
        "/api/referrals",
    ]

    for prefix in expected_prefixes:
        assert any(
            route.startswith(prefix) for route in routes
        ), f"Prefix {prefix} not found in routes"


def test_router_tags():
    """Test that routers have expected tags for documentation."""
    app = FastAPI()
    app.include_router(core_router)

    # Check tags for some routes
    key_routes = [r for r in app.routes if r.path.startswith("/api/keys")]
    assert len(key_routes) > 0

    for route in key_routes:
        assert "API Keys" in route.tags

    webhook_routes = [r for r in app.routes if r.path.startswith("/api/webhooks")]
    assert len(webhook_routes) > 0
    for route in webhook_routes:
        assert "Webhooks" in route.tags
