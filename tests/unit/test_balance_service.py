"""Unit tests for BalanceService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.balance_service import BalanceService
from app.models.user import User


@pytest.mark.asyncio
async def test_get_user_balance_regular_user():
    """Regular user balance should use local database."""
    # Mock database session
    db = MagicMock()
    user = User(
        id="user123",
        email="user@test.com",
        is_admin=False,
        credits=Decimal("25.50")
    )
    db.query().filter().first.return_value = user
    
    # Get balance
    result = await BalanceService.get_user_balance("user123", db)
    
    # Assertions
    assert result["balance"] == 25.50
    assert result["source"] == "local"
    assert result["is_admin"] is False


@pytest.mark.asyncio
async def test_get_user_balance_admin_user():
    """Admin balance should fetch from TextVerified API."""
    # Mock database session
    db = MagicMock()
    user = User(
        id="admin123",
        email="admin@test.com",
        is_admin=True,
        credits=Decimal("10.00")
    )
    db.query().filter().first.return_value = user
    
    # Mock TextVerified service
    with patch("app.services.balance_service.TextVerifiedService") as MockTV:
        mock_tv = MockTV.return_value
        mock_tv.enabled = True
        mock_tv.get_balance = AsyncMock(return_value={"balance": 15.80})
        
        # Get balance
        result = await BalanceService.get_user_balance("admin123", db)
        
        # Assertions
        assert result["balance"] == 15.80
        assert result["source"] == "textverified"
        assert result["is_admin"] is True
        assert "last_synced" in result


@pytest.mark.asyncio
async def test_get_user_balance_admin_fallback_on_error():
    """Admin balance should fallback to cached on API error."""
    # Mock database session
    db = MagicMock()
    user = User(
        id="admin123",
        email="admin@test.com",
        is_admin=True,
        credits=Decimal("10.00")
    )
    db.query().filter().first.return_value = user
    
    # Mock TextVerified service with error
    with patch("app.services.balance_service.TextVerifiedService") as MockTV:
        mock_tv = MockTV.return_value
        mock_tv.enabled = True
        mock_tv.get_balance = AsyncMock(side_effect=Exception("API timeout"))
        
        # Get balance
        result = await BalanceService.get_user_balance("admin123", db)
        
        # Assertions
        assert result["balance"] == 10.00
        assert result["source"] == "cached"
        assert result["is_admin"] is True
        assert "error" in result


@pytest.mark.asyncio
async def test_check_sufficient_balance_sufficient():
    """Should return sufficient=True when balance is enough."""
    # Mock database session
    db = MagicMock()
    user = User(
        id="user123",
        email="user@test.com",
        is_admin=False,
        credits=Decimal("25.50")
    )
    db.query().filter().first.return_value = user
    
    # Check balance
    result = await BalanceService.check_sufficient_balance("user123", 10.00, db)
    
    # Assertions
    assert result["sufficient"] is True
    assert result["current_balance"] == 25.50
    assert result["required"] == 10.00
    assert "shortfall" not in result


@pytest.mark.asyncio
async def test_check_sufficient_balance_insufficient():
    """Should return sufficient=False when balance is not enough."""
    # Mock database session
    db = MagicMock()
    user = User(
        id="user123",
        email="user@test.com",
        is_admin=False,
        credits=Decimal("5.00")
    )
    db.query().filter().first.return_value = user
    
    # Check balance
    result = await BalanceService.check_sufficient_balance("user123", 10.00, db)
    
    # Assertions
    assert result["sufficient"] is False
    assert result["current_balance"] == 5.00
    assert result["required"] == 10.00
    assert result["shortfall"] == 5.00


@pytest.mark.asyncio
async def test_get_user_balance_user_not_found():
    """Should raise ValueError when user not found."""
    # Mock database session
    db = MagicMock()
    db.query().filter().first.return_value = None
    
    # Should raise error
    with pytest.raises(ValueError, match="User not found"):
        await BalanceService.get_user_balance("nonexistent", db)
