"""Expanded unit tests for auth service"""
import pytest
from unittest.mock import Mock, patch
from app.services.auth_service import AuthService
from app.models.user import User

class TestAuthServiceExpanded:
    
    @pytest.fixture
    def auth_service(self, db_session):
        return AuthService(db_session)
    
    def test_register_user_success(self, auth_service, db_session):
        """Test successful user registration"""
        result = auth_service.register_user(
            email="newuser@test.com",
            password="SecurePass123!"
        )
        assert result['success'] == True
        assert 'user_id' in result
    
    def test_register_duplicate_email(self, auth_service, db_session, regular_user):
        """Test registration with existing email"""
        result = auth_service.register_user(
            email=regular_user.email,
            password="AnotherPass123!"
        )
        assert result['success'] == False
    
    def test_login_valid_credentials(self, auth_service, regular_user):
        """Test login with valid credentials"""
        result = auth_service.authenticate(
            email=regular_user.email,
            password="testpass123"
        )
        assert result['success'] == True
        assert 'access_token' in result
    
    def test_login_invalid_password(self, auth_service, regular_user):
        """Test login with wrong password"""
        result = auth_service.authenticate(
            email=regular_user.email,
            password="wrongpassword"
        )
        assert result['success'] == False
    
    def test_login_nonexistent_user(self, auth_service):
        """Test login with non-existent email"""
        result = auth_service.authenticate(
            email="nonexistent@test.com",
            password="anypassword"
        )
        assert result['success'] == False
    
    def test_verify_token_valid(self, auth_service, regular_user):
        """Test token verification"""
        login = auth_service.authenticate(regular_user.email, "testpass123")
        token = login['access_token']
        
        result = auth_service.verify_token(token)
        assert result['valid'] == True
        assert result['user_id'] == regular_user.id
    
    def test_verify_token_invalid(self, auth_service):
        """Test invalid token"""
        result = auth_service.verify_token("invalid_token_123")
        assert result['valid'] == False
    
    def test_refresh_token(self, auth_service, regular_user):
        """Test token refresh"""
        login = auth_service.authenticate(regular_user.email, "testpass123")
        refresh_token = login.get('refresh_token')
        
        if refresh_token:
            result = auth_service.refresh_access_token(refresh_token)
            assert 'access_token' in result
    
    def test_password_reset_request(self, auth_service, regular_user):
        """Test password reset request"""
        result = auth_service.request_password_reset(regular_user.email)
        assert result['success'] == True
    
    def test_password_reset_invalid_email(self, auth_service):
        """Test password reset with invalid email"""
        result = auth_service.request_password_reset("invalid@test.com")
        assert result['success'] == False
    
    def test_weak_password_rejection(self, auth_service):
        """Test registration with weak password"""
        result = auth_service.register_user(
            email="test@test.com",
            password="123"
        )
        assert result['success'] == False
    
    def test_invalid_email_format(self, auth_service):
        """Test registration with invalid email"""
        result = auth_service.register_user(
            email="notanemail",
            password="SecurePass123!"
        )
        assert result['success'] == False
