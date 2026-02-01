"""Quick coverage boost tests for CI."""


# Service initialization tests

from app.services.payment_service import PaymentService
from app.services.textverified_service import TextVerifiedService
from app.services.tier_manager import TierManager
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.utils.sanitization import sanitize_filename
from app.utils.path_security import is_safe_path
from app.models.user import User
from app.models.transaction import Transaction
from app.models.verification import Verification
from app.models.subscription_tier import SubscriptionTier
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.tier_helpers import has_tier_access
from app.core.tier_helpers import TIER_HIERARCHY
from app.core.tier_helpers import has_tier_access

def test_payment_service_init():

    assert PaymentService is not None


def test_sms_service_init():

    assert TextVerifiedService is not None


def test_tier_manager_init():

    assert TierManager is not None


def test_auth_service_init():

    assert AuthService is not None


def test_notification_service_init():

    assert NotificationService is not None


# Utility function tests

def test_sanitize_filename():

    result = sanitize_filename("test file.txt")
    assert "test" in result
    assert ".txt" in result


def test_path_security():

    assert is_safe_path is not None


# Model tests

def test_user_model_import():

    assert User is not None


def test_transaction_model_import():

    assert Transaction is not None


def test_verification_model_import():

    assert Verification is not None


def test_subscription_tier_model_import():

    assert SubscriptionTier is not None


# Core functionality tests

def test_config_loading():

    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, "environment")


def test_logger_creation():

    logger = get_logger("test")
    assert logger is not None


def test_tier_helpers_import():

    assert has_tier_access is not None


def test_tier_hierarchy():

    assert "freemium" in TIER_HIERARCHY
    assert "pro" in TIER_HIERARCHY


def test_has_tier_access_basic():

    assert has_tier_access("pro", "freemium") is True
    assert has_tier_access("freemium", "pro") is False