

import pytest
from app.core.exceptions import ValidationError
from app.models.user import User
from app.services.auth_service import AuthService

class TestAuthService:
    @pytest.fixture
def auth_service(self, db_session):

        return AuthService(db_session)

def test_register_user_success(self, auth_service, db_session):

        email = "newuser@example.com"
        password = "SecurePassword123!"
        user = auth_service.register_user(email, password)

        assert user.email == email
        assert user.password_hash is not None
        assert user.referral_code is not None

        # Verify saved in DB
        db_user = db_session.query(User).filter(User.email == email).first()
        assert db_user is not None
        assert db_user.id == user.id

def test_register_user_duplicate_email(self, auth_service, regular_user):

with pytest.raises(ValidationError, match="Email already registered"):
            auth_service.register_user(regular_user.email, "anypassword")

def test_register_user_with_referral(self, auth_service, regular_user, db_session):
        # regular_user.referral_code is generated in AuthService.register_user or conftest?
        # Let's check conftest or just mock it.
        # Actually register_user generates it.

        # Ensure regular_user has a referral code for this test if not already there
if not regular_user.referral_code:
            regular_user.referral_code = "TESTREF"
            db_session.commit()

        new_email = "referred@example.com"
        user = auth_service.register_user(new_email, "pass123", referral_code=regular_user.referral_code)

        assert user.referred_by == regular_user.id
        assert user.free_verifications == 2.0

def test_authenticate_user_success(self, auth_service, db_session):

        email = "auth_test@example.com"
        password = "Password123!"
        auth_service.register_user(email, password)

        user = auth_service.authenticate_user(email, password)
        assert user is not None
        assert user.email == email

def test_authenticate_user_wrong_password(self, auth_service, db_session):

        email = "wrong_pass@example.com"
        password = "Password123!"
        auth_service.register_user(email, password)

        user = auth_service.authenticate_user(email, "wrongpassword")
        assert user is None

def test_authenticate_user_not_found(self, auth_service):

        user = auth_service.authenticate_user("nonexistent@example.com", "any")
        assert user is None

def test_create_and_verify_api_key(self, auth_service, regular_user):

        name = "Test Key"
        api_key_obj = auth_service.create_api_key(regular_user.id, name)

        assert api_key_obj.user_id == regular_user.id
        assert api_key_obj.name == name
        assert hasattr(api_key_obj, "raw_key")
        assert api_key_obj.raw_key.startswith("nsk_")

        # Verify key
        user = auth_service.verify_api_key(api_key_obj.raw_key)
        assert user is not None
        assert user.id == regular_user.id

def test_verify_api_key_invalid(self, auth_service):

        user = auth_service.verify_api_key("nsk_invalid_key")
        assert user is None

def test_deactivate_api_key(self, auth_service, regular_user):

        api_key_obj = auth_service.create_api_key(regular_user.id, "To Deactivate")

        success = auth_service.deactivate_api_key(api_key_obj.id, regular_user.id)
        assert success is True

        # Should not verify anymore
        user = auth_service.verify_api_key(api_key_obj.raw_key)
        assert user is None

def test_reset_password_flow(self, auth_service, regular_user):
        # 1. Request reset
        token = auth_service.reset_password_request(regular_user.email)
        assert token is not None
        assert regular_user.reset_token == token

        # 2. Reset password
        new_password = "NewSecurePassword123!"
        success = auth_service.reset_password(token, new_password)
        assert success is True
        assert regular_user.reset_token is None

        # 3. Verify new password works
        user = auth_service.authenticate_user(regular_user.email, new_password)
        assert user is not None
        assert user.id == regular_user.id

    async def test_reset_password_invalid_token(self, auth_service):
        success = auth_service.reset_password("invalid_token", "newpassword123")
        assert success is False

def test_authenticate_oauth_user_no_password(self, auth_service, db_session):
        # Create a user without a password hash (OAuth user)
        user = User(email="oauth@example.com", google_id="google123")
        db_session.add(user)
        db_session.commit()

        # Should return None instead of raising error
        auth_result = auth_service.authenticate_user("oauth@example.com", "any_password")
        assert auth_result is None

def test_update_password_success(self, auth_service, regular_user, db_session):

        success = auth_service.update_password(regular_user.id, "brand_new_password")
        assert success is True

        # Verify it can authenticate with new password
        db_session.refresh(regular_user)
        assert auth_service.authenticate_user(regular_user.email, "brand_new_password") is not None

def test_verify_admin_access(self, auth_service, regular_user, admin_user):

        assert auth_service.verify_admin_access(admin_user.id) is True
        assert auth_service.verify_admin_access(regular_user.id) is False

def test_google_oauth_linking(self, auth_service, regular_user, db_session):
        # Test linking to existing email
        user = auth_service.create_or_get_google_user(
            google_id="google_new",
            email=regular_user.email,
            avatar_url="https://avatar.com/1",
        )
        assert user.id == regular_user.id
        assert user.google_id == "google_new"
        assert user.email_verified is True

        # Test creating new
        new_user = auth_service.create_or_get_google_user(google_id="google_brand_new", email="brand_new@gmail.com")
        assert new_user.email == "brand_new@gmail.com"
        assert new_user.provider == "google"

def test_verify_email_success(self, auth_service, db_session):

        user = User(email="verify@example.com", verification_token="token_123")
        db_session.add(user)
        db_session.commit()

        success = auth_service.verify_email("token_123")
        assert success is True

        db_session.refresh(user)
        assert user.email_verified is True
        assert user.verification_token is None

def test_get_user_api_keys(self, auth_service, regular_user):

        auth_service.create_api_key(regular_user.id, "Key 1")
        auth_service.create_api_key(regular_user.id, "Key 2")

        keys = auth_service.get_user_api_keys(regular_user.id)
        assert len(keys) == 2