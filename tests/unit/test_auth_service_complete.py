

from app.services.auth_service import AuthService
from app.utils.security import verify_password

class TestAuthServiceComplete:

    """Complete auth service test suite using actual AuthService implementation."""

    def test_register_user_success(self, db_session):

        """Test successful user registration."""
        service = AuthService(db_session)
        email = "new_auth_user@example.com"
        password = "SecurePass123!"

        user = service.register_user(email, password)

        assert user.id is not None
        assert user.email == email
        assert verify_password(password, user.password_hash)

    def test_authenticate_user_success(self, db_session, regular_user):

        """Test successful authentication."""
        service = AuthService(db_session)
        # Assuming regular_user password is "password123" (see conftest.py)
        user = service.authenticate_user(regular_user.email, "password123")
        assert user is not None
        assert user.id == regular_user.id

    def test_authenticate_user_wrong_password(self, db_session, regular_user):

        """Test authentication with wrong password."""
        service = AuthService(db_session)
        user = service.authenticate_user(regular_user.email, "wrongpassword")
        assert user is None

    def test_api_key_management(self, db_session, regular_user):

        """Test API key operations."""
        service = AuthService(db_session)

        # Create
        api_key = service.create_api_key(regular_user.id, "Test Key")
        assert api_key.name == "Test Key"
        assert hasattr(api_key, "raw_key")

        # Verify
        user = service.verify_api_key(api_key.raw_key)
        assert user.id == regular_user.id

        # Deactivate
        success = service.deactivate_api_key(api_key.id, regular_user.id)
        assert success is True

        # Verify failure
        assert service.verify_api_key(api_key.raw_key) is None

    def test_password_reset_flow(self, db_session, regular_user):

        """Test password reset flow."""
        service = AuthService(db_session)

        token = service.reset_password_request(regular_user.email)
        assert token is not None

        new_pwd = "ResetPass123!"
        success = service.reset_password(token, new_pwd)
        assert success is True

        assert service.authenticate_user(regular_user.email, new_pwd) is not None

    def test_google_oauth(self, db_session):

        """Test Google OAuth user creation."""
        service = AuthService(db_session)
        google_id = "google_new_123"
        email = "google_new@example.com"

        user = service.create_or_get_google_user(google_id, email, "Google User")
        assert user.google_id == google_id
        assert user.provider == "google"

        # Link to existing
        existing_email = "existing_to_link@example.com"
        existing_user = service.register_user(existing_email, "pass123")
        google_id_2 = "google_linked_456"

        linked_user = service.create_or_get_google_user(google_id_2, existing_email)
        assert linked_user.id == existing_user.id
        assert linked_user.google_id == google_id_2

    def test_verify_email(self, db_session):

        """Test email verification."""
        service = AuthService(db_session)
        user = service.register_user("unverified@example.com", "pass123")
        token = "verify_me"
        user.verification_token = token
        user.email_verified = False
        db_session.commit()

        success = service.verify_email(token)
        assert success is True
        assert user.email_verified is True
