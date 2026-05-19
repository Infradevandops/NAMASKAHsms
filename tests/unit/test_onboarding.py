"""Unit tests for onboarding wizard endpoints (OB-16 to OB-19)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestOnboardingStatusDefault:
    """OB-16: new user has completed=False, step=0."""

    def test_default_values(self):
        from app.models.user import User

        user = User()
        # SQLAlchemy Column defaults are None until persisted; server_default
        # applies at DB level. Verify the columns exist and are falsy/zero.
        assert not user.onboarding_completed  # None or False both acceptable
        assert not user.onboarding_step  # None or 0 both acceptable


class TestOnboardingCompleteEndpoint:
    """OB-17: PUT endpoint sets completed=True."""

    @pytest.mark.asyncio
    async def test_complete_sets_flag(self):
        from app.api.auth_routes import complete_onboarding

        mock_user = MagicMock()
        mock_user.onboarding_completed = False
        mock_user.onboarding_step = 3

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_creds = MagicMock()
        mock_creds.credentials = "fake_token"

        with patch("app.api.auth_routes._get_user_from_token", return_value=mock_user):
            result = await complete_onboarding(credentials=mock_creds, db=mock_db)

        assert mock_user.onboarding_completed is True
        assert mock_user.onboarding_step == 6
        mock_db.commit.assert_called_once()
        assert result == {"status": "completed"}

    @pytest.mark.asyncio
    async def test_complete_user_not_found_raises_404(self):
        from app.api.auth_routes import complete_onboarding

        mock_creds = MagicMock()
        mock_creds.credentials = "fake_token"
        mock_db = MagicMock()

        with patch(
            "app.api.auth_routes._get_user_from_token",
            side_effect=HTTPException(status_code=404, detail="User not found"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await complete_onboarding(credentials=mock_creds, db=mock_db)
        assert exc_info.value.status_code == 404


class TestOnboardingStatusEndpoint:
    """OB-17 (status read path): GET returns correct shape."""

    @pytest.mark.asyncio
    async def test_status_returns_correct_shape(self):
        from app.api.auth_routes import get_onboarding_status

        mock_user = MagicMock()
        mock_user.onboarding_completed = False
        mock_user.onboarding_step = 2

        mock_creds = MagicMock()
        mock_creds.credentials = "fake_token"
        mock_db = MagicMock()

        with patch("app.api.auth_routes._get_user_from_token", return_value=mock_user):
            result = await get_onboarding_status(credentials=mock_creds, db=mock_db)

        assert result == {"completed": False, "step": 2}

    @pytest.mark.asyncio
    async def test_status_user_not_found_raises_404(self):
        from app.api.auth_routes import get_onboarding_status

        mock_creds = MagicMock()
        mock_creds.credentials = "fake_token"
        mock_db = MagicMock()

        with patch(
            "app.api.auth_routes._get_user_from_token",
            side_effect=HTTPException(status_code=404, detail="User not found"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_onboarding_status(credentials=mock_creds, db=mock_db)
        assert exc_info.value.status_code == 404


class TestOnboardingAuthRequired:
    """OB-18 & OB-19: endpoints require authentication."""

    def test_onboarding_status_requires_auth(self):
        import inspect

        from app.api.auth_routes import get_onboarding_status

        sig = inspect.signature(get_onboarding_status)
        assert "credentials" in sig.parameters

    def test_onboarding_complete_requires_auth(self):
        import inspect

        from app.api.auth_routes import complete_onboarding

        sig = inspect.signature(complete_onboarding)
        assert "credentials" in sig.parameters
