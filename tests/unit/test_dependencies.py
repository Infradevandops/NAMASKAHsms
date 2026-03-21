"""Unit tests for require_tier() dependency."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.dependencies import require_tier


def _run_dependency(required_tier: str, user_id: str, db):
    """Helper to invoke the inner dependency function directly."""
    dep_fn = require_tier(required_tier)
    # Simulate FastAPI resolving the inner function
    return dep_fn(user_id=user_id, db=db)


class TestRequireTier:

    def test_passes_active_subscription(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
        db.commit()
        with patch("app.core.dependencies.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "pro"
            result = _run_dependency("pro", regular_user.id, db)
        assert result == regular_user.id

    def test_rejects_expired_subscription(self, db, regular_user):
        regular_user.subscription_tier = "pro"
        regular_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
        with patch("app.core.dependencies.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "freemium"
            with pytest.raises(HTTPException) as exc_info:
                _run_dependency("pro", regular_user.id, db)
        assert exc_info.value.status_code == 402

    def test_admin_always_passes_any_tier_gate(self, db, admin_user):
        # Admin bypass happens before TierManager is called
        result = _run_dependency("custom", admin_user.id, db)
        assert result == admin_user.id

    def test_payg_user_blocked_from_pro_gate(self, db, regular_user):
        regular_user.subscription_tier = "payg"
        regular_user.tier_expires_at = None
        db.commit()
        with patch("app.core.dependencies.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "payg"
            with pytest.raises(HTTPException) as exc_info:
                _run_dependency("pro", regular_user.id, db)
        assert exc_info.value.status_code == 402
