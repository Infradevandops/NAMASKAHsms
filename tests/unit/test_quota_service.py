from unittest.mock import MagicMock, patch

import pytest

from app.services.quota_service import QuotaService

# Mock data
TIER_CONFIG_MOCK = {
    "free": {"quota_usd": 10.0, "overage_rate": 0.5},
    "pro": {"quota_usd": 100.0, "overage_rate": 0.3},
}


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_tier_config():
    with patch("app.services.quota_service.TIER_CONFIG", TIER_CONFIG_MOCK):
        yield TIER_CONFIG_MOCK


def test_get_monthly_usage_no_usage(mock_db, mock_tier_config):
    # Mock user query
    user = MagicMock()
    user.subscription_tier = "free"
    mock_db.query.return_value.filter.return_value.first.side_effect = [None, user]
    # First call is for usage (returns None), second for user (returns user)
    # Wait, query chaining: db.query(MonthlyQuotaUsage).filter(...).first()

    # Let's verify the query structure in QuotaService
    # usage = db.query(MonthlyQuotaUsage).filter(...).first()
    # user = db.query(User).filter(...).first()

    # Setup mocks differently
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value

    # We need to handle different return values for different queries
    # This is tricky with simple mocks. Let's rely on patching the models/imports if needed
    # or just checking call arguments if we can't easily differentiate.
    # A cleaner way is to mock return values based on call.

    # Simpler approach: usage is None, user is found.
    # The code does db.query(MonthlyQuotaUsage)... THEN db.query(User)...

    # We can use side_effect on first()
    mock_filter.first.side_effect = [None, user]

    result = QuotaService.get_monthly_usage(mock_db, "user1")

    assert result["quota_used"] == 0.0
    assert result["quota_limit"] == 10.0
    assert result["remaining"] == 10.0


def test_get_monthly_usage_with_usage(mock_db, mock_tier_config):
    usage_mock = MagicMock()
    usage_mock.quota_used = 5.0
    usage_mock.overage_used = 0.0

    user = MagicMock()
    user.subscription_tier = "free"

    mock_db.query.return_value.filter.return_value.first.side_effect = [
        usage_mock,
        user,
    ]

    result = QuotaService.get_monthly_usage(mock_db, "user1")

    assert result["quota_used"] == 5.0
    assert result["remaining"] == 5.0


def test_add_quota_usage_new_record(mock_db):
    # Mock usage query returning None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    QuotaService.add_quota_usage(mock_db, "user1", 2.0)

    # Verify add was called
    assert mock_db.add.called
    assert mock_db.commit.called

    # Get the added object
    added_obj = mock_db.add.call_args[0][0]
    assert added_obj.user_id == "user1"
    assert added_obj.quota_used == 2.0


def test_add_quota_usage_existing_record(mock_db):
    usage_mock = MagicMock()
    usage_mock.quota_used = 1.0
    mock_db.query.return_value.filter.return_value.first.return_value = usage_mock

    QuotaService.add_quota_usage(mock_db, "user1", 2.0)

    assert usage_mock.quota_used == 3.0
    assert mock_db.commit.called


def test_calculate_overage_within_limit(mock_db, mock_tier_config):
    # usage=5, limit=10, cost=1
    usage_mock = MagicMock()
    usage_mock.quota_used = 5.0

    user = MagicMock()
    user.subscription_tier = "free"

    # Logic calls get_monthly_usage first
    # get_monthly_usage calls db twice.
    # Then calculate_overage doesn't call db again unless overage.

    # It's easier to patch get_monthly_usage
    with patch.object(QuotaService, "get_monthly_usage") as mock_get:
        mock_get.return_value = {"quota_used": 5.0, "quota_limit": 10.0}

        overage = QuotaService.calculate_overage(mock_db, "user1", 1.0)
        assert overage == 0.0


def test_calculate_overage_exceeded(mock_db, mock_tier_config):
    # usage=9, limit=10, cost=2 -> total 11 -> 1 overage
    user = MagicMock()
    user.subscription_tier = "free"  # rate 0.5

    mock_db.query.return_value.filter.return_value.first.return_value = user

    with patch.object(QuotaService, "get_monthly_usage") as mock_get:
        mock_get.return_value = {"quota_used": 9.0, "quota_limit": 10.0}

        overage = QuotaService.calculate_overage(mock_db, "user1", 2.0)
        # Expected: (11 - 10) * 0.5 = 0.5
        assert overage == 0.5


def test_get_overage_rate(mock_db, mock_tier_config):
    user = MagicMock()
    user.subscription_tier = "pro"
    mock_db.query.return_value.filter.return_value.first.return_value = user

    rate = QuotaService.get_overage_rate(mock_db, "user1")
    assert rate == 0.3
