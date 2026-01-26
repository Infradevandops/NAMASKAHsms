"""Tests for startup initialization."""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.core.startup import ensure_admin_user


class TestEnsureAdminUser:
    """Test admin user creation and updates."""

    @patch("app.core.startup.SessionLocal")
    @patch("app.core.startup.hash_password")
    def test_admin_user_created_when_not_exists(self, mock_hash, mock_session):
        """Test admin user is created when it doesn't exist."""
        # Setup
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_hash.return_value = "hashed_password"

        with patch.dict(os.environ, {"ADMIN_EMAIL": "test@admin.com", "ADMIN_PASSWORD": "testpass"}):
            # Execute
            ensure_admin_user()

            # Verify
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @patch("app.core.startup.SessionLocal")
    @patch("app.core.startup.hash_password")
    @patch("app.utils.security.verify_password")
    def test_admin_user_updated_when_exists(self, mock_verify, mock_hash, mock_session):
        """Test admin user password is updated when user exists."""
        # Setup
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        existing_admin = MagicMock()
        existing_admin.id = "admin-123"
        existing_admin.email = "admin@test.com"
        existing_admin.password_hash = "old_hash"
        existing_admin.credits = 5000.0
        existing_admin.subscription_tier = "pro"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_admin
        mock_hash.return_value = "new_hashed_password"
        mock_verify.return_value = True

        with patch.dict(
            os.environ,
            {"ADMIN_EMAIL": "admin@test.com", "ADMIN_PASSWORD": "newpassword"},
        ):
            # Execute
            ensure_admin_user()

            # Verify password was updated
            assert existing_admin.password_hash == "new_hashed_password"
            assert existing_admin.is_admin is True
            assert existing_admin.email_verified is True
            assert existing_admin.subscription_tier == "custom"
            assert existing_admin.credits == 10000.0
            assert existing_admin.is_active is True
            assert existing_admin.is_suspended is False
            assert existing_admin.is_banned is False
            mock_db.commit.assert_called_once()

    @patch("app.core.startup.SessionLocal")
    def test_admin_user_skipped_when_no_password(self, mock_session):
        """Test admin user creation is skipped when ADMIN_PASSWORD not set."""
        # Setup
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        with patch.dict(os.environ, {"ADMIN_EMAIL": "admin@test.com"}, clear=True):
            # Execute
            ensure_admin_user()

            # Verify no database operations
            mock_db.add.assert_not_called()
            mock_db.commit.assert_not_called()

    @patch("app.core.startup.SessionLocal")
    @patch("app.core.startup.hash_password")
    @patch("app.utils.security.verify_password")
    def test_admin_password_verification_after_update(self, mock_verify, mock_hash, mock_session):
        """Test password verification is performed after update."""
        # Setup
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        existing_admin = MagicMock()
        existing_admin.password_hash = "old_hash"
        existing_admin.credits = 5000.0
        mock_db.query.return_value.filter.return_value.first.return_value = existing_admin
        mock_hash.return_value = "new_hash"
        mock_verify.return_value = True

        with patch.dict(os.environ, {"ADMIN_PASSWORD": "testpass", "ADMIN_EMAIL": "admin@test.com"}):
            # Execute
            ensure_admin_user()

            # Verify password verification was called
            mock_verify.assert_called_once_with("testpass", "new_hash")
