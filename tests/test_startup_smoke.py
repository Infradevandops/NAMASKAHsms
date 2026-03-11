"""
Startup smoke test — catches every import-level blocker before deploy.
If this test passes, the app will start. If it fails, a startup blocker exists.
"""

import importlib
import pytest


ROUTERS = [
    ("app.api.core.gdpr", "router"),
    ("app.api.admin.router", "router"),
    ("app.api.auth_routes", "router"),
    ("app.api.core.user_settings_endpoints", "router"),
    ("app.api.core.user_settings", "router"),
    ("app.api.core.api_key_endpoints", "router"),
    ("app.api.core.forwarding", "router"),
    ("app.api.core.blacklist", "router"),
    ("app.api.core.referrals", "router"),
    ("app.api.billing.router", "router"),
    ("app.api.compatibility_routes", "router"),
    ("app.api.core.notification_endpoints", "router"),
    ("app.api.dashboard_router", "router"),
    ("app.api.emergency", "router"),
    ("app.api.health", "router"),
    ("app.api.preview_router", "router"),
    ("app.api.main_routes", "router"),
    ("app.api.v1.router", "v1_router"),
    ("app.api.websocket_endpoints", "router"),
    ("app.api.verification.router", "router"),
    ("app.api.core.dashboard_activity", "router"),
    ("app.api.verification.services_endpoint", "router"),
    ("app.api.core.textverified_balance", "router"),
    ("app.services.email_service", "email_service"),
    ("app.utils.security", "hash_password"),
    ("app.utils.security", "get_password_hash"),
]


@pytest.mark.parametrize("module,attr", ROUTERS)
def test_router_imports(module, attr):
    """Every registered router must be importable with its expected attribute."""
    mod = importlib.import_module(module)
    assert hasattr(mod, attr), f"{module} missing attribute '{attr}'"


def test_settings_aliases():
    """Config backward-compat aliases must resolve without AttributeError."""
    from app.core.config import get_settings

    s = get_settings()
    assert s.smtp_host == s.smtp_server
    assert s.smtp_user == s.smtp_username
    assert s.from_email
    assert s.jwt_expiry_hours == s.jwt_expiration_hours


def test_hash_password_alias():
    """hash_password and get_password_hash must both work and produce verifiable hashes."""
    from app.utils.security import hash_password, get_password_hash, verify_password

    assert verify_password("test", hash_password("test"))
    assert verify_password("test", get_password_hash("test"))
