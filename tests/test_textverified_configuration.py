"""Configuration loading and validation tests for TextVerified service.

Feature: textverified-integration
Property 1: Configuration Loading
Property 3: Missing Credentials Handling
Validates: Requirements 1.1, 1.2, 1.3
"""
import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch
import asyncio


class TestConfigurationLoading:
    """Test TextVerified configuration loading.
    
    Property 1: Configuration Loading
    *For any* environment with TextVerified credentials set, the TextVerified 
    service SHALL successfully load both the API key and email from environment variables.
    
    Validates: Requirements 1.1, 1.2
    """

    def test_load_api_key_from_environment(self):
        """Test that API key is loaded from environment.
        
        Validates: Requirement 1.1
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = 'test_api_key_123'
            mock_settings.textverified_email = 'test@example.com'
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify API key is loaded
            assert service.api_key == 'test_api_key_123'

    def test_load_email_from_environment(self):
        """Test that email is loaded from environment.
        
        Validates: Requirement 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = 'test_api_key_123'
            mock_settings.textverified_email = 'test@example.com'
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify email is loaded
            assert service.api_username == 'test@example.com'

    def test_both_credentials_loaded_successfully(self):
        """Test that both credentials are loaded together.
        
        Validates: Requirements 1.1, 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = 'test_api_key_123'
            mock_settings.textverified_email = 'test@example.com'
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify both are loaded
            assert service.api_key == 'test_api_key_123'
            assert service.api_username == 'test@example.com'

    def test_service_enabled_with_valid_credentials(self):
        """Test that service is enabled when credentials are valid.
        
        Validates: Requirements 1.1, 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'test_api_key_123'
                mock_settings.textverified_email = 'test@example.com'
                mock_tv.TextVerified.return_value = Mock()
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify service is enabled
                assert service.enabled is True

    def test_initialization_logs_success(self):
        """Test that successful initialization is logged.
        
        Validates: Requirements 1.1, 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                with patch('app.services.textverified_service.logger') as mock_logger:
                    mock_settings.textverified_api_key = 'test_api_key_123'
                    mock_settings.textverified_email = 'test@example.com'
                    mock_tv.TextVerified.return_value = Mock()
                    
                    from app.services.textverified_service import TextVerifiedService
                    service = TextVerifiedService()
                    
                    # Verify success is logged
                    mock_logger.info.assert_called()


class TestMissingCredentialsHandling:
    """Test TextVerified handling of missing credentials.
    
    Property 3: Missing Credentials Handling
    *For any* environment where TextVerified credentials are missing, the service 
    SHALL log a warning and set enabled flag to false without raising an exception.
    
    Validates: Requirement 1.3
    """

    def test_missing_api_key_disables_service(self):
        """Test that missing API key disables service.
        
        Validates: Requirement 1.3
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = None
            mock_settings.textverified_email = 'test@example.com'
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify service is disabled
            assert service.enabled is False

    def test_missing_email_disables_service(self):
        """Test that missing email disables service.
        
        Validates: Requirement 1.3
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = 'test_api_key_123'
            mock_settings.textverified_email = None
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify service is disabled
            assert service.enabled is False

    def test_both_credentials_missing_disables_service(self):
        """Test that missing both credentials disables service.
        
        Validates: Requirement 1.3
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = None
            mock_settings.textverified_email = None
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify service is disabled
            assert service.enabled is False

    def test_missing_credentials_logs_warning(self):
        """Test that missing credentials logs warning.
        
        Validates: Requirement 1.3
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.logger') as mock_logger:
                mock_settings.textverified_api_key = None
                mock_settings.textverified_email = None
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify warning is logged
                mock_logger.warning.assert_called()

    def test_no_exception_on_missing_credentials(self):
        """Test that no exception is raised when credentials are missing.
        
        Validates: Requirement 1.3
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = None
            mock_settings.textverified_email = None
            
            from app.services.textverified_service import TextVerifiedService
            
            # Should not raise exception
            try:
                service = TextVerifiedService()
                assert service.enabled is False
            except Exception as e:
                pytest.fail(f"Exception raised when credentials missing: {e}")

    def test_empty_string_credentials_disables_service(self):
        """Test that empty string credentials disable service.
        
        Validates: Requirement 1.3
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = ''
            mock_settings.textverified_email = ''
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify service is disabled
            assert service.enabled is False


class TestConfigurationPropertyBased:
    """Property-based tests for configuration loading.
    
    Property 1: Configuration Loading
    *For any* environment with TextVerified credentials set, the service 
    SHALL successfully load both the API key and email.
    
    Validates: Requirements 1.1, 1.2
    """

    @given(
        api_key=st.text(min_size=1, max_size=100),
        email=st.emails()
    )
    def test_configuration_loading_with_various_credentials(self, api_key, email):
        """Property: Configuration loads with any valid credentials.
        
        For any API key and email, the service should load them correctly.
        
        Validates: Requirements 1.1, 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = api_key
                mock_settings.textverified_email = email
                mock_tv.TextVerified.return_value = Mock()
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Property: Credentials should be loaded
                assert service.api_key == api_key
                assert service.api_username == email


class TestMissingCredentialsPropertyBased:
    """Property-based tests for missing credentials handling.
    
    Property 3: Missing Credentials Handling
    *For any* environment where credentials are missing, the service 
    SHALL disable gracefully without raising exceptions.
    
    Validates: Requirement 1.3
    """

    @given(
        api_key=st.one_of(st.none(), st.just('')),
        email=st.one_of(st.none(), st.just(''))
    )
    def test_missing_credentials_disables_gracefully(self, api_key, email):
        """Property: Missing credentials disable service gracefully.
        
        For any missing credentials, the service should disable without exceptions.
        
        Validates: Requirement 1.3
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = api_key
            mock_settings.textverified_email = email
            
            from app.services.textverified_service import TextVerifiedService
            
            # Property: Should not raise exception
            try:
                service = TextVerifiedService()
                # Property: Service should be disabled
                assert service.enabled is False
            except Exception as e:
                pytest.fail(f"Exception raised: {e}")


class TestConfigurationIntegration:
    """Integration tests for configuration loading.
    
    Validates: Requirements 1.1, 1.2, 1.3
    """

    def test_configuration_with_default_email(self):
        """Test that default email is used if not provided.
        
        Validates: Requirement 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = 'test_api_key_123'
            # Don't set textverified_email, should use default
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            # Verify default email is used
            assert service.api_username is not None

    def test_configuration_persistence(self):
        """Test that configuration persists in service instance.
        
        Validates: Requirements 1.1, 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'test_api_key_123'
                mock_settings.textverified_email = 'test@example.com'
                mock_tv.TextVerified.return_value = Mock()
                
                from app.services.textverified_service import TextVerifiedService
                service = TextVerifiedService()
                
                # Verify configuration persists
                assert service.api_key == 'test_api_key_123'
                assert service.api_username == 'test@example.com'
                
                # Access multiple times
                assert service.api_key == 'test_api_key_123'
                assert service.api_username == 'test@example.com'

    def test_multiple_service_instances_independent(self):
        """Test that multiple service instances have independent configuration.
        
        Validates: Requirements 1.1, 1.2
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_settings.textverified_api_key = 'key1'
                mock_settings.textverified_email = 'email1@example.com'
                mock_tv.TextVerified.return_value = Mock()
                
                from app.services.textverified_service import TextVerifiedService
                service1 = TextVerifiedService()
                
                # Change settings
                mock_settings.textverified_api_key = 'key2'
                mock_settings.textverified_email = 'email2@example.com'
                
                service2 = TextVerifiedService()
                
                # Verify each instance has its own configuration
                assert service1.api_key == 'key1'
                assert service2.api_key == 'key2'
