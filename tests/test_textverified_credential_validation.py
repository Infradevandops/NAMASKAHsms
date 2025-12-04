"""Credential validation and service enablement tests for TextVerified service.

Feature: textverified-integration
Property 2: Credential Validation
Validates: Requirements 1.4, 1.5
"""
import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch, MagicMock
import asyncio


class TestCredentialValidation:
    """Test TextVerified credential validation.
    
    Property 2: Credential Validation
    *For any* TextVerified service instance, if credentials are present and valid, 
    the service SHALL initialize successfully and set enabled flag to true.
    
    Validates: Requirements 1.4, 1.5
    """

    def test_valid_credentials_enable_service(self):
        """Test that valid credentials enable service.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'valid_key'
                mock_settings.textverified_email = 'valid@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify service is enabled
                assert service.enabled is True
                # Verify client is created
                assert service.client is not None

    def test_credentials_validated_by_connection_attempt(self):
        """Test that credentials are validated by attempting connection.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'valid_key'
                mock_settings.textverified_email = 'valid@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify TextVerified client was instantiated (connection attempt)
                mock_tv.TextVerified.assert_called_once_with(
                    api_key='valid_key',
                    api_username='valid@example.com'
                )

    def test_client_connection_maintained(self):
        """Test that active client connection is maintained.
        
        Validates: Requirement 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'valid_key'
                mock_settings.textverified_email = 'valid@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify client is stored and accessible
                assert service.client == mock_client
                # Verify client persists across accesses
                assert service.client == mock_client

    def test_enabled_flag_set_correctly(self):
        """Test that enabled flag is set based on validation result.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'valid_key'
                mock_settings.textverified_email = 'valid@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify enabled flag is True
                assert service.enabled is True
                assert isinstance(service.enabled, bool)

    def test_invalid_credentials_disable_service(self):
        """Test that invalid credentials disable service.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'invalid_key'
                mock_settings.textverified_email = 'invalid@example.com'
                # Simulate connection failure
                mock_tv.TextVerified.side_effect = Exception("Invalid credentials")
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify service is disabled
                assert service.enabled is False

    def test_connection_failure_logged(self):
        """Test that connection failure is logged.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                with patch('app.services.textverified_service.logger') as mock_logger:
                    mock_settings.textverified_api_key = 'invalid_key'
                    mock_settings.textverified_email = 'invalid@example.com'
                    mock_tv.TextVerified.side_effect = Exception("Connection failed")
                    
                    from app.services.textverified_service import TextVerifiedService
                    service = TextVerifiedService()
                    
                    # Verify error is logged
                    mock_logger.error.assert_called()

    def test_successful_validation_logged(self):
        """Test that successful validation is logged.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                with patch('app.services.textverified_service.logger') as mock_logger:
                    mock_settings.textverified_api_key = 'valid_key'
                    mock_settings.textverified_email = 'valid@example.com'
                    mock_client = Mock()
                    mock_tv.TextVerified.return_value = mock_client
                    
                    from app.services.textverified_service import TextVerifiedService
                    service = TextVerifiedService()
                    
                    # Verify success is logged
                    mock_logger.info.assert_called()


class TestCredentialValidationPropertyBased:
    """Property-based tests for credential validation.
    
    Property 2: Credential Validation
    *For any* TextVerified service instance, if credentials are present and valid, 
    the service SHALL initialize successfully and set enabled flag to true.
    
    Validates: Requirements 1.4, 1.5
    """

    @given(
        api_key=st.text(min_size=1, max_size=100),
        email=st.emails()
    )
    def test_valid_credentials_always_enable_service(self, api_key, email):
        """Property: Valid credentials always enable service.
        
        For any valid API key and email, the service should be enabled.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = api_key
                mock_settings.textverified_email = email
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Property: Service should be enabled
                assert service.enabled is True
                # Property: Client should be set
                assert service.client is not None

    @given(
        api_key=st.text(min_size=1, max_size=100),
        email=st.emails()
    )
    def test_credentials_used_for_connection(self, api_key, email):
        """Property: Credentials are used for connection attempt.
        
        For any credentials, they should be passed to TextVerified client.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = api_key
                mock_settings.textverified_email = email
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Property: Credentials should be passed to client
                mock_tv.TextVerified.assert_called_once_with(
                    api_key=api_key,
                    api_username=email
                )


class TestInvalidCredentialsHandling:
    """Test handling of invalid credentials.
    
    Validates: Requirements 1.4, 1.5
    """

    def test_connection_error_disables_service(self):
        """Test that connection error disables service.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_tv.TextVerified.side_effect = ConnectionError("Connection failed")
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify service is disabled
                assert service.enabled is False

    def test_authentication_error_disables_service(self):
        """Test that authentication error disables service.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'invalid_key'
                mock_settings.textverified_email = 'email@example.com'
                mock_tv.TextVerified.side_effect = Exception("Invalid API key")
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify service is disabled
                assert service.enabled is False

    def test_timeout_error_disables_service(self):
        """Test that timeout error disables service.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_tv.TextVerified.side_effect = TimeoutError("Connection timeout")
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify service is disabled
                assert service.enabled is False

    def test_no_exception_on_validation_failure(self):
        """Test that no exception is raised on validation failure.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_tv.TextVerified.side_effect = Exception("Validation failed")
                
                from app.services.textverified_service import TextVerifiedService
                
                # Should not raise exception
                try:
                    service = TextVerifiedService()
                    assert service.enabled is False
                except Exception as e:
                    pytest.fail(f"Exception raised on validation failure: {e}")


class TestEnabledFlagBehavior:
    """Test enabled flag behavior.
    
    Validates: Requirements 1.4, 1.5
    """

    def test_enabled_flag_is_boolean(self):
        """Test that enabled flag is always boolean.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify enabled is boolean
                assert isinstance(service.enabled, bool)

    def test_enabled_flag_persists(self):
        """Test that enabled flag persists across accesses.
        
        Validates: Requirements 1.4, 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify enabled flag persists
                assert service.enabled is True
                assert service.enabled is True
                assert service.enabled is True

    def test_enabled_flag_reflects_validation_result(self):
        """Test that enabled flag reflects validation result.
        
        Validates: Requirements 1.4, 1.5
        """
        # Test with valid credentials
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'valid_key'
                mock_settings.textverified_email = 'valid@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service_valid = TextVerifiedService()
                assert service_valid.enabled is True
        
        # Test with invalid credentials
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'invalid_key'
                mock_settings.textverified_email = 'invalid@example.com'
                mock_tv.TextVerified.side_effect = Exception("Invalid")
                
                from app.services.textverified_service import TextVerifiedService
                service_invalid = TextVerifiedService()
                assert service_invalid.enabled is False


class TestClientConnectionMaintenance:
    """Test client connection maintenance.
    
    Validates: Requirement 1.5
    """

    def test_client_stored_in_service(self):
        """Test that client is stored in service instance.
        
        Validates: Requirement 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify client is stored
                assert service.client is mock_client

    def test_client_accessible_throughout_lifetime(self):
        """Test that client is accessible throughout service lifetime.
        
        Validates: Requirement 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_client = Mock()
                mock_tv.TextVerified.return_value = mock_client
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify client is accessible multiple times
                client1 = service.client
                client2 = service.client
                client3 = service.client
                
                assert client1 is client2
                assert client2 is client3
                assert client1 is mock_client

    def test_client_not_created_on_validation_failure(self):
        """Test that client is not created on validation failure.
        
        Validates: Requirement 1.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key'
                mock_settings.textverified_email = 'email@example.com'
                mock_tv.TextVerified.side_effect = Exception("Validation failed")
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify client is not set
                assert not hasattr(service, 'client') or service.client is None
